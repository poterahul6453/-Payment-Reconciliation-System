from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.services import report_service

router = APIRouter(prefix="/export", tags=["Export"])


@router.get("/report/json")
async def export_report_json(
    report_id: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    if report_id:
        report = await report_service.get_report_by_id(session, report_id)
    else:
        report = await report_service.get_latest_report(session)
    if not report or not report.report_json_path:
        raise HTTPException(status_code=404, detail="No report available")
    path = Path(report.report_json_path)
    if not path.exists():
        path = settings.reports_path / report.report_id / "reconciliation_report.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(path, media_type="application/json", filename="reconciliation_report.json")


@router.get("/report/csv")
async def export_report_csv(
    report_type: str = "mismatch",
    report_id: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    if report_id:
        report = await report_service.get_report_by_id(session, report_id)
    else:
        report = await report_service.get_latest_report(session)
    if not report:
        raise HTTPException(status_code=404, detail="No report available")

    filenames = {
        "mismatch": "mismatch_report.csv",
        "duplicate": "duplicate_report.csv",
        "orphan": "orphan_refund_report.csv",
    }
    if report_type not in filenames:
        raise HTTPException(status_code=400, detail=f"report_type must be one of {list(filenames.keys())}")

    path = settings.reports_path / report.report_id / filenames[report_type]
    if not path.exists():
        raise HTTPException(status_code=404, detail="CSV report not found")
    return FileResponse(path, media_type="text/csv", filename=filenames[report_type])
