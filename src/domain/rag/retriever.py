"""Retriever component for RAG pipeline.

Orchestrates embedding generation and vector search to provide a simple
interface for retrieving relevant chunks based on a text query.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

from src.domain.models.chunk import Chunk
from src.domain.rag.embeddings import EmbeddingGenerator
from src.domain.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """Result of a retrieval operation with chunk and similarity score.

    Attributes:
        chunk: The retrieved Chunk object
        score: Similarity score (0-1, higher is more similar)
    """

    chunk: Chunk
    score: float

    def __repr__(self) -> str:
        return (
            f"RetrievalResult(chunk_id={self.chunk.chunk_id!r}, score={self.score:.3f})"
        )


class Retriever:
    """Retrieves relevant chunks for a given text query.

    Orchestrates the embedding generation and vector search steps into a
    single, easy-to-use interface. Handles query embedding generation
    internally so callers only need to provide text queries.

    Features:
    - Single method call for query-to-chunks retrieval
    - Configurable number of results (top_k)
    - Optional filtering by source document
    - Access to similarity scores for debugging/ranking
    - Proper validation and error handling

    Design decisions:
    - Instance-based: Holds references to EmbeddingGenerator and VectorStore
    - Thin orchestration layer: Delegates heavy work to existing components
    - Returns both chunks and scores for flexibility

    Example:
        >>> from src.domain.rag.retriever import Retriever
        >>> from src.domain.rag.embeddings import EmbeddingGenerator
        >>> from src.domain.rag.vector_store import VectorStore
        >>>
        >>> generator = EmbeddingGenerator()
        >>> store = VectorStore()
        >>> retriever = Retriever(store, generator)
        >>>
        >>> # Simple retrieval
        >>> chunks = retriever.retrieve("What is machine learning?", top_k=5)
        >>>
        >>> # With scores
        >>> results = retriever.retrieve_with_scores("What is ML?", top_k=3)
        >>> for result in results:
        ...     print(f"{result.score:.3f}: {result.chunk.text[:50]}...")
    """

    DEFAULT_TOP_K = 5

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_generator: EmbeddingGenerator,
    ):
        """Initialize the retriever.

        Args:
            vector_store: VectorStore instance for similarity search.
            embedding_generator: EmbeddingGenerator instance for query embeddings.
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator

        logger.info(
            f"Initialized Retriever with store: {vector_store.collection_name} "
            f"({vector_store.count()} chunks)"
        )

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        source_document: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[Chunk]:
        """Retrieve relevant chunks for a text query.

        Generates an embedding for the query and performs similarity search
        to find the most relevant chunks.

        Args:
            query: Text query to search for.
            top_k: Number of chunks to return (default: 5).
            source_document: Optional filter to only search within a specific
                source document.
            min_score: Optional minimum similarity score threshold (0-1).
                Results below this score are filtered out.

        Returns:
            List of Chunk objects, ordered by relevance (most relevant first).

        Raises:
            ValueError: If query is empty or top_k is invalid.

        Example:
            >>> retriever = Retriever(store, generator)
            >>> chunks = retriever.retrieve("What is ACID?", top_k=3, min_score=0.5)
            >>> for chunk in chunks:
            ...     print(chunk.text[:100])
        """
        results = self.retrieve_with_scores(
            query=query,
            top_k=top_k,
            source_document=source_document,
            min_score=min_score,
        )

        return [result.chunk for result in results]

    def retrieve_with_scores(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        source_document: Optional[str] = None,
        min_score: Optional[float] = None,
    ) -> List[RetrievalResult]:
        """Retrieve relevant chunks with similarity scores.

        Like retrieve(), but also returns similarity scores for each chunk.
        Useful for debugging, ranking analysis, or implementing score thresholds.

        Args:
            query: Text query to search for.
            top_k: Number of chunks to return (default: 5).
            source_document: Optional filter to only search within a specific
                source document.
            min_score: Optional minimum similarity score threshold (0-1).
                Results below this score are filtered out.

        Returns:
            List of RetrievalResult objects with chunks and scores,
            ordered by score (highest first).

        Raises:
            ValueError: If query is empty, top_k is invalid, or min_score is invalid.

        Example:
            >>> retriever = Retriever(store, generator)
            >>> results = retriever.retrieve_with_scores("What is ML?", min_score=0.5)
            >>> for result in results:
            ...     print(f"Score: {result.score:.3f}")
            ...     print(f"Text: {result.chunk.text[:100]}...")
        """
        # Validate inputs
        self._validate_query(query)
        self._validate_top_k(top_k)
        self._validate_min_score(min_score)

        # Check for empty vector store
        if self.vector_store.count() == 0:
            logger.warning("Vector store is empty, returning no results")
            return []

        # Generate query embedding
        logger.debug(f"Generating embedding for query: {query[:50]}...")
        query_embedding = self.embedding_generator.generate_query_embedding(query)

        # Perform similarity search
        logger.debug(f"Searching for top {top_k} similar chunks")
        search_results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            source_document=source_document,
        )

        # Convert to RetrievalResult objects
        results = [
            RetrievalResult(chunk=chunk, score=score) for chunk, score in search_results
        ]

        # Filter by minimum score if specified
        if min_score is not None and results:
            original_count = len(results)
            results = [r for r in results if r.score >= min_score]
            if len(results) < original_count:
                logger.debug(
                    f"Filtered {original_count - len(results)} results below "
                    f"min_score={min_score}"
                )

        if results:
            logger.info(
                f"Retrieved {len(results)} chunks for query: {query[:30]}... "
                f"(top score: {results[0].score:.3f})"
            )
        else:
            logger.info(f"Retrieved 0 chunks for query: {query[:30]}...")

        return results

    def _validate_query(self, query: str) -> None:
        """Validate the query string.

        Args:
            query: Query string to validate.

        Raises:
            ValueError: If query is empty or whitespace only.
        """
        if not query:
            raise ValueError("Query cannot be empty")
        if not query.strip():
            raise ValueError("Query cannot be whitespace only")

    def _validate_top_k(self, top_k: int) -> None:
        """Validate the top_k parameter.

        Args:
            top_k: Number of results to return.

        Raises:
            ValueError: If top_k is not a positive integer.
        """
        # Check for bool first since bool is a subclass of int in Python
        if isinstance(top_k, bool):
            raise ValueError("top_k must be an integer, got bool")
        if not isinstance(top_k, int):
            raise ValueError(f"top_k must be an integer, got {type(top_k).__name__}")
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

    def _validate_min_score(self, min_score: Optional[float]) -> None:
        """Validate the min_score parameter.

        Args:
            min_score: Minimum similarity score threshold.

        Raises:
            ValueError: If min_score is not None and not in range [0, 1].
        """
        if min_score is None:
            return
        if not isinstance(min_score, (int, float)):
            raise ValueError(
                f"min_score must be a number, got {type(min_score).__name__}"
            )
        if min_score < 0 or min_score > 1:
            raise ValueError(f"min_score must be between 0 and 1, got {min_score}")
