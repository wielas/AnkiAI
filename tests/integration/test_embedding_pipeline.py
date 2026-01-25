"""Integration tests for the embedding pipeline.

These tests use real API calls to OpenAI and should be marked accordingly.
They verify the end-to-end flow: PDF → Chunks → Embeddings → VectorStore → Search
"""

import os
from pathlib import Path

import pytest

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.rag.chunker import Chunker
from src.domain.rag.embeddings import EmbeddingGenerator
from src.domain.rag.vector_store import VectorStore


@pytest.fixture
def sample_pdf_path():
    """Get path to sample PDF for testing."""
    paths = [
        Path("tests/fixtures/sample_technical.pdf"),
        Path("tests/sample_data/023_Transaction Processing or Analytics_.pdf"),
    ]

    for path in paths:
        if path.exists():
            return str(path)

    pytest.skip("No sample PDF found for testing")


@pytest.fixture
def embedding_generator():
    """Create embedding generator, skipping if no API key."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set - skipping API test")
    return EmbeddingGenerator()


@pytest.fixture
def vector_store(tmp_path):
    """Create a temporary vector store for testing."""
    return VectorStore(
        persist_directory=str(tmp_path / "test_chroma"),
        collection_name="integration_test",
    )


@pytest.mark.integration
@pytest.mark.api
class TestEmbeddingPipeline:
    """Integration tests for the complete embedding pipeline."""

    def test_pdf_to_chunks_to_embeddings(self, sample_pdf_path, embedding_generator):
        """Test pipeline: PDF → Chunks → Embeddings."""
        # Step 1: Parse PDF
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=2)
        assert document.content
        print("\n=== Parsed Document ===")
        print(f"Content length: {len(document.content)} chars")

        # Step 2: Chunk document
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)
        assert len(chunks) > 0
        print("\n=== Chunking Complete ===")
        print(f"Number of chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i}: {chunk.token_count} tokens, {chunk.char_count} chars")

        # Step 3: Generate embeddings
        embedding_generator.generate_embeddings(chunks)

        # Verify all chunks have embeddings
        for chunk in chunks:
            assert chunk.has_embedding(), f"Chunk {chunk.chunk_id} missing embedding"
            assert len(chunk.embedding) == 1536, "Wrong embedding dimensions"

        # Print usage stats
        stats = embedding_generator.get_usage_stats()
        print("\n=== Embedding Stats ===")
        print(f"API calls: {stats['api_calls']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Estimated cost: ${stats['estimated_cost']:.6f}")

    def test_embeddings_to_vector_store(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test pipeline: PDF → Chunks → Embeddings → VectorStore."""
        # Parse and chunk
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=2)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        # Generate embeddings
        embedding_generator.generate_embeddings(chunks)

        # Add to vector store
        count = vector_store.add_chunks(chunks)
        assert count == len(chunks)
        assert vector_store.count() == len(chunks)

        print("\n=== Vector Store ===")
        print(f"Chunks added: {count}")
        print(f"Total in store: {vector_store.count()}")

    def test_complete_pipeline_with_search(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test complete pipeline: PDF → Chunks → Embeddings → VectorStore → Search."""
        # Parse and chunk
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=3)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        print("\n=== Document Processing ===")
        print(f"Parsed {len(document.content)} chars")
        print(f"Created {len(chunks)} chunks")

        # Generate embeddings
        embedding_generator.generate_embeddings(chunks)

        # Add to vector store
        vector_store.add_chunks(chunks)

        # Generate query embedding and search
        query = "What are the key concepts discussed in this document?"
        query_embedding = embedding_generator.generate_query_embedding(query)

        assert len(query_embedding) == 1536

        # Search for similar chunks
        results = vector_store.search(query_embedding, top_k=3)

        assert len(results) > 0
        assert len(results) <= 3

        # Verify results structure
        for chunk, score in results:
            assert chunk.chunk_id
            assert chunk.text
            assert 0 <= score <= 1

        # Print results
        print("\n=== Search Results ===")
        print(f"Query: '{query}'")
        print(f"Results: {len(results)}")
        for i, (chunk, score) in enumerate(results):
            print(f"\n[Result {i+1}] Score: {score:.4f}")
            print(f"  Chunk ID: {chunk.chunk_id}")
            print(f"  Text preview: {chunk.text[:150]}...")

        # Verify relevance ordering
        scores = [score for _, score in results]
        assert scores == sorted(
            scores, reverse=True
        ), "Results should be sorted by score"

    def test_search_returns_relevant_chunks(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test that search returns semantically relevant chunks."""
        # Parse multiple pages for diverse content
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=5)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        # Generate embeddings and add to store
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Search for specific topic (adjust based on sample PDF content)
        # The sample_technical.pdf contains ML content
        specific_query = "machine learning algorithms"
        query_embedding = embedding_generator.generate_query_embedding(specific_query)

        results = vector_store.search(query_embedding, top_k=2)

        print("\n=== Relevance Test ===")
        print(f"Query: '{specific_query}'")
        for i, (chunk, score) in enumerate(results):
            print(f"\n[Result {i+1}] Score: {score:.4f}")
            print(f"  Text: {chunk.text[:200]}...")

        # Top result should have reasonable similarity
        if results:
            assert results[0][1] > 0.3, "Top result should have > 0.3 similarity"

    def test_embedding_dimensions_correct(self, sample_pdf_path, embedding_generator):
        """Verify embeddings have correct dimensions."""
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        embedding_generator.generate_embeddings(chunks)

        for chunk in chunks:
            assert (
                len(chunk.embedding) == 1536
            ), f"Expected 1536 dimensions, got {len(chunk.embedding)}"

    def test_query_embedding_matches_chunk_embedding_dimensions(
        self, sample_pdf_path, embedding_generator
    ):
        """Verify query embeddings match chunk embedding dimensions."""
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        embedding_generator.generate_embeddings(chunks)
        query_embedding = embedding_generator.generate_query_embedding("test query")

        assert len(query_embedding) == len(chunks[0].embedding)
        assert len(query_embedding) == 1536

    def test_vector_store_persistence(
        self, sample_pdf_path, embedding_generator, tmp_path
    ):
        """Test that vector store data persists across instances."""
        persist_dir = str(tmp_path / "persist_test")

        # First instance: add chunks
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)

        store1 = VectorStore(persist_directory=persist_dir)
        store1.add_chunks(chunks)
        initial_count = store1.count()
        del store1

        # Second instance: verify data persists
        store2 = VectorStore(persist_directory=persist_dir)
        assert store2.count() == initial_count

        # Verify search still works
        query_embedding = embedding_generator.generate_query_embedding("test")
        results = store2.search(query_embedding, top_k=1)
        assert len(results) == 1

        print("\n=== Persistence Test ===")
        print(f"Chunks persisted: {initial_count}")
        print("Search works after reopen: Yes")


