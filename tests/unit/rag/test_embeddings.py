"""Unit tests for EmbeddingGenerator."""

from unittest.mock import Mock, patch

import pytest
from openai import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

from src.domain.models.chunk import Chunk
from src.domain.rag.embeddings import EmbeddingGenerator


def create_test_chunk(
    chunk_id: str = "test_chunk_001",
    text: str = "This is test text for embedding.",
    position: int = 0,
) -> Chunk:
    """Create a test chunk with default values."""
    return Chunk(
        chunk_id=chunk_id,
        text=text,
        source_document="/path/to/test.pdf",
        page_numbers=[1, 2],
        position=position,
        token_count=10,
        char_count=len(text),
        has_overlap_before=False,
        has_overlap_after=False,
    )


@pytest.mark.unit
class TestEmbeddingGeneratorInit:
    """Test cases for EmbeddingGenerator initialization."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    def test_initialization_with_settings(self, mock_settings):
        """Test initialization loads API key from settings."""
        generator = EmbeddingGenerator()
        assert generator.api_key == "test-api-key"
        assert generator.total_tokens == 0
        assert generator.api_calls == 0

    def test_initialization_with_custom_api_key(self, mock_settings):
        """Test initialization with custom API key."""
        generator = EmbeddingGenerator(api_key="custom-key")
        assert generator.api_key == "custom-key"

    def test_initialization_without_api_key_raises_error(self):
        """Test initialization raises error when no API key available."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = None
            mock.return_value = settings

            with pytest.raises(ValueError, match="OpenAI API key required"):
                EmbeddingGenerator()

    def test_initialization_model_constants(self, mock_settings):
        """Test model constants are set correctly."""
        generator = EmbeddingGenerator()
        assert generator.MODEL == "text-embedding-3-small"
        assert generator.EMBEDDING_DIMENSIONS == 1536
        assert generator.MAX_BATCH_SIZE == 2048


@pytest.mark.unit
class TestGenerateEmbeddings:
    """Test cases for generate_embeddings method."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def generator(self, mock_settings):
        """Create an EmbeddingGenerator instance for testing."""
        return EmbeddingGenerator(min_request_interval=0)

    def test_generate_embeddings_success(self, generator):
        """Test successful embedding generation."""
        chunks = [create_test_chunk("chunk_001"), create_test_chunk("chunk_002")]

        # Create mock embedding (1536 dimensions)
        mock_embedding = [0.1] * 1536

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.data = [
            Mock(embedding=mock_embedding, index=0),
            Mock(embedding=mock_embedding, index=1),
        ]
        mock_response.usage = Mock(total_tokens=100)

        with patch.object(
            generator.client.embeddings, "create", return_value=mock_response
        ):
            result = generator.generate_embeddings(chunks)

        # Verify result
        assert result is chunks  # Returns same list
        assert len(result) == 2
        assert result[0].has_embedding()
        assert result[1].has_embedding()
        assert len(result[0].embedding) == 1536

        # Verify token tracking
        assert generator.total_tokens == 100
        assert generator.api_calls == 1

    def test_generate_embeddings_empty_list(self, generator):
        """Test with empty chunk list."""
        result = generator.generate_embeddings([])
        assert result == []
        assert generator.api_calls == 0

    def test_generate_embeddings_chunk_without_text_raises_error(self, generator):
        """Test that chunk with empty text raises ValueError."""
        chunk = create_test_chunk()
        chunk.text = ""

        with pytest.raises(ValueError, match="has empty text"):
            generator.generate_embeddings([chunk])

    def test_generate_embeddings_chunk_with_whitespace_only_raises_error(
        self, generator
    ):
        """Test that chunk with whitespace-only text raises ValueError."""
        chunk = create_test_chunk()
        chunk.text = "   \n\t  "

        with pytest.raises(ValueError, match="has empty text"):
            generator.generate_embeddings([chunk])

    def test_generate_embeddings_updates_chunks_in_place(self, generator):
        """Test that embeddings are updated in place on the original chunks."""
        chunks = [create_test_chunk()]
        mock_embedding = [0.5] * 1536

        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding, index=0)]
        mock_response.usage = Mock(total_tokens=50)

        with patch.object(
            generator.client.embeddings, "create", return_value=mock_response
        ):
            result = generator.generate_embeddings(chunks)

        # Verify original chunks are modified
        assert chunks[0].embedding == mock_embedding
        assert result[0] is chunks[0]


@pytest.mark.unit
class TestBatching:
    """Test cases for batch processing."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def generator(self, mock_settings):
        """Create an EmbeddingGenerator instance for testing."""
        return EmbeddingGenerator(min_request_interval=0)

    def test_create_batches_single_batch(self, generator):
        """Test that small chunk list stays in single batch."""
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(10)]
        batches = generator._create_batches(chunks)
        assert len(batches) == 1
        assert len(batches[0]) == 10

    def test_create_batches_multiple_batches(self, generator):
        """Test that large chunk list is split into multiple batches."""
        # Create more chunks than MAX_BATCH_SIZE
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(2100)]
        batches = generator._create_batches(chunks)

        assert len(batches) == 2
        assert len(batches[0]) == 2048  # MAX_BATCH_SIZE
        assert len(batches[1]) == 52  # Remainder

    def test_create_batches_exact_batch_size(self, generator):
        """Test exact batch size boundary."""
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(2048)]
        batches = generator._create_batches(chunks)
        assert len(batches) == 1
        assert len(batches[0]) == 2048

    def test_generate_embeddings_processes_all_batches(self, generator):
        """Test that all batches are processed."""
        # Create 5 chunks
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(5)]
        mock_embedding = [0.1] * 1536

        # Mock to return embeddings for any input
        def create_mock_response(input_texts):
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=mock_embedding, index=i) for i in range(len(input_texts))
            ]
            mock_response.usage = Mock(total_tokens=50 * len(input_texts))
            return mock_response

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=lambda model, input: create_mock_response(input),
        ):
            generator.generate_embeddings(chunks)

        # All chunks should have embeddings
        assert all(chunk.has_embedding() for chunk in chunks)


