"""Upload endpoint for PDF files."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, File, UploadFile

from src.api.models.schemas import UploadResponse
from src.api.services.file_storage import FileStorage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to upload"),  # noqa: B008
):
    """Upload a PDF file for flashcard generation.

    The uploaded file is validated (must be PDF, max 50MB) and stored
    with a unique identifier for later processing.

    Args:
        file: The PDF file to upload

    Returns:
        UploadResponse with file_id and metadata

    Raises:
        HTTPException 400: If file is not a PDF or exceeds size limit
        HTTPException 500: If upload fails
    """
    # Validate file type
    FileStorage.validate_pdf(file)

    # Save file and get ID
    file_id, file_path = await FileStorage.save_upload(file)

    logger.info(f"Uploaded file: {file.filename} as {file_id}")

    return UploadResponse(
        file_id=file_id,
        filename=file.filename or "unknown.pdf",
        size=file_path.stat().st_size,
        uploaded_at=datetime.now(UTC),
    )
