"""Unit tests for VectorStore."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.domain.models.chunk import Chunk
from src.domain.rag.vector_store import VectorStore


def create_test_chunk(
    chunk_id: str = "test_chunk_001",
    text: str = "This is test text for embedding.",
    position: int = 0,
    source_document: str = "/path/to/test.pdf",
    embedding: list = None,
) -> Chunk:
    """Create a test chunk with default values."""
    if embedding is None:
        embedding = [0.1] * 1536  # Default embedding

    return Chunk(
        chunk_id=chunk_id,
        text=text,
        source_document=source_document,
        page_numbers=[1, 2],
        position=position,
        token_count=10,
        char_count=len(text),
        has_overlap_before=position > 0,
        has_overlap_after=True,
        overlap_with_previous=f"chunk_{position - 1:03d}" if position > 0 else None,
        overlap_with_next=f"chunk_{position + 1:03d}",
        embedding=embedding,
    )


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch("src.domain.rag.vector_store.get_settings") as mock:
        settings = Mock()
        settings.chroma_db_path = "./test_chroma_db"
        mock.return_value = settings
        yield mock


@pytest.mark.unit
class TestVectorStoreInit:
    """Test cases for VectorStore initialization."""

    def test_initialization_with_custom_path(self, tmp_path: Path, mock_settings):
        """Test initialization with custom persist directory."""
        persist_dir = str(tmp_path / "custom_chroma")
        store = VectorStore(persist_directory=persist_dir)

        assert store.persist_directory == persist_dir
        assert store.collection_name == VectorStore.DEFAULT_COLLECTION_NAME
        assert Path(persist_dir).exists()

    def test_initialization_with_custom_collection(self, tmp_path: Path, mock_settings):
        """Test initialization with custom collection name."""
        store = VectorStore(
            persist_directory=str(tmp_path / "chroma"),
            collection_name="custom_collection",
        )

        assert store.collection_name == "custom_collection"

    def test_initialization_creates_directory(self, tmp_path: Path, mock_settings):
        """Test that initialization creates persist directory if needed."""
        persist_dir = tmp_path / "new_chroma" / "nested"
        _store = VectorStore(persist_directory=str(persist_dir))

        assert persist_dir.exists()

    def test_initialization_reuses_collection(self, tmp_path: Path, mock_settings):
        """Test that reinitializing reuses existing collection."""
        persist_dir = str(tmp_path / "chroma")

        # First initialization
        store1 = VectorStore(persist_directory=persist_dir)
        chunk = create_test_chunk()
        store1.add_chunks([chunk])

        # Second initialization should see existing data
        store2 = VectorStore(persist_directory=persist_dir)
        assert store2.count() == 1


@pytest.mark.unit
class TestAddChunks:
    """Test cases for add_chunks method."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance for testing."""
        return VectorStore(persist_directory=str(tmp_path / "chroma"))

    def test_add_chunks_success(self, store):
        """Test successful chunk addition."""
        chunks = [
            create_test_chunk("chunk_001", "First chunk text"),
            create_test_chunk("chunk_002", "Second chunk text"),
        ]

        count = store.add_chunks(chunks)

        assert count == 2
        assert store.count() == 2

    def test_add_chunks_empty_list(self, store):
        """Test adding empty chunk list."""
        count = store.add_chunks([])
        assert count == 0
        assert store.count() == 0

    def test_add_chunks_without_embedding_raises_error(self, store):
        """Test that adding chunk without embedding raises ValueError."""
        chunk = create_test_chunk()
        chunk.embedding = None

        with pytest.raises(ValueError, match="missing embedding"):
            store.add_chunks([chunk])

    def test_add_chunks_upserts_duplicates(self, store):
        """Test that adding chunks with same ID upserts."""
        chunk1 = create_test_chunk("chunk_001", "Original text")
        chunk2 = create_test_chunk("chunk_001", "Updated text")

        store.add_chunks([chunk1])
        assert store.count() == 1

        store.add_chunks([chunk2])
        assert store.count() == 1  # Still 1, upserted

        # Verify the text was updated
        result = store.get_chunk("chunk_001")
        assert result.text == "Updated text"


