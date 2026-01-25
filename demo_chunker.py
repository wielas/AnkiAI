#!/usr/bin/env python3
"""Demo script to visualize chunker output.

Usage:
    poetry run python demo_chunker.py [path/to/pdf] [--save output.txt]

Options:
    --save, -s FILE    Save all chunk data to a file for manual verification

If no PDF path is provided, uses the test sample PDF.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.models.chunk import Chunk
from src.domain.rag.chunker import Chunker


def save_chunks_to_file(chunks: list[Chunk], output_path: str) -> None:
    """Save all chunk data to a file for manual verification.

    Args:
        chunks: List of chunks to save
        output_path: Path to output file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("CHUNK DATA EXPORT\n")
        f.write(f"Total chunks: {len(chunks)}\n")
        f.write(f"Total tokens: {sum(c.token_count for c in chunks)}\n")
        f.write("=" * 80 + "\n\n")

        for i, chunk in enumerate(chunks):
            f.write("=" * 80 + "\n")
            f.write(f"CHUNK {i + 1} of {len(chunks)}\n")
            f.write("=" * 80 + "\n")
            f.write(f"ID:              {chunk.chunk_id}\n")
            f.write(f"Position:        {chunk.position}\n")
            f.write(f"Token count:     {chunk.token_count}\n")
            f.write(f"Char count:      {chunk.char_count}\n")
            f.write(f"Page numbers:    {chunk.page_numbers}\n")
            f.write(f"Source:          {chunk.source_document}\n")
            f.write(f"Overlap before:  {chunk.has_overlap_before}\n")
            f.write(f"Overlap after:   {chunk.has_overlap_after}\n")
            if chunk.overlap_with_previous:
                f.write(f"Previous chunk:  {chunk.overlap_with_previous}\n")
            if chunk.overlap_with_next:
                f.write(f"Next chunk:      {chunk.overlap_with_next}\n")
            f.write("\n--- TEXT START ---\n")
            f.write(chunk.text)
            f.write("\n--- TEXT END ---\n\n")

    print(f"Saved {len(chunks)} chunks to: {output_path}")


def demo_chunker(pdf_path: str | None = None, save_path: str | None = None) -> None:
    """Demonstrate chunker with a PDF file.

    Args:
        pdf_path: Path to PDF file (optional, uses test PDF if not provided)
        save_path: Path to save chunk data (optional)
    """
    # Use test PDF if none provided
    if pdf_path is None:
        pdf_path = str(Path(__file__).parent / "tests/fixtures/sample_technical.pdf")
        print(f"No PDF provided, using test PDF: {pdf_path}")

    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        print("Run the tests first to generate the sample PDF:")
        print("  poetry run pytest tests/unit/document_processing/test_pdf_parser.py -v")
        return

    print(f"\n{'=' * 60}")
    print("CHUNKER DEMO")
    print(f"{'=' * 60}")

    # Parse the PDF
    print(f"\n1. Parsing PDF: {pdf_path}")
    doc = PDFParser.parse(pdf_path)
    print(f"   - Total characters: {len(doc.content)}")
    print(f"   - Page range: {doc.page_range[0]}-{doc.page_range[1]}")

    # Chunk with default settings
    print("\n2. Chunking with default settings (target=800, overlap=100)")
    chunks = Chunker.chunk(doc)
    print(f"   - Total chunks: {len(chunks)}")
    print(f"   - Average tokens per chunk: {sum(c.token_count for c in chunks) // len(chunks)}")

    # Show first 3 chunks
    print("\n3. First 3 chunks:")
    print("-" * 60)

    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i + 1}:")
        print(f"  ID: {chunk.chunk_id}")
        print(f"  Tokens: {chunk.token_count}")
        print(f"  Characters: {chunk.char_count}")
        print(f"  Overlap before: {chunk.has_overlap_before}")
        print(f"  Overlap after: {chunk.has_overlap_after}")
        if chunk.overlap_with_previous:
            print(f"  Previous chunk: {chunk.overlap_with_previous}")
        if chunk.overlap_with_next:
            print(f"  Next chunk: {chunk.overlap_with_next}")

        # Show preview of text
        preview = chunk.text[:200].replace("\n", " ")
        if len(chunk.text) > 200:
            preview += "..."
        print(f"  Text preview: {preview}")

    # Show different configurations
    print(f"\n{'=' * 60}")
    print("4. Different configurations comparison:")
    print("-" * 60)

    configs = [
        {"target_size": 400, "overlap_size": 50, "label": "Small chunks"},
        {"target_size": 800, "overlap_size": 100, "label": "Default"},
        {"target_size": 1200, "overlap_size": 150, "label": "Large chunks"},
    ]

    for config in configs:
        chunks = Chunker.chunk(
            doc,
            target_size=config["target_size"],
            overlap_size=config["overlap_size"],
        )
        avg_tokens = sum(c.token_count for c in chunks) // len(chunks) if chunks else 0
        print(f"\n  {config['label']}:")
        print(f"    target_size={config['target_size']}, overlap={config['overlap_size']}")
        print(f"    Chunks: {len(chunks)}, Avg tokens: {avg_tokens}")

    # Save chunks to file if requested
    if save_path:
        # Re-chunk with default settings for saving
        chunks = Chunker.chunk(doc)
        save_chunks_to_file(chunks, save_path)

    print(f"\n{'=' * 60}")
    print("Demo complete!")


def parse_args() -> tuple[str | None, str | None]:
    """Parse command line arguments.

    Returns:
        Tuple of (pdf_path, save_path)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Demo script to visualize chunker output.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        default=None,
        help="Path to PDF file (uses test PDF if not provided)",
    )
    parser.add_argument(
        "--save",
        "-s",
        dest="save_path",
        metavar="FILE",
        help="Save all chunk data to a file for manual verification",
    )

    args = parser.parse_args()
    return args.pdf_path, args.save_path


if __name__ == "__main__":
    pdf_path, save_path = parse_args()
    demo_chunker(pdf_path, save_path)
