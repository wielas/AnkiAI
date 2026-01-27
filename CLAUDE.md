# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AnkiAI is an AI-powered PDF to Anki flashcard generator built with a focus on learning RAG (Retrieval-Augmented Generation) architecture and system design. The system intelligently extracts document structure, builds semantic context through RAG, and generates high-quality flashcards using Claude/GPT-4.

**Primary Learning Goals:**
1. Master RAG & Embeddings (primary focus)
2. System design and modular architecture
3. Prompt engineering for quality generation
4. Full-stack development (CLI to web)

## Essential Commands

### Environment Setup
```bash
# Install dependencies
poetry install

# Activate virtual environment (if needed)
poetry shell
```

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

# Run specific test file
poetry run pytest tests/unit/document_processing/test_pdf_parser.py

# Run single test function
poetry run pytest tests/unit/document_processing/test_pdf_parser.py::test_parse_basic_pdf
```

### Code Quality
```bash
# Format code (automatically fixes formatting)
poetry run black src tests

# Lint code (checks for issues)
poetry run ruff check src tests

# Fix auto-fixable linting issues
poetry run ruff check --fix src tests
```

### Application Usage
```bash
# Run the CLI application
poetry run python -m ankiai --help
```

## Architecture: Hybrid Modular Monolith

The codebase uses a layered architecture with clear separation of concerns, designed to be microservices-ready. Each layer depends only on layers below it.

### Layer Structure

```
Interface Layer (CLI/Web)
    ↓
Application Layer (Use Cases & Orchestration)
    ↓
Domain Layer (Core Business Logic)
    ↓
Infrastructure Layer (External Integrations)
```

### Key Directories

- **src/interface/** - User-facing interfaces (CLI now, web later)
- **src/application/** - Orchestration services that coordinate domain modules
- **src/domain/** - Core business logic organized by capability:
  - **models/** - Domain models (Document, Chunk, Flashcard)
  - **document_processing/** - PDF parsing and semantic chunking
  - **rag/** - Embeddings, vector store, retrieval, context building
  - **generation/** - LLM prompts and flashcard generation
  - **output/** - Anki deck formatting and export
- **src/infrastructure/** - External dependencies (config, logging, API clients)
- **tests/** - Test suite organized by test type (unit/integration/e2e)

### Design Principles

1. **Dependency Inversion**: Modules depend on interfaces, not concrete implementations
2. **Stateless Services**: Most classes use static methods or are stateless
3. **Domain-Driven**: Business logic lives in the domain layer, not infrastructure
4. **Testability**: Easy to mock dependencies and test in isolation
5. **Microservices-Ready**: Modules can be extracted to separate services

## Domain Models

All core models are in `src/domain/models/`. Key models:

### Document (`document.py`)
Represents a parsed document with content, metadata, and page range:
- `content: str` - Full extracted text
- `file_path: str` - Source file path
- `page_range: tuple[int, int]` - 1-indexed, inclusive (start, end)
- `metadata: DocumentMetadata` - Title, author, pages, etc.

**Important**: Page ranges are 1-indexed (first page = 1, not 0)

### DocumentMetadata
Required fields: `total_pages`, `file_size_bytes`, `file_format`
Optional fields: `title`, `author`, `subject`, `keywords`, `creation_date`

## Document Processing Module

### PDFParser (`src/domain/document_processing/pdf_parser.py`)

Stateless PDF parser using PyMuPDF (fitz).

**Key Design Decisions:**
- Stateless: All state passed via parameters
- Forgiving on range overflows: Clips to available pages with warning
- Strict on logic errors: Raises ValueError for invalid ranges
- Uses "text" extraction mode for clean output

**Usage:**
```python
from src.domain.document_processing.pdf_parser import PDFParser

# Parse entire document
doc = PDFParser.parse("path/to/file.pdf")

# Parse specific page range (1-indexed, inclusive)
doc = PDFParser.parse("path/to/file.pdf", start_page=5, end_page=10)
```

**Error Handling:**
- Raises `FileNotFoundError` if file doesn't exist
- Raises `ValueError` for invalid page ranges (start > end, start < 1)
- Warns and clips if end_page exceeds total pages

## Testing Strategy

### Test Organization
- **Unit tests** (`tests/unit/`): Individual functions, 80%+ coverage target
- **Integration tests** (`tests/integration/`): Module interactions
- **E2E tests** (`tests/e2e/`): Full workflow tests

### Test Markers
Tests use pytest markers for selective running:
- `@pytest.mark.unit` - Fast, isolated tests
- `@pytest.mark.integration` - Tests involving multiple modules
- `@pytest.mark.e2e` - Full system tests

### Fixtures
Shared fixtures are in `tests/conftest.py` for reuse across test files.

## Development Workflow

### Adding a New Module

1. **Plan the interface** - Define the module's responsibilities and API
2. **Create domain model** (if needed) - Add to `src/domain/models/`
3. **Implement the module** - In appropriate domain subdirectory
4. **Write tests first** (TDD approach recommended) - In `tests/unit/`
5. **Implement functionality** - Make tests pass
6. **Run formatters** - `poetry run black` and `poetry run ruff`
7. **Verify coverage** - `poetry run pytest --cov`

### Debugging Tips

**View test failures in detail:**
```bash
poetry run pytest -vv  # Very verbose output
poetry run pytest -x   # Stop on first failure
poetry run pytest --pdb  # Drop into debugger on failure
```

**Check coverage for specific module:**
```bash
poetry run pytest --cov=src/domain/document_processing --cov-report=term-missing
```

## Code Style

### Python Standards
- **Python version**: 3.11+
- **Line length**: 88 characters (Black default)
- **Type hints**: Use type hints for function signatures
- **Docstrings**: Google-style docstrings for all public functions/classes

### Naming Conventions
- Classes: `PascalCase` (e.g., `PDFParser`)
- Functions/methods: `snake_case` (e.g., `parse_document`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CHUNK_SIZE`)
- Private methods: `_leading_underscore` (e.g., `_extract_metadata`)

