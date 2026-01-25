"""CLI for generating Anki flashcards from PDF documents."""

import logging
import sys
from pathlib import Path
from typing import Tuple

import click

from src.application.flashcard_service import FlashcardGeneratorService
from src.domain.models.document import ProcessingStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_page_range(page_range_str: str) -> Tuple[int, int]:
    """Parse a page range string like '1-10' into a tuple.

    Args:
        page_range_str: String in format "start-end" (e.g., "1-10")

    Returns:
        Tuple of (start_page, end_page)

    Raises:
        click.BadParameter: If format is invalid or range is illogical
    """
    # Support both "1-10" and "1" (single page)
    if "-" in page_range_str:
        parts = page_range_str.split("-")
        if len(parts) != 2:
            raise click.BadParameter(
                f"Invalid page range format: '{page_range_str}'. "
                "Use format 'start-end' (e.g., '1-10') or a single page number."
            )
        try:
            start = int(parts[0].strip())
            end = int(parts[1].strip())
        except ValueError as e:
            raise click.BadParameter(
                f"Invalid page numbers in range: '{page_range_str}'. "
                "Page numbers must be integers."
            ) from e
    else:
        # Single page
        try:
            start = end = int(page_range_str.strip())
        except ValueError as e:
            raise click.BadParameter(
                f"Invalid page number: '{page_range_str}'. "
                "Must be an integer or range like '1-10'."
            ) from e

    # Validate range
    if start < 1:
        raise click.BadParameter("Page numbers must be 1 or greater (1-indexed).")
    if start > end:
        raise click.BadParameter(
            f"Start page ({start}) cannot be greater than end page ({end})."
        )

    return (start, end)


def format_flashcard_preview(card: dict, index: int) -> str:
    """Format a flashcard for terminal preview.

    Args:
        card: Flashcard dict with 'question' and 'answer'
        index: 1-indexed card number

    Returns:
        Formatted string for display
    """
    question = card.get("question", "")
    answer = card.get("answer", "")
    page = card.get("source_page", "?")

    # Wrap long lines
    max_line_length = 80

    def wrap_text(text: str, prefix: str = "   ") -> str:
        words = text.split()
        lines = []
        current_line = prefix

        for word in words:
            if len(current_line) + len(word) + 1 > max_line_length:
                lines.append(current_line)
                current_line = prefix + word
            else:
                if current_line == prefix:
                    current_line += word
                else:
                    current_line += " " + word

        if current_line != prefix:
            lines.append(current_line)

        return "\n".join(lines) if lines else prefix

    output = f"\n  [{index}] Page {page}\n"
    output += f"  Q: {question[:77]}{'...' if len(question) > 77 else ''}\n"
    output += f"  A: {answer[:77]}{'...' if len(answer) > 77 else ''}\n"

    return output


