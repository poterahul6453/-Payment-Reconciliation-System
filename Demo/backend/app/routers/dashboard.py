from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import report_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
async def dashboard_summary(session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    return await report_service.dashboard_summary(session)


@router.get("/mismatch-trends")
async def mismatch_trends(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.mismatch_trends(session)


@router.get("/settlement-delays")
async def settlement_delays(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.settlement_delays(session)


@router.get("/duplicates")
async def duplicates(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.duplicates_dashboard(session)


@router.get("/orphan-refunds")
async def orphan_refunds(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.orphan_refunds_dashboard(session)


@router.get("/daily-trend")
async def daily_trend(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.daily_reconciliation_trend(session)


@router.get("/monthly-analytics")
async def monthly_analytics(session: AsyncSession = Depends(get_db)) -> list[dict[str, Any]]:
    return await report_service.monthly_analytics(session)
