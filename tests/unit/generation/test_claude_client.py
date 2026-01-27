"""Unit tests for ClaudeClient."""

from unittest.mock import Mock, patch

import pytest
from anthropic import (
    APIConnectionError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    RateLimitError,
)

from src.domain.generation.claude_client import (
    ClaudeClient,
    extract_json_from_text,
)


@pytest.mark.unit
class TestClaudeClient:
    """Test cases for ClaudeClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        with patch("src.domain.generation.claude_client.get_settings") as mock:
            settings = Mock()
            settings.anthropic_api_key = "test-api-key"
            settings.claude_model = "claude-sonnet-4-5-20250929"
            settings.claude_temperature = 0.7
            settings.claude_max_tokens = 1024
            mock.return_value = settings
            yield mock

    @pytest.fixture
    def client(self, mock_settings):
        """Create a ClaudeClient instance for testing."""
        # Disable rate limiting in tests to avoid interfering with retry timing tests
        return ClaudeClient(min_request_interval=0)

    def test_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test-api-key"
        assert client.model == "claude-sonnet-4-5-20250929"
        assert client.temperature == 0.7
        assert client.max_tokens == 1024
        assert client.total_input_tokens == 0
        assert client.total_output_tokens == 0
        assert client.api_calls == 0

    def test_initialization_with_custom_api_key(self, mock_settings):
        """Test initialization with custom API key."""
        client = ClaudeClient(api_key="custom-key")
        assert client.api_key == "custom-key"

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_success(self, mock_anthropic, client):
        """Test successful flashcard generation."""
        # Mock API response
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?", "answer": "A."}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Generate flashcard
        result = client.generate_flashcard("Test prompt")

        # Verify result
        assert result == {"question": "Q?", "answer": "A."}

        # Verify token tracking
        assert client.total_input_tokens == 100
        assert client.total_output_tokens == 50
        assert client.api_calls == 1

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_multiple_cards(self, mock_anthropic, client):
        """Test generation of multiple flashcards."""
        # Mock API response with array
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='[{"question": "Q1?", "answer": "A1."}, {"question": "Q2?", "answer": "A2."}]'
            )
        ]
        mock_response.usage = Mock(input_tokens=150, output_tokens=75)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Generate flashcards
        result = client.generate_flashcard("Test prompt")

        # Verify result
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"question": "Q1?", "answer": "A1."}
        assert result[1] == {"question": "Q2?", "answer": "A2."}

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_with_surrounding_text(self, mock_anthropic, client):
        """Test parsing JSON with surrounding text."""
        # Mock API response with surrounding text
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='Here is the flashcard:\n{"question": "Q?", "answer": "A."}\n\nI hope this helps!'
            )
        ]
        mock_response.usage = Mock(input_tokens=100, output_tokens=60)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Generate flashcard
        result = client.generate_flashcard("Test prompt")

        # Should successfully extract JSON
        assert result == {"question": "Q?", "answer": "A."}

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_authentication_error_no_retry(
        self, mock_anthropic, client
    ):
        """Test that authentication errors are not retried."""
        mock_anthropic.return_value.messages.create.side_effect = AuthenticationError(
            "Invalid API key", response=Mock(), body=None
        )
        client.client = mock_anthropic.return_value

        # Should raise without retry
        with pytest.raises(AuthenticationError):
            client.generate_flashcard("Test prompt")

        # Should only try once
        assert mock_anthropic.return_value.messages.create.call_count == 1

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_bad_request_error_no_retry(
        self, mock_anthropic, client
    ):
        """Test that bad request errors are not retried."""
        mock_anthropic.return_value.messages.create.side_effect = BadRequestError(
            "Invalid request", response=Mock(), body=None
        )
        client.client = mock_anthropic.return_value

        # Should raise without retry
        with pytest.raises(BadRequestError):
            client.generate_flashcard("Test prompt")

        # Should only try once
        assert mock_anthropic.return_value.messages.create.call_count == 1

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    @patch("src.domain.generation.claude_client.time.sleep")
    def test_generate_flashcard_rate_limit_retry_success(
        self, mock_sleep, mock_anthropic, client
    ):
        """Test retry on rate limit error."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?", "answer": "A."}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.side_effect = [
            RateLimitError("Rate limited", response=Mock(), body=None),
            mock_response,
        ]
        client.client = mock_anthropic.return_value

        # Should succeed after retry
        result = client.generate_flashcard("Test prompt")

        assert result == {"question": "Q?", "answer": "A."}
        assert mock_anthropic.return_value.messages.create.call_count == 2
        # Should have slept once (exponential backoff: 2^0 = 1 second)
        mock_sleep.assert_called_once_with(1)

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    @patch("src.domain.generation.claude_client.time.sleep")
    def test_generate_flashcard_server_error_retry_success(
        self, mock_sleep, mock_anthropic, client
    ):
        """Test retry on server error."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?", "answer": "A."}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.side_effect = [
            InternalServerError("Server error", response=Mock(), body=None),
            mock_response,
        ]
        client.client = mock_anthropic.return_value

        # Should succeed after retry
        result = client.generate_flashcard("Test prompt")

        assert result == {"question": "Q?", "answer": "A."}
        assert mock_anthropic.return_value.messages.create.call_count == 2

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    @patch("src.domain.generation.claude_client.time.sleep")
    def test_generate_flashcard_connection_error_retry_success(
        self, mock_sleep, mock_anthropic, client
    ):
        """Test retry on connection error."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?", "answer": "A."}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        # APIConnectionError requires message and request parameters
        connection_error = APIConnectionError(
            message="Connection failed", request=Mock()
        )
        mock_anthropic.return_value.messages.create.side_effect = [
            connection_error,
            mock_response,
        ]
        client.client = mock_anthropic.return_value

        # Should succeed after retry
        result = client.generate_flashcard("Test prompt")

        assert result == {"question": "Q?", "answer": "A."}
        assert mock_anthropic.return_value.messages.create.call_count == 2

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    @patch("src.domain.generation.claude_client.time.sleep")
    def test_generate_flashcard_max_retries_exhausted(
        self, mock_sleep, mock_anthropic, client
    ):
        """Test that max retries are respected."""
        # All calls fail
        mock_anthropic.return_value.messages.create.side_effect = RateLimitError(
            "Rate limited", response=Mock(), body=None
        )
        client.client = mock_anthropic.return_value

        # Should raise after max retries
        with pytest.raises(RateLimitError):
            client.generate_flashcard("Test prompt", max_retries=3)

        # Should try 3 times
        assert mock_anthropic.return_value.messages.create.call_count == 3
        # Should sleep 2 times (before retry 2 and 3)
        assert mock_sleep.call_count == 2

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    @patch("src.domain.generation.claude_client.time.sleep")
    def test_generate_flashcard_exponential_backoff(
        self, mock_sleep, mock_anthropic, client
    ):
        """Test exponential backoff timing."""
        # All calls fail
        mock_anthropic.return_value.messages.create.side_effect = RateLimitError(
            "Rate limited", response=Mock(), body=None
        )
        client.client = mock_anthropic.return_value

        # Should raise after max retries
        with pytest.raises(RateLimitError):
            client.generate_flashcard("Test prompt", max_retries=3)

        # Check backoff times: 2^0=1s, 2^1=2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(1)  # First retry
        mock_sleep.assert_any_call(2)  # Second retry

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_invalid_json_raises_error(self, mock_anthropic, client):
        """Test that invalid JSON raises ValueError."""
        mock_response = Mock()
        mock_response.content = [Mock(text="This is not JSON")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Should raise ValueError
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            client.generate_flashcard("Test prompt")

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_missing_required_field(self, mock_anthropic, client):
        """Test that flashcard missing required field raises error."""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?"}')]  # Missing answer
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Should raise ValueError
        with pytest.raises(ValueError, match="missing required field"):
            client.generate_flashcard("Test prompt")

    @patch("src.domain.generation.claude_client.anthropic.Anthropic")
    def test_generate_flashcard_empty_field(self, mock_anthropic, client):
        """Test that flashcard with empty field raises error."""
        mock_response = Mock()
        mock_response.content = [Mock(text='{"question": "Q?", "answer": ""}')]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        mock_anthropic.return_value.messages.create.return_value = mock_response
        client.client = mock_anthropic.return_value

        # Should raise ValueError
        with pytest.raises(ValueError, match="cannot be empty"):
            client.generate_flashcard("Test prompt")

    def test_get_usage_stats(self, client):
        """Test usage statistics calculation."""
        # Manually set token counts
        client.total_input_tokens = 1000
        client.total_output_tokens = 500
        client.api_calls = 3

        stats = client.get_usage_stats()

        assert stats["api_calls"] == 3
        assert stats["total_input_tokens"] == 1000
        assert stats["total_output_tokens"] == 500
        assert stats["total_tokens"] == 1500

        # Check cost calculation
        # Input: 1000 / 1M * $3 = $0.003
        # Output: 500 / 1M * $15 = $0.0075
        # Total: $0.0105
        assert stats["estimated_cost"] == 0.0105
        assert stats["cost_breakdown"]["input_cost"] == 0.003
        assert stats["cost_breakdown"]["output_cost"] == 0.0075

    def test_get_usage_stats_zero(self, client):
        """Test usage stats when no calls made."""
        stats = client.get_usage_stats()

        assert stats["api_calls"] == 0
        assert stats["total_tokens"] == 0
        assert stats["estimated_cost"] == 0

    def test_reset_stats(self, client):
        """Test resetting statistics."""
        # Set some values
        client.total_input_tokens = 1000
        client.total_output_tokens = 500
        client.api_calls = 3

        # Reset
        client.reset_stats()

        # Should be back to zero
        assert client.total_input_tokens == 0
        assert client.total_output_tokens == 0
        assert client.api_calls == 0


@pytest.mark.unit
class TestExtractJsonFromText:
    """Test cases for extract_json_from_text function."""

    def test_extract_json_plain_object(self):
        """Test extracting plain JSON object."""
        text = '{"question": "Q?", "answer": "A."}'
        result = extract_json_from_text(text)
        assert result == {"question": "Q?", "answer": "A."}

    def test_extract_json_plain_array(self):
        """Test extracting plain JSON array."""
        text = '[{"question": "Q1?"}, {"question": "Q2?"}]'
        result = extract_json_from_text(text)
        assert result == [{"question": "Q1?"}, {"question": "Q2?"}]

    def test_extract_json_with_prefix(self):
        """Test extracting JSON with prefix text."""
        text = 'Here is the flashcard:\n{"question": "Q?", "answer": "A."}'
        result = extract_json_from_text(text)
        assert result == {"question": "Q?", "answer": "A."}

    def test_extract_json_with_suffix(self):
        """Test extracting JSON with suffix text."""
        text = '{"question": "Q?", "answer": "A."}\n\nI hope this helps!'
        result = extract_json_from_text(text)
        assert result == {"question": "Q?", "answer": "A."}

    def test_extract_json_with_surrounding_text(self):
        """Test extracting JSON with both prefix and suffix."""
        text = 'Sure! Here you go:\n{"question": "Q?", "answer": "A."}\n\nLet me know if you need changes.'
        result = extract_json_from_text(text)
        assert result == {"question": "Q?", "answer": "A."}

    def test_extract_json_array_with_surrounding_text(self):
        """Test extracting JSON array with surrounding text."""
        text = 'Here are the flashcards:\n[{"q": "Q1?"}, {"q": "Q2?"}]\n\nEnjoy!'
        result = extract_json_from_text(text)
        assert result == [{"q": "Q1?"}, {"q": "Q2?"}]

    def test_extract_json_nested_object(self):
        """Test extracting nested JSON object."""
        text = '{"outer": {"inner": "value"}, "question": "Q?"}'
        result = extract_json_from_text(text)
        assert result == {"outer": {"inner": "value"}, "question": "Q?"}

    def test_extract_json_with_whitespace(self):
        """Test extracting JSON with extra whitespace."""
        text = '  \n  {"question": "Q?", "answer": "A."}  \n  '
        result = extract_json_from_text(text)
        assert result == {"question": "Q?", "answer": "A."}

    def test_extract_json_invalid_raises_error(self):
        """Test that invalid JSON raises ValueError."""
        text = "This is not JSON at all"
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json_from_text(text)

    def test_extract_json_malformed_raises_error(self):
        """Test that malformed JSON raises ValueError."""
        text = '{"question": "Q?", "answer": }'  # Missing value
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json_from_text(text)

    def test_extract_json_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Could not extract valid JSON"):
            extract_json_from_text("")