@pytest.mark.integration
@pytest.mark.api
class TestEmbeddingCostTracking:
    """Integration tests for cost tracking."""

    def test_cost_tracking_accuracy(self, sample_pdf_path, embedding_generator):
        """Test that cost tracking is accurate."""
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        embedding_generator.generate_embeddings(chunks)

        stats = embedding_generator.get_usage_stats()

        # Verify stats are populated
        assert stats["api_calls"] >= 1
        assert stats["total_tokens"] > 0
        assert stats["estimated_cost"] > 0

        # Cost should be very low for embedding small chunks
        # At $0.02 per 1M tokens, even 10k tokens = $0.0002
        assert stats["estimated_cost"] < 0.01

        print("\n=== Cost Tracking ===")
        print(f"API calls: {stats['api_calls']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"Cost: ${stats['estimated_cost']:.6f}")
        print(f"Model: {stats['model']}")

    def test_token_tracking_accumulates(self, sample_pdf_path, embedding_generator):
        """Test that token tracking accumulates across calls."""
        document = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(document, target_size=400, overlap_size=50)

        # Split chunks into batches
        half = len(chunks) // 2
        batch1 = chunks[:half] if half > 0 else chunks
        batch2 = chunks[half:] if half > 0 else []

        # First batch
        embedding_generator.generate_embeddings(batch1)
        stats1 = embedding_generator.get_usage_stats()

        # Second batch (if exists)
        if batch2:
            embedding_generator.generate_embeddings(batch2)
            stats2 = embedding_generator.get_usage_stats()

            assert stats2["total_tokens"] > stats1["total_tokens"]
            assert stats2["api_calls"] > stats1["api_calls"]

        print("\n=== Accumulation Test ===")
        print(f"After batch 1: {stats1['total_tokens']} tokens")
        if batch2:
            print(f"After batch 2: {stats2['total_tokens']} tokens")


@pytest.mark.integration
@pytest.mark.api
class TestMultipleDocuments:
    """Integration tests for handling multiple documents."""

    def test_multiple_documents_in_store(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test storing chunks from multiple documents."""
        # Parse same PDF with different page ranges as "different documents"
        doc1 = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        doc2 = PDFParser.parse(sample_pdf_path, start_page=2, end_page=2)

        # Modify paths to simulate different documents
        doc1.file_path = "/doc1.pdf"
        doc2.file_path = "/doc2.pdf"

        chunks1 = Chunker.chunk(doc1, target_size=400, overlap_size=50)
        chunks2 = Chunker.chunk(doc2, target_size=400, overlap_size=50)

        # Generate embeddings
        all_chunks = chunks1 + chunks2
        embedding_generator.generate_embeddings(all_chunks)

        # Add to store
        vector_store.add_chunks(all_chunks)

        # Verify sources
        sources = vector_store.list_sources()
        assert len(sources) == 2
        assert "/doc1.pdf" in sources
        assert "/doc2.pdf" in sources

        print("\n=== Multiple Documents ===")
        print(f"Total chunks: {vector_store.count()}")
        print(f"Sources: {sources}")

    def test_filter_search_by_source(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test searching within a specific source document."""
        doc1 = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        doc2 = PDFParser.parse(sample_pdf_path, start_page=2, end_page=2)

        doc1.file_path = "/doc1.pdf"
        doc2.file_path = "/doc2.pdf"

        chunks1 = Chunker.chunk(doc1, target_size=400, overlap_size=50)
        chunks2 = Chunker.chunk(doc2, target_size=400, overlap_size=50)

        all_chunks = chunks1 + chunks2
        embedding_generator.generate_embeddings(all_chunks)
        vector_store.add_chunks(all_chunks)

        # Search only in doc1
        query_embedding = embedding_generator.generate_query_embedding("test query")
        results = vector_store.search(
            query_embedding, top_k=10, source_document="/doc1.pdf"
        )

        # All results should be from doc1
        for chunk, _ in results:
            assert chunk.source_document == "/doc1.pdf"

        print("\n=== Filtered Search ===")
        print(f"Results from /doc1.pdf only: {len(results)}")

    def test_delete_by_source(self, sample_pdf_path, embedding_generator, vector_store):
        """Test deleting all chunks from a specific source."""
        doc1 = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        doc2 = PDFParser.parse(sample_pdf_path, start_page=2, end_page=2)

        doc1.file_path = "/doc1.pdf"
        doc2.file_path = "/doc2.pdf"

        chunks1 = Chunker.chunk(doc1, target_size=400, overlap_size=50)
        chunks2 = Chunker.chunk(doc2, target_size=400, overlap_size=50)

        all_chunks = chunks1 + chunks2
        embedding_generator.generate_embeddings(all_chunks)
        vector_store.add_chunks(all_chunks)

        initial_count = vector_store.count()

        # Delete doc1 chunks
        deleted = vector_store.delete_by_source("/doc1.pdf")
        assert deleted == len(chunks1)
        assert vector_store.count() == initial_count - len(chunks1)

        # Only doc2 should remain
        sources = vector_store.list_sources()
        assert sources == ["/doc2.pdf"]

        print("\n=== Delete By Source ===")
        print(f"Deleted: {deleted}")
        print(f"Remaining: {vector_store.count()}")
