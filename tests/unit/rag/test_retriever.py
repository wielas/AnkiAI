"""Unit tests for Retriever component."""

from unittest.mock import Mock

import pytest

from src.domain.models.chunk import Chunk
from src.domain.rag.retriever import RetrievalResult, Retriever


def create_test_chunk(
    chunk_id: str = "test_chunk_001",
    text: str = "This is test text for retrieval.",
    position: int = 0,
    source_document: str = "/path/to/test.pdf",
    embedding: list = None,
) -> Chunk:
    """Create a test chunk with default values."""
    if embedding is None:
        embedding = [0.1] * 1536

    return Chunk(
        chunk_id=chunk_id,
        text=text,
        source_document=source_document,
        page_numbers=[1, 2],
        position=position,
        token_count=10,
        char_count=len(text),
        has_overlap_before=position > 0,
        has_overlap_after=True,
        overlap_with_previous=f"chunk_{position - 1:03d}" if position > 0 else None,
        overlap_with_next=f"chunk_{position + 1:03d}",
        embedding=embedding,
    )


@pytest.fixture
def mock_embedding_generator():
    """Create a mock EmbeddingGenerator."""
    generator = Mock()
    generator.generate_query_embedding.return_value = [0.1] * 1536
    return generator


@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore with test data."""
    store = Mock()
    store.collection_name = "test_collection"
    store.count.return_value = 10

    # Default search results
    chunks = [
        create_test_chunk("chunk_001", "Machine learning is a subset of AI.", 0),
        create_test_chunk("chunk_002", "Deep learning uses neural networks.", 1),
        create_test_chunk("chunk_003", "AI can solve complex problems.", 2),
    ]
    store.search.return_value = [
        (chunks[0], 0.95),
        (chunks[1], 0.85),
        (chunks[2], 0.75),
    ]

    return store


@pytest.fixture
def retriever(mock_vector_store, mock_embedding_generator):
    """Create a Retriever instance with mocked dependencies."""
    return Retriever(mock_vector_store, mock_embedding_generator)


@pytest.mark.unit
class TestRetrieverInit:
    """Test cases for Retriever initialization."""

    def test_initialization(self, mock_vector_store, mock_embedding_generator):
        """Test successful initialization."""
        retriever = Retriever(mock_vector_store, mock_embedding_generator)

        assert retriever.vector_store is mock_vector_store
        assert retriever.embedding_generator is mock_embedding_generator

    def test_initialization_logs_chunk_count(
        self, mock_vector_store, mock_embedding_generator, caplog
    ):
        """Test that initialization logs the chunk count."""
        import logging

        with caplog.at_level(logging.INFO):
            Retriever(mock_vector_store, mock_embedding_generator)

        assert "10 chunks" in caplog.text


@pytest.mark.unit
class TestRetrieve:
    """Test cases for retrieve method."""

    def test_retrieve_returns_correct_number_of_chunks(self, retriever):
        """Test that retrieve returns the expected number of chunks."""
        chunks = retriever.retrieve("What is machine learning?", top_k=3)

        assert len(chunks) == 3

    def test_retrieve_returns_chunks_in_relevance_order(self, retriever):
        """Test that chunks are ordered by relevance (most relevant first)."""
        chunks = retriever.retrieve("What is ML?", top_k=3)

        # First chunk should be the most relevant
        assert chunks[0].chunk_id == "chunk_001"
        assert chunks[1].chunk_id == "chunk_002"
        assert chunks[2].chunk_id == "chunk_003"

    def test_retrieve_generates_query_embedding(
        self, retriever, mock_embedding_generator
    ):
        """Test that retrieve generates embedding for the query."""
        retriever.retrieve("What is AI?", top_k=3)

        mock_embedding_generator.generate_query_embedding.assert_called_once_with(
            "What is AI?"
        )

    def test_retrieve_calls_vector_store_search(self, retriever, mock_vector_store):
        """Test that retrieve calls vector store search with correct parameters."""
        retriever.retrieve("test query", top_k=5)

        mock_vector_store.search.assert_called_once()
        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["top_k"] == 5
        assert call_kwargs["source_document"] is None

    def test_retrieve_with_source_filter(self, retriever, mock_vector_store):
        """Test filtering by source document."""
        retriever.retrieve(
            "test query", top_k=3, source_document="/path/to/specific.pdf"
        )

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["source_document"] == "/path/to/specific.pdf"

    def test_retrieve_uses_default_top_k(self, retriever, mock_vector_store):
        """Test that default top_k is used when not specified."""
        retriever.retrieve("test query")

        call_kwargs = mock_vector_store.search.call_args.kwargs
        assert call_kwargs["top_k"] == Retriever.DEFAULT_TOP_K


@pytest.mark.unit
class TestRetrieveWithScores:
    """Test cases for retrieve_with_scores method."""

    def test_retrieve_with_scores_returns_retrieval_results(self, retriever):
        """Test that retrieve_with_scores returns RetrievalResult objects."""
        results = retriever.retrieve_with_scores("What is ML?", top_k=3)

        assert all(isinstance(r, RetrievalResult) for r in results)
        assert len(results) == 3

    def test_retrieve_with_scores_includes_scores(self, retriever):
        """Test that results include correct similarity scores."""
        results = retriever.retrieve_with_scores("What is ML?", top_k=3)

        assert results[0].score == 0.95
        assert results[1].score == 0.85
        assert results[2].score == 0.75

    def test_retrieve_with_scores_chunks_accessible(self, retriever):
        """Test that chunks are accessible from results."""
        results = retriever.retrieve_with_scores("What is ML?", top_k=3)

        assert results[0].chunk.chunk_id == "chunk_001"
        assert "Machine learning" in results[0].chunk.text


@pytest.mark.unit
class TestRetrieverValidation:
    """Test cases for input validation."""

    def test_empty_query_raises_error(self, retriever):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            retriever.retrieve("")

    def test_whitespace_query_raises_error(self, retriever):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be whitespace only"):
            retriever.retrieve("   ")

    def test_invalid_top_k_zero_raises_error(self, retriever):
        """Test that top_k=0 raises ValueError."""
        with pytest.raises(ValueError, match="top_k must be positive"):
            retriever.retrieve("test query", top_k=0)

    def test_invalid_top_k_negative_raises_error(self, retriever):
        """Test that negative top_k raises ValueError."""
        with pytest.raises(ValueError, match="top_k must be positive"):
            retriever.retrieve("test query", top_k=-1)

    def test_invalid_top_k_type_raises_error(self, retriever):
        """Test that non-integer top_k raises ValueError."""
        with pytest.raises(ValueError, match="top_k must be an integer"):
            retriever.retrieve("test query", top_k=3.5)


@pytest.mark.unit
class TestRetrieverEmptyStore:
    """Test cases for empty vector store behavior."""

    def test_empty_store_returns_empty_list(self, mock_embedding_generator):
        """Test that empty vector store returns empty results."""
        empty_store = Mock()
        empty_store.collection_name = "empty_collection"
        empty_store.count.return_value = 0

        retriever = Retriever(empty_store, mock_embedding_generator)
        chunks = retriever.retrieve("test query", top_k=5)

        assert chunks == []

    def test_empty_store_does_not_generate_embedding(self, mock_embedding_generator):
        """Test that empty store doesn't waste API calls on embedding generation."""
        empty_store = Mock()
        empty_store.collection_name = "empty_collection"
        empty_store.count.return_value = 0

        retriever = Retriever(empty_store, mock_embedding_generator)
        retriever.retrieve("test query", top_k=5)

        # Should not call the embedding generator for empty store
        mock_embedding_generator.generate_query_embedding.assert_not_called()


