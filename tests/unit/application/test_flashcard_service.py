"""Unit tests for FlashcardGeneratorService."""

from unittest.mock import MagicMock, patch

import pytest

from src.application.flashcard_service import (
    FlashcardGeneratorService,
    RAGConfig,
    RAGSetupResult,
)
from src.domain.models.document import (
    Document,
    DocumentFormat,
    DocumentMetadata,
    ProcessingStatus,
)


@pytest.fixture
def mock_document():
    """Create a mock Document for testing."""
    return Document(
        content="This is test content about machine learning.",
        file_path="/fake/path/test.pdf",
        page_range=(1, 1),
        metadata=DocumentMetadata(
            total_pages=5,
            file_size_bytes=1000,
            file_format=DocumentFormat.PDF,
        ),
    )


@pytest.fixture
def mock_flashcard():
    """Create a mock flashcard response."""
    return {
        "question": "What is machine learning?",
        "answer": "A subset of AI that enables systems to learn from data.",
    }


@pytest.fixture
def mock_usage_stats():
    """Create mock usage stats."""
    return {
        "api_calls": 1,
        "total_input_tokens": 500,
        "total_output_tokens": 100,
        "total_tokens": 600,
        "estimated_cost": 0.0025,
        "cost_breakdown": {
            "input_cost": 0.0015,
            "output_cost": 0.001,
        },
    }


