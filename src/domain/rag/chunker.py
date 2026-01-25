"""Semantic chunking functionality for RAG pipeline."""

import logging
import re
from pathlib import Path
from typing import List

import tiktoken

from src.domain.models.chunk import Chunk
from src.domain.models.document import Document

logger = logging.getLogger(__name__)

# Default encoding for OpenAI text-embedding-3-large
DEFAULT_ENCODING = "cl100k_base"


class Chunker:
    """Stateless semantic chunker that splits documents into meaningful chunks.

    This chunker uses a paragraph-first approach to split documents into chunks
    suitable for embedding and retrieval. It respects semantic boundaries
    (paragraphs, sentences) and adds overlap between chunks to preserve context.

    Design decisions:
    - Stateless: No instance variables, all state passed via parameters
    - Paragraph-first: Split by paragraphs, then by sentences if needed
    - Overlap: Add configurable overlap between chunks for context
    - Token-based: Uses tiktoken for accurate token counting
    """

    @staticmethod
    def chunk(
        document: Document,
        target_size: int = 800,
        overlap_size: int = 100,
        max_chunk_size: int = 1200,
    ) -> List[Chunk]:
        """Split document into semantic chunks.

        Strategy:
        1. Split by paragraphs (double newlines)
        2. Accumulate paragraphs until ~target_size tokens
        3. If single paragraph > max_chunk_size, split by sentences
        4. Add overlap_size token overlap between chunks
        5. Track metadata (pages, position, overlap info)

        Args:
            document: Document to chunk (from PDFParser)
            target_size: Target tokens per chunk (default 800)
            overlap_size: Overlap between chunks in tokens (default 100)
            max_chunk_size: Max size before forcing split (default 1200)

        Returns:
            List of Chunk objects in document order

        Raises:
            ValueError: If target_size <= 0 or overlap_size < 0
        """
        # Validate parameters
        if target_size <= 0:
            raise ValueError(f"target_size must be positive, got {target_size}")
        if overlap_size < 0:
            raise ValueError(f"overlap_size must be non-negative, got {overlap_size}")
        if max_chunk_size <= 0:
            raise ValueError(f"max_chunk_size must be positive, got {max_chunk_size}")
        if overlap_size >= target_size:
            raise ValueError(
                f"overlap_size ({overlap_size}) must be less than "
                f"target_size ({target_size})"
            )

        logger.info(
            f"Starting chunking: {document.file_path} "
            f"(target={target_size}, overlap={overlap_size}, max={max_chunk_size})"
        )

        # Handle empty documents
        if not document.content or not document.content.strip():
            logger.warning(f"Empty document: {document.file_path}")
            return []

        # Get encoding for token counting
        encoding = tiktoken.get_encoding(DEFAULT_ENCODING)

        # Split into paragraphs
        paragraphs = Chunker._split_into_paragraphs(document.content)

        if not paragraphs:
            logger.warning(f"No paragraphs found in document: {document.file_path}")
            return []

        # Process paragraphs into chunks
        raw_chunks = Chunker._accumulate_paragraphs(
            paragraphs=paragraphs,
            target_size=target_size,
            max_chunk_size=max_chunk_size,
            encoding=encoding,
        )

        if not raw_chunks:
            return []

        # Add overlap between chunks
        chunks_with_overlap = Chunker._add_overlap(
            raw_chunks=raw_chunks,
            overlap_size=overlap_size,
            encoding=encoding,
        )

        # Build final Chunk objects
        chunks = Chunker._build_chunks(
            texts=chunks_with_overlap,
            document=document,
            encoding=encoding,
        )

        # Link overlap references
        Chunker._link_overlaps(chunks)

        logger.info(
            f"Chunking completed: {document.file_path} -> {len(chunks)} chunks "
            f"(avg {sum(c.token_count for c in chunks) // len(chunks) if chunks else 0} tokens)"
        )

        return chunks

    @staticmethod
    def _split_into_paragraphs(text: str) -> List[str]:
        """Split text into paragraphs.

        Args:
            text: Text to split

        Returns:
            List of non-empty paragraphs
        """
        # Split by double newlines (paragraph breaks)
        paragraphs = re.split(r"\n\s*\n", text)

        # Strip whitespace and filter empty paragraphs
        return [p.strip() for p in paragraphs if p.strip()]

    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences.

        Uses simple heuristics to detect sentence boundaries.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Split on sentence-ending punctuation followed by space and capital letter
        # This regex keeps the punctuation with the sentence
        sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

        # Strip and filter empty sentences
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def _count_tokens(text: str, encoding: tiktoken.Encoding) -> int:
        """Count tokens in text.

        Args:
            text: Text to count tokens for
            encoding: Tiktoken encoding to use

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(encoding.encode(text))

    @staticmethod
    def _generate_chunk_id(document: Document, position: int) -> str:
        """Generate a unique chunk ID.

        Args:
            document: Source document
            position: Position in document (0-indexed)

        Returns:
            Chunk ID in format "filename_chunk_001"
        """
        # Extract filename without extension
        filename = Path(document.file_path).stem

        # Sanitize filename (replace spaces and special chars with underscores)
        filename = re.sub(r"[^\w]", "_", filename)
        filename = re.sub(r"_+", "_", filename)  # Collapse multiple underscores
        filename = filename.strip("_")

        return f"{filename}_chunk_{position:03d}"

    @staticmethod
    def _extract_overlap(
        text: str, size: int, encoding: tiktoken.Encoding, from_end: bool = True
    ) -> str:
        """Extract overlap text from a chunk.

        Args:
            text: Text to extract from
            size: Target overlap size in tokens
            encoding: Tiktoken encoding to use
            from_end: If True, extract from end; if False, extract from start

        Returns:
            Overlap text
        """
        if size <= 0 or not text:
            return ""

        tokens = encoding.encode(text)

        if len(tokens) <= size:
            return text

        if from_end:
            overlap_tokens = tokens[-size:]
        else:
            overlap_tokens = tokens[:size]

        return encoding.decode(overlap_tokens)

    @staticmethod
    def _accumulate_paragraphs(
        paragraphs: List[str],
        target_size: int,
        max_chunk_size: int,
        encoding: tiktoken.Encoding,
    ) -> List[str]:
        """Accumulate paragraphs into chunks.

        Args:
            paragraphs: List of paragraphs
            target_size: Target tokens per chunk
            max_chunk_size: Max tokens before forcing split
            encoding: Tiktoken encoding to use

        Returns:
            List of raw chunk texts (before overlap)
        """
        chunks = []
        current_text = ""

        for paragraph in paragraphs:
            para_tokens = Chunker._count_tokens(paragraph, encoding)

            # Handle oversized paragraphs
            if para_tokens > max_chunk_size:
                # Flush current chunk if not empty
                if current_text:
                    chunks.append(current_text)
                    current_text = ""

                # Split paragraph by sentences
                sentence_chunks = Chunker._split_paragraph_by_sentences(
                    paragraph=paragraph,
                    target_size=target_size,
                    max_chunk_size=max_chunk_size,
                    encoding=encoding,
                )
                chunks.extend(sentence_chunks)
                continue

            # Check if adding this paragraph exceeds target
            combined_text = (
                f"{current_text}\n\n{paragraph}" if current_text else paragraph
            )
            combined_tokens = Chunker._count_tokens(combined_text, encoding)

            if combined_tokens > target_size and current_text:
                # Save current chunk and start new one
                chunks.append(current_text)
                current_text = paragraph
            else:
                # Accumulate
                current_text = combined_text

        # Don't forget the last chunk
        if current_text:
            chunks.append(current_text)

        return chunks

    @staticmethod
    def _split_paragraph_by_sentences(
        paragraph: str,
        target_size: int,
        max_chunk_size: int,
        encoding: tiktoken.Encoding,
    ) -> List[str]:
        """Split an oversized paragraph by sentences.

        Args:
            paragraph: Paragraph to split
            target_size: Target tokens per chunk
            max_chunk_size: Max tokens before forcing split
            encoding: Tiktoken encoding to use

        Returns:
            List of chunk texts
        """
        sentences = Chunker._split_into_sentences(paragraph)

        if not sentences:
            # Fallback: force split by tokens if no sentences found
            return Chunker._force_split(paragraph, target_size, encoding)

        chunks = []
        current_text = ""

        for sentence in sentences:
            sent_tokens = Chunker._count_tokens(sentence, encoding)

            # Handle oversized sentences
            if sent_tokens > max_chunk_size:
                # Flush current chunk if not empty
                if current_text:
                    chunks.append(current_text)
                    current_text = ""

                # Force split the sentence
                sentence_chunks = Chunker._force_split(sentence, target_size, encoding)
                chunks.extend(sentence_chunks)
                continue

            # Check if adding this sentence exceeds target
            combined_text = f"{current_text} {sentence}" if current_text else sentence
            combined_tokens = Chunker._count_tokens(combined_text, encoding)

            if combined_tokens > target_size and current_text:
                # Save current chunk and start new one
                chunks.append(current_text)
                current_text = sentence
            else:
                # Accumulate
                current_text = combined_text

        # Don't forget the last chunk
        if current_text:
            chunks.append(current_text)

        return chunks

    @staticmethod
    def _force_split(
        text: str, target_size: int, encoding: tiktoken.Encoding
    ) -> List[str]:
        """Force split text by token count when semantic splitting fails.

        Args:
            text: Text to split
            target_size: Target tokens per chunk
            encoding: Tiktoken encoding to use

        Returns:
            List of chunk texts
        """
        tokens = encoding.encode(text)
        chunks = []

        for i in range(0, len(tokens), target_size):
            chunk_tokens = tokens[i : i + target_size]
            chunk_text = encoding.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks

    @staticmethod
    def _add_overlap(
        raw_chunks: List[str],
        overlap_size: int,
        encoding: tiktoken.Encoding,
    ) -> List[str]:
        """Add overlap between chunks.

        Args:
            raw_chunks: List of raw chunk texts
            overlap_size: Overlap size in tokens
            encoding: Tiktoken encoding to use

        Returns:
            List of chunk texts with overlap added
        """
        if overlap_size <= 0 or len(raw_chunks) <= 1:
            return raw_chunks

        result = []

        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                # First chunk: no overlap before
                result.append(chunk)
            else:
                # Add overlap from previous chunk
                overlap = Chunker._extract_overlap(
                    raw_chunks[i - 1], overlap_size, encoding, from_end=True
                )
                if overlap:
                    result.append(f"{overlap}\n\n{chunk}")
                else:
                    result.append(chunk)

        return result

    @staticmethod
    def _build_chunks(
        texts: List[str],
        document: Document,
        encoding: tiktoken.Encoding,
    ) -> List[Chunk]:
        """Build Chunk objects from text list.

        Args:
            texts: List of chunk texts
            document: Source document
            encoding: Tiktoken encoding to use

        Returns:
            List of Chunk objects
        """
        chunks = []
        page_numbers = list(range(document.page_range[0], document.page_range[1] + 1))

        for i, text in enumerate(texts):
            chunk_id = Chunker._generate_chunk_id(document, i)
            token_count = Chunker._count_tokens(text, encoding)

            # Determine overlap flags
            has_overlap_before = i > 0
            has_overlap_after = i < len(texts) - 1

            chunk = Chunk(
                chunk_id=chunk_id,
                text=text,
                source_document=document.file_path,
                page_numbers=page_numbers,
                position=i,
                token_count=token_count,
                char_count=len(text),
                has_overlap_before=has_overlap_before,
                has_overlap_after=has_overlap_after,
            )
            chunks.append(chunk)

        return chunks

    @staticmethod
    def _link_overlaps(chunks: List[Chunk]) -> None:
        """Link overlap references between chunks.

        Modifies chunks in place.

        Args:
            chunks: List of chunks to link
        """
        for i, chunk in enumerate(chunks):
            if i > 0:
                chunk.overlap_with_previous = chunks[i - 1].chunk_id
            if i < len(chunks) - 1:
                chunk.overlap_with_next = chunks[i + 1].chunk_id
