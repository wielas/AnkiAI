"""Unit tests for AnkiFormatter."""

import os
import zipfile

import pytest

from src.domain.output.anki_formatter import AnkiFormatter


@pytest.mark.unit
class TestAnkiFormatter:
    """Test suite for AnkiFormatter class."""

    def test_format_flashcards_creates_file(self, tmp_path):
        """Test that format_flashcards creates an .apkg file."""
        flashcards = [
            {"question": "What is Python?", "answer": "A programming language."},
        ]
        output_path = tmp_path / "test.apkg"

        result_path = AnkiFormatter.format_flashcards(
            flashcards=flashcards,
            deck_name="Test Deck",
            output_path=str(output_path),
        )

        assert os.path.exists(result_path)
        assert result_path.endswith(".apkg")

    def test_format_flashcards_returns_absolute_path(self, tmp_path):
        """Test that the returned path is absolute."""
        flashcards = [
            {"question": "Q1", "answer": "A1"},
        ]
        output_path = tmp_path / "test.apkg"

        result_path = AnkiFormatter.format_flashcards(
            flashcards=flashcards,
            deck_name="Test Deck",
            output_path=str(output_path),
        )

        assert os.path.isabs(result_path)

    def test_format_flashcards_with_multiple_cards(self, tmp_path):
        """Test formatting multiple flashcards."""
        flashcards = [
            {"question": "Q1", "answer": "A1"},
            {"question": "Q2", "answer": "A2"},
            {"question": "Q3", "answer": "A3"},
        ]
        output_path = tmp_path / "multi.apkg"

        result_path = AnkiFormatter.format_flashcards(
            flashcards=flashcards,
            deck_name="Multi Card Deck",
            output_path=str(output_path),
        )

        assert os.path.exists(result_path)
        # Verify it's a valid zip (apkg is a zip file)
        assert zipfile.is_zipfile(result_path)

    def test_format_flashcards_with_tags(self, tmp_path):
        """Test that tags are properly included."""
        flashcards = [
            {"question": "Q1", "answer": "A1"},
        ]
        tags = ["test-tag", "chapter-1"]
        output_path = tmp_path / "tagged.apkg"

        result_path = AnkiFormatter.format_flashcards(
            flashcards=flashcards,
            deck_name="Tagged Deck",
            tags=tags,
            output_path=str(output_path),
        )

        # Verify file was created
        assert os.path.exists(result_path)

    def test_format_flashcards_empty_list_raises_error(self, tmp_path):
        """Test that empty flashcard list raises ValueError."""
        output_path = tmp_path / "empty.apkg"

        with pytest.raises(ValueError, match="Cannot create deck with no flashcards"):
            AnkiFormatter.format_flashcards(
                flashcards=[],
                deck_name="Empty Deck",
                output_path=str(output_path),
            )

    def test_format_flashcards_invalid_card_structure_raises_error(self, tmp_path):
        """Test that malformed flashcards raise ValueError."""
        output_path = tmp_path / "invalid.apkg"

        # Missing 'answer' key
        with pytest.raises(ValueError, match="missing required"):
            AnkiFormatter.format_flashcards(
                flashcards=[{"question": "Q1"}],
                deck_name="Invalid Deck",
                output_path=str(output_path),
            )

        # Missing 'question' key
        with pytest.raises(ValueError, match="missing required"):
            AnkiFormatter.format_flashcards(
                flashcards=[{"answer": "A1"}],
                deck_name="Invalid Deck",
                output_path=str(output_path),
            )

    def test_format_flashcards_non_dict_raises_error(self, tmp_path):
        """Test that non-dict flashcard raises ValueError."""
        output_path = tmp_path / "invalid.apkg"

        with pytest.raises(ValueError, match="is not a dictionary"):
            AnkiFormatter.format_flashcards(
                flashcards=["not a dict"],
                deck_name="Invalid Deck",
                output_path=str(output_path),
            )

    def test_format_flashcards_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if they don't exist."""
        flashcards = [
            {"question": "Q1", "answer": "A1"},
        ]
        output_path = tmp_path / "nested" / "dirs" / "test.apkg"

        result_path = AnkiFormatter.format_flashcards(
            flashcards=flashcards,
            deck_name="Nested Deck",
            output_path=str(output_path),
        )

        assert os.path.exists(result_path)

    def test_generate_model_id_is_deterministic(self):
        """Test that model IDs are deterministic for the same name."""
        name = "Test Model"

        id1 = AnkiFormatter._generate_model_id(name)
        id2 = AnkiFormatter._generate_model_id(name)

        assert id1 == id2
        assert isinstance(id1, int)
        assert id1 > 0

    def test_generate_deck_id_is_deterministic(self):
        """Test that deck IDs are deterministic for the same name."""
        name = "Test Deck"

        id1 = AnkiFormatter._generate_deck_id(name)
        id2 = AnkiFormatter._generate_deck_id(name)

        assert id1 == id2
        assert isinstance(id1, int)
        assert id1 > 0

    def test_generate_deck_id_differs_from_model_id(self):
        """Test that deck and model IDs are different for the same name."""
        name = "Same Name"

        model_id = AnkiFormatter._generate_model_id(name)
        deck_id = AnkiFormatter._generate_deck_id(name)

        assert model_id != deck_id

    def test_generate_note_guid_is_deterministic(self):
        """Test that note GUIDs are deterministic."""
        question = "What is X?"
        answer = "X is Y."

        guid1 = AnkiFormatter._generate_note_guid(question, answer)
        guid2 = AnkiFormatter._generate_note_guid(question, answer)

        assert guid1 == guid2

    def test_generate_note_guid_differs_for_different_content(self):
        """Test that note GUIDs differ for different content."""
        guid1 = AnkiFormatter._generate_note_guid("Q1", "A1")
        guid2 = AnkiFormatter._generate_note_guid("Q2", "A2")

        assert guid1 != guid2


