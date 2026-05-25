import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import UploadResponse
from app.services import upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])


async def _save_and_import(
    file: UploadFile,
    session: AsyncSession,
    importer,
) -> UploadResponse:
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    settings.uploads_path.mkdir(parents=True, exist_ok=True)
    dest = settings.uploads_path / file.filename
    dest.write_bytes(content)

    try:
        count = await importer(session, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return UploadResponse(
        filename=file.filename,
        rows_imported=count,
        message=f"Successfully imported {count} rows",
    )


@router.post("/transactions", response_model=UploadResponse)
async def upload_transactions(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    return await _save_and_import(file, session, upload_service.import_transactions)


@router.post("/settlements", response_model=UploadResponse)
async def upload_settlements(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    return await _save_and_import(file, session, upload_service.import_settlements)


@router.post("/refunds", response_model=UploadResponse)
async def upload_refunds(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db),
):
    return await _save_and_import(file, session, upload_service.import_refunds)


@router.post("/sample-data", response_model=dict)
async def load_sample_data(session: AsyncSession = Depends(get_db)):
    sample_dir = settings.sample_data_path
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample data directory not found")
    try:
        tx = await upload_service.load_sample_file(session, sample_dir, "transactions.csv", upload_service.import_transactions)
        st = await upload_service.load_sample_file(session, sample_dir, "settlements.csv", upload_service.import_settlements)
        rf = await upload_service.load_sample_file(session, sample_dir, "refunds.csv", upload_service.import_refunds)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"transactions": tx, "settlements": st, "refunds": rf, "message": "Sample data loaded"}
