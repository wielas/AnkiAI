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
