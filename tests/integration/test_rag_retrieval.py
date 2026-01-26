"""Integration tests for the complete RAG retrieval pipeline.

These tests use real API calls to OpenAI and verify the end-to-end flow:
PDF → Chunks → Embeddings → VectorStore → Retriever → ContextBuilder
"""

import os
from pathlib import Path

import pytest

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.rag.chunker import Chunker
from src.domain.rag.context_builder import ChunkOrdering, ContextBuilder
from src.domain.rag.embeddings import EmbeddingGenerator
from src.domain.rag.retriever import Retriever
from src.domain.rag.vector_store import VectorStore


@pytest.fixture
def sample_pdf_path():
    """Get path to sample PDF for testing."""
    paths = [
        Path("tests/fixtures/sample_technical.pdf"),
        Path("tests/sample_data/023_Transaction Processing or Analytics_.pdf"),
        Path("tests/sample_data/DDIA.pdf"),
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
        collection_name="rag_retrieval_test",
    )


@pytest.fixture
def retriever(vector_store, embedding_generator):
    """Create a Retriever instance for testing."""
    return Retriever(vector_store, embedding_generator)


@pytest.mark.integration
@pytest.mark.api
class TestCompleteRAGPipeline:
    """Integration tests for the complete RAG pipeline."""

    def test_complete_rag_pipeline(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test: PDF → Chunks → Embed → Index → Retrieve → Format Context.

        This is the main integration test that proves the complete RAG
        workflow works with real data.
        """
        # 1. Setup: Parse, chunk, embed, index
        print("\n=== Step 1: Parse Document ===")
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=5)
        print(f"Parsed {len(doc.content)} characters from {sample_pdf_path}")

        print("\n=== Step 2: Chunk Document ===")
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        print(f"Created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks[:3]):
            print(f"  Chunk {i}: {chunk.token_count} tokens")

        print("\n=== Step 3: Generate Embeddings ===")
        embedding_generator.generate_embeddings(chunks)
        stats = embedding_generator.get_usage_stats()
        print(
            f"Generated embeddings: {stats['total_tokens']} tokens, ${stats['estimated_cost']:.6f}"
        )

        print("\n=== Step 4: Index in Vector Store ===")
        vector_store.add_chunks(chunks)
        print(f"Indexed {vector_store.count()} chunks")

        # 2. Create retriever and retrieve
        print("\n=== Step 5: Retrieve Relevant Chunks ===")
        retriever = Retriever(vector_store, embedding_generator)
        query = "data processing and storage concepts"
        retrieved = retriever.retrieve(query, top_k=3)

        # Should return min(top_k, available_chunks)
        assert len(retrieved) == min(3, len(chunks))
        assert len(retrieved) > 0
        print(f"Query: '{query}'")
        print(f"Retrieved {len(retrieved)} chunks")

        # 3. Build context
        print("\n=== Step 6: Build Context ===")
        context = ContextBuilder.build_context(retrieved, include_metadata=True)

        assert context  # Not empty
        print(f"Context length: {len(context)} chars")

        # 4. Print for manual inspection
        print("\n=== Retrieved Chunks ===")
        for i, chunk in enumerate(retrieved):
            print(f"\nChunk {i+1}: {chunk.chunk_id}")
            print(f"  Tokens: {chunk.token_count}")
            print(f"  Preview: {chunk.text[:150]}...")

        print("\n=== Context (first 800 chars) ===")
        print(context[:800])
        if len(context) > 800:
            print("...")

        # 5. Cleanup
        vector_store.clear()

    def test_retriever_with_scores(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test retrieval with similarity scores."""
        # Setup
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=3)
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Retrieve with scores
        retriever = Retriever(vector_store, embedding_generator)
        query = "database systems"
        results = retriever.retrieve_with_scores(query, top_k=5)

        assert len(results) <= 5
        assert len(results) > 0

        # Verify scores are in descending order
        scores = [r.score for r in results]
        assert scores == sorted(
            scores, reverse=True
        ), "Results should be sorted by score"

        # Verify score range
        for result in results:
            assert 0 <= result.score <= 1, f"Score {result.score} out of range"

        print("\n=== Retrieval with Scores ===")
        print(f"Query: '{query}'")
        for i, result in enumerate(results):
            print(f"[{i+1}] Score: {result.score:.4f} - {result.chunk.text[:80]}...")

        vector_store.clear()

    def test_retriever_source_document_filter(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test filtering retrieval by source document."""
        # Create "two documents" from same PDF but different pages
        doc1 = PDFParser.parse(sample_pdf_path, start_page=1, end_page=2)
        doc2 = PDFParser.parse(sample_pdf_path, start_page=3, end_page=4)

        # Simulate different source paths
        doc1.file_path = "/documents/doc1.pdf"
        doc2.file_path = "/documents/doc2.pdf"

        chunks1 = Chunker.chunk(doc1, target_size=400, overlap_size=50)
        chunks2 = Chunker.chunk(doc2, target_size=400, overlap_size=50)

        all_chunks = chunks1 + chunks2
        embedding_generator.generate_embeddings(all_chunks)
        vector_store.add_chunks(all_chunks)

        # Retrieve only from doc1
        retriever = Retriever(vector_store, embedding_generator)
        results = retriever.retrieve(
            "test query", top_k=10, source_document="/documents/doc1.pdf"
        )

        # All results should be from doc1
        for chunk in results:
            assert chunk.source_document == "/documents/doc1.pdf"

        print("\n=== Source Document Filter Test ===")
        print(f"Total chunks in store: {vector_store.count()}")
        print(f"Results from doc1 only: {len(results)}")

        vector_store.clear()


@pytest.mark.integration
@pytest.mark.api
class TestContextBuilderIntegration:
    """Integration tests for ContextBuilder with real retrieved chunks."""

    def test_context_builder_with_retrieved_chunks(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test building context from actually retrieved chunks."""
        # Setup pipeline
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=5)
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Retrieve
        retriever = Retriever(vector_store, embedding_generator)
        retrieved = retriever.retrieve("key concepts", top_k=3)

        # Build context without metadata
        context_simple = ContextBuilder.build_context(retrieved)
        assert context_simple
        assert "---" in context_simple  # Default separator

        # Build context with metadata
        context_with_meta = ContextBuilder.build_context(
            retrieved, include_metadata=True
        )
        assert "[Source:" in context_with_meta
        assert "Pages:" in context_with_meta

        print("\n=== Context Building ===")
        print(f"Simple context: {len(context_simple)} chars")
        print(f"Context with metadata: {len(context_with_meta)} chars")

        vector_store.clear()

    def test_context_token_estimation_accuracy(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test that token estimation is accurate for real chunks."""
        # Setup
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=3)
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Retrieve
        retriever = Retriever(vector_store, embedding_generator)
        retrieved = retriever.retrieve("database", top_k=5)

        # Estimate tokens
        estimated = ContextBuilder.estimate_tokens(retrieved, include_metadata=True)

        # Build and get actual token count
        result = ContextBuilder.build_context_with_limit(
            retrieved, max_tokens=10000, include_metadata=True
        )

        # They should be close (estimate is from estimate_tokens, actual from build)
        # Allow small variance due to different calculation paths
        print("\n=== Token Estimation ===")
        print(f"Estimated: {estimated}")
        print(f"Actual: {result.token_count}")

        # Difference should be minimal
        assert abs(estimated - result.token_count) < 10

        vector_store.clear()

    def test_context_with_token_limit(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test building context with a strict token limit."""
        # Setup with more chunks
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=10)
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Retrieve many chunks
        retriever = Retriever(vector_store, embedding_generator)
        retrieved = retriever.retrieve("concepts and methods", top_k=10)

        # Build with strict token limit
        max_tokens = 500
        result = ContextBuilder.build_context_with_limit(
            retrieved, max_tokens=max_tokens, include_metadata=True
        )

        assert result.token_count <= max_tokens
        assert result.chunk_count <= len(retrieved)

        print("\n=== Token Limited Context ===")
        print(f"Max tokens: {max_tokens}")
        print(f"Actual tokens: {result.token_count}")
        print(f"Chunks included: {result.chunk_count}/{len(retrieved)}")
        print(f"Truncated: {result.truncated}")

        vector_store.clear()

    def test_context_ordering_options(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test different chunk ordering options."""
        # Setup
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=5)
        chunks = Chunker.chunk(doc, target_size=400, overlap_size=50)
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        # Retrieve
        retriever = Retriever(vector_store, embedding_generator)
        retrieved = retriever.retrieve("test query", top_k=5)

        # Build with relevance ordering (default)
        context_relevance = ContextBuilder.build_context(
            retrieved, ordering=ChunkOrdering.RELEVANCE
        )

        # Build with position ordering
        context_position = ContextBuilder.build_context(
            retrieved, ordering=ChunkOrdering.POSITION
        )

        # Contexts should potentially be different if chunks from different positions
        print("\n=== Ordering Comparison ===")
        print(f"Relevance order (first 200 chars): {context_relevance[:200]}")
        print(f"Position order (first 200 chars): {context_position[:200]}")

        # Both should have all the text, just ordered differently
        for chunk in retrieved:
            # Check text content exists (may be split by metadata)
            assert chunk.text[:50] in context_relevance
            assert chunk.text[:50] in context_position

        vector_store.clear()


@pytest.mark.integration
@pytest.mark.api
class TestRAGEdgeCases:
    """Integration tests for edge cases in the RAG pipeline."""

    def test_empty_results_handling(self, embedding_generator, tmp_path):
        """Test handling when no results are found."""
        # Create empty vector store
        empty_store = VectorStore(
            persist_directory=str(tmp_path / "empty_store"),
            collection_name="empty_test",
        )

        retriever = Retriever(empty_store, embedding_generator)

        # Should return empty list, not error
        results = retriever.retrieve("any query", top_k=5)
        assert results == []

        # Context builder should handle empty list
        context = ContextBuilder.build_context(results)
        assert context == ""

    def test_single_chunk_retrieval(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test retrieval when only one chunk exists."""
        # Create document with minimal content
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=1)
        chunks = Chunker.chunk(
            doc, target_size=2000, overlap_size=100
        )  # Large size = fewer chunks

        if len(chunks) > 1:
            chunks = chunks[:1]  # Limit to one chunk

        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        retriever = Retriever(vector_store, embedding_generator)
        results = retriever.retrieve("test", top_k=5)

        assert len(results) == 1  # Should return only what's available

        context = ContextBuilder.build_context(results)
        assert context  # Should have content
        assert "---" not in context  # No separator for single chunk

        vector_store.clear()

    def test_retrieval_respects_top_k(
        self, sample_pdf_path, embedding_generator, vector_store
    ):
        """Test that top_k parameter is respected."""
        doc = PDFParser.parse(sample_pdf_path, start_page=1, end_page=5)
        chunks = Chunker.chunk(
            doc, target_size=100, overlap_size=15
        )  # Small target size for more chunks
        embedding_generator.generate_embeddings(chunks)
        vector_store.add_chunks(chunks)

        total_chunks = vector_store.count()
        assert total_chunks >= 2  # Need at least 2 chunks for meaningful test

        retriever = Retriever(vector_store, embedding_generator)

        # Test various top_k values - each should return min(k, total_chunks)
        for k in [1, 2, total_chunks]:
            results = retriever.retrieve("test query", top_k=k)
            expected = min(k, total_chunks)
            assert (
                len(results) == expected
            ), f"Expected {expected} results, got {len(results)}"

        # Test requesting more than available
        results = retriever.retrieve("test query", top_k=total_chunks + 5)
        assert (
            len(results) == total_chunks
        ), "Should return all available when top_k > total"

        print("\n=== Top-K Test ===")
        print(f"Total chunks: {total_chunks}")
        print(f"Tested top_k values up to {total_chunks}, all returned correct counts")

        vector_store.clear()
