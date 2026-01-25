"""Anki deck formatting and export using genanki."""

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import genanki

logger = logging.getLogger(__name__)


class AnkiFormatter:
    """Formats flashcards into Anki .apkg format.

    Uses genanki library to create Anki-compatible decks with proper
    note models, tags, and metadata.

    Design decisions:
    - Stateless: All state passed via parameters
    - Deterministic IDs: Uses hash-based IDs for reproducibility
    - Basic note model: Front/back card type (sufficient for Week 1)
    - Rich metadata: Includes source info as tags
    """

    # CSS styling for the cards
    CARD_CSS = """
    .card {
        font-family: arial;
        font-size: 18px;
        text-align: left;
        color: black;
        background-color: white;
        padding: 20px;
    }
    .question {
        font-weight: bold;
    }
    .answer {
        margin-top: 10px;
    }
    """

    @staticmethod
    def _generate_model_id(name: str) -> int:
        """Generate a deterministic model ID from a name.

        Args:
            name: Name to hash

        Returns:
            Positive integer ID suitable for genanki
        """
        # Use hash for determinism, take first 8 bytes
        hash_bytes = hashlib.md5(name.encode()).digest()[:8]
        # Convert to positive integer (genanki requires positive IDs)
        return abs(int.from_bytes(hash_bytes, byteorder="big")) % (2**31)

    @staticmethod
    def _generate_deck_id(name: str) -> int:
        """Generate a deterministic deck ID from a name.

        Args:
            name: Deck name to hash

        Returns:
            Positive integer ID suitable for genanki
        """
        # Use different salt than model ID to avoid collisions
        hash_input = f"deck_{name}"
        hash_bytes = hashlib.md5(hash_input.encode()).digest()[:8]
        return abs(int.from_bytes(hash_bytes, byteorder="big")) % (2**31)

    @staticmethod
    def _generate_note_guid(question: str, answer: str) -> str:
        """Generate a unique GUID for a note.

        Args:
            question: The question text
            answer: The answer text

        Returns:
            Unique string GUID for the note
        """
        content = f"{question}|{answer}"
        return hashlib.md5(content.encode()).hexdigest()[:10]

    @staticmethod
    def _create_note_model(model_name: str = "AnkiAI Basic") -> genanki.Model:
        """Create a basic front/back note model.

        Args:
            model_name: Name for the model

        Returns:
            genanki.Model configured for Q&A flashcards
        """
        model_id = AnkiFormatter._generate_model_id(model_name)

        return genanki.Model(
            model_id,
            model_name,
            fields=[
                {"name": "Question"},
                {"name": "Answer"},
            ],
            templates=[
                {
                    "name": "Card 1",
                    "qfmt": '<div class="question">{{Question}}</div>',
                    "afmt": '{{FrontSide}}<hr id="answer"><div class="answer">{{Answer}}</div>',
                },
            ],
            css=AnkiFormatter.CARD_CSS,
        )

    @staticmethod
    def format_flashcards(
        flashcards: List[dict],
        deck_name: str = "Generated Flashcards",
        tags: Optional[List[str]] = None,
        output_path: str = "flashcards.apkg",
    ) -> str:
        """Convert flashcards to Anki .apkg format.

        Args:
            flashcards: List of dicts with "question" and "answer" keys
            deck_name: Name for the Anki deck
            tags: Optional list of tags to apply to all cards
            output_path: Where to save the .apkg file

        Returns:
            Absolute path to the created .apkg file

        Raises:
            ValueError: If flashcards list is empty or cards are malformed
            OSError: If output path is not writable
        """
        if not flashcards:
            raise ValueError("Cannot create deck with no flashcards")

        # Validate flashcards structure
        for i, card in enumerate(flashcards):
            if not isinstance(card, dict):
                raise ValueError(f"Flashcard {i} is not a dictionary")
            if "question" not in card or "answer" not in card:
                raise ValueError(
                    f"Flashcard {i} missing required 'question' or 'answer' field"
                )

        logger.info(
            f"Formatting {len(flashcards)} flashcards into Anki deck: {deck_name}"
        )

        # Create model and deck
        model = AnkiFormatter._create_note_model()
        deck_id = AnkiFormatter._generate_deck_id(deck_name)
        deck = genanki.Deck(deck_id, deck_name)

        # Prepare tags
        all_tags = tags or []
        # Add generation timestamp tag
        timestamp_tag = f"generated:{datetime.now().strftime('%Y-%m-%d')}"
        all_tags.append(timestamp_tag)

        # Add notes to deck
        for card in flashcards:
            question = card["question"].strip()
            answer = card["answer"].strip()

            # Generate unique GUID for this note
            guid = AnkiFormatter._generate_note_guid(question, answer)

            note = genanki.Note(
                model=model,
                fields=[question, answer],
                tags=all_tags,
                guid=guid,
            )
            deck.add_note(note)

        # Create package and write to file
        package = genanki.Package(deck)

        # Ensure output directory exists
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        package.write_to_file(str(output_path_obj))

        absolute_path = str(output_path_obj.resolve())
        logger.info(f"Created Anki deck: {absolute_path} ({len(flashcards)} cards)")

        return absolute_path

    @staticmethod
    def create_tags_from_metadata(
        source_filename: str,
        page_range: tuple,
        difficulty: str,
        additional_tags: Optional[List[str]] = None,
    ) -> List[str]:
        """Create standardized tags from generation metadata.

        Args:
            source_filename: Name of the source PDF file
            page_range: Tuple of (start_page, end_page)
            difficulty: Difficulty level used for generation
            additional_tags: Optional extra tags to include

        Returns:
            List of formatted tags
        """
        tags = []

        # Source file tag (sanitized for Anki)
        source_tag = Path(source_filename).stem
        # Replace spaces and special chars with underscores
        source_tag = "".join(c if c.isalnum() else "_" for c in source_tag)
        source_tag = source_tag.strip("_")
        if source_tag:
            tags.append(f"source:{source_tag}")

        # Page range tag
        start, end = page_range
        tags.append(f"pages:{start}-{end}")

        # Difficulty tag
        if difficulty:
            tags.append(f"difficulty:{difficulty}")

        # Add any additional tags
        if additional_tags:
            tags.extend(additional_tags)

        return tags
