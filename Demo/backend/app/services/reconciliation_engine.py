"""Payment reconciliation engine using Pandas and Decimal."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ReconciliationReport, Refund, Settlement, Transaction

logger = logging.getLogger(__name__)

TOLERANCE = Decimal(str(settings.tolerance))


def _to_decimal(value: Any) -> Decimal:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return Decimal("0")
    return Decimal(str(value))


def _amounts_match(expected: Decimal, actual: Decimal) -> bool:
    return abs(expected - actual) <= TOLERANCE


def _health_score(matched: int, total_success: int, issues: int) -> float:
    if total_success == 0:
        return 100.0
    base = (matched / total_success) * 100
    penalty = min(issues * 2, 40)
    return round(max(0.0, min(100.0, base - penalty)), 2)


class ReconciliationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.report_id = str(uuid.uuid4())
        self.generated_at = datetime.now(timezone.utc)

    async def _load_dataframes(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        txns = (await self.session.execute(select(Transaction))).scalars().all()
        stls = (await self.session.execute(select(Settlement))).scalars().all()
        refs = (await self.session.execute(select(Refund))).scalars().all()

        txn_df = pd.DataFrame(
            [
                {
                    "txn_id": t.txn_id,
                    "customer_id": t.customer_id,
                    "order_id": t.order_id,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "payment_status": t.payment_status,
                    "payment_method": t.payment_method,
                    "txn_timestamp": t.txn_timestamp,
                    "gateway_reference": t.gateway_reference,
                }
                for t in txns
            ]
        )
        stl_df = pd.DataFrame(
            [
                {
                    "settlement_id": s.settlement_id,
                    "txn_id": s.txn_id,
                    "settled_amount": float(s.settled_amount),
                    "settlement_status": s.settlement_status,
                    "settlement_date": s.settlement_date,
                    "gateway_fee": float(s.gateway_fee),
                    "tax": float(s.tax),
                    "bank_reference": s.bank_reference,
                }
                for s in stls
            ]
        )
        ref_df = pd.DataFrame(
            [
                {
                    "refund_id": r.refund_id,
                    "txn_id": r.txn_id,
                    "refund_amount": float(r.refund_amount),
                    "refund_date": r.refund_date,
                }
                for r in refs
            ]
        )
        return txn_df, stl_df, ref_df

    def _run_reconciliation(
        self,
        txn_df: pd.DataFrame,
        stl_df: pd.DataFrame,
        ref_df: pd.DataFrame,
        period_end: datetime | None = None,
    ) -> dict[str, Any]:
        matched: list[dict] = []
        mismatches: list[dict] = []
        duplicates: list[dict] = []
        orphan_refunds: list[dict] = []
        settlement_delays: list[dict] = []

        if txn_df.empty and stl_df.empty and ref_df.empty:
            return self._empty_report()

        success_txns = (
            txn_df[txn_df["payment_status"].str.lower() == "success"].copy()
            if not txn_df.empty
            else pd.DataFrame()
        )
        txn_ids = set(success_txns["txn_id"].astype(str)) if not success_txns.empty else set()

        # Null transaction IDs in settlements
        if not stl_df.empty:
            null_txn = stl_df[stl_df["txn_id"].isna() | (stl_df["txn_id"].astype(str).str.strip() == "")]
            for _, row in null_txn.iterrows():
                mismatches.append(
                    {
                        "category": "null_transaction_id",
                        "txn_id": None,
                        "settlement_id": row["settlement_id"],
                        "expected_amount": None,
                        "actual_amount": float(row["settled_amount"]),
                        "detail": "Settlement has null or empty transaction ID",
                    }
                )

        valid_stl = stl_df.dropna(subset=["txn_id"]).copy() if not stl_df.empty else pd.DataFrame()
        if not valid_stl.empty:
            valid_stl["txn_id"] = valid_stl["txn_id"].astype(str)

        # Duplicate settlements
        if not valid_stl.empty:
            dup_groups = valid_stl.groupby("txn_id").filter(lambda x: len(x) > 1)
            for txn_id, group in dup_groups.groupby("txn_id"):
                rows = group.to_dict("records")
                duplicates.append(
                    {
                        "txn_id": txn_id,
                        "settlement_ids": [r["settlement_id"] for r in rows],
                        "settled_amounts": [r["settled_amount"] for r in rows],
                        "count": len(rows),
                    }
                )
                for r in rows:
                    mismatches.append(
                        {
                            "category": "duplicate_settlement",
                            "txn_id": txn_id,
                            "settlement_id": r["settlement_id"],
                            "expected_amount": None,
                            "actual_amount": r["settled_amount"],
                            "detail": f"Duplicate settlement for {txn_id}",
                        }
                    )

        # Group settlements by txn (excluding duplicates for amount logic — use first for match, flag rest)
        stl_by_txn: dict[str, list[dict]] = {}
        if not valid_stl.empty:
            for _, row in valid_stl.iterrows():
                tid = str(row["txn_id"])
                stl_by_txn.setdefault(tid, []).append(row.to_dict())

        processed_txn: set[str] = set()

        for _, txn in success_txns.iterrows():
            txn_id = str(txn["txn_id"])
            if txn_id in processed_txn:
                continue
            processed_txn.add(txn_id)

            expected = _to_decimal(txn["amount"])
            txn_time = pd.Timestamp(txn["txn_timestamp"])
            settlements = stl_by_txn.get(txn_id, [])

            if not settlements:
                mismatches.append(
                    {
                        "category": "missing_settlement",
                        "txn_id": txn_id,
                        "settlement_id": None,
                        "expected_amount": float(expected),
                        "actual_amount": None,
                        "detail": "No settlement found for successful transaction",
                    }
                )
                continue

            # Use first settlement for primary match; duplicates already flagged
            primary = settlements[0]
            actual = _to_decimal(primary["settled_amount"])
            stl_date = pd.Timestamp(primary["settlement_date"])
            delay_days = (stl_date - txn_time).days

            if delay_days > 2:
                settlement_delays.append(
                    {
                        "txn_id": txn_id,
                        "settlement_id": primary["settlement_id"],
                        "txn_timestamp": str(txn_time),
                        "settlement_date": str(stl_date),
                        "delay_days": delay_days,
                        "category": "delayed_settlement",
                    }
                )

            if txn_time.month != stl_date.month or txn_time.year != stl_date.year:
                mismatches.append(
                    {
                        "category": "cross_month_settlement",
                        "txn_id": txn_id,
                        "settlement_id": primary["settlement_id"],
                        "expected_amount": float(expected),
                        "actual_amount": float(actual),
                        "detail": f"Txn month {txn_time.month} vs settlement month {stl_date.month}",
                    }
                )

            diff = abs(expected - actual)
            if _amounts_match(expected, actual):
                category = "matched"
            elif diff <= Decimal("0.05") and not _amounts_match(expected, actual):
                category = "rounding_mismatch"
                mismatches.append(
                    {
                        "category": category,
                        "txn_id": txn_id,
                        "settlement_id": primary["settlement_id"],
                        "expected_amount": float(expected),
                        "actual_amount": float(actual),
                        "detail": f"Rounding difference of {float(diff)} exceeds tolerance {float(TOLERANCE)}",
                    }
                )
                continue
            elif actual < expected - TOLERANCE:
                category = "partial_settlement"
                mismatches.append(
                    {
                        "category": category,
                        "txn_id": txn_id,
                        "settlement_id": primary["settlement_id"],
                        "expected_amount": float(expected),
                        "actual_amount": float(actual),
                        "detail": f"Under-paid by {float(expected - actual)}",
                    }
                )
                continue
            elif actual > expected + TOLERANCE:
                category = "over_settlement"
                mismatches.append(
                    {
                        "category": category,
                        "txn_id": txn_id,
                        "settlement_id": primary["settlement_id"],
                        "expected_amount": float(expected),
                        "actual_amount": float(actual),
                        "detail": f"Over-paid by {float(actual - expected)}",
                    }
                )
                continue
            matched.append(
                {
                    "txn_id": txn_id,
                    "settlement_id": primary["settlement_id"],
                    "amount": float(expected),
                    "settled_amount": float(actual),
                    "delay_days": delay_days,
                }
            )

        # Failed transactions that were settled
        failed_txns = (
            txn_df[txn_df["payment_status"].str.lower() != "success"]
            if not txn_df.empty
            else pd.DataFrame()
        )
        for _, txn in failed_txns.iterrows():
            txn_id = str(txn["txn_id"])
            if txn_id in stl_by_txn:
                for stl in stl_by_txn[txn_id]:
                    mismatches.append(
                        {
                            "category": "failed_transaction_settled",
                            "txn_id": txn_id,
                            "settlement_id": stl["settlement_id"],
                            "expected_amount": float(txn["amount"]),
                            "actual_amount": stl["settled_amount"],
                            "detail": f"Transaction status {txn['payment_status']} but settlement exists",
                        }
                    )

        # Settlements without matching success txn
        if not valid_stl.empty:
            for txn_id in valid_stl["txn_id"].unique():
                if txn_id not in txn_ids:
                    group = valid_stl[valid_stl["txn_id"] == txn_id]
                    for _, row in group.iterrows():
                        mismatches.append(
                            {
                                "category": "orphan_settlement",
                                "txn_id": txn_id,
                                "settlement_id": row["settlement_id"],
                                "expected_amount": None,
                                "actual_amount": float(row["settled_amount"]),
                                "detail": "Settlement without matching successful transaction",
                            }
                        )

        # Orphan refunds
        if not ref_df.empty:
            all_txn_ids = set(txn_df["txn_id"].astype(str)) if not txn_df.empty else set()
            for _, ref in ref_df.iterrows():
                ref_txn = str(ref["txn_id"])
                if ref_txn not in all_txn_ids:
                    orphan_refunds.append(
                        {
                            "refund_id": ref["refund_id"],
                            "txn_id": ref_txn,
                            "refund_amount": float(ref["refund_amount"]),
                            "refund_date": str(ref["refund_date"]),
                            "detail": "Refund references non-existent transaction",
                        }
                    )
                    mismatches.append(
                        {
                            "category": "orphan_refund",
                            "txn_id": ref_txn,
                            "settlement_id": None,
                            "expected_amount": None,
                            "actual_amount": float(ref["refund_amount"]),
                            "detail": "Orphan refund",
                        }
                    )

        matched_count = len(matched)
        mismatch_count = len([m for m in mismatches if m["category"] != "duplicate_settlement"]) or len(mismatches)
        duplicate_count = len(duplicates)
        orphan_count = len(orphan_refunds)
        total_success = len(success_txns) if not success_txns.empty else 0
        issues = mismatch_count + duplicate_count + orphan_count
        health = _health_score(matched_count, total_success, issues)

        category_counts: dict[str, int] = {}
        for m in mismatches:
            cat = m["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "summary": {
                "report_id": self.report_id,
                "generated_at": self.generated_at.isoformat(),
                "total_transactions": len(txn_df),
                "successful_transactions": total_success,
                "total_settlements": len(stl_df),
                "total_refunds": len(ref_df),
                "matched_count": matched_count,
                "mismatch_count": mismatch_count,
                "duplicate_count": duplicate_count,
                "orphan_refund_count": orphan_count,
                "reconciliation_health_score": health,
                "mismatch_by_category": category_counts,
            },
            "matched_transactions": matched,
            "mismatches": mismatches,
            "duplicates": duplicates,
            "orphan_refunds": orphan_refunds,
            "settlement_delays": settlement_delays,
            "reconciliation_health_score": health,
        }

    def _empty_report(self) -> dict[str, Any]:
        return {
            "summary": {
                "report_id": self.report_id,
                "generated_at": self.generated_at.isoformat(),
                "total_transactions": 0,
                "successful_transactions": 0,
                "total_settlements": 0,
                "total_refunds": 0,
                "matched_count": 0,
                "mismatch_count": 0,
                "duplicate_count": 0,
                "orphan_refund_count": 0,
                "reconciliation_health_score": 100.0,
                "mismatch_by_category": {},
            },
            "matched_transactions": [],
            "mismatches": [],
            "duplicates": [],
            "orphan_refunds": [],
            "settlement_delays": [],
            "reconciliation_health_score": 100.0,
        }

    def _write_reports(self, report: dict[str, Any]) -> Path:
        reports_path = settings.reports_path
        reports_path.mkdir(parents=True, exist_ok=True)
        report_dir = reports_path / self.report_id
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / "reconciliation_report.json"
        with open(json_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        mismatches = report.get("mismatches", [])
        if mismatches:
            pd.DataFrame(mismatches).to_csv(report_dir / "mismatch_report.csv", index=False)
        else:
            pd.DataFrame(columns=["category", "txn_id", "detail"]).to_csv(
                report_dir / "mismatch_report.csv", index=False
            )

        duplicates = report.get("duplicates", [])
        if duplicates:
            pd.DataFrame(duplicates).to_csv(report_dir / "duplicate_report.csv", index=False)
        else:
            pd.DataFrame(columns=["txn_id", "count"]).to_csv(report_dir / "duplicate_report.csv", index=False)

        orphans = report.get("orphan_refunds", [])
        if orphans:
            pd.DataFrame(orphans).to_csv(report_dir / "orphan_refund_report.csv", index=False)
        else:
            pd.DataFrame(columns=["refund_id", "txn_id"]).to_csv(
                report_dir / "orphan_refund_report.csv", index=False
            )

        return json_path

    async def run(self, period_end: datetime | None = None) -> dict[str, Any]:
        txn_df, stl_df, ref_df = await self._load_dataframes()
        report = self._run_reconciliation(txn_df, stl_df, ref_df, period_end)
        json_path = self._write_reports(report)

        summary = report["summary"]
        db_report = ReconciliationReport(
            report_id=self.report_id,
            generated_at=self.generated_at,
            matched_count=summary["matched_count"],
            mismatch_count=summary["mismatch_count"],
            duplicate_count=summary["duplicate_count"],
            orphan_refund_count=summary["orphan_refund_count"],
            reconciliation_health_score=Decimal(str(summary["reconciliation_health_score"])),
            report_json_path=f"{self.report_id}/reconciliation_report.json",
        )
        self.session.add(db_report)
        await self.session.flush()

        logger.info("Reconciliation complete: %s health=%s", self.report_id, summary["reconciliation_health_score"])
        return report
