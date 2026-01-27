"""Pydantic models for API request and response schemas."""

from datetime import UTC, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


def _utcnow() -> datetime:
    """Get current UTC time in a timezone-aware format."""
    return datetime.now(UTC)


class GenerateRequest(BaseModel):
    """Request body for starting flashcard generation.

    Attributes:
        start_page: First page to process (1-indexed, inclusive)
        end_page: Last page to process (1-indexed, inclusive)
        difficulty: Difficulty level for generated flashcards
        cards_per_page: Number of flashcards to generate per page
    """

    start_page: int = Field(ge=1, description="First page to process (1-indexed)")
    end_page: int = Field(ge=1, description="Last page to process (1-indexed)")
    difficulty: Literal["beginner", "intermediate", "advanced"] = Field(
        default="intermediate", description="Difficulty level for flashcards"
    )
    cards_per_page: int = Field(
        default=1, ge=1, le=10, description="Number of flashcards per page"
    )

    @model_validator(mode="after")
    def validate_page_range(self) -> "GenerateRequest":
        """Ensure start_page <= end_page."""
        if self.start_page > self.end_page:
            raise ValueError("start_page must be less than or equal to end_page")
        return self


class UploadResponse(BaseModel):
    """Response after successful PDF upload.

    Attributes:
        file_id: Unique identifier for the uploaded file
        filename: Original filename
        size: File size in bytes
        uploaded_at: Timestamp of upload
    """

    file_id: str
    filename: str
    size: int
    uploaded_at: datetime


class JobResponse(BaseModel):
    """Response containing job status and progress.

    Attributes:
        job_id: Unique identifier for the job
        file_id: ID of the uploaded file being processed
        status: Current job status
        progress: Progress percentage (0.0-1.0)
        current_page: Page currently being processed
        total_pages: Total pages to process
        message: Current status message
        created_at: Job creation timestamp
        completed_at: Job completion timestamp (if completed)
        error: Error message (if failed)
    """

    job_id: str
    file_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    progress: float = Field(ge=0.0, le=1.0, description="Progress percentage (0.0-1.0)")
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error response format.

    Attributes:
        detail: Human-readable error message
        error_code: Machine-readable error code
        timestamp: When the error occurred
    """

    detail: str
    error_code: str
    timestamp: datetime = Field(default_factory=_utcnow)


class WebSocketMessage(BaseModel):
    """WebSocket message for progress updates.

    Attributes:
        type: Message type (progress, complete, error)
        progress: Current progress (0.0-1.0)
        current_page: Page being processed
        total_pages: Total pages
        message: Status message
        status: Job status (for complete/error types)
        error: Error message (for error type)
    """

    type: Literal["progress", "complete", "error"]
    progress: Optional[float] = None
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    message: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