@pytest.mark.unit
class TestRetrievalResult:
    """Test cases for RetrievalResult dataclass."""

    def test_retrieval_result_repr(self):
        """Test RetrievalResult string representation."""
        chunk = create_test_chunk("test_001", "Test text")
        result = RetrievalResult(chunk=chunk, score=0.85)

        repr_str = repr(result)
        assert "test_001" in repr_str
        assert "0.850" in repr_str

    def test_retrieval_result_attributes(self):
        """Test RetrievalResult attribute access."""
        chunk = create_test_chunk("test_001", "Test text")
        result = RetrievalResult(chunk=chunk, score=0.92)

        assert result.chunk.chunk_id == "test_001"
        assert result.score == 0.92


@pytest.mark.unit
class TestRetrieverMinScore:
    """Test cases for min_score filtering."""

    def test_min_score_filters_low_scores(self, mock_embedding_generator):
        """Test that min_score filters out results below threshold."""
        store = Mock()
        store.collection_name = "test_collection"
        store.count.return_value = 10

        # Set up results with varying scores
        chunks = [
            create_test_chunk("chunk_001", "High relevance", 0),
            create_test_chunk("chunk_002", "Medium relevance", 1),
            create_test_chunk("chunk_003", "Low relevance", 2),
        ]
        store.search.return_value = [
            (chunks[0], 0.90),
            (chunks[1], 0.50),
            (chunks[2], 0.20),
        ]

        retriever = Retriever(store, mock_embedding_generator)
        results = retriever.retrieve("test query", top_k=5, min_score=0.45)

        assert len(results) == 2
        assert results[0].chunk_id == "chunk_001"
        assert results[1].chunk_id == "chunk_002"

    def test_min_score_none_returns_all(self, mock_embedding_generator):
        """Test that min_score=None returns all results."""
        store = Mock()
        store.collection_name = "test_collection"
        store.count.return_value = 10

        chunks = [
            create_test_chunk("chunk_001", "Test", 0),
            create_test_chunk("chunk_002", "Test", 1),
        ]
        store.search.return_value = [
            (chunks[0], 0.90),
            (chunks[1], 0.10),
        ]

        retriever = Retriever(store, mock_embedding_generator)
        results = retriever.retrieve("test query", top_k=5, min_score=None)

        assert len(results) == 2

    def test_min_score_filters_all_returns_empty(self, mock_embedding_generator):
        """Test that high min_score can filter all results."""
        store = Mock()
        store.collection_name = "test_collection"
        store.count.return_value = 10

        chunks = [create_test_chunk("chunk_001", "Test", 0)]
        store.search.return_value = [(chunks[0], 0.30)]

        retriever = Retriever(store, mock_embedding_generator)
        results = retriever.retrieve("test query", top_k=5, min_score=0.50)

        assert len(results) == 0


