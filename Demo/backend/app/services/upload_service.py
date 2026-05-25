"""CSV upload and persistence service."""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Refund, Settlement, Transaction

logger = logging.getLogger(__name__)


def _parse_datetime(value) -> datetime:
    if pd.isna(value):
        return datetime.utcnow()
    ts = pd.to_datetime(value, utc=True)
    if ts.tzinfo:
        return ts.replace(tzinfo=None)
    return ts.to_pydatetime()


async def import_transactions(session: AsyncSession, content: bytes, replace: bool = True) -> int:
    df = pd.read_csv(BytesIO(content))
    required = {"txn_id", "customer_id", "order_id", "amount", "payment_status", "payment_method", "txn_timestamp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if replace:
        await session.execute(delete(Transaction))

    count = 0
    for _, row in df.iterrows():
        session.add(
            Transaction(
                txn_id=str(row["txn_id"]),
                customer_id=str(row["customer_id"]),
                order_id=str(row["order_id"]),
                amount=Decimal(str(row["amount"])),
                currency=str(row.get("currency", "USD")),
                payment_status=str(row["payment_status"]),
                payment_method=str(row["payment_method"]),
                txn_timestamp=_parse_datetime(row["txn_timestamp"]),
                gateway_reference=str(row["gateway_reference"]) if pd.notna(row.get("gateway_reference")) else None,
            )
        )
        count += 1
    await session.flush()
    logger.info("Imported %d transactions", count)
    return count


async def import_settlements(session: AsyncSession, content: bytes, replace: bool = True) -> int:
    df = pd.read_csv(BytesIO(content))
    required = {"settlement_id", "settled_amount", "settlement_status", "settlement_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if replace:
        await session.execute(delete(Settlement))

    count = 0
    for _, row in df.iterrows():
        txn_val = row.get("txn_id")
        txn_id = None if pd.isna(txn_val) or str(txn_val).strip() == "" else str(txn_val)
        session.add(
            Settlement(
                settlement_id=str(row["settlement_id"]),
                txn_id=txn_id,
                settled_amount=Decimal(str(row["settled_amount"])),
                settlement_status=str(row["settlement_status"]),
                settlement_date=_parse_datetime(row["settlement_date"]),
                gateway_fee=Decimal(str(row.get("gateway_fee", 0))),
                tax=Decimal(str(row.get("tax", 0))),
                bank_reference=str(row["bank_reference"]) if pd.notna(row.get("bank_reference")) else None,
            )
        )
        count += 1
    await session.flush()
    logger.info("Imported %d settlements", count)
    return count


async def import_refunds(session: AsyncSession, content: bytes, replace: bool = True) -> int:
    df = pd.read_csv(BytesIO(content))
    required = {"refund_id", "txn_id", "refund_amount", "refund_date"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if replace:
        await session.execute(delete(Refund))

    count = 0
    for _, row in df.iterrows():
        session.add(
            Refund(
                refund_id=str(row["refund_id"]),
                txn_id=str(row["txn_id"]),
                refund_amount=Decimal(str(row["refund_amount"])),
                refund_date=_parse_datetime(row["refund_date"]),
            )
        )
        count += 1
    await session.flush()
    logger.info("Imported %d refunds", count)
    return count


async def load_sample_file(session: AsyncSession, sample_dir: Path, filename: str, importer) -> int:
    path = sample_dir / filename
    if not path.exists():
        raise FileNotFoundError(f"Sample file not found: {path}")
    content = path.read_bytes()
    return await importer(session, content, replace=True)
