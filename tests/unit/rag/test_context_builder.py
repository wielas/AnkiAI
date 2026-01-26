"""Unit tests for ContextBuilder component."""

import pytest
import tiktoken

from src.domain.models.chunk import Chunk
from src.domain.rag.context_builder import (
    ChunkOrdering,
    ContextBuilder,
    ContextResult,
)


def create_test_chunk(
    chunk_id: str = "test_chunk_001",
    text: str = "This is test text for context building.",
    position: int = 0,
    source_document: str = "/path/to/test.pdf",
    page_numbers: list = None,
    token_count: int = 10,
) -> Chunk:
    """Create a test chunk with default values."""
    if page_numbers is None:
        page_numbers = [1, 2]

    return Chunk(
        chunk_id=chunk_id,
        text=text,
        source_document=source_document,
        page_numbers=page_numbers,
        position=position,
        token_count=token_count,
        char_count=len(text),
        has_overlap_before=position > 0,
        has_overlap_after=True,
        overlap_with_previous=f"chunk_{position - 1:03d}" if position > 0 else None,
        overlap_with_next=f"chunk_{position + 1:03d}",
        embedding=None,
    )


@pytest.mark.unit
class TestBuildContextEmpty:
    """Test cases for empty input handling."""

    def test_empty_chunks_returns_empty_string(self):
        """Test that empty chunk list returns empty string."""
        context = ContextBuilder.build_context([])
        assert context == ""

    def test_empty_chunks_with_metadata_returns_empty_string(self):
        """Test that empty list with metadata=True still returns empty."""
        context = ContextBuilder.build_context([], include_metadata=True)
        assert context == ""


@pytest.mark.unit
class TestBuildContextSingleChunk:
    """Test cases for single chunk formatting."""

    def test_single_chunk_without_metadata(self):
        """Test formatting a single chunk without metadata."""
        chunk = create_test_chunk(text="Hello world.")
        context = ContextBuilder.build_context([chunk])

        assert context == "Hello world."

    def test_single_chunk_with_metadata(self):
        """Test formatting a single chunk with metadata."""
        chunk = create_test_chunk(
            text="Hello world.",
            source_document="/docs/example.pdf",
            page_numbers=[5],
        )
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        assert "[Source: example.pdf, Pages: 5]" in context
        assert "Hello world." in context


@pytest.mark.unit
class TestBuildContextMultipleChunks:
    """Test cases for multiple chunk formatting."""

    def test_multiple_chunks_with_separator(self):
        """Test that multiple chunks are joined with separator."""
        chunks = [
            create_test_chunk("chunk_001", "First chunk.", 0),
            create_test_chunk("chunk_002", "Second chunk.", 1),
            create_test_chunk("chunk_003", "Third chunk.", 2),
        ]
        context = ContextBuilder.build_context(chunks)

        assert "First chunk." in context
        assert "Second chunk." in context
        assert "Third chunk." in context
        assert context.count("---") == 2  # Two separators for three chunks

    def test_custom_separator(self):
        """Test using a custom separator."""
        chunks = [
            create_test_chunk("chunk_001", "First.", 0),
            create_test_chunk("chunk_002", "Second.", 1),
        ]
        context = ContextBuilder.build_context(chunks, separator="\n===\n")

        assert "First.\n===\nSecond." == context

    def test_multiple_chunks_with_metadata(self):
        """Test multiple chunks with metadata headers."""
        chunks = [
            create_test_chunk(
                "chunk_001",
                "First chunk.",
                0,
                source_document="/docs/doc1.pdf",
                page_numbers=[1],
            ),
            create_test_chunk(
                "chunk_002",
                "Second chunk.",
                1,
                source_document="/docs/doc2.pdf",
                page_numbers=[5, 6],
            ),
        ]
        context = ContextBuilder.build_context(chunks, include_metadata=True)

        assert "[Source: doc1.pdf, Pages: 1]" in context
        assert "[Source: doc2.pdf, Pages: 5-6]" in context


@pytest.mark.unit
class TestBuildContextOrdering:
    """Test cases for chunk ordering strategies."""

    def test_relevance_ordering_preserves_order(self):
        """Test that RELEVANCE ordering preserves input order."""
        chunks = [
            create_test_chunk("chunk_003", "Third by position.", 2),
            create_test_chunk("chunk_001", "First by position.", 0),
            create_test_chunk("chunk_002", "Second by position.", 1),
        ]
        context = ContextBuilder.build_context(chunks, ordering=ChunkOrdering.RELEVANCE)

        # Should preserve input order
        assert context.index("Third") < context.index("First")
        assert context.index("First") < context.index("Second")

    def test_position_ordering_sorts_by_position(self):
        """Test that POSITION ordering sorts by document position."""
        chunks = [
            create_test_chunk("chunk_003", "Third by position.", 2),
            create_test_chunk("chunk_001", "First by position.", 0),
            create_test_chunk("chunk_002", "Second by position.", 1),
        ]
        context = ContextBuilder.build_context(chunks, ordering=ChunkOrdering.POSITION)

        # Should be sorted by position
        assert context.index("First") < context.index("Second")
        assert context.index("Second") < context.index("Third")

    def test_position_ordering_groups_by_source(self):
        """Test that POSITION ordering groups by source document."""
        chunks = [
            create_test_chunk("chunk_b1", "Doc B chunk 1.", 0, "/docs/b.pdf"),
            create_test_chunk("chunk_a1", "Doc A chunk 1.", 0, "/docs/a.pdf"),
            create_test_chunk("chunk_a2", "Doc A chunk 2.", 1, "/docs/a.pdf"),
        ]
        context = ContextBuilder.build_context(chunks, ordering=ChunkOrdering.POSITION)

        # Doc A should come before Doc B (alphabetically)
        assert context.index("Doc A chunk 1") < context.index("Doc A chunk 2")
        assert context.index("Doc A chunk 2") < context.index("Doc B chunk 1")


