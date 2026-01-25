"""Unit tests for FlashcardGeneratorService."""

from unittest.mock import MagicMock, patch

import pytest

from src.application.flashcard_service import FlashcardGeneratorService
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
        assert progress_calls[0][0] == 1  # Current page
        assert progress_calls[0][1] == 3  # Total pages
        assert progress_calls[2][0] == 3  # Last call

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