@pytest.mark.unit
class TestSearch:
    """Test cases for search method."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance with test data."""
        store = VectorStore(persist_directory=str(tmp_path / "chroma"))

        # Add test chunks with different embeddings
        chunks = [
            create_test_chunk(
                "chunk_001", "Machine learning basics", embedding=[1.0] + [0.0] * 1535
            ),
            create_test_chunk(
                "chunk_002",
                "Deep learning neural networks",
                embedding=[0.9] + [0.1] + [0.0] * 1534,
            ),
            create_test_chunk(
                "chunk_003",
                "Python programming tutorial",
                embedding=[0.0] * 1535 + [1.0],
            ),
        ]
        store.add_chunks(chunks)
        return store

    def test_search_returns_ranked_results(self, store):
        """Test that search returns results ranked by similarity."""
        # Query similar to chunk_001 and chunk_002 (ML related)
        query_embedding = [1.0] + [0.0] * 1535

        results = store.search(query_embedding, top_k=3)

        assert len(results) == 3
        # First result should be most similar
        assert results[0][0].chunk_id == "chunk_001"
        # Similarity scores should be in descending order
        assert results[0][1] >= results[1][1] >= results[2][1]

    def test_search_top_k(self, store):
        """Test that top_k limits results."""
        query_embedding = [0.5] * 1536

        results = store.search(query_embedding, top_k=2)

        assert len(results) == 2

    def test_search_returns_chunk_and_score_tuples(self, store):
        """Test that search returns (Chunk, score) tuples."""
        query_embedding = [0.5] * 1536

        results = store.search(query_embedding, top_k=1)

        assert len(results) == 1
        chunk, score = results[0]
        assert isinstance(chunk, Chunk)
        assert isinstance(score, float)
        assert 0 <= score <= 1  # Similarity should be in [0, 1]

    def test_search_empty_collection(self, tmp_path: Path, mock_settings):
        """Test search on empty collection."""
        store = VectorStore(persist_directory=str(tmp_path / "empty_chroma"))
        query_embedding = [0.5] * 1536

        results = store.search(query_embedding, top_k=5)

        assert results == []

    def test_search_reconstructs_chunk(self, store):
        """Test that search reconstructs Chunk with all fields."""
        query_embedding = [1.0] + [0.0] * 1535

        results = store.search(query_embedding, top_k=1)
        chunk = results[0][0]

        assert chunk.chunk_id == "chunk_001"
        assert chunk.text == "Machine learning basics"
        assert chunk.source_document == "/path/to/test.pdf"
        assert chunk.page_numbers == [1, 2]
        assert chunk.position == 0

    def test_search_with_source_filter(self, tmp_path: Path, mock_settings):
        """Test search filtered by source document."""
        store = VectorStore(persist_directory=str(tmp_path / "chroma"))

        # Add chunks from different sources
        chunk1 = create_test_chunk("doc1_chunk", source_document="/doc1.pdf")
        chunk2 = create_test_chunk("doc2_chunk", source_document="/doc2.pdf")
        store.add_chunks([chunk1, chunk2])

        query_embedding = [0.1] * 1536

        # Search only in doc1
        results = store.search(query_embedding, top_k=10, source_document="/doc1.pdf")

        assert len(results) == 1
        assert results[0][0].source_document == "/doc1.pdf"


@pytest.mark.unit
class TestGetChunk:
    """Test cases for get_chunk method."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance for testing."""
        store = VectorStore(persist_directory=str(tmp_path / "chroma"))
        chunk = create_test_chunk("chunk_001", "Test content")
        store.add_chunks([chunk])
        return store

    def test_get_chunk_success(self, store):
        """Test successful chunk retrieval."""
        chunk = store.get_chunk("chunk_001")

        assert chunk is not None
        assert chunk.chunk_id == "chunk_001"
        assert chunk.text == "Test content"

    def test_get_chunk_not_found(self, store):
        """Test retrieval of non-existent chunk."""
        chunk = store.get_chunk("nonexistent_chunk")
        assert chunk is None

    def test_get_chunk_reconstructs_all_fields(self, store):
        """Test that get_chunk reconstructs all Chunk fields."""
        chunk = store.get_chunk("chunk_001")

        assert chunk.chunk_id == "chunk_001"
        assert chunk.text == "Test content"
        assert chunk.source_document == "/path/to/test.pdf"
        assert chunk.page_numbers == [1, 2]
        assert chunk.position == 0
        assert chunk.token_count == 10
        assert chunk.has_overlap_before is False
        assert chunk.has_overlap_after is True