@pytest.mark.unit
class TestMetadataFormatting:
    """Test cases for metadata formatting specifics."""

    def test_single_page_number(self):
        """Test formatting with a single page number."""
        chunk = create_test_chunk(page_numbers=[5])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        assert "Pages: 5]" in context

    def test_consecutive_page_range(self):
        """Test formatting with consecutive page numbers."""
        chunk = create_test_chunk(page_numbers=[1, 2, 3, 4, 5])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        assert "Pages: 1-5]" in context

    def test_non_consecutive_pages(self):
        """Test formatting with non-consecutive page numbers."""
        chunk = create_test_chunk(page_numbers=[1, 3, 7])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        assert "Pages: 1, 3, 7]" in context

    def test_empty_page_numbers(self):
        """Test formatting with no page numbers."""
        chunk = create_test_chunk(page_numbers=[])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        assert "Pages: unknown]" in context

    def test_unsorted_page_numbers_sorted_in_output(self):
        """Test that unsorted page numbers are sorted in metadata."""
        chunk = create_test_chunk(page_numbers=[5, 2, 8, 3])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        # Should show sorted, non-consecutive pages
        assert "Pages: 2, 3, 5, 8]" in context

    def test_unsorted_consecutive_pages_become_range(self):
        """Test that unsorted but consecutive pages become a range."""
        chunk = create_test_chunk(page_numbers=[3, 1, 2])
        context = ContextBuilder.build_context([chunk], include_metadata=True)

        # Should recognize as consecutive range after sorting
        assert "Pages: 1-3]" in context


@pytest.mark.unit
class TestEstimateTokens:
    """Test cases for token estimation."""

    def test_estimate_tokens_empty_list(self):
        """Test token estimation for empty list."""
        tokens = ContextBuilder.estimate_tokens([])
        assert tokens == 0

    def test_estimate_tokens_single_chunk(self):
        """Test token estimation for single chunk."""
        chunk = create_test_chunk(text="Hello world, this is a test.")
        tokens = ContextBuilder.estimate_tokens([chunk])

        # Verify it's a reasonable positive number
        assert tokens > 0
        assert tokens < 100  # Simple text shouldn't be too many tokens

    def test_estimate_tokens_multiple_chunks(self):
        """Test token estimation includes separators."""
        chunks = [
            create_test_chunk("chunk_001", "First chunk text.", 0),
            create_test_chunk("chunk_002", "Second chunk text.", 1),
        ]

        tokens_without_sep = ContextBuilder.estimate_tokens([chunks[0]])
        tokens_with_both = ContextBuilder.estimate_tokens(chunks)

        # Should include separator tokens
        assert tokens_with_both > tokens_without_sep * 2 - 5  # Allow some variance

    def test_estimate_tokens_with_metadata(self):
        """Test that metadata increases token count."""
        chunk = create_test_chunk(text="Short text.")

        tokens_without = ContextBuilder.estimate_tokens([chunk], include_metadata=False)
        tokens_with = ContextBuilder.estimate_tokens([chunk], include_metadata=True)

        assert tokens_with > tokens_without