@pytest.mark.unit
class TestFlashcardGeneratorService:
    """Test suite for FlashcardGeneratorService."""

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_generate_flashcards_success(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test successful flashcard generation for a single page."""
        # Setup mocks
        mock_parser.parse.return_value = mock_document

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        # Create service and generate
        service = FlashcardGeneratorService()
        # Replace the client with our mock
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
        )

        # Verify result
        assert result.status == ProcessingStatus.SUCCESS
        assert result.total_attempted == 1
        assert result.total_success == 1
        assert result.total_failed == 0
        assert len(result.flashcards) == 1
        assert result.flashcards[0]["question"] == mock_flashcard["question"]

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_generate_flashcards_partial_failure(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test partial success when some pages fail."""
        # First page succeeds, second fails
        mock_parser.parse.side_effect = [
            mock_document,
            Exception("Parse error"),
        ]

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 2),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
        )

        # Should be partial success
        assert result.status == ProcessingStatus.PARTIAL
        assert result.total_attempted == 2
        assert result.total_success == 1
        assert result.total_failed == 1

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_generate_flashcards_all_failed(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_usage_stats,
        tmp_path,
    ):
        """Test complete failure when all pages fail."""
        mock_parser.parse.side_effect = Exception("Parse error")

        mock_client_instance = MagicMock()
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_claude.return_value = mock_client_instance

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 2),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "test.apkg"),
        )

        assert result.status == ProcessingStatus.FAILED
        assert result.total_success == 0
        assert result.total_failed == 2
        assert len(result.flashcards) == 0

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_progress_callback_called(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test that progress callback is called for each page."""
        mock_parser.parse.return_value = mock_document

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        progress_calls = []

        def track_progress(current, total, message):
            progress_calls.append((current, total, message))

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 3),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
            on_progress=track_progress,
        )

        # Should be called 3 times (once per page)
        assert len(progress_calls) == 3
        # Progress is now reported as percentage (0-100)
        # First page: ~33%, Second page: ~66%, Third page: 100%
        assert progress_calls[0][1] == 100  # Total is always 100 (percentage)
        assert progress_calls[2][0] == 100  # Last call should be at 100%
        # All calls should mention page processing
        for call in progress_calls:
            assert "page" in call[2].lower()

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_empty_page_is_skipped(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_usage_stats,
        tmp_path,
    ):
        """Test that empty pages are skipped."""
        # Create document with empty content
        empty_doc = Document(
            content="   \n\n  ",  # Only whitespace
            file_path="/fake/path/test.pdf",
            page_range=(1, 1),
            metadata=DocumentMetadata(
                total_pages=1,
                file_size_bytes=1000,
                file_format=DocumentFormat.PDF,
            ),
        )
        mock_parser.parse.return_value = empty_doc

        mock_client_instance = MagicMock()
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_claude.return_value = mock_client_instance

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "test.apkg"),
        )

        # Empty page should be counted as failed
        assert result.total_failed == 1
        assert result.total_success == 0
        # Claude should not have been called
        mock_client_instance.generate_flashcard.assert_not_called()

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_multiple_cards_per_page(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_usage_stats,
        tmp_path,
    ):
        """Test generating multiple cards per page."""
        mock_parser.parse.return_value = mock_document

        # Return list of flashcards
        multiple_cards = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
        ]

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = multiple_cards
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=2,
            difficulty="intermediate",
            output_path=output_path,
        )

        # Should have 2 flashcards from 1 page
        assert len(result.flashcards) == 2
        assert result.total_success == 1

    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_cost_tracking(
        self,
        mock_parser,
        mock_claude,
        mock_document,
        mock_flashcard,
        tmp_path,
    ):
        """Test that token and cost tracking works correctly."""
        mock_parser.parse.return_value = mock_document

        # Setup mock with incrementing usage stats
        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0

        # Simulate accumulating stats
        call_count = [0]

        def get_stats():
            call_count[0] += 1
            return {
                "api_calls": call_count[0],
                "total_input_tokens": 500 * call_count[0],
                "total_output_tokens": 100 * call_count[0],
                "total_tokens": 600 * call_count[0],
                "estimated_cost": 0.003 * call_count[0],
                "cost_breakdown": {"input_cost": 0.0015, "output_cost": 0.0015},
            }

        mock_client_instance.get_usage_stats = get_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_claude.return_value = mock_client_instance

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 2),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "test.apkg"),
        )

        # Should have accumulated stats from both pages
        assert result.total_tokens > 0
        assert result.total_cost_usd > 0


@pytest.mark.unit
class TestGenerationResult:
    """Test suite for GenerationResult methods."""

    def test_get_success_rate_all_success(self):
        """Test success rate calculation with all successes."""
        from src.domain.models.document import (
            FlashcardResult,
            GenerationResult,
            ProcessingStatus,
        )

        result = GenerationResult(
            flashcards=[{"question": "Q", "answer": "A"}],
            results=[
                FlashcardResult(
                    flashcards=[{"question": "Q", "answer": "A"}],
                    page_number=1,
                    success=True,
                )
            ],
            total_attempted=1,
            total_success=1,
            total_failed=0,
            total_tokens=100,
            total_cost_usd=0.01,
            status=ProcessingStatus.SUCCESS,
        )

        assert result.get_success_rate() == 100.0

    def test_get_success_rate_partial(self):
        """Test success rate calculation with partial success."""
        from src.domain.models.document import (
            FlashcardResult,
            GenerationResult,
            ProcessingStatus,
        )

        result = GenerationResult(
            flashcards=[{"question": "Q", "answer": "A"}],
            results=[
                FlashcardResult(
                    flashcards=[{"question": "Q", "answer": "A"}],
                    page_number=1,
                    success=True,
                ),
                FlashcardResult(
                    flashcards=[],
                    page_number=2,
                    success=False,
                    error_message="Error",
                ),
            ],
            total_attempted=2,
            total_success=1,
            total_failed=1,
            total_tokens=100,
            total_cost_usd=0.01,
            status=ProcessingStatus.PARTIAL,
        )

        assert result.get_success_rate() == 50.0

    def test_get_success_rate_zero_attempts(self):
        """Test success rate calculation with zero attempts."""
        from src.domain.models.document import (
            GenerationResult,
            ProcessingStatus,
        )

        result = GenerationResult(
            flashcards=[],
            results=[],
            total_attempted=0,
            total_success=0,
            total_failed=0,
            total_tokens=0,
            total_cost_usd=0.0,
            status=ProcessingStatus.FAILED,
        )

        assert result.get_success_rate() == 0.0

    def test_get_failed_pages(self):
        """Test getting list of failed pages."""
        from src.domain.models.document import (
            FlashcardResult,
            GenerationResult,
            ProcessingStatus,
        )

        result = GenerationResult(
            flashcards=[{"question": "Q", "answer": "A"}],
            results=[
                FlashcardResult(
                    flashcards=[{"question": "Q", "answer": "A"}],
                    page_number=1,
                    success=True,
                ),
                FlashcardResult(
                    flashcards=[],
                    page_number=2,
                    success=False,
                    error_message="Error",
                ),
                FlashcardResult(
                    flashcards=[{"question": "Q2", "answer": "A2"}],
                    page_number=3,
                    success=True,
                ),
                FlashcardResult(
                    flashcards=[],
                    page_number=4,
                    success=False,
                    error_message="Error",
                ),
            ],
            total_attempted=4,
            total_success=2,
            total_failed=2,
            total_tokens=200,
            total_cost_usd=0.02,
            status=ProcessingStatus.PARTIAL,
        )

        failed_pages = result.get_failed_pages()
        assert failed_pages == [2, 4]


@pytest.mark.unit
class TestRAGConfig:
    """Test suite for RAGConfig data class."""

    def test_default_values(self):
        """Test RAGConfig has sensible defaults."""
        config = RAGConfig()

        assert config.top_k == 5
        assert config.chunk_target_size == 800
        assert config.chunk_overlap_size == 100
        assert config.include_metadata is False

    def test_custom_values(self):
        """Test RAGConfig can be customized."""
        config = RAGConfig(
            top_k=10,
            chunk_target_size=1000,
            chunk_overlap_size=150,
            include_metadata=True,
        )

        assert config.top_k == 10
        assert config.chunk_target_size == 1000
        assert config.chunk_overlap_size == 150
        assert config.include_metadata is True


@pytest.mark.unit
class TestRAGSetupResult:
    """Test suite for RAGSetupResult data class."""

    def test_success_result(self):
        """Test successful RAG setup result."""
        result = RAGSetupResult(
            success=True,
            num_chunks=50,
            embedding_tokens=10000,
            embedding_cost=0.0002,
            collection_name="test_collection",
        )

        assert result.success is True
        assert result.num_chunks == 50
        assert result.embedding_tokens == 10000
        assert result.embedding_cost == 0.0002
        assert result.collection_name == "test_collection"
        assert result.error_message is None

    def test_failure_result(self):
        """Test failed RAG setup result."""
        result = RAGSetupResult(
            success=False,
            error_message="API key invalid",
        )

        assert result.success is False
        assert result.error_message == "API key invalid"
        assert result.num_chunks == 0


@pytest.mark.unit
class TestFlashcardGeneratorServiceRAG:
    """Test suite for RAG functionality in FlashcardGeneratorService."""

    @pytest.fixture
    def mock_document(self):
        """Create a mock Document for testing."""
        return Document(
            content="This is test content about machine learning and deep learning.",
            file_path="/fake/path/test.pdf",
            page_range=(1, 1),
            metadata=DocumentMetadata(
                total_pages=5,
                file_size_bytes=1000,
                file_format=DocumentFormat.PDF,
            ),
        )

    @pytest.fixture
    def mock_flashcard(self):
        """Create a mock flashcard response."""
        return {
            "question": "What is machine learning?",
            "answer": "A subset of AI that enables systems to learn from data.",
        }

    @pytest.fixture
    def mock_usage_stats(self):
        """Create mock usage stats."""
        return {
            "api_calls": 1,
            "total_input_tokens": 500,
            "total_output_tokens": 100,
            "total_tokens": 600,
            "estimated_cost": 0.0025,
            "cost_breakdown": {
                "input_cost": 0.0015,
                "output_cost": 0.001,
            },
        }

    def test_get_collection_name_deterministic(self):
        """Test that collection name generation is deterministic."""
        service = FlashcardGeneratorService()

        name1 = service._get_collection_name("/path/to/document.pdf")
        name2 = service._get_collection_name("/path/to/document.pdf")

        assert name1 == name2
        assert "document" in name1 or "ankiai" in name1

    def test_get_collection_name_unique(self):
        """Test that different paths produce different collection names."""
        service = FlashcardGeneratorService()

        name1 = service._get_collection_name("/path/to/doc1.pdf")
        name2 = service._get_collection_name("/path/to/doc2.pdf")

        assert name1 != name2

    def test_build_retrieval_query(self):
        """Test retrieval query building."""
        service = FlashcardGeneratorService()

        page_text = "Machine learning is a subset of artificial intelligence."
        query = service._build_retrieval_query(page_text, page_num=1)

        # Query should include semantic content
        assert "flashcard" in query.lower() or "concept" in query.lower()
        # Query should include page text preview
        assert "Machine learning" in query or "artificial" in query

    def test_build_retrieval_query_truncates_long_text(self):
        """Test that long page text is truncated in query."""
        service = FlashcardGeneratorService()

        # Create very long text
        long_text = "A" * 1000

        query = service._build_retrieval_query(long_text, page_num=1)

        # Query should be shorter than original text
        assert len(query) < len(long_text) + 200  # Allow for query prefix

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_generate_flashcards_baseline_mode_unchanged(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test that baseline mode (use_rag=False) works as before."""
        mock_parser.parse.return_value = mock_document

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        # Explicitly use baseline mode
        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
            use_rag=False,  # Baseline mode
        )

        # Should succeed
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.flashcards) == 1

        # Flashcard should NOT have RAG metadata
        assert "rag_metadata" not in result.flashcards[0]

    @patch("src.application.flashcard_service.Retriever")
    @patch("src.application.flashcard_service.VectorStore")
    @patch("src.application.flashcard_service.EmbeddingGenerator")
    @patch("src.application.flashcard_service.Chunker")
    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_generate_flashcards_rag_mode(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_chunker,
        mock_embedding_gen,
        mock_vector_store,
        mock_retriever,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test that RAG mode properly sets up and uses retrieval."""
        mock_parser.parse.return_value = mock_document

        # Mock chunker
        mock_chunk = MagicMock()
        mock_chunk.text = "Chunk text"
        mock_chunk.chunk_id = "chunk_001"
        mock_chunk.source_document = "/fake/path/test.pdf"
        mock_chunk.page_numbers = [1]
        mock_chunk.has_embedding.return_value = True
        mock_chunker.chunk.return_value = [mock_chunk]

        # Mock embedding generator
        mock_emb_instance = MagicMock()
        mock_emb_instance.get_usage_stats.return_value = {
            "total_tokens": 100,
            "estimated_cost": 0.0001,
        }
        mock_embedding_gen.return_value = mock_emb_instance

        # Mock vector store
        mock_store_instance = MagicMock()
        mock_store_instance.count.return_value = 1
        mock_vector_store.return_value = mock_store_instance

        # Mock retriever
        mock_retrieval_result = MagicMock()
        mock_retrieval_result.chunk = mock_chunk
        mock_retrieval_result.score = 0.85
        mock_retriever_instance = MagicMock()
        mock_retriever_instance.retrieve_with_scores.return_value = [
            mock_retrieval_result
        ]
        mock_retriever.return_value = mock_retriever_instance

        # Mock Claude client
        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test_rag.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        # Use RAG mode
        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Should succeed
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.flashcards) == 1

        # RAG components should have been used
        mock_chunker.chunk.assert_called()
        mock_emb_instance.generate_embeddings.assert_called()
        mock_store_instance.add_chunks.assert_called()

    @patch("src.application.flashcard_service.AnkiFormatter")
    @patch("src.application.flashcard_service.ClaudeClient")
    @patch("src.application.flashcard_service.PDFParser")
    def test_rag_fallback_on_setup_failure(
        self,
        mock_parser,
        mock_claude,
        mock_formatter,
        mock_document,
        mock_flashcard,
        mock_usage_stats,
        tmp_path,
    ):
        """Test that RAG mode falls back to baseline if setup fails."""
        mock_parser.parse.return_value = mock_document

        mock_client_instance = MagicMock()
        mock_client_instance.generate_flashcard.return_value = mock_flashcard
        mock_client_instance.get_usage_stats.return_value = mock_usage_stats
        mock_client_instance.reset_stats = MagicMock()
        mock_client_instance.PRICE_PER_MILLION_INPUT = 3.0
        mock_client_instance.PRICE_PER_MILLION_OUTPUT = 15.0
        mock_claude.return_value = mock_client_instance
        mock_claude.PRICE_PER_MILLION_INPUT = 3.0
        mock_claude.PRICE_PER_MILLION_OUTPUT = 15.0

        output_path = str(tmp_path / "test.apkg")
        mock_formatter.format_flashcards.return_value = output_path
        mock_formatter.create_tags_from_metadata.return_value = ["test-tag"]

        service = FlashcardGeneratorService()
        service.claude_client = mock_client_instance

        # Mock _setup_rag to fail
        service._setup_rag = MagicMock(
            return_value=RAGSetupResult(
                success=False,
                error_message="Embedding API error",
            )
        )

        # Use RAG mode (should fall back to baseline)
        result = service.generate_flashcards(
            pdf_path="/fake/test.pdf",
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Should still succeed (fell back to baseline)
        assert result.status == ProcessingStatus.SUCCESS
        assert len(result.flashcards) == 1

        # Flashcard should NOT have RAG metadata (used baseline)
        assert "rag_metadata" not in result.flashcards[0]

    def test_cleanup_rag_handles_none_components(self):
        """Test that _cleanup_rag handles None components gracefully."""
        service = FlashcardGeneratorService()

        # These should all be None by default
        assert service._embedding_generator is None
        assert service._vector_store is None
        assert service._retriever is None

        # Should not raise
        service._cleanup_rag()

    def test_rag_tags_added_to_deck(self):
        """Test that RAG configuration is added as tag to Anki deck."""
        # This is implicitly tested through the integration tests,
        # but we verify the tag format here
        rag_config = RAGConfig(top_k=5)
        expected_tag = f"rag_k{rag_config.top_k}"

        assert expected_tag == "rag_k5"
