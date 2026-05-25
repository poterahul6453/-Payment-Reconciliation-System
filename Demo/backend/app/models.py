from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    txn_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), nullable=False)
    order_id: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    payment_status: Mapped[str] = mapped_column(String(32), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    txn_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    gateway_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Settlement(Base):
    __tablename__ = "settlements"

    settlement_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    txn_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    settled_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    settlement_status: Mapped[str] = mapped_column(String(32), nullable=False)
    settlement_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    gateway_fee: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    tax: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0)
    bank_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)


class Refund(Base):
    __tablename__ = "refunds"

    refund_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    txn_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    refund_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    refund_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class ReconciliationReport(Base):
    __tablename__ = "reconciliation_reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    matched_count: Mapped[int] = mapped_column(default=0)
    mismatch_count: Mapped[int] = mapped_column(default=0)
    duplicate_count: Mapped[int] = mapped_column(default=0)
    orphan_refund_count: Mapped[int] = mapped_column(default=0)
    reconciliation_health_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    report_json_path: Mapped[str | None] = mapped_column(Text, nullable=True)
