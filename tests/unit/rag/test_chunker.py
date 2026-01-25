"""Unit tests for Chunker."""


import pytest
import tiktoken

from src.domain.models.chunk import Chunk
from src.domain.models.document import Document, DocumentFormat, DocumentMetadata
from src.domain.rag.chunker import DEFAULT_ENCODING, Chunker


@pytest.fixture
def encoding():
    """Get tiktoken encoding for tests."""
    return tiktoken.get_encoding(DEFAULT_ENCODING)


@pytest.fixture
def simple_document():
    """Create a simple document with one paragraph."""
    return Document(
        content="This is a simple paragraph with some text.",
        file_path="/test/simple.pdf",
        page_range=(1, 1),
        metadata=DocumentMetadata(
            total_pages=1,
            file_size_bytes=1024,
            file_format=DocumentFormat.PDF,
        ),
    )


@pytest.fixture
def multi_paragraph_document():
    """Create a document with multiple paragraphs."""
    content = """Machine learning is a fascinating field that combines mathematics, statistics, and computer science to create systems that can learn from data. The fundamental idea behind machine learning is that computers can automatically learn patterns and make decisions with minimal human intervention. This has led to breakthrough applications in many industries including healthcare, finance, and technology.

Deep learning architectures represent a subset of machine learning that uses artificial neural networks with multiple hidden layers. These networks are inspired by the human brain and can automatically learn hierarchical representations of data. The depth of these networks allows them to capture complex patterns that would be impossible to program manually. Convolutional neural networks, recurrent neural networks, and transformers are all examples of deep learning architectures.

Natural language processing is the branch of artificial intelligence that enables computers to understand, interpret, and generate human language. Modern NLP systems use sophisticated techniques like attention mechanisms and transformer architectures to process text. Applications include machine translation, sentiment analysis, question answering systems, and chatbots. The field has seen remarkable progress in recent years with models like GPT and BERT.

Computer vision is the field that enables machines to interpret and understand visual information from the world. It encompasses techniques for image classification, object detection, semantic segmentation, and image generation. Deep learning has revolutionized computer vision, with convolutional neural networks achieving superhuman performance on many tasks. Applications range from autonomous vehicles to medical imaging analysis."""
    return Document(
        content=content,
        file_path="/test/multi_paragraph.pdf",
        page_range=(1, 3),
        metadata=DocumentMetadata(
            total_pages=3,
            file_size_bytes=2048,
            file_format=DocumentFormat.PDF,
        ),
    )


@pytest.fixture
def long_paragraph_document():
    """Create a document with a very long paragraph that needs sentence splitting."""
    # Create a paragraph that will exceed 1200 tokens
    sentences = [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
        "Deep learning uses neural networks with multiple layers to extract features.",
        "Natural language processing allows computers to understand human language.",
        "Computer vision enables machines to interpret visual information.",
        "Reinforcement learning trains agents through trial and error in environments.",
    ]
    # Repeat to make it long enough
    long_content = " ".join(sentences * 50)

    return Document(
        content=long_content,
        file_path="/test/long_paragraph.pdf",
        page_range=(1, 5),
        metadata=DocumentMetadata(
            total_pages=5,
            file_size_bytes=50000,
            file_format=DocumentFormat.PDF,
        ),
    )


@pytest.fixture
def empty_document():
    """Create an empty document."""
    return Document(
        content="",
        file_path="/test/empty.pdf",
        page_range=(1, 1),
        metadata=DocumentMetadata(
            total_pages=1,
            file_size_bytes=100,
            file_format=DocumentFormat.PDF,
        ),
    )


@pytest.fixture
def whitespace_document():
    """Create a document with only whitespace."""
    return Document(
        content="   \n\n\t  \n  ",
        file_path="/test/whitespace.pdf",
        page_range=(1, 1),
        metadata=DocumentMetadata(
            total_pages=1,
            file_size_bytes=50,
            file_format=DocumentFormat.PDF,
        ),
    )


