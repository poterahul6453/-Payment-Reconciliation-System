import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session, get_db
from app.schemas import ReconcileRunResponse
from app.services.reconciliation_engine import ReconciliationEngine
from app.services import report_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reconcile", tags=["Reconciliation"])

_reconcile_status: dict[str, str] = {}


async def _run_reconciliation_job(report_id: str):
    async with async_session() as session:
        try:
            engine = ReconciliationEngine(session)
            engine.report_id = report_id
            await engine.run()
            await session.commit()
            _reconcile_status[report_id] = "completed"
        except Exception as exc:
            logger.exception("Reconciliation job failed: %s", exc)
            await session.rollback()
            _reconcile_status[report_id] = f"failed: {exc}"


@router.post("/run", response_model=ReconcileRunResponse)
async def run_reconciliation(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    import uuid

    report_id = str(uuid.uuid4())
    _reconcile_status[report_id] = "running"

    async def job():
        await _run_reconciliation_job(report_id)

    background_tasks.add_task(job)
    return ReconcileRunResponse(
        report_id=report_id,
        status="running",
        message="Reconciliation job started. Poll GET /reconcile/report/{report_id} for results.",
    )


@router.post("/run-sync", response_model=dict)
async def run_reconciliation_sync(session: AsyncSession = Depends(get_db)):
    """Synchronous reconciliation for tests and immediate results."""
    engine = ReconciliationEngine(session)
    report = await engine.run()
    return {"report_id": engine.report_id, "summary": report["summary"]}


@router.get("/report/{report_id}")
async def get_report(report_id: str, session: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    status = _reconcile_status.get(report_id)
    db_report = await report_service.get_report_by_id(session, report_id)
    if not db_report:
        if status == "running":
            return {"report_id": report_id, "status": "running", "message": "Reconciliation in progress"}
        raise HTTPException(status_code=404, detail="Report not found")

    data = report_service.load_report_json(db_report)
    if not data:
        raise HTTPException(status_code=404, detail="Report file not found")
    return {"report_id": report_id, "status": "completed", **data}
