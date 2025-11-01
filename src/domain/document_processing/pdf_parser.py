"""PDF parsing functionality using PyMuPDF."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from src.domain.models.document import Document, DocumentFormat, DocumentMetadata

logger = logging.getLogger(__name__)


class PDFParser:
    """Stateless PDF parser that extracts text and metadata from PDF files.

    This parser uses PyMuPDF (fitz) to extract text content and metadata from
    PDF documents. It supports page range extraction and validates all inputs.

    Design decisions:
    - Stateless: No instance variables, all state passed via parameters
    - Forgiving on range overflows: Clips to available pages with warning
    - Strict on logic errors: Raises ValueError for invalid ranges
    - Text mode: Uses "text" extraction mode for clean text output
    """

    @staticmethod
    def supports(file_format: str) -> bool:
        """Check if this parser supports the given file format.

        Args:
            file_format: File extension or format identifier (case-insensitive)

        Returns:
            True if format is "pdf", False otherwise
        """
        return file_format.lower() == "pdf"

    @staticmethod
    def parse(
        file_path: str,
        start_page: int = 1,
        end_page: Optional[int] = None,
    ) -> Document:
        """Parse a PDF file and extract text content with metadata.

        Args:
            file_path: Path to the PDF file to parse
            start_page: Starting page number (1-indexed, inclusive). Defaults to 1.
            end_page: Ending page number (1-indexed, inclusive). If None, uses last page.

        Returns:
            Document object containing extracted text, metadata, and page range info

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If page range is invalid (start > end, start < 1)

        Notes:
            - Pages are 1-indexed (first page is 1, not 0)
            - If end_page exceeds total pages, it will be clipped with a warning
            - Uses PyMuPDF's "text" mode for clean text extraction
        """
        # Let FileNotFoundError propagate naturally
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting PDF parsing: {file_path}")

        # Open the PDF
        doc = fitz.open(file_path)
        try:
            total_pages = len(doc)

            # Set end_page to last page if not specified
            if end_page is None:
                end_page = total_pages

            # Validate page range - strict for logic errors
            if start_page < 1:
                raise ValueError(
                    f"Invalid page range: pages are 1-indexed, got start={start_page}"
                )

            if start_page > end_page:
                raise ValueError(
                    f"Invalid page range: start ({start_page}) > end ({end_page})"
                )

            # Forgiving for range overflows - clip with warning
            original_end = end_page
            if end_page > total_pages:
                end_page = total_pages
                logger.warning(
                    f"Page range exceeds document length. "
                    f"Requested end_page={original_end}, but document has only "
                    f"{total_pages} pages. Clipping to page {total_pages}."
                )

            # Additional validation after clipping
            if start_page > total_pages:
                raise ValueError(
                    f"Invalid page range: start ({start_page}) exceeds "
                    f"total pages ({total_pages})"
                )

            # Extract text from specified page range
            content_parts = []
            # Convert to 0-indexed for PyMuPDF
            for page_num in range(start_page - 1, end_page):
                page = doc[page_num]
                text = page.get_text("text")
                content_parts.append(text)

            content = "\n".join(content_parts)

            # Extract metadata
            metadata = PDFParser._extract_metadata(doc, file_path)

            logger.info(
                f"PDF parsing completed: {file_path} "
                f"(pages {start_page}-{end_page}, {len(content)} chars)"
            )

            return Document(
                content=content,
                file_path=str(Path(file_path).resolve()),
                page_range=(start_page, end_page),
                metadata=metadata,
            )

        finally:
            doc.close()

    @staticmethod
    def _extract_metadata(doc: fitz.Document, file_path: str) -> DocumentMetadata:
        """Extract metadata from a PDF document.

        Args:
            doc: Opened PyMuPDF document
            file_path: Path to the PDF file (for file size calculation)

        Returns:
            DocumentMetadata object with extracted metadata

        Notes:
            - All optional fields are safely extracted (may be None)
            - Keywords are parsed from comma-separated string
            - Creation date is parsed from PDF format: "D:YYYYMMDDHHmmSS..."
        """
        # Required metadata
        total_pages = len(doc)
        file_size_bytes = os.path.getsize(file_path)

        # Optional metadata - safely extract from PDF metadata dict
        pdf_metadata = doc.metadata or {}

        title = pdf_metadata.get("title") or None
        author = pdf_metadata.get("author") or None
        subject = pdf_metadata.get("subject") or None

        # Parse keywords from comma-separated string
        keywords_str = pdf_metadata.get("keywords", "")
        keywords = (
            [k.strip() for k in keywords_str.split(",") if k.strip()]
            if keywords_str
            else []
        )

        # Parse creation date
        creation_date = None
        creation_date_str = pdf_metadata.get("creationDate")
        if creation_date_str:
            creation_date = PDFParser._parse_pdf_date(creation_date_str)

        return DocumentMetadata(
            total_pages=total_pages,
            file_size_bytes=file_size_bytes,
            file_format=DocumentFormat.PDF,
            title=title,
            author=author,
            subject=subject,
            keywords=keywords,
            creation_date=creation_date,
        )

    @staticmethod
    def _parse_pdf_date(date_str: str) -> Optional[datetime]:
        """Parse PDF date format to datetime.

        PDF date format: "D:YYYYMMDDHHmmSS+HH'mm'"
        Example: "D:20230815143022+02'00'"

        Args:
            date_str: PDF date string

        Returns:
            datetime object if parsing succeeds, None otherwise
        """
        if not date_str:
            return None

        try:
            # Remove "D:" prefix if present
            if date_str.startswith("D:"):
                date_str = date_str[2:]

            # Extract the basic date/time part (first 14 characters: YYYYMMDDHHmmSS)
            # Ignore timezone for simplicity
            if len(date_str) >= 14:
                date_part = date_str[:14]
                return datetime.strptime(date_part, "%Y%m%d%H%M%S")

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse PDF date '{date_str}': {e}")

        return None
