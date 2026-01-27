"""Download endpoint for retrieving generated Anki decks."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from src.api.services.file_storage import FileStorage
from src.api.services.job_manager import JobManager, get_job_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["download"])


@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),  # noqa: B008
):
    """Download the generated Anki deck for a completed job.

    Returns the .apkg file that can be imported into Anki.

    Args:
        job_id: The unique job identifier
        job_manager: Job state manager

    Returns:
        FileResponse with the .apkg file

    Raises:
        HTTPException 404: If job_id doesn't exist
        HTTPException 400: If job is not completed yet
        HTTPException 500: If output file is missing
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    if job.status != "completed":
        if job.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=f"Job failed: {job.error or 'Unknown error'}",
            )
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed yet. Current status: {job.status}",
        )

    # Verify output file exists
    output_path = FileStorage.get_output_path(job_id)
    if not output_path.exists():
        logger.error(f"Output file missing for completed job: {job_id}")
        raise HTTPException(
            status_code=500,
            detail="Output file not found. This is an internal error.",
        )

    # Generate a meaningful filename from the original upload
    filename = f"flashcards_{job_id[:8]}.apkg"

    logger.info(f"Serving download for job: {job_id}")

    return FileResponse(
        path=output_path,
        media_type="application/octet-stream",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
