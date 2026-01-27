"""Job manager for tracking flashcard generation jobs.

NOTE: This implementation uses in-memory storage, which is acceptable
for learning/development but NOT production-ready. Production would use
a database (Redis, PostgreSQL) for persistence and multi-instance support.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware format."""
    return datetime.now(UTC)


@dataclass
class Job:
    """Represents a flashcard generation job.

    Attributes:
        job_id: Unique identifier for the job
        file_id: ID of the uploaded PDF file
        status: Current status (pending, processing, completed, failed)
        progress: Progress percentage (0.0-1.0)
        current_page: Page currently being processed
        total_pages: Total pages to process
        message: Current status message
        created_at: Job creation timestamp
        completed_at: Completion timestamp (if finished)
        error: Error message (if failed)
        result_path: Path to output .apkg file (if completed)
        config: Generation configuration
    """

    job_id: str
    file_id: str
    status: str = "pending"
    progress: float = 0.0
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime = field(default_factory=_utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result_path: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            "job_id": self.job_id,
            "file_id": self.file_id,
            "status": self.status,
            "progress": self.progress,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "message": self.message,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "error": self.error,
        }


class JobManager:
    """Thread-safe in-memory job state management.

    Handles job lifecycle:
    1. Create job (pending)
    2. Update progress during processing
    3. Complete or fail the job
    4. Broadcast updates to WebSocket clients

    Limitations (acceptable for learning, not production):
    - In-memory storage (lost on restart)
    - Single-instance only (no shared state)
    - No job cleanup (accumulates indefinitely)
    """

    def __init__(self):
        """Initialize job manager with empty state."""
        self._jobs: Dict[str, Job] = {}
        self._websockets: Dict[str, List[WebSocket]] = {}
        self._lock = asyncio.Lock()
        logger.info("JobManager initialized")

    async def create_job(self, file_id: str, config: Dict[str, Any]) -> Job:
        """Create a new job in pending state.

        Args:
            file_id: ID of the uploaded file
            config: Generation configuration

        Returns:
            The created Job instance
        """
        job_id = str(uuid.uuid4())
        job = Job(
            job_id=job_id,
            file_id=file_id,
            config=config,
            total_pages=config.get("end_page", 0) - config.get("start_page", 0) + 1,
        )

        async with self._lock:
            self._jobs[job_id] = job
            self._websockets[job_id] = []

        logger.info(f"Created job: {job_id} for file: {file_id}")
        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID.

        Args:
            job_id: The job identifier

        Returns:
            The Job instance if found, None otherwise
        """
        async with self._lock:
            return self._jobs.get(job_id)

    async def update_progress(
        self,
        job_id: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        """Update job progress and notify WebSocket clients.

        Args:
            job_id: The job identifier
            current: Current progress value (percentage 0-100)
            total: Total value (typically 100)
            message: Status message
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found for progress update: {job_id}")
                return

            # Update job state
            job.status = "processing"
            job.progress = current / total if total > 0 else 0.0
            job.message = message

            # Try to extract page number from message like "Processing page 5..."
            if "page" in message.lower():
                try:
                    parts = message.split()
                    for i, part in enumerate(parts):
                        if part.lower() == "page" and i + 1 < len(parts):
                            page_num = parts[i + 1].rstrip(".")
                            if page_num.isdigit():
                                job.current_page = int(page_num)
                                break
                except (ValueError, IndexError):
                    pass

        # Broadcast to WebSocket clients (outside lock to avoid deadlock)
        await self._broadcast_progress(
            job_id,
            {
                "type": "progress",
                "progress": job.progress,
                "current_page": job.current_page,
                "total_pages": job.total_pages,
                "message": message,
            },
        )

    async def complete_job(self, job_id: str, result_path: str) -> None:
        """Mark a job as completed.

        Args:
            job_id: The job identifier
            result_path: Path to the output .apkg file
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found for completion: {job_id}")
                return

            job.status = "completed"
            job.progress = 1.0
            job.completed_at = _utcnow()
            job.result_path = result_path
            job.message = "Generation complete"

        logger.info(f"Job completed: {job_id}")

        await self._broadcast_progress(
            job_id,
            {
                "type": "complete",
                "status": "completed",
                "progress": 1.0,
                "message": "Generation complete",
            },
        )

    async def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as failed.

        Args:
            job_id: The job identifier
            error: Error message describing the failure
        """
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job not found for failure: {job_id}")
                return

            job.status = "failed"
            job.completed_at = _utcnow()
            job.error = error
            job.message = f"Failed: {error}"

        logger.error(f"Job failed: {job_id} - {error}")

        await self._broadcast_progress(
            job_id,
            {
                "type": "error",
                "status": "failed",
                "error": error,
            },
        )

    async def register_websocket(self, job_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket connection for job updates.

        Args:
            job_id: The job identifier
            websocket: The WebSocket connection
        """
        async with self._lock:
            if job_id in self._websockets:
                self._websockets[job_id].append(websocket)
                logger.debug(f"WebSocket registered for job: {job_id}")

    async def unregister_websocket(self, job_id: str, websocket: WebSocket) -> None:
        """Unregister a WebSocket connection.

        Args:
            job_id: The job identifier
            websocket: The WebSocket connection to remove
        """
        async with self._lock:
            if job_id in self._websockets:
                try:
                    self._websockets[job_id].remove(websocket)
                    logger.debug(f"WebSocket unregistered for job: {job_id}")
                except ValueError:
                    pass

    async def _broadcast_progress(self, job_id: str, data: Dict[str, Any]) -> None:
        """Broadcast progress update to all connected WebSocket clients.

        Args:
            job_id: The job identifier
            data: Data to send to clients
        """
        async with self._lock:
            websockets = self._websockets.get(job_id, []).copy()

        disconnected = []
        for ws in websockets:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.debug(f"WebSocket send failed: {e}")
                disconnected.append(ws)

        # Clean up disconnected clients
        if disconnected:
            async with self._lock:
                for ws in disconnected:
                    try:
                        self._websockets[job_id].remove(ws)
                    except (ValueError, KeyError):
                        pass


# Singleton instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the singleton JobManager instance.

    Returns:
        The global JobManager instance
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
