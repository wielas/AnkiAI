"""Generate endpoint for starting flashcard generation jobs."""

import asyncio
import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from src.api.models.schemas import GenerateRequest, JobResponse
from src.api.services.file_storage import FileStorage
from src.api.services.job_manager import JobManager, get_job_manager
from src.application.flashcard_service import FlashcardGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["generate"])


@router.post("/generate/{file_id}", response_model=JobResponse, status_code=202)
async def start_generation(
    file_id: str,
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    job_manager: JobManager = Depends(get_job_manager),  # noqa: B008
):
    """Start flashcard generation for an uploaded PDF.

    Creates a background job that processes the PDF and generates
    an Anki deck. Returns immediately with a job_id that can be
    used to track progress.

    Args:
        file_id: ID of the previously uploaded PDF
        request: Generation configuration (page range, difficulty, etc.)
        background_tasks: FastAPI background task handler
        job_manager: Job state manager

    Returns:
        JobResponse with job_id and initial status

    Raises:
        HTTPException 404: If the file_id doesn't exist
        HTTPException 400: If the configuration is invalid
    """
    # Validate file exists
    pdf_path = FileStorage.get_upload_path(file_id)
    if not pdf_path:
        raise HTTPException(status_code=404, detail=f"File not found: {file_id}")

    # Create job
    job = await job_manager.create_job(file_id, request.model_dump())

    # Start background task
    background_tasks.add_task(
        run_generation,
        job.job_id,
        pdf_path,
        request,
        job_manager,
    )

    logger.info(f"Started generation job: {job.job_id} for file: {file_id}")

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


async def run_generation(
    job_id: str,
    pdf_path: Path,
    config: GenerateRequest,
    job_manager: JobManager,
) -> None:
    """Background task that runs flashcard generation.

    This function runs the synchronous FlashcardGeneratorService in a
    thread pool executor, bridging the sync progress callback to async
    job state updates.

    Args:
        job_id: The job identifier
        pdf_path: Path to the PDF file
        config: Generation configuration
        job_manager: Job state manager for progress updates
    """
    loop = asyncio.get_event_loop()

    def progress_callback(current: int, total: int, message: str) -> None:
        """Bridge sync progress callback to async job manager.

        This function is called from the sync FlashcardGeneratorService
        running in a thread pool. It schedules async updates on the
        main event loop.
        """
        asyncio.run_coroutine_threadsafe(
            job_manager.update_progress(job_id, current, total, message),
            loop,
        )

    try:
        # Create fresh service instance
        service = FlashcardGeneratorService()
        output_path = FileStorage.get_output_path(job_id)

        logger.info(f"Starting generation for job: {job_id}")

        # Run synchronous service in thread pool
        result = await loop.run_in_executor(
            None,
            lambda: service.generate_flashcards(
                pdf_path=str(pdf_path),
                page_range=(config.start_page, config.end_page),
                cards_per_page=config.cards_per_page,
                difficulty=config.difficulty,
                output_path=str(output_path),
                on_progress=progress_callback,
            ),
        )

        # Check result status
        if result.status.value == "FAILED":
            await job_manager.fail_job(job_id, "All pages failed to generate")
        else:
            await job_manager.complete_job(job_id, str(output_path))
            logger.info(
                f"Job {job_id} completed: {result.total_success}/{result.total_attempted} pages, "
                f"{len(result.flashcards)} flashcards"
            )

    except Exception as e:
        logger.exception(f"Job {job_id} failed with error: {e}")
        await job_manager.fail_job(job_id, str(e))