@pytest.mark.unit
class TestDeleteChunks:
    """Test cases for delete_chunks method."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance with test data."""
        store = VectorStore(persist_directory=str(tmp_path / "chroma"))
        chunks = [
            create_test_chunk("chunk_001"),
            create_test_chunk("chunk_002"),
            create_test_chunk("chunk_003"),
        ]
        store.add_chunks(chunks)
        return store

    def test_delete_chunks_success(self, store):
        """Test successful chunk deletion."""
        count = store.delete_chunks(["chunk_001", "chunk_002"])

        assert count == 2
        assert store.count() == 1
        assert store.get_chunk("chunk_003") is not None

    def test_delete_chunks_empty_list(self, store):
        """Test deleting empty list."""
        count = store.delete_chunks([])
        assert count == 0
        assert store.count() == 3

    def test_delete_chunks_nonexistent(self, store):
        """Test deleting non-existent chunks."""
        count = store.delete_chunks(["nonexistent"])
        assert count == 0
        assert store.count() == 3


@pytest.mark.unit
class TestDeleteBySource:
    """Test cases for delete_by_source method."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance with chunks from different sources."""
        store = VectorStore(persist_directory=str(tmp_path / "chroma"))
        chunks = [
            create_test_chunk("doc1_001", source_document="/doc1.pdf"),
            create_test_chunk("doc1_002", source_document="/doc1.pdf"),
            create_test_chunk("doc2_001", source_document="/doc2.pdf"),
        ]
        store.add_chunks(chunks)
        return store

    def test_delete_by_source_success(self, store):
        """Test successful deletion by source."""
        count = store.delete_by_source("/doc1.pdf")

        assert count == 2
        assert store.count() == 1
        assert store.get_chunk("doc2_001") is not None

    def test_delete_by_source_nonexistent(self, store):
        """Test deleting from non-existent source."""
        count = store.delete_by_source("/nonexistent.pdf")
        assert count == 0
        assert store.count() == 3


@pytest.mark.unit
class TestCollectionManagement:
    """Test cases for collection management methods."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance for testing."""
        return VectorStore(persist_directory=str(tmp_path / "chroma"))

    def test_count_empty(self, store):
        """Test count on empty collection."""
        assert store.count() == 0

    def test_count_with_chunks(self, store):
        """Test count after adding chunks."""
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(5)]
        store.add_chunks(chunks)
        assert store.count() == 5

    def test_list_sources_empty(self, store):
        """Test list_sources on empty collection."""
        sources = store.list_sources()
        assert sources == []

    def test_list_sources_with_data(self, store):
        """Test list_sources with chunks from multiple documents."""
        chunks = [
            create_test_chunk("chunk_1", source_document="/doc1.pdf"),
            create_test_chunk("chunk_2", source_document="/doc2.pdf"),
            create_test_chunk("chunk_3", source_document="/doc1.pdf"),  # Duplicate
        ]
        store.add_chunks(chunks)

        sources = store.list_sources()

        assert len(sources) == 2
        assert "/doc1.pdf" in sources
        assert "/doc2.pdf" in sources

    def test_clear_removes_all_chunks(self, store):
        """Test that clear removes all chunks."""
        chunks = [create_test_chunk(f"chunk_{i}") for i in range(5)]
        store.add_chunks(chunks)
        assert store.count() == 5

        deleted = store.clear()

        assert deleted == 5
        assert store.count() == 0

    def test_clear_empty_collection(self, store):
        """Test clear on empty collection."""
        deleted = store.clear()
        assert deleted == 0


