import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import report_service

router = APIRouter(prefix="/export", tags=["Export"])

_CSV_KEYS = {
    "mismatch": ("mismatches", "mismatch_report.csv"),
    "duplicate": ("duplicates", "duplicate_report.csv"),
    "orphan": ("orphan_refunds", "orphan_refund_report.csv"),
}


def _csv_response(rows: list, filename: str) -> StreamingResponse:
    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/report/json")
async def export_report_json(
    report_id: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    if report_id:
        report = await report_service.get_report_by_id(session, report_id)
    else:
        report = await report_service.get_latest_report(session)
    if not report:
        raise HTTPException(status_code=404, detail="No report available")

    path = report_service.resolve_report_json_path(report)
    if path:
        return FileResponse(path, media_type="application/json", filename="reconciliation_report.json")

    data = report_service.load_report_json(report)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="Report file not found. Run reconciliation again after deploy.",
        )
    return JSONResponse(content=data)


@router.get("/report/csv")
async def export_report_csv(
    report_type: str = "mismatch",
    report_id: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    if report_type not in _CSV_KEYS:
        raise HTTPException(status_code=400, detail=f"report_type must be one of {list(_CSV_KEYS.keys())}")

    if report_id:
        report = await report_service.get_report_by_id(session, report_id)
    else:
        report = await report_service.get_latest_report(session)
    if not report:
        raise HTTPException(status_code=404, detail="No report available")

    _, filename = _CSV_KEYS[report_type]
    path = report_service.resolve_report_csv_path(report, filename)
    if path:
        return FileResponse(path, media_type="text/csv", filename=filename)

    data = report_service.load_report_json(report)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="CSV report not found. Run reconciliation again after deploy.",
        )
    rows_key, _ = _CSV_KEYS[report_type]
    return _csv_response(data.get(rows_key, []), filename)
