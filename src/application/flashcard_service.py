"""Flashcard generation service orchestrating the full pipeline."""

import logging
from pathlib import Path
from typing import Callable, List, Optional

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.generation.claude_client import ClaudeClient
from src.domain.generation.prompt_builder import PromptBuilder
from src.domain.models.document import (
    FlashcardResult,
    GenerationResult,
    ProcessingStatus,
)
from src.domain.output.anki_formatter import AnkiFormatter

logger = logging.getLogger(__name__)


# Type alias for progress callback
ProgressCallback = Callable[[int, int, str], None]


class FlashcardGeneratorService:
    """Orchestrates the flashcard generation pipeline.

    This service coordinates:
    1. PDF parsing and text extraction
    2. Prompt building for each page
    3. Claude API calls for flashcard generation
    4. Anki deck creation and export

    Design decisions:
    - Continues on single-page failures (partial results better than none)
    - Tracks costs and tokens across all operations
    - Supports progress callbacks for CLI/UI updates
    - Creates fresh client instance for clean token tracking
    """

    def __init__(self):
        """Initialize the service with fresh component instances."""
        self.claude_client = ClaudeClient()
        logger.info("FlashcardGeneratorService initialized")

    def generate_flashcards(
        self,
        pdf_path: str,
        page_range: tuple,
        cards_per_page: int = 1,
        difficulty: str = "intermediate",
        output_path: str = "flashcards.apkg",
        on_progress: Optional[ProgressCallback] = None,
    ) -> GenerationResult:
        """Generate flashcards from PDF and save to Anki format.

        Args:
            pdf_path: Path to PDF file
            page_range: (start, end) page numbers (1-indexed, inclusive)
            cards_per_page: Number of flashcards per page
            difficulty: Difficulty level for flashcards (beginner/intermediate/advanced)
            output_path: Where to save .apkg file
            on_progress: Optional callback(current, total, message) for progress updates

        Returns:
            GenerationResult with flashcards, statistics, and status

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If page range is invalid
        """
        start_page, end_page = page_range
        total_pages = end_page - start_page + 1

        logger.info(
            f"Starting flashcard generation: {pdf_path} "
            f"(pages {start_page}-{end_page}, {cards_per_page} cards/page)"
        )

        # Reset token tracking for fresh stats
        self.claude_client.reset_stats()

        # Collect results
        all_flashcards: List[dict] = []
        page_results: List[FlashcardResult] = []
        failed_count = 0
        success_count = 0

        # Process each page
        for page_idx, page_num in enumerate(range(start_page, end_page + 1)):
            current = page_idx + 1

            # Report progress
            if on_progress:
                on_progress(current, total_pages, f"Processing page {page_num}...")

            # Extract text for this specific page
            try:
                doc = PDFParser.parse(pdf_path, start_page=page_num, end_page=page_num)
                page_text = doc.content
            except Exception as e:
                logger.error(f"Failed to parse page {page_num}: {e}")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message=f"PDF parsing error: {str(e)}",
                    )
                )
                failed_count += 1
                continue

            # Skip empty pages
            if not page_text.strip():
                logger.warning(f"Page {page_num} has no text content, skipping")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message="Page has no text content",
                    )
                )
                failed_count += 1
                continue

            # Build prompt and generate flashcard
            try:
                prompt = PromptBuilder.build_flashcard_prompt(
                    context=page_text,
                    difficulty=difficulty,
                    num_cards=cards_per_page,
                )

                # Get usage stats before call for delta calculation
                stats_before = self.claude_client.get_usage_stats()
                tokens_before = stats_before["total_tokens"]

                # Generate flashcard(s)
                result = self.claude_client.generate_flashcard(prompt)

                # Calculate tokens used for this call
                stats_after = self.claude_client.get_usage_stats()
                tokens_used = stats_after["total_tokens"] - tokens_before

                # Calculate cost for this call
                input_delta = (
                    stats_after["total_input_tokens"]
                    - stats_before["total_input_tokens"]
                )
                output_delta = (
                    stats_after["total_output_tokens"]
                    - stats_before["total_output_tokens"]
                )
                cost = (
                    input_delta / 1_000_000 * ClaudeClient.PRICE_PER_MILLION_INPUT
                    + output_delta / 1_000_000 * ClaudeClient.PRICE_PER_MILLION_OUTPUT
                )

                # Normalize result to list
                if isinstance(result, dict):
                    flashcards = [result]
                else:
                    flashcards = result

                # Add page reference to each flashcard
                for card in flashcards:
                    card["source_page"] = page_num

                all_flashcards.extend(flashcards)

                page_results.append(
                    FlashcardResult(
                        flashcards=flashcards,
                        page_number=page_num,
                        success=True,
                        tokens_used=tokens_used,
                        cost_usd=round(cost, 6),
                    )
                )
                success_count += 1

                logger.info(
                    f"Generated {len(flashcards)} flashcard(s) for page {page_num}"
                )

            except Exception as e:
                logger.error(f"Failed to generate flashcard for page {page_num}: {e}")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message=str(e),
                    )
                )
                failed_count += 1

        # Get final usage stats
        final_stats = self.claude_client.get_usage_stats()

        # Determine overall status
        if success_count == 0:
            status = ProcessingStatus.FAILED
        elif failed_count > 0:
            status = ProcessingStatus.PARTIAL
        else:
            status = ProcessingStatus.SUCCESS

        # Format to Anki if we have any flashcards
        final_output_path = None
        if all_flashcards:
            try:
                # Create tags from metadata
                source_filename = Path(pdf_path).name
                tags = AnkiFormatter.create_tags_from_metadata(
                    source_filename=source_filename,
                    page_range=page_range,
                    difficulty=difficulty,
                )

                # Create deck name from filename
                deck_name = f"AnkiAI - {Path(pdf_path).stem}"

                final_output_path = AnkiFormatter.format_flashcards(
                    flashcards=all_flashcards,
                    deck_name=deck_name,
                    tags=tags,
                    output_path=output_path,
                )

                logger.info(f"Created Anki deck: {final_output_path}")

            except Exception as e:
                logger.error(f"Failed to create Anki deck: {e}")
                # Don't fail the whole result, just note the error
                if status == ProcessingStatus.SUCCESS:
                    status = ProcessingStatus.PARTIAL

        result = GenerationResult(
            flashcards=all_flashcards,
            results=page_results,
            total_attempted=total_pages,
            total_success=success_count,
            total_failed=failed_count,
            total_tokens=final_stats["total_tokens"],
            total_cost_usd=final_stats["estimated_cost"],
            status=status,
            output_path=final_output_path,
        )

        logger.info(
            f"Generation complete: {success_count}/{total_pages} successful, "
            f"{len(all_flashcards)} flashcards, ${final_stats['estimated_cost']:.4f}"
        )

        return result