### Imports
- Standard library first
- Third-party packages second
- Local imports third
- Alphabetically sorted within each group

Example:
```python
import logging
import os
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF

from src.domain.models.document import Document, DocumentMetadata
```

## RAG Implementation

### Overview

A complete RAG (Retrieval-Augmented Generation) pipeline was implemented to explore retrieval-augmented generation as an alternative to direct page-based flashcard generation.

### Architecture

```
PDF → Chunker → EmbeddingGenerator → VectorStore → Retriever → ContextBuilder → LLM
```

### Components Built

- **Chunker** (`src/domain/rag/chunker.py`): Semantic chunking with 800 token target, 100 token overlap
- **EmbeddingGenerator** (`src/domain/rag/embeddings.py`): OpenAI text-embedding-3-small integration with batch processing
- **VectorStore** (`src/domain/rag/vector_store.py`): ChromaDB persistence with similarity search
- **Retriever** (`src/domain/rag/retriever.py`): High-level retrieval API with configurable top_k
- **ContextBuilder** (`src/domain/rag/context_builder.py`): Format retrieved chunks for LLM consumption

### Experimental Evaluation

Tested configurations: baseline vs. RAG with k={1,3,5,10}

**Key findings:**
- **Semantic similarity trap**: Same or highly similar chunks retrieved repeatedly across different queries
- **Duplicate flashcards**: Similar concepts generated identical or near-identical flashcard content
- **No clear quality improvement**: RAG-generated flashcards did not demonstrate measurable quality gains over baseline
- **Added complexity**: Additional pipeline stages increased processing time and cost without corresponding benefits

### Production Decision

The baseline (non-RAG) approach is used for production flashcard generation. RAG components are preserved in the codebase for future experimentation.

**Rationale:** Testing revealed that RAG did not provide clear quality improvements over baseline generation, while adding significant complexity. Key issues included semantic similarity causing duplicate retrievals and repeated flashcard concepts.

### Technical Specifications

| Specification | Value |
|--------------|-------|
| Embedding model | text-embedding-3-small |
| Embedding dimensions | 1536 |
| Embedding cost | ~$0.003 per 200-page document |
| Vector database | ChromaDB with persistent storage |
| Distance metric | L2 (converted to 0-1 similarity scores) |
| Chunk target size | 800 tokens |
| Chunk overlap | 100 tokens |

### Cost Target

~$0.13-0.15 per 20-page document (using baseline generation)

## Important Project Context

### Quality Metrics
- **Flashcard acceptance rate**: Target 80%+
- **Test coverage**: 80%+
- **Processing speed**: < 5 minutes for 20 pages
- **Duplicate rate**: < 5%

### Development Status
- **Baseline pipeline**: Complete (PDF → LLM → Flashcards)
- **RAG pipeline**: Complete (experimental, not used in production)
- **Quality optimization**: In progress (prompt engineering, deduplication)
- **Web interface**: Planned

### Iterative Prompt Engineering
Prompts are versioned and improved based on quality analysis:
- v1.0: Basic template
- v2.0: Few-shot examples with improved structure
- v3.0: Optimized based on failure analysis

## Common Patterns

### Stateless Design
Most classes use static methods and have no instance state:
```python
class PDFParser:
    @staticmethod
    def parse(file_path: str, start_page: int = 1) -> Document:
        # All state passed via parameters
        pass
```

### Error Handling
- Let built-in exceptions propagate when appropriate (e.g., FileNotFoundError)
- Raise ValueError for logic errors (invalid parameters)
- Log warnings for recoverable issues
- Use try-finally for resource cleanup

### Logging
Use structured logging throughout:
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"Processing document: {file_path}")
logger.warning(f"Page range clipped to {total_pages}")
logger.error(f"Failed to parse: {error}")
```

## Environment Variables

Required API keys (see `.env.example`):
- `ANTHROPIC_API_KEY` - For Claude API
- `OPENAI_API_KEY` - For embeddings and GPT-4

## Additional Resources

See `docs/` for detailed guides:
- `docs/anki_project_guide.md` - Complete project roadmap and requirements
- `docs/claude_code_workflow.md` - How to use Claude Code effectively

## Key Reminders

1. **Pages are 1-indexed** - First page is 1, not 0 (affects page_range tuples)
2. **Baseline mode for production** - Use direct page-to-flashcard generation (RAG available for experimentation)
3. **Test-driven development** - Write tests alongside code
4. **Stateless by default** - Prefer static methods and pure functions
5. **Document as you go** - Docstrings for all public APIs
6. **Cost awareness** - Track API usage during development