@pytest.mark.unit
class TestRetryLogic:
    """Test cases for retry behavior."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def generator(self, mock_settings):
        """Create an EmbeddingGenerator instance for testing."""
        return EmbeddingGenerator(min_request_interval=0)

    def test_authentication_error_no_retry(self, generator):
        """Test that authentication errors are not retried."""
        chunks = [create_test_chunk()]

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=AuthenticationError(
                "Invalid API key", response=Mock(), body=None
            ),
        ):
            with pytest.raises(AuthenticationError):
                generator.generate_embeddings(chunks)

        # Should only call once (no retry)
        assert generator.api_calls == 0  # Not incremented on failure

    def test_bad_request_error_no_retry(self, generator):
        """Test that bad request errors are not retried."""
        chunks = [create_test_chunk()]

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=BadRequestError("Invalid request", response=Mock(), body=None),
        ):
            with pytest.raises(BadRequestError):
                generator.generate_embeddings(chunks)

    @patch("src.domain.rag.embeddings.time.sleep")
    def test_rate_limit_retry_success(self, mock_sleep, generator):
        """Test retry on rate limit error."""
        chunks = [create_test_chunk()]
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding, index=0)]
        mock_response.usage = Mock(total_tokens=50)

        # First call fails, second succeeds
        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=[
                RateLimitError("Rate limited", response=Mock(), body=None),
                mock_response,
            ],
        ):
            result = generator.generate_embeddings(chunks)

        assert result[0].has_embedding()
        mock_sleep.assert_called_once_with(1)  # Exponential backoff: 2^0 = 1

    @patch("src.domain.rag.embeddings.time.sleep")
    def test_server_error_retry_success(self, mock_sleep, generator):
        """Test retry on server error."""
        chunks = [create_test_chunk()]
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding, index=0)]
        mock_response.usage = Mock(total_tokens=50)

        # First call fails, second succeeds
        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=[
                InternalServerError("Server error", response=Mock(), body=None),
                mock_response,
            ],
        ):
            result = generator.generate_embeddings(chunks)

        assert result[0].has_embedding()

    @patch("src.domain.rag.embeddings.time.sleep")
    def test_connection_error_retry_success(self, mock_sleep, generator):
        """Test retry on connection error."""
        chunks = [create_test_chunk()]
        mock_embedding = [0.1] * 1536

        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding, index=0)]
        mock_response.usage = Mock(total_tokens=50)

        # First call fails, second succeeds
        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=[
                APIConnectionError(message="Connection failed", request=Mock()),
                mock_response,
            ],
        ):
            result = generator.generate_embeddings(chunks)

        assert result[0].has_embedding()

    @patch("src.domain.rag.embeddings.time.sleep")
    def test_max_retries_exhausted(self, mock_sleep, generator):
        """Test that max retries are respected."""
        chunks = [create_test_chunk()]

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=RateLimitError("Rate limited", response=Mock(), body=None),
        ):
            with pytest.raises(RateLimitError):
                generator.generate_embeddings(chunks, max_retries=3)

        # Should sleep before retry 2 and 3
        assert mock_sleep.call_count == 2

    @patch("src.domain.rag.embeddings.time.sleep")
    def test_exponential_backoff(self, mock_sleep, generator):
        """Test exponential backoff timing."""
        chunks = [create_test_chunk()]

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=RateLimitError("Rate limited", response=Mock(), body=None),
        ):
            with pytest.raises(RateLimitError):
                generator.generate_embeddings(chunks, max_retries=3)

        # Check backoff times: 2^0=1s, 2^1=2s
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)


@pytest.mark.unit
class TestUsageTracking:
    """Test cases for usage statistics."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def generator(self, mock_settings):
        """Create an EmbeddingGenerator instance for testing."""
        return EmbeddingGenerator(min_request_interval=0)

    def test_get_usage_stats_initial(self, generator):
        """Test initial usage stats."""
        stats = generator.get_usage_stats()

        assert stats["api_calls"] == 0
        assert stats["total_tokens"] == 0
        assert stats["estimated_cost"] == 0
        assert stats["model"] == "text-embedding-3-small"
        assert stats["dimensions"] == 1536

    def test_get_usage_stats_after_calls(self, generator):
        """Test usage stats after API calls."""
        generator.total_tokens = 100000  # 100k tokens
        generator.api_calls = 5

        stats = generator.get_usage_stats()

        assert stats["api_calls"] == 5
        assert stats["total_tokens"] == 100000
        # Cost: 100k / 1M * $0.02 = $0.002
        assert stats["estimated_cost"] == 0.002

    def test_reset_stats(self, generator):
        """Test resetting statistics."""
        generator.total_tokens = 50000
        generator.api_calls = 3

        generator.reset_stats()

        assert generator.total_tokens == 0
        assert generator.api_calls == 0

    def test_usage_accumulates_across_calls(self, generator):
        """Test that usage accumulates across multiple generate_embeddings calls."""
        mock_embedding = [0.1] * 1536

        def create_response(input_texts):
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=mock_embedding, index=i) for i in range(len(input_texts))
            ]
            mock_response.usage = Mock(total_tokens=100)
            return mock_response

        with patch.object(
            generator.client.embeddings,
            "create",
            side_effect=lambda model, input: create_response(input),
        ):
            generator.generate_embeddings([create_test_chunk("chunk_1")])
            generator.generate_embeddings([create_test_chunk("chunk_2")])
            generator.generate_embeddings([create_test_chunk("chunk_3")])

        assert generator.total_tokens == 300  # 100 per call
        assert generator.api_calls == 3


@pytest.mark.unit
class TestGenerateQueryEmbedding:
    """Test cases for generate_query_embedding method."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.rag.embeddings.get_settings") as mock:
            settings = Mock()
            settings.openai_api_key = "test-api-key"
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def generator(self, mock_settings):
        """Create an EmbeddingGenerator instance for testing."""
        return EmbeddingGenerator(min_request_interval=0)

    def test_generate_query_embedding_success(self, generator):
        """Test successful query embedding generation."""
        mock_embedding = [0.5] * 1536

        mock_response = Mock()
        mock_response.data = [Mock(embedding=mock_embedding, index=0)]
        mock_response.usage = Mock(total_tokens=10)

        with patch.object(
            generator.client.embeddings, "create", return_value=mock_response
        ):
            result = generator.generate_query_embedding("What is machine learning?")

        assert result == mock_embedding
        assert len(result) == 1536

    def test_generate_query_embedding_empty_raises_error(self, generator):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            generator.generate_query_embedding("")

    def test_generate_query_embedding_whitespace_raises_error(self, generator):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            generator.generate_query_embedding("   \n\t  ")