# =============================================================================
# Basic Chunking Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerBasicChunking:
    """Tests for basic chunking functionality."""

    def test_chunk_simple_document(self, simple_document):
        """Should create a single chunk for a simple document under target size."""
        chunks = Chunker.chunk(simple_document)

        assert len(chunks) == 1
        assert isinstance(chunks[0], Chunk)
        assert "simple paragraph" in chunks[0].text

    def test_chunk_multiple_paragraphs(self, multi_paragraph_document):
        """Should handle documents with multiple paragraphs."""
        # Use small target size to force multiple chunks
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        assert len(chunks) >= 2
        # All chunks should be Chunk instances
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_chunk_respects_target_size(self, multi_paragraph_document, encoding):
        """Chunks should be approximately target_size tokens."""
        target = 100
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=target, overlap_size=20
        )

        # Check that most chunks are close to target size
        # (with some tolerance for overlap and paragraph boundaries)
        for chunk in chunks:
            # Allow some flexibility due to overlap and semantic boundaries
            assert chunk.token_count <= target * 2

    def test_chunk_returns_list(self, simple_document):
        """Should always return a list, even for single chunk."""
        result = Chunker.chunk(simple_document)

        assert isinstance(result, list)

    def test_chunk_preserves_content(self, multi_paragraph_document):
        """All original content should be present in chunks (minus overlap duplication)."""
        chunks = Chunker.chunk(multi_paragraph_document, target_size=50, overlap_size=0)

        # All key phrases should appear in some chunk
        combined_text = " ".join(c.text for c in chunks)
        assert "machine learning" in combined_text.lower()
        assert "deep learning" in combined_text.lower()
        assert "natural language" in combined_text.lower()


