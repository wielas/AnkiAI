"""Vector store for semantic search using ChromaDB."""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings

from src.domain.models.chunk import Chunk
from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Persistent vector store for chunk embeddings using ChromaDB.

    Stores chunks with their embeddings and metadata for semantic similarity
    search. Uses ChromaDB with persistent storage so embeddings survive
    across sessions.

    Features:
    - Persistent storage (embeddings saved to disk)
    - Semantic similarity search
    - Full chunk reconstruction from stored data
    - Support for multiple documents via metadata filtering
    - Collection management (create, delete, list)

    Design decisions:
    - Uses a single collection with document metadata for filtering
    - Stores all chunk fields as metadata for full reconstruction
    - Returns similarity scores (higher = more similar)
    - ChromaDB uses L2 distance, we convert to similarity

    Example:
        >>> from src.domain.rag.vector_store import VectorStore
        >>> from src.domain.rag.embeddings import EmbeddingGenerator
        >>>
        >>> # Initialize store
        >>> store = VectorStore()
        >>>
        >>> # Add chunks with embeddings
        >>> generator = EmbeddingGenerator()
        >>> chunks = generator.generate_embeddings(chunks)
        >>> store.add_chunks(chunks)
        >>>
        >>> # Search for similar chunks
        >>> query_embedding = generator.generate_query_embedding("What is ML?")
        >>> results = store.search(query_embedding, top_k=5)
        >>> for chunk, score in results:
        ...     print(f"{score:.3f}: {chunk.text[:50]}...")
    """

    DEFAULT_COLLECTION_NAME = "ankiai_chunks"

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        """Initialize the vector store.

        Args:
            persist_directory: Path to ChromaDB storage directory.
                If None, uses settings.chroma_db_path.
            collection_name: Name of the collection to use.
                If None, uses DEFAULT_COLLECTION_NAME.
        """
        settings = get_settings()
        self.persist_directory = persist_directory or settings.chroma_db_path
        self.collection_name = collection_name or self.DEFAULT_COLLECTION_NAME

        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistent storage
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AnkiAI chunk embeddings for RAG"},
        )

        logger.info(
            f"Initialized VectorStore: {self.persist_directory}/{self.collection_name} "
            f"({self.collection.count()} chunks)"
        )

    def add_chunks(self, chunks: List[Chunk]) -> int:
        """Add chunks with embeddings to the vector store.

        Args:
            chunks: List of Chunk objects with embeddings populated.

        Returns:
            Number of chunks added.

        Raises:
            ValueError: If any chunk is missing an embedding.

        Example:
            >>> store = VectorStore()
            >>> generator = EmbeddingGenerator()
            >>> chunks = generator.generate_embeddings(chunks)
            >>> count = store.add_chunks(chunks)
            >>> print(f"Added {count} chunks")
        """
        if not chunks:
            logger.warning("No chunks provided to add")
            return 0

        # Validate all chunks have embeddings
        for chunk in chunks:
            if not chunk.has_embedding():
                raise ValueError(
                    f"Chunk {chunk.chunk_id} is missing embedding. "
                    "Run EmbeddingGenerator.generate_embeddings() first."
                )

        # Prepare data for ChromaDB
        ids = [chunk.chunk_id for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [self._chunk_to_metadata(chunk) for chunk in chunks]

        # Add to collection (upsert to handle duplicates)
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Added {len(chunks)} chunks to collection '{self.collection_name}'"
        )
        return len(chunks)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        source_document: Optional[str] = None,
    ) -> List[Tuple[Chunk, float]]:
        """Search for chunks similar to query embedding.

        Args:
            query_embedding: Query embedding vector (1536 dimensions).
            top_k: Number of results to return (default: 5).
            source_document: Optional filter to only search within a specific
                source document.

        Returns:
            List of (Chunk, similarity_score) tuples, sorted by similarity
            (highest first). Similarity scores are in range [0, 1].

        Example:
            >>> store = VectorStore()
            >>> generator = EmbeddingGenerator()
            >>> query_emb = generator.generate_query_embedding("What is ML?")
            >>> results = store.search(query_emb, top_k=3)
            >>> for chunk, score in results:
            ...     print(f"Score: {score:.3f}")
            ...     print(f"Text: {chunk.text[:100]}...")
        """
        if self.collection.count() == 0:
            logger.warning("Collection is empty, returning no results")
            return []

        # Build where clause for filtering
        where = None
        if source_document:
            where = {"source_document": source_document}

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count()),
            where=where,
            include=["embeddings", "documents", "metadatas", "distances"],
        )

        # Convert results to (Chunk, similarity) tuples
        chunks_with_scores = []

        if not results["ids"] or not results["ids"][0]:
            return []

        for i, chunk_id in enumerate(results["ids"][0]):
            # Reconstruct chunk from stored data
            chunk = self._metadata_to_chunk(
                chunk_id=chunk_id,
                text=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                embedding=(
                    results["embeddings"][0][i] if results["embeddings"] else None
                ),
            )

            # Convert L2 distance to similarity score
            # ChromaDB returns L2 distance (lower = more similar)
            # We convert to similarity: 1 / (1 + distance)
            distance = results["distances"][0][i]
            similarity = 1 / (1 + distance)

            chunks_with_scores.append((chunk, similarity))

        logger.debug(
            f"Search returned {len(chunks_with_scores)} results "
            f"(top score: {chunks_with_scores[0][1]:.3f})"
        )

        return chunks_with_scores

    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Retrieve a specific chunk by ID.

        Args:
            chunk_id: The chunk ID to retrieve.

        Returns:
            The Chunk if found, None otherwise.

        Example:
            >>> store = VectorStore()
            >>> chunk = store.get_chunk("document_chunk_001")
            >>> if chunk:
            ...     print(chunk.text)
        """
        results = self.collection.get(
            ids=[chunk_id],
            include=["embeddings", "documents", "metadatas"],
        )

        if not results["ids"]:
            return None

        # Handle embeddings - check if it's not None and has content
        embedding = None
        if results["embeddings"] is not None and len(results["embeddings"]) > 0:
            embedding = results["embeddings"][0]

        return self._metadata_to_chunk(
            chunk_id=results["ids"][0],
            text=results["documents"][0],
            metadata=results["metadatas"][0],
            embedding=embedding,
        )

    def delete_chunks(self, chunk_ids: List[str]) -> int:
        """Delete specific chunks by ID.

        Args:
            chunk_ids: List of chunk IDs to delete.

        Returns:
            Number of chunks that existed before deletion.

        Example:
            >>> store = VectorStore()
            >>> store.delete_chunks(["doc_chunk_001", "doc_chunk_002"])
        """
        if not chunk_ids:
            return 0

        # Check how many exist before deleting
        existing = self.collection.get(ids=chunk_ids)
        count = len(existing["ids"])

        if count > 0:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {count} chunks")

        return count

    def delete_by_source(self, source_document: str) -> int:
        """Delete all chunks from a specific source document.

        Args:
            source_document: Path of the source document.

        Returns:
            Number of chunks deleted.

        Example:
            >>> store = VectorStore()
            >>> store.delete_by_source("/path/to/document.pdf")
        """
        # Find all chunks from this source
        results = self.collection.get(
            where={"source_document": source_document},
            include=[],  # Only need IDs
        )

        if not results["ids"]:
            logger.debug(f"No chunks found for source: {source_document}")
            return 0

        self.collection.delete(ids=results["ids"])
        logger.info(f"Deleted {len(results['ids'])} chunks from {source_document}")
        return len(results["ids"])

    def count(self) -> int:
        """Get total number of chunks in the collection.

        Returns:
            Number of chunks stored.
        """
        return self.collection.count()

    def list_sources(self) -> List[str]:
        """List all unique source documents in the collection.

        Returns:
            List of source document paths.
        """
        # Get all metadatas
        results = self.collection.get(include=["metadatas"])

        if not results["metadatas"]:
            return []

        sources = set()
        for metadata in results["metadatas"]:
            if "source_document" in metadata:
                sources.add(metadata["source_document"])

        return sorted(sources)

    def clear(self) -> int:
        """Delete all chunks from the collection.

        Returns:
            Number of chunks deleted.
        """
        count = self.collection.count()
        if count > 0:
            # Delete the collection and recreate it
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "AnkiAI chunk embeddings for RAG"},
            )
            logger.info(f"Cleared {count} chunks from collection")
        return count

    def _chunk_to_metadata(self, chunk: Chunk) -> dict:
        """Convert chunk fields to ChromaDB metadata dict.

        Args:
            chunk: Chunk object to convert.

        Returns:
            Dictionary of metadata fields.
        """
        return {
            "source_document": chunk.source_document,
            "page_numbers": ",".join(map(str, chunk.page_numbers)),
            "position": chunk.position,
            "token_count": chunk.token_count,
            "char_count": chunk.char_count,
            "has_overlap_before": chunk.has_overlap_before,
            "has_overlap_after": chunk.has_overlap_after,
            "overlap_with_previous": chunk.overlap_with_previous or "",
            "overlap_with_next": chunk.overlap_with_next or "",
        }

    def _metadata_to_chunk(
        self,
        chunk_id: str,
        text: str,
        metadata: dict,
        embedding: Optional[List[float]] = None,
    ) -> Chunk:
        """Reconstruct a Chunk from ChromaDB metadata.

        Args:
            chunk_id: The chunk ID.
            text: The chunk text.
            metadata: The metadata dictionary.
            embedding: Optional embedding vector.

        Returns:
            Reconstructed Chunk object.
        """
        # Parse page numbers from comma-separated string
        page_numbers_str = metadata.get("page_numbers", "")
        page_numbers = (
            [int(p) for p in page_numbers_str.split(",") if p]
            if page_numbers_str
            else []
        )

        return Chunk(
            chunk_id=chunk_id,
            text=text,
            source_document=metadata.get("source_document", ""),
            page_numbers=page_numbers,
            position=metadata.get("position", 0),
            token_count=metadata.get("token_count", 0),
            char_count=metadata.get("char_count", len(text)),
            has_overlap_before=metadata.get("has_overlap_before", False),
            has_overlap_after=metadata.get("has_overlap_after", False),
            overlap_with_previous=metadata.get("overlap_with_previous") or None,
            overlap_with_next=metadata.get("overlap_with_next") or None,
            embedding=embedding,
        )
