"""Unit tests for PDFParser."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.models.document import Document, DocumentFormat, DocumentMetadata


@pytest.fixture
def parser():
    """Create a PDFParser instance."""
    return PDFParser()


@pytest.mark.unit
class TestPDFParserSupports:
    """Tests for the supports() method."""

    def test_supports_pdf_format(self, parser):
        """Should return True for 'pdf' format."""
        assert parser.supports("pdf") is True

    def test_supports_pdf_format_case_insensitive(self, parser):
        """Should return True for 'PDF' (case-insensitive)."""
        assert parser.supports("PDF") is True
        assert parser.supports("Pdf") is True

    def test_rejects_other_formats(self, parser):
        """Should return False for non-PDF formats."""
        assert parser.supports("docx") is False
        assert parser.supports("txt") is False
        assert parser.supports("epub") is False
        assert parser.supports("") is False


@pytest.mark.unit
class TestPDFParserParse:
    """Tests for the parse() method."""

    def test_parse_valid_pdf(self, parser, sample_pdf_path):
        """Should successfully parse a valid PDF and return Document."""
        result = parser.parse(str(sample_pdf_path))

        assert isinstance(result, Document)
        assert result.content is not None
        assert len(result.content) > 0
        assert result.file_path == str(Path(sample_pdf_path).resolve())
        assert result.page_range == (1, 5)  # Default: all pages
        assert isinstance(result.metadata, DocumentMetadata)
        assert isinstance(result.processed_at, datetime)

    def test_parse_extracts_metadata(self, parser, sample_pdf_path):
        """Should extract metadata fields correctly."""
        result = parser.parse(str(sample_pdf_path))

        metadata = result.metadata
        assert metadata.total_pages == 5
        assert metadata.file_size_bytes > 0
        assert metadata.file_format == DocumentFormat.PDF
        assert metadata.title == "Introduction to Machine Learning"
        assert metadata.author == "Dr. Jane Smith"
        assert metadata.subject == "Machine Learning and AI Fundamentals"
        assert "machine learning" in metadata.keywords
        assert "deep learning" in metadata.keywords
        assert "AI" in metadata.keywords
        assert "neural networks" in metadata.keywords
        assert isinstance(metadata.creation_date, datetime)
        assert metadata.creation_date.year == 2023
        assert metadata.creation_date.month == 8
        assert metadata.creation_date.day == 15

    def test_parse_with_page_range(self, parser, sample_pdf_path):
        """Should correctly extract specified page range."""
        result = parser.parse(str(sample_pdf_path), start_page=2, end_page=4)

        assert result.page_range == (2, 4)
        assert result.get_page_count() == 3
        # Content should be from pages 2-4 only
        assert "Deep Learning Architecture" in result.content
        assert "Natural Language Processing" in result.content
        assert "Computer Vision Techniques" in result.content
        # Should not contain content from page 1
        assert "Machine Learning Fundamentals" not in result.content

    def test_parse_single_page(self, parser, sample_pdf_path):
        """Should correctly extract a single page."""
        result = parser.parse(str(sample_pdf_path), start_page=3, end_page=3)

        assert result.page_range == (3, 3)
        assert result.get_page_count() == 1
        assert "Natural Language Processing" in result.content

    def test_parse_default_page_range(self, parser, sample_pdf_path):
        """Should parse all pages when no end_page specified."""
        result = parser.parse(str(sample_pdf_path), start_page=1)

        assert result.page_range == (1, 5)
        assert result.get_page_count() == 5

    def test_parse_content_not_empty(self, parser, sample_pdf_path):
        """Should extract non-empty text content."""
        result = parser.parse(str(sample_pdf_path))

        assert len(result.content) > 0
        assert len(result) > 0  # Test __len__ method
        # Should contain some expected content
        assert "Machine Learning" in result.content
        assert "Deep Learning" in result.content

    def test_parse_calculates_page_count(self, parser, sample_pdf_path):
        """Should correctly calculate page count via get_page_count()."""
        # Test different ranges
        result1 = parser.parse(str(sample_pdf_path), start_page=1, end_page=5)
        assert result1.get_page_count() == 5

        result2 = parser.parse(str(sample_pdf_path), start_page=2, end_page=4)
        assert result2.get_page_count() == 3

        result3 = parser.parse(str(sample_pdf_path), start_page=1, end_page=1)
        assert result3.get_page_count() == 1

    def test_keywords_parsing(self, parser, sample_pdf_path):
        """Should correctly parse comma-separated keywords."""
        result = parser.parse(str(sample_pdf_path))

        keywords = result.metadata.keywords
        assert len(keywords) == 4
        assert "machine learning" in keywords
        assert "deep learning" in keywords
        assert "AI" in keywords
        assert "neural networks" in keywords
        # Should not have empty strings or extra whitespace
        assert "" not in keywords
        assert all(k == k.strip() for k in keywords)


@pytest.mark.unit
class TestPDFParserValidation:
    """Tests for input validation and error handling."""

    def test_invalid_page_range_start_greater_than_end(self, parser, sample_pdf_path):
        """Should raise ValueError when start > end."""
        with pytest.raises(ValueError, match="Invalid page range: start.*>.*end"):
            parser.parse(str(sample_pdf_path), start_page=5, end_page=2)

    def test_invalid_page_range_zero_indexed(self, parser, sample_pdf_path):
        """Should raise ValueError for start=0 (pages are 1-indexed)."""
        with pytest.raises(ValueError, match="pages are 1-indexed"):
            parser.parse(str(sample_pdf_path), start_page=0, end_page=5)

    def test_invalid_page_range_negative_start(self, parser, sample_pdf_path):
        """Should raise ValueError for negative start page."""
        with pytest.raises(ValueError, match="pages are 1-indexed"):
            parser.parse(str(sample_pdf_path), start_page=-1, end_page=5)

    def test_invalid_page_range_start_exceeds_total(self, parser, sample_pdf_path):
        """Should raise ValueError when start exceeds total pages."""
        with pytest.raises(ValueError, match="start.*exceeds total pages"):
            parser.parse(str(sample_pdf_path), start_page=10, end_page=15)

    def test_page_range_exceeds_document(self, parser, sample_pdf_path, caplog):
        """Should clip end_page to document length and log warning."""
        import logging

        caplog.set_level(logging.WARNING)

        result = parser.parse(str(sample_pdf_path), start_page=1, end_page=10)

        # Should clip to actual page count
        assert result.page_range == (1, 5)
        assert result.get_page_count() == 5

        # Should log a warning
        assert "Page range exceeds document length" in caplog.text
        assert "Clipping to page 5" in caplog.text

    def test_parse_nonexistent_file(self, parser):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            parser.parse("/path/to/nonexistent/file.pdf")


@pytest.mark.unit
class TestPDFParserDateParsing:
    """Tests for PDF date parsing functionality."""

    def test_parse_pdf_date_valid(self):
        """Should parse valid PDF date string."""
        date_str = "D:20230815143022+02'00'"
        result = PDFParser._parse_pdf_date(date_str)

        assert result is not None
        assert isinstance(result, datetime)
        assert result.year == 2023
        assert result.month == 8
        assert result.day == 15
        assert result.hour == 14
        assert result.minute == 30
        assert result.second == 22

    def test_parse_pdf_date_without_prefix(self):
        """Should parse PDF date without 'D:' prefix."""
        date_str = "20230815143022"
        result = PDFParser._parse_pdf_date(date_str)

        assert result is not None
        assert result.year == 2023
        assert result.month == 8
        assert result.day == 15

    def test_parse_pdf_date_invalid(self):
        """Should return None for invalid date string."""
        result = PDFParser._parse_pdf_date("invalid_date")
        assert result is None

    def test_parse_pdf_date_empty(self):
        """Should return None for empty date string."""
        result = PDFParser._parse_pdf_date("")
        assert result is None

    def test_parse_pdf_date_none(self):
        """Should return None for None input."""
        result = PDFParser._parse_pdf_date(None)
        assert result is None


@pytest.mark.unit
class TestPDFParserMetadataExtraction:
    """Tests for metadata extraction with various scenarios."""

    @patch("fitz.open")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_extract_metadata_with_missing_fields(
        self, mock_getsize, mock_exists, mock_fitz_open, parser
    ):
        """Should handle missing optional metadata fields gracefully."""
        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        # Create mock document with minimal metadata
        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=3)
        mock_doc.metadata = {
            "title": None,
            "author": None,
            "subject": None,
            "keywords": None,
            "creationDate": None,
        }

        # Create mock pages
        mock_pages = []
        for i in range(3):
            mock_page = MagicMock()
            mock_page.get_text.return_value = f"Page {i+1} content"
            mock_pages.append(mock_page)

        mock_doc.__getitem__ = lambda self, idx: mock_pages[idx]
        mock_fitz_open.return_value = mock_doc

        result = parser.parse("/fake/path.pdf")

        # Should still create valid metadata
        assert result.metadata.title is None
        assert result.metadata.author is None
        assert result.metadata.subject is None
        assert result.metadata.keywords == []
        assert result.metadata.creation_date is None
        assert result.metadata.total_pages == 3
        assert result.metadata.file_size_bytes == 1024

    @patch("fitz.open")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_extract_metadata_with_empty_keywords(
        self, mock_getsize, mock_exists, mock_fitz_open, parser
    ):
        """Should handle empty keywords string correctly."""
        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.metadata = {"keywords": ""}

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Content"
        mock_doc.__getitem__ = lambda self, idx: mock_page

        mock_fitz_open.return_value = mock_doc

        result = parser.parse("/fake/path.pdf")

        assert result.metadata.keywords == []

    @patch("fitz.open")
    @patch("os.path.exists")
    @patch("os.path.getsize")
    def test_extract_metadata_with_whitespace_keywords(
        self, mock_getsize, mock_exists, mock_fitz_open, parser
    ):
        """Should trim whitespace from keywords."""
        # Setup mocks
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_doc = MagicMock()
        mock_doc.__len__ = Mock(return_value=1)
        mock_doc.metadata = {"keywords": "  keyword1  ,  keyword2  , keyword3  "}

        mock_page = MagicMock()
        mock_page.get_text.return_value = "Content"
        mock_doc.__getitem__ = lambda self, idx: mock_page

        mock_fitz_open.return_value = mock_doc

        result = parser.parse("/fake/path.pdf")

        assert result.metadata.keywords == ["keyword1", "keyword2", "keyword3"]


@pytest.mark.unit
class TestPDFParserStateless:
    """Tests to verify stateless behavior."""

    def test_multiple_parses_independent(self, parser, sample_pdf_path):
        """Should handle multiple parse calls independently (stateless)."""
        result1 = parser.parse(str(sample_pdf_path), start_page=1, end_page=2)
        result2 = parser.parse(str(sample_pdf_path), start_page=3, end_page=5)

        # Results should be independent
        assert result1.page_range == (1, 2)
        assert result2.page_range == (3, 5)
        assert result1.content != result2.content
        assert "Machine Learning Fundamentals" in result1.content
        assert "Natural Language Processing" in result2.content

    def test_no_instance_variables(self, parser):
        """Should not have any instance variables (stateless design)."""
        # Parser should have no instance attributes
        assert len(vars(parser)) == 0
