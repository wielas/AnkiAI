"""Unit tests for PromptBuilder."""

import pytest

from src.domain.generation.prompt_builder import PromptBuilder


@pytest.mark.unit
class TestPromptBuilder:
    """Test cases for PromptBuilder class."""

    def test_build_flashcard_prompt_contains_key_elements(self):
        """Test that prompt contains essential elements."""
        context = "Distributed systems use leader-based replication for consistency."
        prompt = PromptBuilder.build_flashcard_prompt(context)

        # Check for key elements
        assert "flashcard" in prompt.lower()
        assert "question" in prompt.lower()
        assert "answer" in prompt.lower()
        assert "json" in prompt.lower()
        assert context in prompt

    def test_build_flashcard_prompt_includes_examples(self):
        """Test that prompt includes example flashcards."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context)

        # Should include at least one example
        assert "Example" in prompt or "example" in prompt
        # Check for example content
        assert "leader node" in prompt or "replication" in prompt

    def test_build_flashcard_prompt_difficulty_intermediate(self):
        """Test prompt generation with intermediate difficulty."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(
            context, difficulty="intermediate"
        )

        assert "intermediate" in prompt.lower()
        assert "understanding" in prompt.lower()

    def test_build_flashcard_prompt_difficulty_beginner(self):
        """Test prompt generation with beginner difficulty."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context, difficulty="beginner")

        assert "beginner" in prompt.lower()
        assert "basic" in prompt.lower() or "fundamental" in prompt.lower()

    def test_build_flashcard_prompt_difficulty_advanced(self):
        """Test prompt generation with advanced difficulty."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context, difficulty="advanced")

        assert "advanced" in prompt.lower()
        assert "deep" in prompt.lower() or "challenging" in prompt.lower()

    def test_build_flashcard_prompt_invalid_difficulty_defaults_to_intermediate(
        self, caplog
    ):
        """Test that invalid difficulty defaults to intermediate with warning."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context, difficulty="expert")

        # Should default to intermediate
        assert "intermediate" in prompt.lower()
        # Should log warning
        assert "Invalid difficulty" in caplog.text

    def test_build_flashcard_prompt_single_card(self):
        """Test prompt for single flashcard."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context, num_cards=1)

        # Should request 1 card
        assert "1 high-quality flashcard" in prompt
        # Should show single object format
        assert '"question": "Your question here"' in prompt

    def test_build_flashcard_prompt_multiple_cards(self):
        """Test prompt for multiple flashcards."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context, num_cards=3)

        # Should request 3 cards
        assert "3 high-quality flashcards" in prompt
        # Should show array format
        assert "JSON array" in prompt or "[" in prompt

    def test_build_flashcard_prompt_includes_quality_criteria(self):
        """Test that prompt includes quality criteria."""
        context = "Test context"
        prompt = PromptBuilder.build_flashcard_prompt(context)

        # Check for quality criteria
        assert "clear" in prompt.lower()
        assert "specific" in prompt.lower()
        assert "concise" in prompt.lower()
        assert "accurate" in prompt.lower()

    def test_build_flashcard_prompt_reasonable_length(self):
        """Test that prompt is not excessively long."""
        context = "Short context"
        prompt = PromptBuilder.build_flashcard_prompt(context)

        # Prompt should be reasonable (< 5000 chars for short context)
        # This is a sanity check to prevent prompt bloat
        assert len(prompt) < 5000

    def test_build_flashcard_prompt_scales_with_context(self):
        """Test that prompt length scales with context length."""
        short_context = "Short."
        long_context = "Long context. " * 100

        short_prompt = PromptBuilder.build_flashcard_prompt(short_context)
        long_prompt = PromptBuilder.build_flashcard_prompt(long_context)

        # Long context should produce longer prompt
        assert len(long_prompt) > len(short_prompt)

    def test_estimate_prompt_tokens(self):
        """Test token estimation."""
        # Short text
        short_text = "Hello world"
        tokens = PromptBuilder.estimate_prompt_tokens(short_text)
        # ~4 chars per token, so "Hello world" (11 chars) ≈ 2-3 tokens
        assert 1 <= tokens <= 5

        # Longer text
        long_text = "A" * 400  # 400 chars
        tokens = PromptBuilder.estimate_prompt_tokens(long_text)
        # Should be around 100 tokens (400/4)
        assert 80 <= tokens <= 120

    def test_estimate_prompt_tokens_empty_string(self):
        """Test token estimation with empty string."""
        tokens = PromptBuilder.estimate_prompt_tokens("")
        assert tokens == 0