@pytest.mark.unit
class TestMetadataConversion:
    """Test cases for metadata conversion methods."""

    @pytest.fixture
    def store(self, tmp_path: Path, mock_settings):
        """Create a VectorStore instance for testing."""
        return VectorStore(persist_directory=str(tmp_path / "chroma"))

    def test_chunk_to_metadata(self, store):
        """Test converting chunk to metadata dict."""
        chunk = Chunk(
            chunk_id="test_chunk",
            text="Test text",
            source_document="/path/to/doc.pdf",
            page_numbers=[1, 2, 3],
            position=5,
            token_count=100,
            char_count=500,
            has_overlap_before=True,
            has_overlap_after=False,
            overlap_with_previous="prev_chunk",
            overlap_with_next=None,
            embedding=[0.1] * 1536,
        )

        metadata = store._chunk_to_metadata(chunk)

        assert metadata["source_document"] == "/path/to/doc.pdf"
        assert metadata["page_numbers"] == "1,2,3"
        assert metadata["position"] == 5
        assert metadata["token_count"] == 100
        assert metadata["char_count"] == 500
        assert metadata["has_overlap_before"] is True
        assert metadata["has_overlap_after"] is False
        assert metadata["overlap_with_previous"] == "prev_chunk"
        assert metadata["overlap_with_next"] == ""

    def test_metadata_to_chunk(self, store):
        """Test reconstructing chunk from metadata."""
        metadata = {
            "source_document": "/path/to/doc.pdf",
            "page_numbers": "1,2,3",
            "position": 5,
            "token_count": 100,
            "char_count": 500,
            "has_overlap_before": True,
            "has_overlap_after": False,
            "overlap_with_previous": "prev_chunk",
            "overlap_with_next": "",
        }

        chunk = store._metadata_to_chunk(
            chunk_id="test_chunk",
            text="Test text",
            metadata=metadata,
            embedding=[0.1] * 1536,
        )

        assert chunk.chunk_id == "test_chunk"
        assert chunk.text == "Test text"
        assert chunk.source_document == "/path/to/doc.pdf"
        assert chunk.page_numbers == [1, 2, 3]
        assert chunk.position == 5
        assert chunk.token_count == 100
        assert chunk.char_count == 500
        assert chunk.has_overlap_before is True
        assert chunk.has_overlap_after is False
        assert chunk.overlap_with_previous == "prev_chunk"
        assert chunk.overlap_with_next is None
        assert chunk.has_embedding()

    def test_metadata_roundtrip(self, store):
        """Test that chunk survives metadata roundtrip."""
        original = Chunk(
            chunk_id="roundtrip_test",
            text="Roundtrip test content",
            source_document="/test.pdf",
            page_numbers=[5, 6],
            position=3,
            token_count=50,
            char_count=25,
            has_overlap_before=True,
            has_overlap_after=True,
            overlap_with_previous="chunk_2",
            overlap_with_next="chunk_4",
            embedding=[0.5] * 1536,
        )

        # Add and retrieve
        store.add_chunks([original])
        retrieved = store.get_chunk("roundtrip_test")

        # Verify all fields match
        assert retrieved.chunk_id == original.chunk_id
        assert retrieved.text == original.text
        assert retrieved.source_document == original.source_document
        assert retrieved.page_numbers == original.page_numbers
        assert retrieved.position == original.position
        assert retrieved.token_count == original.token_count
        assert retrieved.has_overlap_before == original.has_overlap_before
        assert retrieved.has_overlap_after == original.has_overlap_after
        assert retrieved.overlap_with_previous == original.overlap_with_previous
        assert retrieved.overlap_with_next == original.overlap_with_next


@pytest.mark.unit
class TestPersistence:
    """Test cases for data persistence."""

    def test_data_persists_across_instances(self, tmp_path: Path, mock_settings):
        """Test that data persists when creating new store instance."""
        persist_dir = str(tmp_path / "persistent_chroma")

        # First instance: add data
        store1 = VectorStore(persist_directory=persist_dir)
        chunks = [
            create_test_chunk("chunk_001", "First chunk"),
            create_test_chunk("chunk_002", "Second chunk"),
        ]
        store1.add_chunks(chunks)

        # Force close by deleting reference
        del store1

        # Second instance: data should persist
        store2 = VectorStore(persist_directory=persist_dir)
        assert store2.count() == 2
        assert store2.get_chunk("chunk_001") is not None
        assert store2.get_chunk("chunk_002") is not None

    def test_search_works_after_persistence(self, tmp_path: Path, mock_settings):
        """Test that search works after reopening store."""
        persist_dir = str(tmp_path / "searchable_chroma")

        # First instance: add data
        store1 = VectorStore(persist_directory=persist_dir)
        chunk = create_test_chunk("searchable_chunk", embedding=[1.0] + [0.0] * 1535)
        store1.add_chunks([chunk])
        del store1

        # Second instance: search should work
        store2 = VectorStore(persist_directory=persist_dir)
        query_embedding = [1.0] + [0.0] * 1535
        results = store2.search(query_embedding, top_k=1)

        assert len(results) == 1
        assert results[0][0].chunk_id == "searchable_chunk"