@pytest.mark.unit
class TestCreateTagsFromMetadata:
    """Test suite for create_tags_from_metadata method."""

    def test_creates_source_tag(self):
        """Test source filename is converted to tag."""
        tags = AnkiFormatter.create_tags_from_metadata(
            source_filename="my_document.pdf",
            page_range=(1, 10),
            difficulty="intermediate",
        )

        assert "source:my_document" in tags

    def test_creates_page_range_tag(self):
        """Test page range is included as tag."""
        tags = AnkiFormatter.create_tags_from_metadata(
            source_filename="doc.pdf",
            page_range=(5, 15),
            difficulty="intermediate",
        )

        assert "pages:5-15" in tags

    def test_creates_difficulty_tag(self):
        """Test difficulty is included as tag."""
        tags = AnkiFormatter.create_tags_from_metadata(
            source_filename="doc.pdf",
            page_range=(1, 1),
            difficulty="advanced",
        )

        assert "difficulty:advanced" in tags

    def test_includes_additional_tags(self):
        """Test additional tags are included."""
        additional = ["custom-tag", "chapter-3"]

        tags = AnkiFormatter.create_tags_from_metadata(
            source_filename="doc.pdf",
            page_range=(1, 5),
            difficulty="beginner",
            additional_tags=additional,
        )

        assert "custom-tag" in tags
        assert "chapter-3" in tags

    def test_sanitizes_source_filename(self):
        """Test special characters in filename are sanitized."""
        tags = AnkiFormatter.create_tags_from_metadata(
            source_filename="my file (2024).pdf",
            page_range=(1, 1),
            difficulty="intermediate",
        )

        # Check that spaces and special chars are replaced
        source_tags = [t for t in tags if t.startswith("source:")]
        assert len(source_tags) == 1
        # Should not contain spaces or parentheses
        assert " " not in source_tags[0]
        assert "(" not in source_tags[0]
        assert ")" not in source_tags[0]
