# AnkiAI

AI-powered PDF to Anki flashcard generator with intelligent context extraction and semantic understanding.

## Description

AnkiAI transforms PDF documents into high-quality Anki flashcards using advanced AI models (Claude and GPT-4). The system intelligently extracts document structure, builds semantic context through RAG, and generates contextually-aware flashcards with proper formatting.

## Features

- PDF document processing with structure preservation
- Semantic chunking and context extraction
- RAG-based context retrieval for intelligent flashcard generation
- Multi-model support (Anthropic Claude, OpenAI GPT-4)
- ChromaDB vector storage for efficient similarity search
- Automatic Anki deck generation (.apkg format)
- CLI interface for easy interaction

## Architecture

Built using Hybrid Modular Monolith architecture with clear separation of concerns:

- **Interface Layer**: CLI and user interactions
- **Application Layer**: Use cases and orchestration
- **Domain Layer**: Core business logic (document processing, RAG, generation, output)
- **Infrastructure Layer**: External integrations (LLM APIs, vector DB, file I/O)

## Setup

### Prerequisites

- Python 3.11 or higher
- Poetry for dependency management

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AnkiAI
```

2. Install dependencies:
```bash
poetry install
```

3. Configure environment variables:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `OPENAI_API_KEY`: Your OpenAI API key

### Usage

```bash
poetry run python -m ankiai --help
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test types
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests
```

## Project Structure

```
AnkiAI/
├── src/
│   ├── interface/          # CLI and user interactions
│   ├── application/        # Use cases and orchestration
│   ├── domain/            # Core business logic
│   │   ├── models/        # Domain models
│   │   ├── document_processing/  # PDF processing
│   │   ├── rag/           # Context retrieval
│   │   ├── generation/    # Flashcard generation
│   │   └── output/        # Anki deck creation
│   └── infrastructure/    # External integrations
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── e2e/             # End-to-end tests
│   └── fixtures/        # Test fixtures
└── docs/                # Documentation
```

## License

MIT
