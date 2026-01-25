"""Document models for representing parsed documents and their metadata."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentFormat(Enum):
    """Supported document formats."""

    PDF = "pdf"
    DOCX = "docx"
    EPUB = "epub"


class ProcessingStatus(Enum):
    """Status of flashcard generation processing."""

    SUCCESS = "success"  # All pages processed successfully
    PARTIAL = "partial"  # Some pages failed, but we have results
    FAILED = "failed"  # No flashcards generated


@dataclass
class DocumentMetadata:
    """Metadata about the source document.

    Attributes:
        total_pages: Total number of pages in the document (required)
        file_size_bytes: Size of the file in bytes (required)
        file_format: Format of the document (required)
        title: Document title if available (optional)
        author: Document author if available (optional)
        subject: Document subject if available (optional)
        keywords: List of keywords associated with the document (optional)
        creation_date: When the document was created (optional)
        custom_metadata: Additional metadata fields for extensibility (optional)
    """

    # Always available (required)
    total_pages: int
    file_size_bytes: int
    file_format: DocumentFormat

    # Often available (optional)
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    creation_date: Optional[datetime] = None

    # Extensibility
    custom_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Represents a parsed document ready for processing.

    Attributes:
        content: Full extracted text from the document
        file_path: Path to the source file
        page_range: Tuple of (start_page, end_page) inclusive, 1-indexed
        metadata: Document metadata
        processed_at: Timestamp when the document was processed
    """

    # Core content
    content: str  # Full extracted text

    # Source information
    file_path: str
    page_range: tuple[int, int]  # (start_page, end_page) inclusive, 1-indexed

    # Metadata
    metadata: DocumentMetadata

    # Processing info
    processed_at: datetime = field(default_factory=datetime.now)

    def get_page_count(self) -> int:
        """Calculate number of pages in the range.

        Returns:
            Number of pages from start_page to end_page (inclusive)
        """
        return self.page_range[1] - self.page_range[0] + 1

    def __len__(self) -> int:
        """Return character count of content.

        Returns:
            Number of characters in the document content
        """
        return len(self.content)


@dataclass
class FlashcardResult:
    """Result from generating flashcard(s) for a single page.

    Attributes:
        flashcards: List of flashcard dicts, each with "question" and "answer" keys
        page_number: Page number this result is for (1-indexed)
        success: Whether generation was successful
        error_message: Error message if generation failed
        tokens_used: Total tokens used for this generation
        cost_usd: Estimated cost in USD for this generation
    """

    flashcards: List[Dict[str, str]]  # [{"question": "...", "answer": "..."}]
    page_number: int
    success: bool
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


@dataclass
class GenerationResult:
    """Result from full flashcard generation process.

    Attributes:
        flashcards: All successfully generated flashcards
        results: Detailed results for each page attempt
        total_attempted: Number of pages attempted
        total_success: Number of pages successfully processed
        total_failed: Number of pages that failed
        total_tokens: Total tokens used across all generations
        total_cost_usd: Total estimated cost in USD
        status: Overall processing status
        output_path: Path to the generated .apkg file (if created)
    """

    flashcards: List[Dict[str, str]]  # All successful flashcards
    results: List[FlashcardResult]  # Details for each page

    # Summary statistics
    total_attempted: int
    total_success: int
    total_failed: int

    # Cost tracking
    total_tokens: int
    total_cost_usd: float

    # Status
    status: ProcessingStatus

    # Output
    output_path: Optional[str] = None

    def get_success_rate(self) -> float:
        """Calculate percentage of successful generations.

        Returns:
            Success rate as a percentage (0.0 to 100.0)
        """
        if self.total_attempted == 0:
            return 0.0
        return (self.total_success / self.total_attempted) * 100

    def get_failed_pages(self) -> List[int]:
        """Get list of page numbers that failed.

        Returns:
            List of 1-indexed page numbers that failed to generate
        """
        return [r.page_number for r in self.results if not r.success]
