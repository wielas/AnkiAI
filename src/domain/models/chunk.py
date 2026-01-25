"""Chunk model for representing document chunks in the RAG pipeline."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Chunk:
    """Represents a text chunk from a document for RAG processing.

    A chunk is a semantically meaningful portion of a document used for
    embedding generation and context retrieval. Chunks typically overlap
    with adjacent chunks to preserve context at boundaries.

    Attributes:
        chunk_id: Unique identifier in format "source_filename_chunk_001"
        text: The chunk text content
        source_document: Path to the source document
        page_numbers: List of pages this chunk spans (1-indexed)
        position: Order in document (0-indexed: 0, 1, 2...)
        token_count: Token count (using tiktoken)
        char_count: Character count
        has_overlap_before: True if chunk overlaps with previous
        has_overlap_after: True if chunk overlaps with next
        overlap_with_previous: Previous chunk_id if overlapping
        overlap_with_next: Next chunk_id if overlapping
        embedding: Vector embedding (populated during embedding phase)
    """

    # Core content
    chunk_id: str
    text: str

    # Source tracking
    source_document: str
    page_numbers: List[int]
    position: int

    # Size metrics
    token_count: int
    char_count: int

    # Overlap tracking
    has_overlap_before: bool
    has_overlap_after: bool
    overlap_with_previous: Optional[str] = None
    overlap_with_next: Optional[str] = None

    # Embedding (will be populated in Day 3)
    embedding: Optional[List[float]] = field(default=None, repr=False)

    def __len__(self) -> int:
        """Return character count.

        Returns:
            Number of characters in the chunk text
        """
        return self.char_count

    def __str__(self) -> str:
        """Return a human-readable string representation.

        Returns:
            String showing chunk ID and preview of text
        """
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"Chunk({self.chunk_id}: {preview!r})"

    def has_embedding(self) -> bool:
        """Check if this chunk has an embedding.

        Returns:
            True if embedding is populated, False otherwise
        """
        return self.embedding is not None and len(self.embedding) > 0
