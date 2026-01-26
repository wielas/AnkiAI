"""ContextBuilder component for RAG pipeline.

Formats retrieved chunks into LLM-ready context strings with proper
formatting, metadata, and token management.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

import tiktoken

from src.domain.models.chunk import Chunk

logger = logging.getLogger(__name__)

# Default encoding for OpenAI models
DEFAULT_ENCODING = "cl100k_base"

# Ellipsis used for truncated text
TRUNCATION_ELLIPSIS = "..."


class ChunkOrdering(Enum):
    """Ordering strategy for chunks in context.

    Attributes:
        RELEVANCE: Order by retrieval score (most relevant first) - default
        POSITION: Order by position in source document (preserves reading order)
    """

    RELEVANCE = "relevance"
    POSITION = "position"


@dataclass
class ContextResult:
    """Result of context building with metadata.

    Attributes:
        context: The formatted context string
        token_count: Estimated token count
        chunk_count: Number of chunks included
        truncated: Whether any chunks were truncated
    """

    context: str
    token_count: int
    chunk_count: int
    truncated: bool = False


class ContextBuilder:
    """Builds LLM-ready context strings from retrieved chunks.

    Formats multiple chunks into a single context string suitable for
    inclusion in LLM prompts. Handles metadata formatting, separators,
    token estimation, and truncation.

    Features:
    - Configurable chunk separators
    - Optional metadata inclusion (source, pages)
    - Token count estimation
    - Truncation to fit token limits
    - Multiple ordering strategies (relevance vs position)

    Design decisions:
    - Stateless: All methods are static or class methods
    - Simple defaults: Works out of the box with sensible defaults
    - Flexible: Many options for customization when needed

    Example:
        >>> from src.domain.rag.context_builder import ContextBuilder
        >>>
        >>> # Simple usage
        >>> context = ContextBuilder.build_context(chunks)
        >>>
        >>> # With metadata
        >>> context = ContextBuilder.build_context(chunks, include_metadata=True)
        >>>
        >>> # With token limit
        >>> result = ContextBuilder.build_context_with_limit(
        ...     chunks, max_tokens=2000
        ... )
        >>> print(f"Context uses {result.token_count} tokens")
    """

    # Default separator between chunks
    DEFAULT_SEPARATOR = "\n\n---\n\n"

    # Default metadata format
    METADATA_FORMAT = "[Source: {source}, Pages: {pages}]"

    @staticmethod
    def build_context(
        chunks: List[Chunk],
        separator: str = DEFAULT_SEPARATOR,
        include_metadata: bool = False,
        ordering: ChunkOrdering = ChunkOrdering.RELEVANCE,
    ) -> str:
        """Build a context string from chunks.

        Assembles multiple chunks into a single string with separators.
        Optionally includes metadata (source file, page numbers) for each chunk.

        Args:
            chunks: List of Chunk objects to include in context.
            separator: String to use between chunks (default: "\\n\\n---\\n\\n").
            include_metadata: Whether to include source/page metadata (default: False).
            ordering: How to order chunks - RELEVANCE keeps retrieval order,
                POSITION orders by document position (default: RELEVANCE).

        Returns:
            Formatted context string.

        Example:
            >>> chunks = retriever.retrieve("What is ML?", top_k=3)
            >>> context = ContextBuilder.build_context(chunks)
            >>> print(context)
        """
        if not chunks:
            logger.debug("No chunks provided, returning empty context")
            return ""

        # Apply ordering
        ordered_chunks = ContextBuilder._order_chunks(chunks, ordering)

        # Format each chunk
        formatted_chunks = []
        for chunk in ordered_chunks:
            formatted = ContextBuilder._format_chunk(chunk, include_metadata)
            formatted_chunks.append(formatted)

        # Join with separator
        context = separator.join(formatted_chunks)

        logger.debug(
            f"Built context from {len(chunks)} chunks "
            f"({len(context)} chars, metadata={include_metadata})"
        )

        return context

    @staticmethod
    def build_context_with_limit(
        chunks: List[Chunk],
        max_tokens: int,
        separator: str = DEFAULT_SEPARATOR,
        include_metadata: bool = False,
        ordering: ChunkOrdering = ChunkOrdering.RELEVANCE,
    ) -> ContextResult:
        """Build context with a token limit, truncating if necessary.

        Includes chunks until the token limit is reached. If a chunk would
        exceed the limit, it is truncated to fit.

        Args:
            chunks: List of Chunk objects to include in context.
            max_tokens: Maximum tokens for the context.
            separator: String to use between chunks.
            include_metadata: Whether to include source/page metadata.
            ordering: How to order chunks.

        Returns:
            ContextResult with context string and metadata.

        Raises:
            ValueError: If max_tokens is not positive.

        Example:
            >>> result = ContextBuilder.build_context_with_limit(
            ...     chunks, max_tokens=2000, include_metadata=True
            ... )
            >>> print(f"Used {result.token_count} tokens, truncated: {result.truncated}")
        """
        if max_tokens <= 0:
            raise ValueError(f"max_tokens must be positive, got {max_tokens}")

        if not chunks:
            return ContextResult(context="", token_count=0, chunk_count=0)

        encoding = tiktoken.get_encoding(DEFAULT_ENCODING)

        # Apply ordering
        ordered_chunks = ContextBuilder._order_chunks(chunks, ordering)

        # Build context incrementally
        formatted_chunks = []
        total_tokens = 0
        truncated = False
        separator_tokens = len(encoding.encode(separator))

        for chunk in ordered_chunks:
            formatted = ContextBuilder._format_chunk(chunk, include_metadata)
            chunk_tokens = len(encoding.encode(formatted))

            # Account for separator (not needed for first chunk)
            needed_tokens = chunk_tokens
            if formatted_chunks:
                needed_tokens += separator_tokens

            # Check if we can fit the full chunk
            if total_tokens + needed_tokens <= max_tokens:
                formatted_chunks.append(formatted)
                total_tokens += needed_tokens
            else:
                # Try to fit a truncated version
                remaining_tokens = max_tokens - total_tokens
                if formatted_chunks:
                    remaining_tokens -= separator_tokens

                # Account for ellipsis tokens
                ellipsis_tokens = len(encoding.encode(TRUNCATION_ELLIPSIS))
                min_meaningful_tokens = 50 + ellipsis_tokens

                if remaining_tokens > min_meaningful_tokens:
                    # Reserve space for ellipsis
                    truncated_text = ContextBuilder._truncate_to_tokens(
                        formatted, remaining_tokens - ellipsis_tokens, encoding
                    )
                    if truncated_text:
                        formatted_chunks.append(truncated_text + TRUNCATION_ELLIPSIS)
                        truncated = True

                # Stop adding more chunks
                break

        # Join with separator
        context = separator.join(formatted_chunks)

        # Recalculate actual token count
        actual_tokens = len(encoding.encode(context)) if context else 0

        logger.debug(
            f"Built context with limit: {len(formatted_chunks)}/{len(chunks)} chunks, "
            f"{actual_tokens} tokens, truncated={truncated}"
        )

        return ContextResult(
            context=context,
            token_count=actual_tokens,
            chunk_count=len(formatted_chunks),
            truncated=truncated,
        )

    @staticmethod
    def estimate_tokens(
        chunks: List[Chunk],
        separator: str = DEFAULT_SEPARATOR,
        include_metadata: bool = False,
    ) -> int:
        """Estimate the token count for a context built from chunks.

        Useful for checking if chunks will fit within a token budget
        before building the full context.

        Args:
            chunks: List of Chunk objects.
            separator: Separator that will be used.
            include_metadata: Whether metadata will be included.

        Returns:
            Estimated token count.

        Example:
            >>> tokens = ContextBuilder.estimate_tokens(chunks, include_metadata=True)
            >>> if tokens > 4000:
            ...     chunks = chunks[:5]  # Reduce chunk count
        """
        if not chunks:
            return 0

        encoding = tiktoken.get_encoding(DEFAULT_ENCODING)
        separator_tokens = len(encoding.encode(separator))  # Cache once

        total_tokens = 0
        for i, chunk in enumerate(chunks):
            formatted = ContextBuilder._format_chunk(chunk, include_metadata)
            total_tokens += len(encoding.encode(formatted))

            # Add separator tokens (not for first chunk)
            if i > 0:
                total_tokens += separator_tokens

        return total_tokens

    @staticmethod
    def _format_chunk(chunk: Chunk, include_metadata: bool) -> str:
        """Format a single chunk with optional metadata.

        Args:
            chunk: Chunk to format.
            include_metadata: Whether to include metadata header.

        Returns:
            Formatted chunk string.
        """
        if not include_metadata:
            return chunk.text

        # Format metadata
        source = Path(chunk.source_document).name
        pages = chunk.page_numbers

        # Format page numbers compactly
        if pages:
            sorted_pages = sorted(pages)
            if len(sorted_pages) == 1:
                page_str = str(sorted_pages[0])
            elif sorted_pages == list(range(sorted_pages[0], sorted_pages[-1] + 1)):
                # Consecutive range
                page_str = f"{sorted_pages[0]}-{sorted_pages[-1]}"
            else:
                # Non-consecutive - display sorted for consistency
                page_str = ", ".join(map(str, sorted_pages))
        else:
            page_str = "unknown"

        metadata = ContextBuilder.METADATA_FORMAT.format(
            source=source,
            pages=page_str,
        )

        return f"{metadata}\n{chunk.text}"

    @staticmethod
    def _order_chunks(chunks: List[Chunk], ordering: ChunkOrdering) -> List[Chunk]:
        """Order chunks according to the specified strategy.

        Args:
            chunks: List of chunks to order.
            ordering: Ordering strategy.

        Returns:
            Ordered list of chunks.
        """
        if ordering == ChunkOrdering.RELEVANCE:
            # Keep original order (assumed to be by relevance)
            return chunks
        elif ordering == ChunkOrdering.POSITION:
            # Sort by document position
            return sorted(chunks, key=lambda c: (c.source_document, c.position))
        else:
            return chunks

    @staticmethod
    def _truncate_to_tokens(
        text: str,
        max_tokens: int,
        encoding: tiktoken.Encoding,
    ) -> str:
        """Truncate text to fit within a token limit.

        Args:
            text: Text to truncate.
            max_tokens: Maximum tokens.
            encoding: Tiktoken encoding.

        Returns:
            Truncated text.
        """
        tokens = encoding.encode(text)

        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
