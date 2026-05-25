import io
import logging
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import UploadResponse
from app.services import upload_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upload", tags=["Upload"])

SampleDataset = Literal["transactions", "settlements", "refunds"]

SAMPLE_CSV_FILES: dict[SampleDataset, str] = {
    "transactions": "transactions.csv",
    "settlements": "settlements.csv",
    "refunds": "refunds.csv",
}


def _sample_csv_path(dataset: SampleDataset) -> Path:
    sample_dir = settings.sample_data_path
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample data directory not found")
    path = sample_dir / SAMPLE_CSV_FILES[dataset]
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Sample file not found: {SAMPLE_CSV_FILES[dataset]}")
    return path


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


@router.get("/sample-data/download/all")
async def download_all_sample_csv():
    """Download transactions, settlements, and refunds sample CSVs as a zip."""
    sample_dir = settings.sample_data_path
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample data directory not found")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for filename in SAMPLE_CSV_FILES.values():
            path = sample_dir / filename
            if path.exists():
                archive.write(path, arcname=filename)
    if not buffer.getbuffer().nbytes:
        raise HTTPException(status_code=404, detail="No sample CSV files found")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="sample_data.zip"'},
    )


@router.get("/sample-data/download/{dataset}")
async def download_sample_csv(dataset: SampleDataset):
    """Download a single sample CSV (demo rows included)."""
    path = _sample_csv_path(dataset)
    return FileResponse(path, media_type="text/csv", filename=SAMPLE_CSV_FILES[dataset])


@router.get("/sample-data/template/{dataset}")
async def download_sample_template(dataset: SampleDataset):
    """Download a blank CSV with headers only for manual data entry."""
    path = _sample_csv_path(dataset)
    header = path.read_text(encoding="utf-8").splitlines()[0]
    filename = SAMPLE_CSV_FILES[dataset].replace(".csv", "_template.csv")
    return Response(
        content=f"{header}\n",
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
