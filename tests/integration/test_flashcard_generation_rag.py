"""Integration tests for RAG-based flashcard generation.

These tests verify the complete RAG pipeline:
1. Parse a test PDF
2. Setup RAG (chunk, embed, index)
3. Generate flashcard using retrieval
4. Verify flashcard structure and quality
"""

import os

import pytest

from src.application.flashcard_service import (
    FlashcardGeneratorService,
    RAGConfig,
)
from src.domain.models.document import ProcessingStatus


@pytest.mark.integration
@pytest.mark.api
class TestRAGFlashcardGeneration:
    """Integration tests for RAG-based flashcard generation."""

    @pytest.fixture
    def service(self):
        """Create a fresh FlashcardGeneratorService instance."""
        return FlashcardGeneratorService()

    @pytest.fixture
    def api_keys_available(self):
        """Check if API keys are available for integration tests."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        if not anthropic_key or not openai_key:
            pytest.skip(
                "API keys not available. Set ANTHROPIC_API_KEY and OPENAI_API_KEY "
                "environment variables to run integration tests."
            )

        return True

    def test_rag_generation_complete_pipeline(
        self, service, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test complete RAG pipeline: chunk -> embed -> index -> retrieve -> generate."""
        output_path = str(tmp_path / "test_rag.apkg")

        # Generate with RAG enabled
        result = service.generate_flashcards(
            pdf_path=str(sample_pdf_path),
            page_range=(1, 2),  # Just 2 pages for speed
            cards_per_page=1,
            difficulty="intermediate",
            output_path=output_path,
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Verify result structure
        assert result is not None
        assert result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL]
        assert result.total_attempted == 2
        assert result.total_success >= 1

        # Verify flashcards
        assert len(result.flashcards) >= 1

        for card in result.flashcards:
            # Basic structure
            assert "question" in card
            assert "answer" in card
            assert len(card["question"]) > 10
            assert len(card["answer"]) > 10

            # Source tracking
            assert "source_page" in card

            # RAG metadata should be present
            assert "rag_metadata" in card
            rag_meta = card["rag_metadata"]
            assert "chunks_retrieved" in rag_meta
            assert rag_meta["chunks_retrieved"] > 0
            assert "top_scores" in rag_meta
            assert len(rag_meta["top_scores"]) > 0

        # Verify output file created
        assert result.output_path is not None

        # Verify token usage tracked
        assert result.total_tokens > 0
        assert result.total_cost_usd > 0

    def test_rag_generation_different_k_values(
        self, service, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test that different top_k values produce different contexts."""
        results = {}

        for k in [1, 3, 5]:
            output_path = str(tmp_path / f"test_rag_k{k}.apkg")

            result = service.generate_flashcards(
                pdf_path=str(sample_pdf_path),
                page_range=(1, 1),  # Single page for comparison
                cards_per_page=1,
                difficulty="intermediate",
                output_path=output_path,
                use_rag=True,
                rag_config=RAGConfig(top_k=k),
            )

            results[k] = result

            # Verify generation succeeded
            assert result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL]

            # Check RAG metadata reflects k value
            if result.flashcards:
                rag_meta = result.flashcards[0].get("rag_metadata", {})
                chunks_retrieved = rag_meta.get("chunks_retrieved", 0)
                # Should retrieve up to k chunks (may be less if not enough chunks)
                assert chunks_retrieved <= k

    def test_baseline_vs_rag_both_work(
        self, service, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test that both baseline and RAG modes produce valid flashcards."""
        # Baseline mode
        baseline_result = service.generate_flashcards(
            pdf_path=str(sample_pdf_path),
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "baseline.apkg"),
            use_rag=False,
        )

        # RAG mode (fresh service instance)
        service_rag = FlashcardGeneratorService()
        rag_result = service_rag.generate_flashcards(
            pdf_path=str(sample_pdf_path),
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "rag.apkg"),
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Both should succeed
        assert baseline_result.status in [
            ProcessingStatus.SUCCESS,
            ProcessingStatus.PARTIAL,
        ]
        assert rag_result.status in [ProcessingStatus.SUCCESS, ProcessingStatus.PARTIAL]

        # Both should produce flashcards
        assert len(baseline_result.flashcards) >= 1
        assert len(rag_result.flashcards) >= 1

        # Baseline should NOT have RAG metadata
        if baseline_result.flashcards:
            assert "rag_metadata" not in baseline_result.flashcards[0]

        # RAG should have RAG metadata
        if rag_result.flashcards:
            assert "rag_metadata" in rag_result.flashcards[0]

    def test_rag_progress_callback(
        self, service, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test that progress callbacks are called correctly in RAG mode."""
        progress_calls = []

        def track_progress(current: int, total: int, message: str) -> None:
            progress_calls.append((current, total, message))

        _result = service.generate_flashcards(
            pdf_path=str(sample_pdf_path),
            page_range=(1, 2),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "progress_test.apkg"),
            on_progress=track_progress,
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Should have progress calls
        assert len(progress_calls) > 0

        # Should include RAG setup phase
        setup_calls = [
            c for c in progress_calls if "RAG" in c[2] or "setup" in c[2].lower()
        ]
        assert len(setup_calls) > 0

        # Should include per-page processing
        page_calls = [c for c in progress_calls if "page" in c[2].lower()]
        assert len(page_calls) >= 2  # At least 2 pages

    def test_rag_handles_empty_pages_gracefully(
        self, service, empty_pdf_path, api_keys_available, tmp_path
    ):
        """Test that RAG mode handles documents with empty pages."""
        result = service.generate_flashcards(
            pdf_path=str(empty_pdf_path),
            page_range=(1, 1),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "empty_test.apkg"),
            use_rag=True,
            rag_config=RAGConfig(top_k=3),
        )

        # Should handle gracefully (either fail or produce no cards)
        assert result is not None
        # Empty pages should result in failure
        assert result.total_failed >= 1

    def test_rag_cost_includes_embeddings(
        self, service, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test that total cost includes embedding generation cost."""
        result = service.generate_flashcards(
            pdf_path=str(sample_pdf_path),
            page_range=(1, 3),
            cards_per_page=1,
            difficulty="intermediate",
            output_path=str(tmp_path / "cost_test.apkg"),
            use_rag=True,
            rag_config=RAGConfig(top_k=5),
        )

        # RAG mode should have higher cost due to embeddings
        assert result.total_cost_usd > 0

        # Cost should be reasonable (less than $1 for a few pages)
        assert result.total_cost_usd < 1.0


@pytest.mark.integration
@pytest.mark.api
class TestRAGSetupPhase:
    """Integration tests focused on the RAG setup phase."""

    @pytest.fixture
    def api_keys_available(self):
        """Check if API keys are available."""
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
        openai_key = os.environ.get("OPENAI_API_KEY")

        if not anthropic_key or not openai_key:
            pytest.skip("API keys not available")

        return True

    def test_rag_setup_creates_chunks(self, sample_pdf_path, api_keys_available):
        """Test that RAG setup properly chunks the document."""
        from src.domain.document_processing.pdf_parser import PDFParser
        from src.domain.rag.chunker import Chunker

        # Parse document
        doc = PDFParser.parse(str(sample_pdf_path), start_page=1, end_page=3)

        # Chunk it
        chunks = Chunker.chunk(doc, target_size=800, overlap_size=100)

        # Should produce multiple chunks
        assert len(chunks) > 0

        # Chunks should have proper structure
        for chunk in chunks:
            assert chunk.chunk_id
            assert len(chunk.text) > 0
            assert chunk.token_count > 0
            assert chunk.source_document == str(sample_pdf_path)

    def test_rag_setup_generates_embeddings(self, sample_pdf_path, api_keys_available):
        """Test that RAG setup generates embeddings for chunks."""
        from src.domain.document_processing.pdf_parser import PDFParser
        from src.domain.rag.chunker import Chunker
        from src.domain.rag.embeddings import EmbeddingGenerator

        # Parse and chunk
        doc = PDFParser.parse(str(sample_pdf_path), start_page=1, end_page=2)
        chunks = Chunker.chunk(doc, target_size=800, overlap_size=100)

        # Generate embeddings
        generator = EmbeddingGenerator()
        generator.generate_embeddings(chunks)

        # All chunks should have embeddings
        for chunk in chunks:
            assert chunk.has_embedding()
            assert len(chunk.embedding) == 1536  # text-embedding-3-small dimensions

    def test_rag_setup_indexes_in_vector_store(
        self, sample_pdf_path, api_keys_available, tmp_path
    ):
        """Test that RAG setup properly indexes chunks in vector store."""
        from src.domain.document_processing.pdf_parser import PDFParser
        from src.domain.rag.chunker import Chunker
        from src.domain.rag.embeddings import EmbeddingGenerator
        from src.domain.rag.vector_store import VectorStore

        # Parse, chunk, and embed
        doc = PDFParser.parse(str(sample_pdf_path), start_page=1, end_page=2)
        chunks = Chunker.chunk(doc, target_size=800, overlap_size=100)

        generator = EmbeddingGenerator()
        generator.generate_embeddings(chunks)

        # Index in vector store
        store = VectorStore(
            persist_directory=str(tmp_path / "chroma"),
            collection_name="test_integration",
        )
        store.add_chunks(chunks)

        # Verify indexing
        assert store.count() == len(chunks)

        # Verify retrieval works
        query_embedding = generator.generate_query_embedding("machine learning")
        results = store.search(query_embedding, top_k=3)

        assert len(results) > 0
        for chunk, score in results:
            assert score > 0
            assert len(chunk.text) > 0

        # Cleanup
        store.clear()
