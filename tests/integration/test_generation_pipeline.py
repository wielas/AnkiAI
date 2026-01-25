"""Integration tests for the generation pipeline.

These tests use real API calls to Claude and should be marked accordingly.
They verify the end-to-end flow: PDFParser → PromptBuilder → ClaudeClient
"""

import os
from pathlib import Path

import pytest

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.generation.claude_client import ClaudeClient
from src.domain.generation.prompt_builder import PromptBuilder


@pytest.fixture
def sample_pdf_path():
    """Get path to sample PDF for testing."""
    # Try both possible locations
    paths = [
        Path("tests/fixtures/sample_technical.pdf"),
        Path("tests/sample_data/023_Transaction Processing or Analytics_.pdf"),
    ]

    for path in paths:
        if path.exists():
            return str(path)

    pytest.skip("No sample PDF found for testing")


@pytest.mark.integration
@pytest.mark.api
class TestGenerationPipeline:
    """Integration tests for the complete generation pipeline."""

    def test_pdf_to_flashcard_single_card(self, sample_pdf_path):
        """Test complete pipeline: PDF → prompt → flashcard (single card)."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        # Step 1: Parse PDF (first 2 pages)
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=2)

        assert document.content
        assert len(document.content) > 100  # Should have substantial content

        # Step 2: Build prompt
        # Use first 1000 chars to keep it reasonable for test
        context = document.content[:1000]
        prompt = PromptBuilder.build_flashcard_prompt(
            context=context, difficulty="intermediate", num_cards=1
        )

        assert prompt
        assert context in prompt

        # Step 3: Generate flashcard
        client = ClaudeClient()
        flashcard = client.generate_flashcard(prompt)

        # Verify flashcard structure
        assert isinstance(flashcard, dict)
        assert "question" in flashcard
        assert "answer" in flashcard
        assert flashcard["question"].strip()
        assert flashcard["answer"].strip()

        # Verify token tracking
        stats = client.get_usage_stats()
        assert stats["api_calls"] == 1
        assert stats["total_input_tokens"] > 0
        assert stats["total_output_tokens"] > 0
        assert stats["estimated_cost"] > 0

        # Log results for manual inspection
        print("\n=== Generated Flashcard ===")
        print(f"Question: {flashcard['question']}")
        print(f"Answer: {flashcard['answer']}")
        print("\n=== Usage Stats ===")
        print(f"API Calls: {stats['api_calls']}")
        print(f"Input Tokens: {stats['total_input_tokens']}")
        print(f"Output Tokens: {stats['total_output_tokens']}")
        print(f"Estimated Cost: ${stats['estimated_cost']:.4f}")

    def test_pdf_to_flashcard_multiple_cards(self, sample_pdf_path):
        """Test complete pipeline: PDF → prompt → flashcards (multiple cards)."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        # Step 1: Parse PDF (pages 1-3 for more content)
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=3)

        # Step 2: Build prompt for 2 flashcards
        context = document.content[:1500]  # Bit more context for 2 cards
        prompt = PromptBuilder.build_flashcard_prompt(
            context=context, difficulty="intermediate", num_cards=2
        )

        # Step 3: Generate flashcards
        client = ClaudeClient()
        flashcards = client.generate_flashcard(prompt)

        # Verify flashcards structure
        assert isinstance(flashcards, list)
        assert len(flashcards) >= 1  # Should get at least 1, ideally 2

        for i, card in enumerate(flashcards):
            assert "question" in card
            assert "answer" in card
            assert card["question"].strip()
            assert card["answer"].strip()

            print(f"\n=== Generated Flashcard {i+1} ===")
            print(f"Question: {card['question']}")
            print(f"Answer: {card['answer']}")

        # Verify token tracking
        stats = client.get_usage_stats()
        assert stats["api_calls"] == 1
        print("\n=== Usage Stats ===")
        print(f"Cost: ${stats['estimated_cost']:.4f}")

    def test_pdf_to_flashcard_beginner_difficulty(self, sample_pdf_path):
        """Test pipeline with beginner difficulty level."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        # Parse and generate with beginner difficulty
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        context = document.content[:800]

        prompt = PromptBuilder.build_flashcard_prompt(
            context=context, difficulty="beginner", num_cards=1
        )

        client = ClaudeClient()
        flashcard = client.generate_flashcard(prompt)

        # Verify structure
        assert isinstance(flashcard, dict)
        assert "question" in flashcard
        assert "answer" in flashcard

        print("\n=== Beginner Difficulty Flashcard ===")
        print(f"Question: {flashcard['question']}")
        print(f"Answer: {flashcard['answer']}")

    def test_cost_estimation_accuracy(self, sample_pdf_path):
        """Test that cost estimation is reasonable."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        # Generate a flashcard and check cost
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        context = document.content[:500]

        prompt = PromptBuilder.build_flashcard_prompt(context, num_cards=1)

        client = ClaudeClient()
        client.generate_flashcard(prompt)

        stats = client.get_usage_stats()

        # Cost for a single flashcard should be very low (< $0.01)
        assert stats["estimated_cost"] < 0.01

        # Sanity checks on token counts
        assert 100 < stats["total_input_tokens"] < 2000  # Reasonable input
        assert 10 < stats["total_output_tokens"] < 500  # Reasonable output

        print("\n=== Cost Analysis ===")
        print(f"Input tokens: {stats['total_input_tokens']}")
        print(f"Output tokens: {stats['total_output_tokens']}")
        print(f"Cost: ${stats['estimated_cost']:.4f}")
        print(
            f"Input cost: ${stats['cost_breakdown']['input_cost']:.4f} "
            f"({stats['total_input_tokens']/1000:.1f}k tokens)"
        )
        print(
            f"Output cost: ${stats['cost_breakdown']['output_cost']:.4f} "
            f"({stats['total_output_tokens']/1000:.1f}k tokens)"
        )

    def test_token_tracking_across_multiple_calls(self, sample_pdf_path):
        """Test that token tracking accumulates correctly across calls."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        context = document.content[:500]

        client = ClaudeClient()

        # Make first call
        prompt1 = PromptBuilder.build_flashcard_prompt(context, num_cards=1)
        client.generate_flashcard(prompt1)

        stats_after_first = client.get_usage_stats()
        first_call_input = stats_after_first["total_input_tokens"]
        first_call_output = stats_after_first["total_output_tokens"]

        # Make second call
        prompt2 = PromptBuilder.build_flashcard_prompt(context, num_cards=1)
        client.generate_flashcard(prompt2)

        stats_after_second = client.get_usage_stats()

        # Verify accumulation
        assert stats_after_second["api_calls"] == 2
        assert stats_after_second["total_input_tokens"] > first_call_input
        assert stats_after_second["total_output_tokens"] > first_call_output

        # Second call should roughly double the tokens (within reason)
        assert stats_after_second["total_input_tokens"] >= first_call_input * 1.5

        print("\n=== Token Tracking Test ===")
        print(f"After call 1: {first_call_input} in, {first_call_output} out")
        print(
            f"After call 2: {stats_after_second['total_input_tokens']} in, "
            f"{stats_after_second['total_output_tokens']} out"
        )

        # Test reset
        client.reset_stats()
        stats_after_reset = client.get_usage_stats()
        assert stats_after_reset["api_calls"] == 0
        assert stats_after_reset["total_tokens"] == 0


@pytest.mark.integration
@pytest.mark.api
class TestFullPipelineIntegration:
    """Integration tests for the complete end-to-end pipeline including Anki export."""

    def test_full_pipeline_pdf_to_anki(self, sample_pdf_path, tmp_path):
        """Test complete pipeline: PDF → Claude → Anki .apkg file."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        from src.application.flashcard_service import FlashcardGeneratorService
        from src.domain.models.document import ProcessingStatus

        # Setup output path
        output_path = tmp_path / "test_output.apkg"

        # Create service and generate flashcards (2-3 pages for real test)
        service = FlashcardGeneratorService()

        progress_log = []

        def log_progress(current, total, message):
            progress_log.append((current, total, message))
            print(f"[{current}/{total}] {message}")

        result = service.generate_flashcards(
            pdf_path=sample_pdf_path,
            page_range=(1, 3),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(output_path),
            on_progress=log_progress,
        )

        # Verify result structure
        assert result is not None
        assert result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL]
        assert result.total_attempted == 3

        # At least some pages should succeed
        assert result.total_success >= 1
        assert len(result.flashcards) >= 1

        # Verify flashcard structure
        for card in result.flashcards:
            assert "question" in card
            assert "answer" in card
            assert card["question"].strip()
            assert card["answer"].strip()

        # Verify .apkg file was created
        assert result.output_path is not None
        assert os.path.exists(result.output_path)
        assert result.output_path.endswith(".apkg")

        # Verify token and cost tracking
        assert result.total_tokens > 0
        assert result.total_cost_usd > 0

        # Verify progress was tracked
        assert len(progress_log) == 3

        # Print results for inspection
        print("\n" + "=" * 50)
        print("=== Full Pipeline Test Results ===")
        print("=" * 50)
        print(f"Status: {result.status.value}")
        print(f"Pages processed: {result.total_success}/{result.total_attempted}")
        print(f"Flashcards generated: {len(result.flashcards)}")
        print(f"Tokens used: {result.total_tokens:,}")
        print(f"Cost: ${result.total_cost_usd:.4f}")
        print(f"Output file: {result.output_path}")

        print("\n=== Generated Flashcards ===")
        for i, card in enumerate(result.flashcards, 1):
            print(f"\n[Card {i}] (Page {card.get('source_page', '?')})")
            print(f"Q: {card['question']}")
            print(f"A: {card['answer']}")

        if result.total_failed > 0:
            print(f"\n=== Failed Pages: {result.get_failed_pages()} ===")
            for r in result.results:
                if not r.success:
                    print(f"Page {r.page_number}: {r.error_message}")

    def test_full_pipeline_single_page(self, sample_pdf_path, tmp_path):
        """Test pipeline with a single page for faster testing."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        from src.application.flashcard_service import FlashcardGeneratorService
        from src.domain.models.document import ProcessingStatus

        output_path = tmp_path / "single_page.apkg"

        service = FlashcardGeneratorService()
        result = service.generate_flashcards(
            pdf_path=sample_pdf_path,
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="beginner",
            output_path=str(output_path),
        )

        assert result.status == ProcessingStatus.SUCCESS
        assert result.total_success == 1
        assert len(result.flashcards) == 1
        assert os.path.exists(result.output_path)

        print("\n=== Single Page Test ===")
        print(f"Q: {result.flashcards[0]['question']}")
        print(f"A: {result.flashcards[0]['answer']}")
        print(f"Cost: ${result.total_cost_usd:.4f}")

    def test_full_pipeline_multiple_cards_per_page(self, sample_pdf_path, tmp_path):
        """Test generating multiple flashcards per page."""
        # Skip if no API key configured
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set - skipping API test")

        from src.application.flashcard_service import FlashcardGeneratorService

        output_path = tmp_path / "multi_cards.apkg"

        service = FlashcardGeneratorService()
        result = service.generate_flashcards(
            pdf_path=sample_pdf_path,
            page_range=(1, 2),
            cards_per_page=2,
            difficulty="intermediate",
            output_path=str(output_path),
        )

        # Should get up to 4 flashcards (2 pages * 2 cards)
        assert len(result.flashcards) >= 2  # At least some multi-card generation
        assert os.path.exists(result.output_path)

        print("\n=== Multi-Card Per Page Test ===")
        print(f"Generated {len(result.flashcards)} flashcards from 2 pages")
        for i, card in enumerate(result.flashcards, 1):
            print(f"\n[{i}] Q: {card['question'][:80]}...")
        print(f"Cost: ${result.total_cost_usd:.4f}")
