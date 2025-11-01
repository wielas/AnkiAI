"""Claude API client for flashcard generation."""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Union

import anthropic
from anthropic import APIError, RateLimitError

from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Client for interacting with Claude API for flashcard generation.

    Features:
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Cost estimation
    - Robust JSON parsing

    Design decisions:
    - Instance-based for token tracking across multiple calls
    - Retry on rate limits, network errors, server errors (5xx)
    - Don't retry on auth errors or bad requests (4xx except 429)
    - Parse JSON robustly (handle surrounding text)
    """

    # Pricing for Claude Sonnet 4.5 (per million tokens)
    PRICE_PER_MILLION_INPUT = 3.00  # $3 per 1M input tokens
    PRICE_PER_MILLION_OUTPUT = 15.00  # $15 per 1M output tokens

    def __init__(
        self, api_key: Optional[str] = None, min_request_interval: float = 0.1
    ):
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key. If None, loads from settings.
            min_request_interval: Minimum seconds between requests for rate limiting.
                Default 0.1s (10 req/sec). Set to 0 to disable.
        """
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = settings.claude_model
        self.temperature = settings.claude_temperature
        self.max_tokens = settings.claude_max_tokens

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)

        # Token tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.api_calls = 0

        # Rate limiting (client-side protection)
        self.min_request_interval = min_request_interval
        self.last_request_time = 0.0

        logger.info(f"Initialized ClaudeClient with model: {self.model}")

    def generate_flashcard(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> Union[Dict[str, str], List[Dict[str, str]]]:
        """Generate flashcard(s) from a prompt using Claude API.

        Args:
            prompt: The prompt text for flashcard generation
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            Single flashcard dict or list of flashcard dicts, each with:
            - question: str
            - answer: str

        Raises:
            anthropic.AuthenticationError: Invalid API key (not retried)
            anthropic.BadRequestError: Invalid request (not retried)
            anthropic.APIError: API error after all retries exhausted
            ValueError: Failed to parse JSON from response
        """
        attempt = 0
        last_error = None

        while attempt < max_retries:
            try:
                attempt += 1

                # Rate limiting: enforce minimum interval between requests
                if self.min_request_interval > 0:
                    elapsed = time.time() - self.last_request_time
                    if elapsed < self.min_request_interval:
                        sleep_time = self.min_request_interval - elapsed
                        logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
                        time.sleep(sleep_time)
                    self.last_request_time = time.time()

                # Make API call
                logger.info(
                    f"Calling Claude API (attempt {attempt}/{max_retries}, "
                    f"model: {self.model})"
                )

                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Track usage
                self.total_input_tokens += response.usage.input_tokens
                self.total_output_tokens += response.usage.output_tokens
                self.api_calls += 1

                logger.info(
                    f"API call successful. Tokens: {response.usage.input_tokens} in, "
                    f"{response.usage.output_tokens} out"
                )

                # Extract text from response
                response_text = response.content[0].text

                # Parse JSON from response
                flashcards = extract_json_from_text(response_text)

                # Validate structure
                if isinstance(flashcards, dict):
                    _validate_flashcard(flashcards)
                elif isinstance(flashcards, list):
                    for card in flashcards:
                        _validate_flashcard(card)
                else:
                    raise ValueError(
                        f"Expected dict or list, got {type(flashcards).__name__}"
                    )

                return flashcards

            except (
                anthropic.AuthenticationError,
                anthropic.PermissionDeniedError,
            ) as e:
                # Don't retry auth errors - they won't succeed
                logger.error(f"Authentication error: {e}")
                raise

            except anthropic.BadRequestError as e:
                # Don't retry bad requests (except rate limits)
                logger.error(f"Bad request error: {e}")
                raise

            except (
                RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
                anthropic.APITimeoutError,
            ) as e:
                # Retry on rate limits, server errors, network issues
                last_error = e
                if attempt < max_retries:
                    # Exponential backoff: 1s, 2s, 4s, ...
                    wait_time = 2 ** (attempt - 1)
                    logger.warning(
                        f"Retryable error ({type(e).__name__}): {e}. "
                        f"Retrying in {wait_time}s... (attempt {attempt}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Max retries ({max_retries}) exhausted. Last error: {e}"
                    )
                    raise

            except (ValueError, json.JSONDecodeError) as e:
                # JSON parsing errors - don't retry, raise immediately
                logger.error(f"Failed to parse response: {e}")
                raise

            except Exception as e:
                # Unexpected errors
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
                raise

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise APIError("Failed to generate flashcard after all retries")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics and cost estimation.

        Returns:
            Dictionary with usage stats:
            - api_calls: Number of API calls made
            - total_input_tokens: Total input tokens
            - total_output_tokens: Total output tokens
            - total_tokens: Sum of input and output tokens
            - estimated_cost: Estimated cost in USD
            - cost_breakdown: Dict with input_cost and output_cost
        """
        total_tokens = self.total_input_tokens + self.total_output_tokens

        # Calculate costs
        input_cost = (
            self.total_input_tokens / 1_000_000
        ) * self.PRICE_PER_MILLION_INPUT
        output_cost = (
            self.total_output_tokens / 1_000_000
        ) * self.PRICE_PER_MILLION_OUTPUT
        total_cost = input_cost + output_cost

        return {
            "api_calls": self.api_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": round(total_cost, 4),
            "cost_breakdown": {
                "input_cost": round(input_cost, 4),
                "output_cost": round(output_cost, 4),
            },
        }

    def reset_stats(self) -> None:
        """Reset token usage statistics."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.api_calls = 0
        logger.debug("Reset usage statistics")


def extract_json_from_text(text: str) -> Union[Dict, List]:
    """Extract JSON object or array from text that may contain surrounding content.

    Handles cases like:
    - "Here's the flashcard: {...}"
    - "{...}\\n\\nI made it about X because..."
    - Plain JSON: "{...}"
    - JSON array: "[{...}, {...}]"

    Args:
        text: Text containing JSON (possibly with surrounding text)

    Returns:
        Parsed JSON object (dict) or array (list)

    Raises:
        ValueError: If no valid JSON found or JSON is invalid
    """
    text = text.strip()

    # Try parsing as-is first (common case)
    try:
        result = json.loads(text)
        logger.debug("Parsed JSON directly (no surrounding text)")
        return result
    except json.JSONDecodeError:
        pass

    # Try to extract JSON using bracket matching
    # Find first occurrence of { or [
    json_start = -1
    start_char = None

    for i, char in enumerate(text):
        if char in "{[":
            json_start = i
            start_char = char
            break

    if json_start == -1:
        # No JSON-like structure found
        logger.error(f"No JSON structure found in text: {text[:200]}...")
        raise ValueError(
            "Could not extract valid JSON from response. "
            "Response may not contain properly formatted JSON."
        )

    # Match brackets/braces
    end_char = "}" if start_char == "{" else "]"
    depth = 0
    in_string = False
    escape_next = False

    for i in range(json_start, len(text)):
        char = text[i]

        # Handle string escaping
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        # Track if we're inside a string
        if char == '"':
            in_string = not in_string
            continue

        # Only count brackets outside of strings
        if not in_string:
            if char == start_char:
                depth += 1
            elif char == end_char:
                depth -= 1
                if depth == 0:
                    # Found matching bracket
                    json_str = text[json_start : i + 1]
                    try:
                        result = json.loads(json_str)
                        logger.debug(
                            f"Extracted JSON {start_char}...{end_char} from surrounding text"
                        )
                        return result
                    except json.JSONDecodeError:
                        pass
                    break

    # Failed to find valid JSON
    logger.error(f"Failed to extract JSON from text: {text[:200]}...")
    raise ValueError(
        "Could not extract valid JSON from response. "
        "Response may not contain properly formatted JSON."
    )


def _validate_flashcard(card: Dict[str, str]) -> None:
    """Validate that a flashcard has required fields.

    Args:
        card: Flashcard dictionary

    Raises:
        ValueError: If required fields are missing or empty
    """
    required_fields = ["question", "answer"]

    for field in required_fields:
        if field not in card:
            raise ValueError(f"Flashcard missing required field: {field}")
        if not isinstance(card[field], str):
            raise ValueError(
                f"Flashcard field '{field}' must be string, "
                f"got {type(card[field]).__name__}"
            )
        if not card[field].strip():
            raise ValueError(f"Flashcard field '{field}' cannot be empty")
