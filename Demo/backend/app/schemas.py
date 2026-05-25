from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ReconcileRunResponse(BaseModel):
    report_id: str
    status: str
    message: str


class ReportSummary(BaseModel):
    report_id: str
    generated_at: datetime
    matched_count: int
    mismatch_count: int
    duplicate_count: int
    orphan_refund_count: int
    reconciliation_health_score: float


class DashboardSummary(BaseModel):
    total_transactions: int
    total_settlements: int
    total_refunds: int
    latest_report: ReportSummary | None
    matched_count: int
    mismatch_count: int
    duplicate_count: int
    orphan_refund_count: int
    reconciliation_health_score: float
    matched_vs_mismatched: list[dict[str, Any]]


class UploadResponse(BaseModel):
    filename: str
    rows_imported: int
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str
