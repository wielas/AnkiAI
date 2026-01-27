"""Jobs endpoint for checking generation status."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.models.schemas import JobResponse
from src.api.services.job_manager import JobManager, get_job_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),  # noqa: B008
):
    """Get the status of a flashcard generation job.

    Returns current progress, status, and any error messages
    for the specified job.

    Args:
        job_id: The unique job identifier
        job_manager: Job state manager

    Returns:
        JobResponse with current status and progress

    Raises:
        HTTPException 404: If job_id doesn't exist
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")

    return JobResponse(
        job_id=job.job_id,
        file_id=job.file_id,
        status=job.status,
        progress=job.progress,
        current_page=job.current_page,
        total_pages=job.total_pages,
        message=job.message,
        created_at=job.created_at,
        completed_at=job.completed_at,
        error=job.error,
    )