@pytest.mark.unit
class TestBuildContextWithLimit:
    """Test cases for context building with token limits."""

    def test_build_with_limit_returns_context_result(self):
        """Test that build_context_with_limit returns ContextResult."""
        chunks = [create_test_chunk(text="Test text.")]
        result = ContextBuilder.build_context_with_limit(chunks, max_tokens=1000)

        assert isinstance(result, ContextResult)
        assert result.context
        assert result.token_count > 0
        assert result.chunk_count == 1
        assert result.truncated is False

    def test_build_with_limit_empty_chunks(self):
        """Test with empty chunk list."""
        result = ContextBuilder.build_context_with_limit([], max_tokens=1000)

        assert result.context == ""
        assert result.token_count == 0
        assert result.chunk_count == 0
        assert result.truncated is False

    def test_build_with_limit_fits_all_chunks(self):
        """Test when all chunks fit within limit."""
        chunks = [
            create_test_chunk("chunk_001", "Short text one.", 0),
            create_test_chunk("chunk_002", "Short text two.", 1),
        ]
        result = ContextBuilder.build_context_with_limit(chunks, max_tokens=1000)

        assert result.chunk_count == 2
        assert result.truncated is False

    def test_build_with_limit_truncates_to_fit(self):
        """Test truncation when chunks exceed limit."""
        # Create chunks with longer text
        long_text = "This is a longer text. " * 50  # ~400 tokens
        chunks = [
            create_test_chunk("chunk_001", long_text, 0),
            create_test_chunk("chunk_002", long_text, 1),
            create_test_chunk("chunk_003", long_text, 2),
        ]

        # Set a limit that won't fit all chunks
        result = ContextBuilder.build_context_with_limit(chunks, max_tokens=500)

        assert result.token_count <= 500
        assert result.chunk_count < 3 or result.truncated

    def test_build_with_limit_respects_token_count(self):
        """Test that result stays within token limit."""
        long_text = "Word " * 100
        chunks = [create_test_chunk(text=long_text)]

        result = ContextBuilder.build_context_with_limit(chunks, max_tokens=50)

        assert result.token_count <= 50

    def test_build_with_limit_invalid_max_tokens(self):
        """Test that invalid max_tokens raises ValueError."""
        chunks = [create_test_chunk()]

        with pytest.raises(ValueError, match="max_tokens must be positive"):
            ContextBuilder.build_context_with_limit(chunks, max_tokens=0)

        with pytest.raises(ValueError, match="max_tokens must be positive"):
            ContextBuilder.build_context_with_limit(chunks, max_tokens=-10)

    def test_build_with_limit_includes_metadata(self):
        """Test that metadata is included when requested."""
        chunk = create_test_chunk(
            text="Test text.",
            source_document="/docs/test.pdf",
            page_numbers=[1],
        )
        result = ContextBuilder.build_context_with_limit(
            [chunk], max_tokens=1000, include_metadata=True
        )

        assert "[Source: test.pdf" in result.context

    def test_build_with_limit_applies_ordering(self):
        """Test that ordering is applied correctly."""
        chunks = [
            create_test_chunk("chunk_003", "Third.", 2),
            create_test_chunk("chunk_001", "First.", 0),
        ]

        result = ContextBuilder.build_context_with_limit(
            chunks, max_tokens=1000, ordering=ChunkOrdering.POSITION
        )

        # POSITION ordering should put First before Third
        assert result.context.index("First") < result.context.index("Third")


@pytest.mark.unit
class TestTokenAccuracy:
    """Test cases for token counting accuracy."""

    def test_token_count_matches_tiktoken(self):
        """Test that token estimates match tiktoken directly."""
        text = "The quick brown fox jumps over the lazy dog."
        chunk = create_test_chunk(text=text)

        estimated = ContextBuilder.estimate_tokens([chunk])

        # Verify against tiktoken directly
        encoding = tiktoken.get_encoding("cl100k_base")
        actual = len(encoding.encode(text))

        assert estimated == actual

    def test_context_result_token_count_accurate(self):
        """Test that ContextResult.token_count is accurate."""
        chunks = [
            create_test_chunk("chunk_001", "First test chunk text.", 0),
            create_test_chunk("chunk_002", "Second test chunk text.", 1),
        ]

        result = ContextBuilder.build_context_with_limit(chunks, max_tokens=10000)

        # Verify against tiktoken directly
        encoding = tiktoken.get_encoding("cl100k_base")
        actual = len(encoding.encode(result.context))

        assert result.token_count == actual

    def test_truncated_context_respects_token_limit(self):
        """Test that truncation with ellipsis stays within max_tokens."""
        # Create a chunk that will definitely need truncation
        long_text = "This is a test sentence. " * 100  # Much longer than limit
        chunk = create_test_chunk(text=long_text)

        max_tokens = 100
        result = ContextBuilder.build_context_with_limit([chunk], max_tokens=max_tokens)

        # Verify against tiktoken directly
        encoding = tiktoken.get_encoding("cl100k_base")
        actual_tokens = len(encoding.encode(result.context))

        # The actual token count should not exceed max_tokens
        assert (
            actual_tokens <= max_tokens
        ), f"Truncated context has {actual_tokens} tokens, exceeds limit of {max_tokens}"
        assert result.truncated is True
        assert result.context.endswith("...")


@pytest.mark.unit
class TestContextResult:
    """Test cases for ContextResult dataclass."""

    def test_context_result_attributes(self):
        """Test ContextResult attribute access."""
        result = ContextResult(
            context="Test context",
            token_count=5,
            chunk_count=2,
            truncated=True,
        )

        assert result.context == "Test context"
        assert result.token_count == 5
        assert result.chunk_count == 2
        assert result.truncated is True

    def test_context_result_default_truncated(self):
        """Test that truncated defaults to False."""
        result = ContextResult(
            context="Test",
            token_count=1,
            chunk_count=1,
        )

        assert result.truncated is False
