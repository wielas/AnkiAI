"""Root conftest.py to make fixtures available across all test modules."""

import sys
from pathlib import Path

import fitz  # PyMuPDF
import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def sample_pdf_path(fixtures_dir: Path) -> Path:
    """Create a sample PDF for testing if it doesn't exist.

    Creates a 5-page PDF with:
    - Technical content on each page
    - Metadata (title, author, subject, keywords, creation date)
    - Different content per page for testing page ranges

    Returns:
        Path to the sample PDF file
    """
    pdf_path = fixtures_dir / "sample_technical.pdf"

    # Create the PDF if it doesn't exist
    if not pdf_path.exists():
        doc = fitz.open()  # Create new PDF

        # Define content for each page
        page_contents = [
            """Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to learn
and improve from experience without being explicitly programmed. The core idea is to
develop algorithms that can receive input data and use statistical analysis to predict
an output while updating outputs as new data becomes available.

Key concepts include:
- Supervised Learning: Training with labeled data
- Unsupervised Learning: Finding patterns in unlabeled data
- Reinforcement Learning: Learning through trial and error
- Neural Networks: Interconnected nodes mimicking brain structure
""",
            """Deep Learning Architecture

Deep learning uses artificial neural networks with multiple layers between input and
output. Each layer extracts increasingly abstract features from the raw input.

Popular architectures:
1. Convolutional Neural Networks (CNNs) - Image processing
2. Recurrent Neural Networks (RNNs) - Sequential data
3. Transformers - Natural language processing
4. Generative Adversarial Networks (GANs) - Content generation

The depth of these networks allows them to learn hierarchical representations.
""",
            """Natural Language Processing

NLP enables computers to understand, interpret, and generate human language.
Modern NLP leverages deep learning models, particularly transformer architectures.

Common NLP tasks:
- Text Classification
- Named Entity Recognition
- Machine Translation
- Sentiment Analysis
- Question Answering
- Text Summarization

Transfer learning through pre-trained models like BERT, GPT, and T5 has
revolutionized the field.
""",
            """Computer Vision Techniques

Computer vision enables machines to interpret and understand visual information
from the world. It combines techniques from AI, machine learning, and image processing.

Applications include:
- Object Detection: Identifying objects in images
- Image Segmentation: Partitioning images into segments
- Facial Recognition: Identifying individuals from faces
- Optical Character Recognition (OCR): Reading text from images
- Image Generation: Creating synthetic images

CNNs are the backbone of modern computer vision systems.
""",
            """AI Ethics and Considerations

As AI systems become more prevalent, ethical considerations are crucial:

1. Bias and Fairness: Ensuring AI doesn't perpetuate discrimination
2. Privacy: Protecting personal data in training and deployment
3. Transparency: Making AI decisions interpretable
4. Accountability: Determining responsibility for AI actions
5. Safety: Preventing harmful outcomes

Responsible AI development requires careful consideration of these factors
throughout the entire lifecycle of AI systems.
""",
        ]

        # Create 5 pages with content
        for i, content in enumerate(page_contents, 1):
            page = doc.new_page(width=595, height=842)  # A4 size
            # Add text to page
            text_rect = fitz.Rect(50, 50, 545, 792)  # Margins
            page.insert_textbox(
                text_rect,
                content,
                fontsize=11,
                fontname="helv",
                align=fitz.TEXT_ALIGN_LEFT,
            )

            # Add page number at bottom
            page.insert_text(
                (297, 820),  # Center bottom
                f"Page {i}",
                fontsize=9,
                color=(0.5, 0.5, 0.5),
            )

        # Set metadata
        doc.set_metadata(
            {
                "title": "Introduction to Machine Learning",
                "author": "Dr. Jane Smith",
                "subject": "Machine Learning and AI Fundamentals",
                "keywords": "machine learning, deep learning, AI, neural networks",
                "creationDate": "D:20230815143022+02'00'",
            }
        )

        # Save the PDF
        doc.save(str(pdf_path))
        doc.close()

    return pdf_path


@pytest.fixture(scope="session")
def empty_pdf_path(fixtures_dir: Path) -> Path:
    """Create an empty PDF (no text content) for testing.

    Returns:
        Path to the empty PDF file
    """
    pdf_path = fixtures_dir / "empty.pdf"

    if not pdf_path.exists():
        doc = fitz.open()
        # Create a single blank page
        doc.new_page(width=595, height=842)
        doc.save(str(pdf_path))
        doc.close()

    return pdf_path


@pytest.fixture
def temp_pdf_path(tmp_path: Path) -> Path:
    """Create a temporary PDF path for testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path where a temporary PDF can be created
    """
    return tmp_path / "temp_test.pdf"
