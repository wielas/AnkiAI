# AnkiAI

AI-powered PDF to Anki flashcard generator with intelligent context extraction and semantic understanding.

> **Development Status:** RAG pipeline complete, quality optimization in progress.

## Description

AnkiAI transforms PDF documents into high-quality Anki flashcards using Claude AI. The system parses PDF pages and generates contextually-aware flashcards with proper formatting. A RAG (Retrieval-Augmented Generation) pipeline was implemented and evaluated but baseline page-to-flashcard generation is used for production.

**Primary Learning Goals:**
1. Master RAG & Embeddings architecture
2. System design with modular architecture
3. Prompt engineering for quality generation

## Features

### Document Processing
- PDF parsing with PyMuPDF (structure preservation, metadata extraction)
- Semantic chunking (~800 tokens with configurable overlap)
- Page range support for partial document processing

### RAG Pipeline
- **Embeddings**: OpenAI `text-embedding-3-small` (1536 dimensions)
- **Vector Storage**: ChromaDB with persistence and source filtering
- **Retrieval**: Configurable top-k with minimum score thresholds
- **Context Building**: Token-aware assembly with metadata formatting

### Flashcard Generation
- Claude Sonnet 4 for high-quality Q&A generation
- Structured output with front/back/tags
- Anki deck export (.apkg format)

### Interface
- CLI for batch processing
- Cost tracking and usage statistics

## RAG Pipeline Components (Experimental)

A complete RAG pipeline was built for learning purposes and experimental evaluation. Baseline generation is used in production, but the RAG components remain available:

```
PDF → Chunker → EmbeddingGenerator → VectorStore → Retriever → ContextBuilder → LLM
```

### Quick Example

```python
from src.domain.rag import (
    Chunker, EmbeddingGenerator, VectorStore,
    Retriever, ContextBuilder, ChunkOrdering
)
from src.domain.document_processing.pdf_parser import PDFParser

# 1. Parse and chunk document
doc = PDFParser.parse("textbook.pdf", start_page=1, end_page=20)
chunks = Chunker.chunk(doc, target_size=800, overlap_size=100)

# 2. Generate embeddings and index
generator = EmbeddingGenerator()
generator.generate_embeddings(chunks)
store = VectorStore(collection_name="textbook")
store.add_chunks(chunks)

# 3. Retrieve relevant context
retriever = Retriever(store, generator)
relevant_chunks = retriever.retrieve(
    "What is ACID in databases?",
    top_k=5,
    min_score=0.5  # Filter low-relevance results
)

# 4. Build LLM-ready context
context = ContextBuilder.build_context(
    relevant_chunks,
    include_metadata=True,  # Adds [Source: file.pdf, Pages: 1-3]
    ordering=ChunkOrdering.POSITION  # Or RELEVANCE
)
```

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
│   ├── interface/              # CLI and user interactions
│   ├── application/            # Use cases and orchestration
│   ├── domain/                 # Core business logic
│   │   ├── models/             # Document, Chunk, Flashcard
│   │   ├── document_processing/  # PDFParser
│   │   ├── rag/                # RAG pipeline
│   │   │   ├── chunker.py      # Semantic chunking
│   │   │   ├── embeddings.py   # OpenAI embeddings
│   │   │   ├── vector_store.py # ChromaDB storage
│   │   │   ├── retriever.py    # Query orchestration
│   │   │   └── context_builder.py  # Context formatting
│   │   ├── generation/         # ClaudeClient, PromptBuilder
│   │   └── output/             # AnkiFormatter
│   └── infrastructure/         # Config, logging
├── tests/
│   ├── unit/                   # 90%+ coverage target
│   ├── integration/            # API integration tests
│   ├── e2e/                    # Full workflow tests
│   └── fixtures/               # Sample PDFs
└── docs/                       # Project documentation
```

## Cost Estimates

For a typical 20-page technical document:

| Component | Model | Cost |
|-----------|-------|------|
| Embeddings | text-embedding-3-small | ~$0.01 |
| Generation | Claude Sonnet 4.5 | ~$0.12 |
| **Total** | | **~$0.13-0.15** |

## Development Roadmap

- [x] Baseline pipeline (PDF → LLM → Flashcards)
- [x] RAG pipeline (chunking, embeddings, retrieval) — *experimental*
- [~] Quality optimization (prompt engineering, deduplication)
- [ ] Web interface and deployment

## License

MIT