@pytest.mark.unit
class TestRetrieverMinScoreValidation:
    """Test cases for min_score validation."""

    def test_min_score_invalid_type_raises_error(self, retriever):
        """Test that non-numeric min_score raises ValueError."""
        with pytest.raises(ValueError, match="min_score must be a number"):
            retriever.retrieve("test query", min_score="high")

    def test_min_score_below_zero_raises_error(self, retriever):
        """Test that min_score < 0 raises ValueError."""
        with pytest.raises(ValueError, match="min_score must be between 0 and 1"):
            retriever.retrieve("test query", min_score=-0.1)

    def test_min_score_above_one_raises_error(self, retriever):
        """Test that min_score > 1 raises ValueError."""
        with pytest.raises(ValueError, match="min_score must be between 0 and 1"):
            retriever.retrieve("test query", min_score=1.5)

    def test_min_score_boundary_values_valid(self, retriever):
        """Test that min_score at boundaries (0 and 1) is valid."""
        # Should not raise - these are edge-valid values
        retriever.retrieve("test query", min_score=0.0)
        retriever.retrieve("test query", min_score=1.0)


@pytest.mark.unit
class TestRetrieverBooleanValidation:
    """Test cases for boolean type validation."""

    def test_boolean_top_k_raises_error(self, retriever):
        """Test that boolean top_k is rejected."""
        with pytest.raises(ValueError, match="top_k must be an integer, got bool"):
            retriever.retrieve("test query", top_k=True)

        with pytest.raises(ValueError, match="top_k must be an integer, got bool"):
            retriever.retrieve("test query", top_k=False)
