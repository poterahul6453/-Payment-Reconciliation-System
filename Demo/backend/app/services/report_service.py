"""Report retrieval and dashboard analytics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ReconciliationReport, Refund, Settlement, Transaction


async def get_latest_report(session: AsyncSession) -> ReconciliationReport | None:
    result = await session.execute(
        select(ReconciliationReport).order_by(desc(ReconciliationReport.generated_at)).limit(1)
    )
    return result.scalar_one_or_none()


async def get_report_by_id(session: AsyncSession, report_id: str) -> ReconciliationReport | None:
    result = await session.execute(
        select(ReconciliationReport).where(ReconciliationReport.report_id == report_id)
    )
    return result.scalar_one_or_none()


def load_report_json(report: ReconciliationReport) -> dict[str, Any] | None:
    if not report.report_json_path:
        return None
    path = Path(report.report_json_path)
    if not path.exists():
        alt = settings.reports_path / report.report_id / "reconciliation_report.json"
        path = alt if alt.exists() else path
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


async def dashboard_summary(session: AsyncSession) -> dict[str, Any]:
    txn_count = await session.scalar(select(func.count()).select_from(Transaction)) or 0
    stl_count = await session.scalar(select(func.count()).select_from(Settlement)) or 0
    ref_count = await session.scalar(select(func.count()).select_from(Refund)) or 0
    latest = await get_latest_report(session)

    matched = mismatch = duplicate = orphan = 0
    health = 0.0
    pie_data = [{"name": "Matched", "value": 0}, {"name": "Mismatched", "value": 0}]

    if latest:
        matched = latest.matched_count
        mismatch = latest.mismatch_count
        duplicate = latest.duplicate_count
        orphan = latest.orphan_refund_count
        health = float(latest.reconciliation_health_score)
        pie_data = [
            {"name": "Matched", "value": matched},
            {"name": "Mismatched", "value": mismatch},
        ]

    return {
        "total_transactions": txn_count,
        "total_settlements": stl_count,
        "total_refunds": ref_count,
        "latest_report": {
            "report_id": latest.report_id,
            "generated_at": latest.generated_at.isoformat(),
            "matched_count": latest.matched_count,
            "mismatch_count": latest.mismatch_count,
            "duplicate_count": latest.duplicate_count,
            "orphan_refund_count": latest.orphan_refund_count,
            "reconciliation_health_score": health,
        }
        if latest
        else None,
        "matched_count": matched,
        "mismatch_count": mismatch,
        "duplicate_count": duplicate,
        "orphan_refund_count": orphan,
        "reconciliation_health_score": health,
        "matched_vs_mismatched": pie_data,
    }


async def mismatch_trends(session: AsyncSession) -> list[dict[str, Any]]:
    report = await get_latest_report(session)
    if not report:
        return []
    data = load_report_json(report)
    if not data:
        return []
    categories = data.get("summary", {}).get("mismatch_by_category", {})
    return [{"category": k, "count": v} for k, v in categories.items()]


async def settlement_delays(session: AsyncSession) -> list[dict[str, Any]]:
    report = await get_latest_report(session)
    if not report:
        return []
    data = load_report_json(report)
    if not data:
        return []
    delays = data.get("settlement_delays", [])
    return [
        {"txn_id": d["txn_id"], "delay_days": d["delay_days"], "settlement_date": d.get("settlement_date", "")}
        for d in delays
    ]


async def duplicates_dashboard(session: AsyncSession) -> list[dict[str, Any]]:
    report = await get_latest_report(session)
    if not report:
        return []
    data = load_report_json(report)
    return data.get("duplicates", []) if data else []


async def orphan_refunds_dashboard(session: AsyncSession) -> list[dict[str, Any]]:
    report = await get_latest_report(session)
    if not report:
        return []
    data = load_report_json(report)
    return data.get("orphan_refunds", []) if data else []


async def daily_reconciliation_trend(session: AsyncSession) -> list[dict[str, Any]]:
    result = await session.execute(
        select(ReconciliationReport).order_by(ReconciliationReport.generated_at)
    )
    reports = result.scalars().all()
    return [
        {
            "date": r.generated_at.strftime("%Y-%m-%d"),
            "matched": r.matched_count,
            "mismatched": r.mismatch_count,
            "health_score": float(r.reconciliation_health_score),
        }
        for r in reports
    ]


async def monthly_analytics(session: AsyncSession) -> list[dict[str, Any]]:
    trend = await daily_reconciliation_trend(session)
    monthly: dict[str, dict] = {}
    for t in trend:
        month = t["date"][:7]
        if month not in monthly:
            monthly[month] = {"month": month, "matched": 0, "mismatched": 0, "runs": 0}
        monthly[month]["matched"] += t["matched"]
        monthly[month]["mismatched"] += t["mismatched"]
        monthly[month]["runs"] += 1
    return list(monthly.values())