@click.command()
@click.option(
    "--pdf",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to PDF file",
)
@click.option(
    "--pages",
    required=True,
    help='Page range (e.g., "1-10" or "5" for single page)',
)
@click.option(
    "--output",
    default="flashcards.apkg",
    help="Output .apkg file path",
)
@click.option(
    "--cards-per-page",
    default=1,
    type=click.IntRange(1, 5),
    help="Number of flashcards per page (1-5)",
)
@click.option(
    "--difficulty",
    type=click.Choice(["beginner", "intermediate", "advanced"]),
    default="intermediate",
    help="Flashcard difficulty level",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Minimal output (no progress or preview)",
)
@click.option(
    "--no-preview",
    is_flag=True,
    help="Skip flashcard preview",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed logging output",
)
def generate(
    pdf: Path,
    pages: str,
    output: str,
    cards_per_page: int,
    difficulty: str,
    quiet: bool,
    no_preview: bool,
    verbose: bool,
):
    """Generate Anki flashcards from PDF documents.

    Examples:

        # Generate flashcards from pages 1-10
        ankiai --pdf document.pdf --pages 1-10

        # Generate with advanced difficulty
        ankiai --pdf document.pdf --pages 5-15 --difficulty advanced

        # Generate 2 cards per page, quiet mode
        ankiai --pdf document.pdf --pages 1-5 --cards-per-page 2 --quiet
    """
    # Configure logging based on verbose flag
    if not verbose:
        # Suppress detailed logging unless --verbose is set
        logging.getLogger("src").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        # Parse page range
        page_range = parse_page_range(pages)
        start_page, end_page = page_range

        if not quiet:
            click.echo(
                f"\nGenerating flashcards from {pdf.name} "
                f"(pages {start_page}-{end_page})...\n"
            )

        # Create service
        service = FlashcardGeneratorService()

        def progress_callback(current: int, total: int, message: str):
            """Progress callback that tracks results."""
            if quiet:
                return
            click.echo(f"[{current}/{total}] {message}", nl=False)

        # Generate flashcards
        result = service.generate_flashcards(
            pdf_path=str(pdf),
            page_range=page_range,
            cards_per_page=cards_per_page,
            difficulty=difficulty,
            output_path=output,
            on_progress=progress_callback if not quiet else None,
        )

        # Show detailed progress results
        if not quiet:
            # Clear the "Processing..." line and show actual results
            click.echo("\r" + " " * 50 + "\r", nl=False)  # Clear line

            for page_result in result.results:
                page_num = page_result.page_number
                if page_result.success:
                    click.echo(f"[{page_num}] Processing page {page_num}... ", nl=False)
                    click.secho("OK", fg="green")
                    # Show preview of flashcards for this page
                    if not no_preview:
                        for card in page_result.flashcards:
                            q = card.get("question", "")[:70]
                            a = card.get("answer", "")[:70]
                            click.echo(
                                f"    Q: {q}{'...' if len(card.get('question', '')) > 70 else ''}"
                            )
                            click.echo(
                                f"    A: {a}{'...' if len(card.get('answer', '')) > 70 else ''}"
                            )
                else:
                    click.echo(f"[{page_num}] Processing page {page_num}... ", nl=False)
                    click.secho("FAILED", fg="red")
                    if page_result.error_message:
                        click.echo(f"    Error: {page_result.error_message}")

        # Summary
        click.echo("\n" + "=" * 50)
        click.echo("Summary:")
        click.echo("=" * 50)

        # Success/failure stats
        if result.status == ProcessingStatus.SUCCESS:
            click.secho(
                f"  Status: SUCCESS ({result.total_success}/{result.total_attempted} pages)",
                fg="green",
            )
        elif result.status == ProcessingStatus.PARTIAL:
            click.secho(
                f"  Status: PARTIAL ({result.total_success}/{result.total_attempted} pages)",
                fg="yellow",
            )
        else:
            click.secho(
                f"  Status: FAILED (0/{result.total_attempted} pages)",
                fg="red",
            )

        # Token and cost info
        click.echo(f"  Tokens: {result.total_tokens:,}")
        click.echo(f"  Cost: ${result.total_cost_usd:.4f}")
        click.echo(f"  Flashcards: {len(result.flashcards)}")

        # Output file
        if result.output_path:
            click.echo(f"  Output: {result.output_path}")
        else:
            click.secho(
                "  Output: No file created (no successful flashcards)", fg="yellow"
            )

        # Failed pages detail
        failed_pages = result.get_failed_pages()
        if failed_pages:
            click.echo(f"\nFailed pages: {', '.join(map(str, failed_pages))}")
            if not quiet:
                click.echo("(See logs above for error details)")

        click.echo()

        # Exit with error code if all failed
        if result.status == ProcessingStatus.FAILED:
            sys.exit(1)

    except FileNotFoundError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except click.BadParameter as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during generation")
        click.secho(f"Unexpected error: {e}", fg="red", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    generate()


if __name__ == "__main__":
    main()