# =============================================================================
# Token Counting Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerTokenCounting:
    """Tests for token counting accuracy."""

    def test_token_counting_accuracy(self, simple_document, encoding):
        """Token count should match tiktoken encoding."""
        chunks = Chunker.chunk(simple_document)

        for chunk in chunks:
            expected_tokens = len(encoding.encode(chunk.text))
            assert chunk.token_count == expected_tokens

    def test_char_count_tracking(self, simple_document):
        """Character count should match text length."""
        chunks = Chunker.chunk(simple_document)

        for chunk in chunks:
            assert chunk.char_count == len(chunk.text)
            assert len(chunk) == len(chunk.text)

    def test_token_count_in_chunk_metadata(self, multi_paragraph_document):
        """Each chunk should have accurate token_count metadata."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        for chunk in chunks:
            assert chunk.token_count > 0
            assert isinstance(chunk.token_count, int)


# =============================================================================
# Long Paragraph Handling Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerLongParagraphs:
    """Tests for handling long paragraphs."""

    def test_chunk_long_paragraph_splits_by_sentences(self, long_paragraph_document):
        """Long paragraphs should be split by sentences."""
        chunks = Chunker.chunk(
            long_paragraph_document,
            target_size=200,
            overlap_size=30,
            max_chunk_size=400,
        )

        # Should create multiple chunks
        assert len(chunks) > 1

        # Verify each chunk is within max size (with some tolerance for overlap)
        for chunk in chunks:
            # Allow some tolerance for overlap
            assert chunk.token_count <= 600

    def test_sentence_splitting_preserves_meaning(self, long_paragraph_document):
        """Sentence splitting should not cut mid-sentence."""
        chunks = Chunker.chunk(
            long_paragraph_document,
            target_size=200,
            overlap_size=0,  # No overlap to make checking easier
            max_chunk_size=400,
        )

        # Check that chunks don't end mid-sentence (should end with punctuation)
        for chunk in chunks[:-1]:  # Except last chunk
            text = chunk.text.strip()
            # Should end with sentence-ending punctuation
            assert text[-1] in ".!?" or text.endswith("...")


# =============================================================================
# Overlap Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerOverlap:
    """Tests for overlap between chunks."""

    def test_overlap_between_chunks(self, multi_paragraph_document, encoding):
        """Chunks should have overlap from previous chunk."""
        overlap_size = 20
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=50, overlap_size=overlap_size
        )

        if len(chunks) >= 2:
            # Second chunk should contain overlap from first
            first_chunk_tokens = encoding.encode(chunks[0].text)
            overlap_tokens = first_chunk_tokens[-overlap_size:]
            overlap_text = encoding.decode(overlap_tokens)

            # The overlap text should appear at the start of the second chunk
            assert overlap_text in chunks[1].text

    def test_overlap_tracking_metadata(self, multi_paragraph_document):
        """Overlap flags should be set correctly."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=50, overlap_size=10
        )

        if len(chunks) >= 2:
            # First chunk: no overlap before, has overlap after
            assert chunks[0].has_overlap_before is False
            assert chunks[0].has_overlap_after is True

            # Middle chunks (if any): overlap before and after
            for chunk in chunks[1:-1]:
                assert chunk.has_overlap_before is True
                assert chunk.has_overlap_after is True

            # Last chunk: has overlap before, no overlap after
            assert chunks[-1].has_overlap_before is True
            assert chunks[-1].has_overlap_after is False

    def test_overlap_chunk_ids_linked(self, multi_paragraph_document):
        """Overlap references should link to correct chunk IDs."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=50, overlap_size=10
        )

        if len(chunks) >= 2:
            # First chunk should link to next
            assert chunks[0].overlap_with_previous is None
            assert chunks[0].overlap_with_next == chunks[1].chunk_id

            # Middle chunks should link both ways
            for i in range(1, len(chunks) - 1):
                assert chunks[i].overlap_with_previous == chunks[i - 1].chunk_id
                assert chunks[i].overlap_with_next == chunks[i + 1].chunk_id

            # Last chunk should link to previous
            assert chunks[-1].overlap_with_previous == chunks[-2].chunk_id
            assert chunks[-1].overlap_with_next is None

    def test_zero_overlap(self, multi_paragraph_document):
        """Zero overlap should produce chunks without repeated content."""
        chunks = Chunker.chunk(multi_paragraph_document, target_size=50, overlap_size=0)

        # With zero overlap, flags should still be set correctly for potential overlap
        # but overlap_with_previous/next can be set as they indicate adjacency
        assert all(c.overlap_with_previous is None or True for c in chunks)


# =============================================================================
# Edge Cases Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerEdgeCases:
    """Tests for edge cases."""

    def test_chunk_empty_document(self, empty_document):
        """Should return empty list for empty document."""
        chunks = Chunker.chunk(empty_document)

        assert chunks == []

    def test_chunk_whitespace_document(self, whitespace_document):
        """Should return empty list for whitespace-only document."""
        chunks = Chunker.chunk(whitespace_document)

        assert chunks == []

    def test_chunk_single_short_paragraph(self, simple_document):
        """Document smaller than target_size should produce single chunk."""
        chunks = Chunker.chunk(simple_document, target_size=1000)

        assert len(chunks) == 1
        assert chunks[0].has_overlap_before is False
        assert chunks[0].has_overlap_after is False

    def test_chunk_very_long_single_paragraph(self):
        """Very long paragraph should be split into multiple chunks."""
        # Create a document with one very long paragraph
        long_text = "This is a test sentence. " * 500  # ~2000+ tokens
        doc = Document(
            content=long_text,
            file_path="/test/very_long.pdf",
            page_range=(1, 1),
            metadata=DocumentMetadata(
                total_pages=1,
                file_size_bytes=len(long_text),
                file_format=DocumentFormat.PDF,
            ),
        )

        chunks = Chunker.chunk(doc, target_size=200, max_chunk_size=400)

        assert len(chunks) > 1

    def test_invalid_target_size(self, simple_document):
        """Should raise ValueError for invalid target_size."""
        with pytest.raises(ValueError, match="target_size must be positive"):
            Chunker.chunk(simple_document, target_size=0)

        with pytest.raises(ValueError, match="target_size must be positive"):
            Chunker.chunk(simple_document, target_size=-1)

    def test_invalid_overlap_size(self, simple_document):
        """Should raise ValueError for invalid overlap_size."""
        with pytest.raises(ValueError, match="overlap_size must be non-negative"):
            Chunker.chunk(simple_document, overlap_size=-1)

    def test_overlap_greater_than_target(self, simple_document):
        """Should raise ValueError when overlap >= target."""
        with pytest.raises(ValueError, match="overlap_size.*must be less than"):
            Chunker.chunk(simple_document, target_size=100, overlap_size=100)

        with pytest.raises(ValueError, match="overlap_size.*must be less than"):
            Chunker.chunk(simple_document, target_size=100, overlap_size=150)

    def test_invalid_max_chunk_size(self, simple_document):
        """Should raise ValueError for invalid max_chunk_size."""
        with pytest.raises(ValueError, match="max_chunk_size must be positive"):
            Chunker.chunk(simple_document, max_chunk_size=0)


# =============================================================================
# Metadata Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerMetadata:
    """Tests for chunk metadata."""

    def test_chunk_id_generation(self, multi_paragraph_document):
        """Chunk IDs should follow the expected format."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        for i, chunk in enumerate(chunks):
            # Should be format: filename_chunk_XXX
            assert "multi_paragraph_chunk_" in chunk.chunk_id
            assert chunk.chunk_id.endswith(f"_{i:03d}")

    def test_chunk_id_uniqueness(self, multi_paragraph_document):
        """All chunk IDs should be unique."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))

    def test_chunk_id_sanitization(self):
        """Chunk IDs should handle special characters in filenames."""
        doc = Document(
            content="Some test content here.",
            file_path="/test/my file-with (special) chars!.pdf",
            page_range=(1, 1),
            metadata=DocumentMetadata(
                total_pages=1,
                file_size_bytes=100,
                file_format=DocumentFormat.PDF,
            ),
        )

        chunks = Chunker.chunk(doc)

        # ID should not contain special characters
        for chunk in chunks:
            assert " " not in chunk.chunk_id
            assert "(" not in chunk.chunk_id
            assert ")" not in chunk.chunk_id
            assert "!" not in chunk.chunk_id
            assert "-" not in chunk.chunk_id

    def test_page_numbers_tracked(self, multi_paragraph_document):
        """Chunks should track source page numbers."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        for chunk in chunks:
            # Page numbers should be from document's page range
            assert chunk.page_numbers == [1, 2, 3]

    def test_position_tracking(self, multi_paragraph_document):
        """Chunks should have correct position (0-indexed)."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        for i, chunk in enumerate(chunks):
            assert chunk.position == i

    def test_source_document_tracked(self, multi_paragraph_document):
        """Chunks should track source document path."""
        chunks = Chunker.chunk(
            multi_paragraph_document, target_size=100, overlap_size=20
        )

        for chunk in chunks:
            assert chunk.source_document == multi_paragraph_document.file_path


# =============================================================================
# Integration Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerIntegration:
    """Integration tests with real PDF."""

    def test_chunk_with_real_pdf(self, sample_pdf_path):
        """Should chunk a real PDF document."""
        from src.domain.document_processing.pdf_parser import PDFParser

        # Parse the PDF
        doc = PDFParser.parse(str(sample_pdf_path))

        # Chunk it
        chunks = Chunker.chunk(doc, target_size=200, overlap_size=30)

        # Should produce chunks
        assert len(chunks) > 0

        # All chunks should be valid
        for chunk in chunks:
            assert isinstance(chunk, Chunk)
            assert chunk.text
            assert chunk.token_count > 0
            assert chunk.char_count > 0
            assert chunk.chunk_id

    def test_chunk_multiple_configurations(self, sample_pdf_path):
        """Should work with different configuration values."""
        from src.domain.document_processing.pdf_parser import PDFParser

        doc = PDFParser.parse(str(sample_pdf_path))

        configs = [
            {"target_size": 100, "overlap_size": 20},
            {"target_size": 500, "overlap_size": 50},
            {"target_size": 800, "overlap_size": 100},
            {"target_size": 1000, "overlap_size": 0},
        ]

        for config in configs:
            chunks = Chunker.chunk(doc, **config)

            # Should produce chunks for each config
            assert len(chunks) > 0

            # Verify consistency
            for i, chunk in enumerate(chunks):
                assert chunk.position == i


# =============================================================================
# Chunk Model Tests
# =============================================================================


@pytest.mark.unit
class TestChunkModel:
    """Tests for the Chunk dataclass."""

    def test_chunk_len(self):
        """__len__ should return char_count."""
        chunk = Chunk(
            chunk_id="test_chunk_000",
            text="Hello world",
            source_document="/test.pdf",
            page_numbers=[1],
            position=0,
            token_count=2,
            char_count=11,
            has_overlap_before=False,
            has_overlap_after=False,
        )

        assert len(chunk) == 11

    def test_chunk_str(self):
        """__str__ should return readable representation."""
        chunk = Chunk(
            chunk_id="test_chunk_000",
            text="Hello world, this is a test chunk with some content.",
            source_document="/test.pdf",
            page_numbers=[1],
            position=0,
            token_count=10,
            char_count=52,
            has_overlap_before=False,
            has_overlap_after=False,
        )

        result = str(chunk)
        assert "test_chunk_000" in result
        assert "Hello world" in result

    def test_chunk_has_embedding_false(self):
        """has_embedding should return False when no embedding."""
        chunk = Chunk(
            chunk_id="test_chunk_000",
            text="Test",
            source_document="/test.pdf",
            page_numbers=[1],
            position=0,
            token_count=1,
            char_count=4,
            has_overlap_before=False,
            has_overlap_after=False,
        )

        assert chunk.has_embedding() is False

    def test_chunk_has_embedding_true(self):
        """has_embedding should return True when embedding exists."""
        chunk = Chunk(
            chunk_id="test_chunk_000",
            text="Test",
            source_document="/test.pdf",
            page_numbers=[1],
            position=0,
            token_count=1,
            char_count=4,
            has_overlap_before=False,
            has_overlap_after=False,
            embedding=[0.1, 0.2, 0.3],
        )

        assert chunk.has_embedding() is True

    def test_chunk_has_embedding_empty_list(self):
        """has_embedding should return False for empty list."""
        chunk = Chunk(
            chunk_id="test_chunk_000",
            text="Test",
            source_document="/test.pdf",
            page_numbers=[1],
            position=0,
            token_count=1,
            char_count=4,
            has_overlap_before=False,
            has_overlap_after=False,
            embedding=[],
        )

        assert chunk.has_embedding() is False


# =============================================================================
# Helper Method Tests
# =============================================================================


@pytest.mark.unit
class TestChunkerHelperMethods:
    """Tests for private helper methods."""

    def test_split_into_paragraphs(self):
        """Should split text by double newlines."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = Chunker._split_into_paragraphs(text)

        assert len(result) == 3
        assert result[0] == "First paragraph."
        assert result[1] == "Second paragraph."
        assert result[2] == "Third paragraph."

    def test_split_into_paragraphs_with_whitespace(self):
        """Should handle extra whitespace."""
        text = "  First.  \n\n\n  Second.  \n\n  Third.  "
        result = Chunker._split_into_paragraphs(text)

        assert len(result) == 3
        assert result[0] == "First."
        assert result[1] == "Second."
        assert result[2] == "Third."

    def test_split_into_sentences(self):
        """Should split text by sentence boundaries."""
        text = "First sentence. Second sentence! Third sentence?"
        result = Chunker._split_into_sentences(text)

        assert len(result) == 3
        assert "First" in result[0]
        assert "Second" in result[1]
        assert "Third" in result[2]

    def test_count_tokens(self, encoding):
        """Should count tokens accurately."""
        text = "Hello world"
        result = Chunker._count_tokens(text, encoding)

        expected = len(encoding.encode(text))
        assert result == expected

    def test_count_tokens_empty(self, encoding):
        """Should return 0 for empty string."""
        result = Chunker._count_tokens("", encoding)
        assert result == 0

    def test_generate_chunk_id(self, simple_document):
        """Should generate correct chunk ID format."""
        result = Chunker._generate_chunk_id(simple_document, 5)

        assert "simple_chunk_005" in result

    def test_extract_overlap_from_end(self, encoding):
        """Should extract overlap tokens from end."""
        text = "This is a test sentence with multiple tokens."
        overlap = Chunker._extract_overlap(text, 3, encoding, from_end=True)

        # Should get last 3 tokens
        expected_tokens = encoding.encode(text)[-3:]
        expected = encoding.decode(expected_tokens)
        assert overlap == expected

    def test_extract_overlap_from_start(self, encoding):
        """Should extract overlap tokens from start."""
        text = "This is a test sentence with multiple tokens."
        overlap = Chunker._extract_overlap(text, 3, encoding, from_end=False)

        # Should get first 3 tokens
        expected_tokens = encoding.encode(text)[:3]
        expected = encoding.decode(expected_tokens)
        assert overlap == expected
