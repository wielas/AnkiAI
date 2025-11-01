#!/usr/bin/env python
"""Demo script to test the generation module."""

import os
import sys

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.generation.claude_client import ClaudeClient
from src.domain.generation.prompt_builder import PromptBuilder


def main():
    """Run a simple generation demo."""
    # Check if API key is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("  export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Find a sample PDF
    sample_paths = [
        "tests/fixtures/sample_technical.pdf",
        "tests/sample_data/023_Transaction Processing or Analytics_.pdf",
    ]

    pdf_path = None
    for path in sample_paths:
        if os.path.exists(path):
            pdf_path = path
            break

    if not pdf_path:
        print("ERROR: No sample PDF found for testing")
        sys.exit(1)

    print("=" * 70)
    print("AnkiAI Generation Module Demo")
    print("=" * 70)
    print()

    # Step 1: Parse PDF
    print(f"Step 1: Parsing PDF: {pdf_path}")
    print("         (first 2 pages)")
    document = PDFParser.parse(pdf_path, start_page=1, end_page=2)
    print(f"         ✓ Extracted {len(document.content)} characters")
    print()

    # Step 2: Build prompt
    print("Step 2: Building prompt")
    context = document.content[:1000]  # Use first 1000 chars
    prompt = PromptBuilder.build_flashcard_prompt(
        context=context, difficulty="intermediate", num_cards=1
    )
    estimated_tokens = PromptBuilder.estimate_prompt_tokens(prompt)
    print(f"         ✓ Prompt built (~{estimated_tokens} tokens)")
    print()

    # Step 3: Generate flashcard
    print("Step 3: Calling Claude API...")
    client = ClaudeClient()

    try:
        flashcard = client.generate_flashcard(prompt)

        print("         ✓ Flashcard generated!")
        print()

        # Display results
        print("=" * 70)
        print("GENERATED FLASHCARD")
        print("=" * 70)
        print()
        print(f"Question: {flashcard['question']}")
        print()
        print(f"Answer: {flashcard['answer']}")
        print()

        # Display usage stats
        stats = client.get_usage_stats()
        print("=" * 70)
        print("USAGE STATISTICS")
        print("=" * 70)
        print()
        print(f"API Calls:      {stats['api_calls']}")
        print(f"Input Tokens:   {stats['total_input_tokens']:,}")
        print(f"Output Tokens:  {stats['total_output_tokens']:,}")
        print(f"Total Tokens:   {stats['total_tokens']:,}")
        print()
        print(f"Estimated Cost: ${stats['estimated_cost']:.4f}")
        print(f"  Input cost:   ${stats['cost_breakdown']['input_cost']:.4f}")
        print(f"  Output cost:  ${stats['cost_breakdown']['output_cost']:.4f}")
        print()
        print("=" * 70)

    except Exception as e:
        print(f"         ✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
