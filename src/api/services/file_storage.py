"""File storage service for handling PDF uploads and output files.

NOTE: This implementation uses local filesystem storage, which is acceptable
for learning/development but NOT production-ready. Production would use
cloud storage (S3, R2, etc.) for persistence and scalability.
"""

import logging
import uuid
from pathlib import Path
from typing import Optional, Tuple

import aiofiles
from fastapi import HTTPException, UploadFile

logger = logging.getLogger(__name__)


class FileStorage:
    """Handles file upload and output storage operations.

    Limitations (acceptable for learning, not production):
    - Uses local filesystem (not persistent on serverless platforms)
    - No automatic cleanup (files accumulate)
    - Single-instance only (no shared storage)
    """

    UPLOAD_DIR = Path("./uploads")
    OUTPUT_DIR = Path("./outputs")
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_CONTENT_TYPES = {"application/pdf"}

    @classmethod
    def init_directories(cls) -> None:
        """Create upload and output directories if they don't exist."""
        cls.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(
            f"Initialized storage directories: {cls.UPLOAD_DIR}, {cls.OUTPUT_DIR}"
        )

    @classmethod
    def validate_pdf(cls, file: UploadFile) -> None:
        """Validate that the uploaded file is a PDF.

        Args:
            file: The uploaded file to validate

        Raises:
            HTTPException: If file is not a PDF or exceeds size limit
        """
        # Check content type
        if file.content_type not in cls.ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {file.content_type}. Only PDF files are allowed.",
            )

        # Check filename extension
        if file.filename and not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail="Invalid file extension. Only .pdf files are allowed.",
            )

    @classmethod
    async def save_upload(cls, file: UploadFile) -> Tuple[str, Path]:
        """Save an uploaded file and return its ID and path.

        Args:
            file: The uploaded file to save

        Returns:
            Tuple of (file_id, file_path)

        Raises:
            HTTPException: If file is too large or save fails
        """
        file_id = str(uuid.uuid4())
        file_path = cls.UPLOAD_DIR / f"{file_id}.pdf"

        try:
            # Read and validate size
            content = await file.read()
            if len(content) > cls.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {cls.MAX_FILE_SIZE // (1024 * 1024)}MB.",
                )

            # Save to disk
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)

            logger.info(f"Saved upload: {file_id} ({len(content)} bytes)")
            return file_id, file_path

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to save upload: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to save uploaded file."
            ) from e

    @classmethod
    def get_upload_path(cls, file_id: str) -> Optional[Path]:
        """Get the path to an uploaded file by ID.

        Args:
            file_id: The unique file identifier

        Returns:
            Path to the file if it exists, None otherwise
        """
        file_path = cls.UPLOAD_DIR / f"{file_id}.pdf"
        if file_path.exists():
            return file_path
        return None

    @classmethod
    def get_output_path(cls, job_id: str) -> Path:
        """Get the output path for a job's .apkg file.

        Args:
            job_id: The unique job identifier

        Returns:
            Path where the output should be saved
        """
        return cls.OUTPUT_DIR / f"{job_id}.apkg"

    @classmethod
    def output_exists(cls, job_id: str) -> bool:
        """Check if the output file for a job exists.

        Args:
            job_id: The unique job identifier

        Returns:
            True if the output file exists
        """
        return cls.get_output_path(job_id).exists()
