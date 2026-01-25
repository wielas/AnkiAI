"""Embedding generation for RAG pipeline using OpenAI's text-embedding-3-small."""

import logging
import time
from typing import Any, Dict, List, Optional

import openai
from openai import APIError, RateLimitError

from src.domain.models.chunk import Chunk
from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generates embeddings for text chunks using OpenAI's embedding API.

    Features:
    - Batch processing with automatic splitting for large inputs
    - Automatic retry with exponential backoff for rate limits and transient errors
    - Token usage tracking and cost estimation
    - Updates chunks in-place with embedding vectors

    Design decisions:
    - Instance-based for token tracking across multiple calls
    - Uses text-embedding-3-small (1536 dimensions, $0.02 per 1M tokens)
    - Batch size of 2048 (OpenAI limit) for efficiency
    - Retry on rate limits and server errors, fail fast on auth/bad requests

    Example:
        >>> from src.domain.rag.embeddings import EmbeddingGenerator
        >>> from src.domain.models.chunk import Chunk
        >>>
        >>> generator = EmbeddingGenerator()
        >>> chunks = [Chunk(chunk_id="test_001", text="Hello world", ...)]
        >>> generator.generate_embeddings(chunks)
        >>> assert chunks[0].has_embedding()
    """

    # OpenAI embedding model settings
    MODEL = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS = 1536
    MAX_BATCH_SIZE = 2048  # OpenAI limit per API call
    MAX_INPUT_TOKENS = 8191  # Per text input

    # Pricing for text-embedding-3-small (per million tokens)
    PRICE_PER_MILLION_TOKENS = 0.02  # $0.02 per 1M tokens

    def __init__(
        self,
        api_key: Optional[str] = None,
        min_request_interval: float = 0.1,
    ):
        """Initialize the embedding generator.

        Args:
            api_key: OpenAI API key. If None, loads from settings.
            min_request_interval: Minimum seconds between requests for rate limiting.
                Default 0.1s (10 req/sec). Set to 0 to disable.

        Raises:
            ValueError: If no API key is provided and none found in settings.
        """
        settings = get_settings()
        self.api_key = api_key or settings.openai_api_key

        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY in .env or pass api_key."
            )

        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)

        # Token tracking
        self.total_tokens = 0
        self.api_calls = 0

        # Rate limiting
        self.min_request_interval = min_request_interval
        self.last_request_time = 0.0

        logger.info(f"Initialized EmbeddingGenerator with model: {self.MODEL}")

    def generate_embeddings(
        self,
        chunks: List[Chunk],
        max_retries: int = 3,
    ) -> List[Chunk]:
        """Generate embeddings for a list of chunks.

        Updates each chunk's embedding field in-place and returns the chunks.

        Args:
            chunks: List of Chunk objects to generate embeddings for.
            max_retries: Maximum retry attempts per batch (default: 3).

        Returns:
            The same list of chunks with embedding field populated.

        Raises:
            openai.AuthenticationError: Invalid API key (not retried).
            openai.BadRequestError: Invalid request (not retried).
            openai.APIError: API error after all retries exhausted.
            ValueError: If chunks list is empty or contains invalid data.

        Example:
            >>> generator = EmbeddingGenerator()
            >>> chunks = chunker.chunk(document)
            >>> generator.generate_embeddings(chunks)
            >>> for chunk in chunks:
            ...     assert chunk.has_embedding()
        """
        if not chunks:
            logger.warning("No chunks provided for embedding generation")
            return chunks

        # Validate chunks have text
        for i, chunk in enumerate(chunks):
            if not chunk.text or not chunk.text.strip():
                raise ValueError(f"Chunk at index {i} has empty text: {chunk.chunk_id}")

        logger.info(f"Generating embeddings for {len(chunks)} chunks")

        # Split into batches if needed
        batches = self._create_batches(chunks)
        logger.info(f"Split into {len(batches)} batch(es)")

        # Process each batch
        for batch_idx, batch in enumerate(batches):
            logger.debug(
                f"Processing batch {batch_idx + 1}/{len(batches)} "
                f"({len(batch)} chunks)"
            )

            embeddings = self._generate_batch_embeddings(
                texts=[chunk.text for chunk in batch],
                max_retries=max_retries,
            )

            # Update chunks with embeddings
            for chunk, embedding in zip(batch, embeddings, strict=True):
                chunk.embedding = embedding

        logger.info(
            f"Embedding generation complete. "
            f"Total tokens: {self.total_tokens}, API calls: {self.api_calls}"
        )

        return chunks

    def _create_batches(self, chunks: List[Chunk]) -> List[List[Chunk]]:
        """Split chunks into batches respecting OpenAI's batch size limit.

        Args:
            chunks: List of chunks to batch.

        Returns:
            List of chunk batches, each with at most MAX_BATCH_SIZE chunks.
        """
        batches = []
        for i in range(0, len(chunks), self.MAX_BATCH_SIZE):
            batch = chunks[i : i + self.MAX_BATCH_SIZE]
            batches.append(batch)
        return batches

    def _generate_batch_embeddings(
        self,
        texts: List[str],
        max_retries: int = 3,
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of text strings to embed.
            max_retries: Maximum retry attempts.

        Returns:
            List of embedding vectors (each is a list of 1536 floats).

        Raises:
            openai.AuthenticationError: Invalid API key.
            openai.BadRequestError: Invalid request.
            openai.APIError: After all retries exhausted.
        """
        attempt = 0
        last_error = None

        while attempt < max_retries:
            try:
                attempt += 1

                # Rate limiting
                if self.min_request_interval > 0:
                    elapsed = time.time() - self.last_request_time
                    if elapsed < self.min_request_interval:
                        sleep_time = self.min_request_interval - elapsed
                        logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
                        time.sleep(sleep_time)
                    self.last_request_time = time.time()

                # Make API call
                logger.debug(
                    f"Calling OpenAI Embeddings API "
                    f"(attempt {attempt}/{max_retries}, texts: {len(texts)})"
                )

                response = self.client.embeddings.create(
                    model=self.MODEL,
                    input=texts,
                )

                # Track usage
                self.total_tokens += response.usage.total_tokens
                self.api_calls += 1

                logger.debug(
                    f"API call successful. Tokens used: {response.usage.total_tokens}"
                )

                # Extract embeddings in order
                # Response data is ordered by input index
                embeddings = [item.embedding for item in response.data]

                return embeddings

            except openai.AuthenticationError as e:
                logger.error(f"Authentication error: {e}")
                raise

            except openai.BadRequestError as e:
                logger.error(f"Bad request error: {e}")
                raise

            except (
                RateLimitError,
                openai.InternalServerError,
                openai.APIConnectionError,
                openai.APITimeoutError,
            ) as e:
                last_error = e
                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)  # Exponential backoff
                    logger.warning(
                        f"Retryable error ({type(e).__name__}): {e}. "
                        f"Retrying in {wait_time}s... "
                        f"(attempt {attempt}/{max_retries})"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        f"Max retries ({max_retries}) exhausted. Last error: {e}"
                    )
                    raise

            except Exception as e:
                logger.error(f"Unexpected error: {type(e).__name__}: {e}")
                raise

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise APIError("Failed to generate embeddings after all retries")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get token usage statistics and cost estimation.

        Returns:
            Dictionary with usage stats:
            - api_calls: Number of API calls made
            - total_tokens: Total tokens used
            - estimated_cost: Estimated cost in USD

        Example:
            >>> generator = EmbeddingGenerator()
            >>> generator.generate_embeddings(chunks)
            >>> stats = generator.get_usage_stats()
            >>> print(f"Cost: ${stats['estimated_cost']:.4f}")
        """
        estimated_cost = (self.total_tokens / 1_000_000) * self.PRICE_PER_MILLION_TOKENS

        return {
            "api_calls": self.api_calls,
            "total_tokens": self.total_tokens,
            "estimated_cost": round(estimated_cost, 6),
            "model": self.MODEL,
            "dimensions": self.EMBEDDING_DIMENSIONS,
        }

    def reset_stats(self) -> None:
        """Reset token usage statistics."""
        self.total_tokens = 0
        self.api_calls = 0
        logger.debug("Reset usage statistics")

    def generate_query_embedding(
        self,
        query: str,
        max_retries: int = 3,
    ) -> List[float]:
        """Generate embedding for a single query string.

        Convenience method for generating a single embedding, useful for
        search queries.

        Args:
            query: Query text to embed.
            max_retries: Maximum retry attempts.

        Returns:
            Embedding vector (list of 1536 floats).

        Raises:
            ValueError: If query is empty.
            openai.APIError: If API call fails.

        Example:
            >>> generator = EmbeddingGenerator()
            >>> query_embedding = generator.generate_query_embedding(
            ...     "What is machine learning?"
            ... )
            >>> len(query_embedding)
            1536
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        embeddings = self._generate_batch_embeddings([query], max_retries)
        return embeddings[0]
