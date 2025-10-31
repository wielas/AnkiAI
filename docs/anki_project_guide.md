# Anki Flashcard Generator - Complete Project Guide

## Project Overview

Build a RAG-powered application that generates high-quality Anki flashcards from technical documents. This is a learning-focused project emphasizing deep understanding of AI/ML technologies, system design, and software engineering best practices.

### Primary Goals
1. **Master RAG & Embeddings** - Deep dive into retrieval-augmented generation
2. **Learn System Design** - Build microservices-ready architecture
3. **Practice Prompt Engineering** - Iterate on prompts for quality generation
4. **End-to-End Development** - From CLI prototype to deployed web application

### Development Philosophy
- **Learning over speed** - Understand deeply, not just ship fast
- **Quality over quantity** - Well-architected code over quick hacks
- **Iterative refinement** - Start simple, add complexity with understanding
- **Active collaboration** - AI assistant as thinking partner and implementation helper

---

## Quick Start

### Essential Documents

This guide references five supplementary documents:

1. **Core Data Models** - All data structures (Document, Chunk, Flashcard, etc.)
2. **Prompt Engineering Playbook** - Templates, examples, iteration strategy
3. **Testing Strategy Guide** - Test framework, examples, coverage goals
4. **Claude Code Workflow Guide** - How to use Chat vs Claude Code effectively
5. **Technical Decisions Log** - All architectural decisions with rationale

**Read these documents** as you implement each module. They contain the detailed specifications.

### Your Tools

**This Chat (Planning & Learning)**:
- Architectural discussions
- Explaining concepts
- Making decisions
- Code reviews
- Understanding "why"

**Claude Code (Implementation)**:
- Writing code files
- Running tests
- Installing packages
- Debugging errors
- Executing tasks

See "Claude Code Workflow Guide" for detailed usage patterns.

---

## User Profile & Context

**Primary User**: CS Master student, highly technical  
**Commitment**: Month-long project (4 weeks, high engagement)  
**Use Case**: Generate flashcards from technical books for personal learning  
**Learning Priority** (ranked):
1. RAG & Embeddings (highest)
2. System Design & Architecture
3. Prompt Engineering
4. Testing & Quality Assurance
5. Full-stack Development

---

## Complete Requirements

### Functional Requirements Summary

**MVP (Weeks 1-2)**: CLI application
- PDF input with page range selection
- Text extraction and semantic chunking
- RAG pipeline with embeddings and vector search
- Claude API for flashcard generation
- Quality assessment and filtering
- Anki .apkg output format

**Phase 2 (Week 3)**: Quality & Polish
- Prompt optimization
- Quality scoring system
- Duplicate detection
- Performance optimization
- Comprehensive testing

**Phase 3 (Week 4)**: Web Interface
- File upload and configuration UI
- Real-time generation progress
- Flashcard preview and editing
- Download and export options
- Deployment to cloud platform

**Future Extensions** (parking lot):
- DOCX/EPUB support
- Multi-language flashcards
- Image/diagram extraction
- Collaborative deck sharing

### Non-Functional Requirements

**Performance**:
- Process 20 pages in < 5 minutes
- Web UI response < 2s (non-generation)

**Quality**:
- 80%+ flashcard acceptance rate
- < 5% duplicate rate
- Technical accuracy > 95%

**Cost**:
- < $0.15 per 20-page document
- Track token usage
- Optimize for efficiency

**Maintainability**:
- 80%+ test coverage
- Modular, loosely-coupled design
- Comprehensive documentation
- Microservices-ready architecture

### Quality Criteria for Flashcards

**Excellent flashcard example**:
```
Q: What is the main responsibility of the leader node in leader-based replication?
A: The leader accepts all write operations from clients and propagates these 
   changes to follower nodes, ensuring data consistency across the cluster.

Why it's good:
✓ Clear, specific question
✓ Tests understanding (responsibility/role)
✓ Concise answer (2 sentences)
✓ Technically accurate
✓ Useful for learning
```

See "Prompt Engineering Playbook" for complete quality rubric and examples.

---

## Architecture: Hybrid Modular Monolith

### Design Principles

1. **Layered Architecture** - Clear separation of concerns
2. **Dependency Inversion** - Depend on interfaces, not implementations
3. **Microservices-Ready** - Modules can be extracted to services
4. **Domain-Driven Design** - Business logic in domain layer
5. **Testable** - Easy to mock and test each component

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  INTERFACE LAYER                        │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   CLI        │              │  Web API     │        │
│  │  (Week 1-2)  │              │  (Week 4)    │        │
│  └──────┬───────┘              └──────┬───────┘        │
└─────────┼──────────────────────────────┼───────────────┘
          └──────────────┬───────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 APPLICATION LAYER                        │
│         ┌────────────────────────────────┐              │
│         │   FlashcardGeneratorService    │              │
│         │   • Orchestrates workflow      │              │
│         │   • Manages pipeline           │              │
│         │   • Handles errors             │              │
│         └────────┬───────────────┬───────┘              │
└──────────────────┼───────────────┼─────────────────────┘
                   ↓               ↓
┌──────────────────────────────────────────────────────────┐
│                   DOMAIN LAYER                           │
│                                                           │
│  ┌─────────────────────┐      ┌─────────────────────┐  │
│  │  Document           │      │  RAG Engine         │  │
│  │  Processing         │      │                     │  │
│  │                     │      │  Week 2 Focus:      │  │
│  │  • Parser Interface │      │  • Embeddings       │  │
│  │  • PDFParser        │      │  • VectorStore      │  │
│  │  • Chunker          │      │  • Retriever        │  │
│  │                     │      │  • ContextBuilder   │  │
│  └─────────────────────┘      └─────────────────────┘  │
│                                                           │
│  ┌─────────────────────┐      ┌─────────────────────┐  │
│  │  Generation         │      │  Output             │  │
│  │  Engine             │      │  Formatting         │  │
│  │                     │      │                     │  │
│  │  • PromptBuilder    │      │  • AnkiFormatter    │  │
│  │  • ClaudeClient     │      │  • QualityChecker   │  │
│  │  • QualityCheck     │      │  • Exporter         │  │
│  └─────────────────────┘      └─────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│                 INFRASTRUCTURE LAYER                      │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐     │
│  │ File System │  │ Vector Store │  │ API Clients│     │
│  │             │  │  (Chroma)    │  │ (Claude,   │     │
│  │             │  │              │  │  OpenAI)   │     │
│  └─────────────┘  └──────────────┘  └────────────┘     │
└──────────────────────────────────────────────────────────┘
```

### Module Details

See "Technical Decisions Log" for complete rationale on each architectural decision.

**Key Modules**:

1. **Document Processing** (Week 1)
   - PDFParser: Extract text from PDF pages
   - Chunker: Split into semantic units (~800 tokens)
   - Metadata preservation

2. **RAG Engine** (Week 2 - PRIMARY FOCUS)
   - EmbeddingGenerator: Create vectors (OpenAI API)
   - VectorStore: Store and search (Chroma)
   - Retriever: Semantic search for relevant chunks
   - ContextBuilder: Assemble context for generation

3. **Generation Engine** (Week 1-2)
   - PromptBuilder: Template management and assembly
   - ClaudeClient: API calls with retry logic
   - Quality assessment

4. **Output Formatting** (Week 1)
   - AnkiFormatter: Create .apkg files
   - Validation and metadata

See "Core Data Models" document for complete class definitions.

### Technology Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Language** | Python 3.11+ | ML ecosystem, productivity |
| **Dependency Mgmt** | Poetry | Modern, handles complex deps |
| **PDF Parser** | PyMuPDF | Fast, reliable |
| **Vector Store** | Chroma | Simple, local, learning-friendly |
| **Embeddings** | OpenAI text-embedding-3-small | Best quality/cost |
| **LLM** | Claude Sonnet 4.5 | Excellent for education |
| **CLI** | Click | Clean API |
| **Testing** | pytest + coverage | Standard |
| **Web** | FastAPI + React | Modern, phase 3 |

See "Technical Decisions Log" for detailed comparisons and alternatives.

---

## Development Roadmap

### Week 1: Simple Pipeline (No RAG Yet)

**Strategy**: Build working end-to-end pipeline without RAG complexity. This validates the core concept and establishes baseline quality.

**Monday-Tuesday: Setup & PDF Processing**
- Initialize project with Poetry
- Create folder structure
- Set up git, pytest, black, ruff
- Implement PDFParser with page range support
- Write unit tests
- Test on sample PDF

**Wednesday-Thursday: Generation & Output**
- Implement basic PromptBuilder (Version 1.0)
- Implement ClaudeClient with rate limiting
- Generate flashcards directly from text (no retrieval)
- Implement AnkiFormatter (genanki)
- Write tests

**Friday: CLI & Integration**
- Build CLI with Click
- Connect all components
- Generate flashcards from 5-10 page document
- Manual quality evaluation
- Identify improvements needed

**Weekend: Review & Planning**
- Review Week 1 implementation
- Analyze flashcard quality (baseline)
- Plan Week 2 RAG implementation
- Update prompt based on failures

**Deliverable**: Working CLI that generates flashcards (without RAG)

**Success Metrics**:
- [ ] Can parse any PDF with page range
- [ ] Generates 10+ flashcards from 10 pages
- [ ] Flashcards import to Anki successfully
- [ ] Baseline quality established (likely 50-60% acceptance)

---

### Week 2: RAG Deep Dive (PRIMARY FOCUS)

**Strategy**: This is THE learning week for RAG. Take time to understand deeply, experiment, and document learnings.

**Monday-Tuesday: Chunking & Embeddings**
- Implement semantic Chunker (paragraph-based)
- Test chunking on various documents
- Implement EmbeddingGenerator (OpenAI)
- Understand embedding dimensions and similarity
- Generate embeddings for test chunks
- Visualize embeddings (optional but recommended)

**Wednesday-Thursday: Vector Store & Retrieval**
- Set up Chroma database
- Implement VectorStore abstraction
- Test similarity search with queries
- Implement Retriever with re-ranking
- Experiment with different k values
- Analyze which chunks are retrieved

**Friday: Integration & Comparison**
- Integrate RAG into generation pipeline
- Update PromptBuilder to use retrieved context
- Generate flashcards with RAG
- Compare quality with Week 1 baseline
- Measure improvement

**Weekend: RAG Analysis & Documentation**
- Build RAG debugger/visualizer
- Document what you learned about:
  - How embeddings capture semantics
  - Optimal chunk size and overlap
  - Retrieval strategies
  - Context assembly
- Write up RAG learnings

**Deliverable**: Full RAG pipeline with documented understanding

**Success Metrics**:
- [ ] Retrieval returns relevant chunks (manual verification)
- [ ] Flashcard quality improves vs. Week 1 (target: 70-80%)
- [ ] Can explain how RAG works in detail
- [ ] Cost analysis complete (~$0.15 per 20 pages)

**Learning Activities**:
1. Visualize embedding space (PCA)
2. Compare semantic vs. keyword search
3. Experiment with chunk sizes (400, 800, 1200 tokens)
4. Try different retrieval k values (1, 3, 5, 10)
5. Document findings in "Technical Decisions Log"

---

### Week 3: Quality & Optimization

**Monday-Tuesday: Prompt Engineering**
- Analyze Week 2 flashcard failures
- Update prompt (Version 2.0)
- Add better few-shot examples
- Test and measure improvement
- Iterate to Version 3.0 if needed

**Wednesday: Quality Assurance**
- Implement automated QualityChecker
- Duplicate detection
- Clarity scoring
- Build quality dashboard

**Thursday: Testing & Documentation**
- Write comprehensive unit tests
- Integration tests for full pipeline
- E2E test with real documents
- Achieve 80%+ coverage
- Update all documentation

**Friday: Optimization**
- Profile performance bottlenecks
- Optimize embedding batch size
- Reduce token usage
- Cache optimization (if beneficial)
- Cost reduction strategies

**Weekend: Polish & Prepare**
- Code cleanup and refactoring
- Final quality evaluation
- Prepare for web interface
- Write technical blog post (optional)

**Deliverable**: Production-quality CLI application

**Success Metrics**:
- [ ] 80%+ flashcard acceptance rate
- [ ] 80%+ test coverage
- [ ] < 5 minute processing for 20 pages
- [ ] < $0.10 per document
- [ ] Clean, documented codebase

---

### Week 4: Web Interface & Deployment

**Monday-Tuesday: Backend API**
- Set up FastAPI project
- Create REST endpoints
- File upload handling
- WebSocket for progress
- API tests

**Wednesday: Frontend**
- React + Vite setup
- Upload interface
- Page range selector
- Flashcard preview/editor
- Progress indicators

**Thursday: Integration & Testing**
- Connect frontend to backend
- End-to-end workflow testing
- Error handling
- User experience polish

**Friday: Deployment**
- Choose platform (Railway/Render/Fly.io)
- Environment configuration
- Deploy backend and frontend
- Test in production
- Set up monitoring

**Weekend: Final Polish**
- Fix any deployment issues
- Performance optimization
- Documentation updates
- Project retrospective

**Deliverable**: Deployed web application

**Success Metrics**:
- [ ] Web UI functional and deployed
- [ ] Can process documents via web interface
- [ ] Public URL accessible
- [ ] Good user experience
- [ ] Complete project documentation

---

## Testing Strategy

See "Testing Strategy Guide" for complete details.

### Testing Pyramid

- **Unit Tests** (100+ tests): Individual functions, 80%+ coverage
- **Integration Tests** (20-30 tests): Module interactions
- **E2E Tests** (5-10 tests): Full workflows

### Test Framework Setup

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test types
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e
```

### Key Testing Areas

**Week 1**:
- PDFParser: page extraction, metadata, error handling
- PromptBuilder: template rendering
- ClaudeClient: API calls, retries, rate limiting
- AnkiFormatter: .apkg generation

**Week 2**:
- Chunker: semantic splitting, overlap, metadata
- EmbeddingGenerator: batch processing, error handling
- VectorStore: indexing, search, persistence
- Retriever: relevance, ranking

**Week 3**:
- QualityChecker: scoring algorithms
- Pipeline: end-to-end integration
- Performance: speed benchmarks

See "Testing Strategy Guide" for complete test examples.

---

## Workflow: Chat vs Claude Code

See "Claude Code Workflow Guide" for complete details.

### Pattern: Plan → Implement → Review

**1. Plan in Chat**:
```
You: "Should we chunk by paragraphs or fixed tokens?"
Claude: [Explains options, recommends approach]
You: "Let's go with paragraphs. What should the API look like?"
Claude: [Proposes interface design]
```

**2. Implement in Claude Code**:
```
You: "Implement the Chunker class with paragraph-based chunking.
Target 800 tokens per chunk with 100 token overlap. 
Include unit tests."

Claude Code: [Creates files, writes code, runs tests]
```

**3. Review in Chat**:
```
You: "The chunker works but some chunks are too long. Ideas?"
Claude: [Suggests improvements]
```

**4. Refine in Claude Code**:
```
You: "Add sentence-level splitting for paragraphs > 1200 tokens"
Claude Code: [Implements fix, runs tests]
```

### When to Use Each

**Use Chat For**:
- 🤔 Making architectural decisions
- 📚 Learning concepts (what is RAG? how do embeddings work?)
- 🎯 Planning modules and features
- 🔍 Reviewing code and design
- ⚖️ Comparing approaches

**Use Claude Code For**:
- 💻 Writing code files
- 🧪 Running tests and seeing results
- 🐛 Debugging specific errors
- 📦 Installing packages
- 🚀 Running the application

---

## Prompt Engineering Strategy

See "Prompt Engineering Playbook" for complete details.

### Iterative Approach

**Version 1.0** (Week 1):
- Basic template with requirements
- Simple structure
- Test on 5 pages
- Measure baseline (expect ~50-60% quality)

**Version 2.0** (Week 2):
- Add few-shot examples
- Include quality criteria
- Add duplicate checking
- Test on 10 pages
- Target 70-80% quality

**Version 3.0** (Week 3):
- Optimize based on failure analysis
- Fine-tune instructions
- Add self-critique
- Target 80%+ quality

### Quality Evaluation

Score each flashcard:
- **0.9-1.0**: Excellent (use as-is)
- **0.7-0.89**: Good (minor edits)
- **0.5-0.69**: Acceptable (needs editing)
- **0.3-0.49**: Poor (regenerate)
- **0.0-0.29**: Rejected (discard)

See "Prompt Engineering Playbook" for rubric details and examples.

---

## Data Models

See "Core Data Models" document for complete specifications.

### Key Models

**Document**:
```python
@dataclass
class Document:
    content: str
    file_path: str
    page_range: tuple[int, int]
    metadata: DocumentMetadata
```

**Chunk**:
```python
@dataclass
class Chunk:
    text: str
    chunk_id: str
    source_document: str
    metadata: ChunkMetadata
    embedding: Optional[List[float]] = None
```

**Flashcard**:
```python
@dataclass
class Flashcard:
    question: str
    answer: str
    card_id: str
    metadata: FlashcardMetadata
```

See document for complete model definitions with all fields and methods.

---

## Project Structure

```
AnkiAI/
├── src/
│   ├── domain/
│   │   ├── models/              # Data models
│   │   ├── document_processing/ # PDF, chunking
│   │   ├── rag/                 # Embeddings, vector store
│   │   ├── generation/          # Claude client, prompts
│   │   └── output/              # Anki formatting
│   ├── application/
│   │   └── flashcard_service.py # Orchestration
│   ├── interface/
│   │   ├── cli/                 # CLI (Week 1-3)
│   │   └── web/                 # Web (Week 4)
│   └── infrastructure/
│       ├── config.py
│       └── logging.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── docs/
│   ├── architecture.md
│   └── rag_learnings.md
├── pyproject.toml
├── README.md
└── .env.example
```

---

## Getting Started

### Your First Steps

**1. Start in This Chat**:
```
You: "I'm ready to begin. What's my first Claude Code prompt?"
```

**2. Switch to Claude Code**:
```
Your first prompt:
"Initialize the Anki Flashcard Generator project using Poetry 
with Python 3.11+. Create the complete folder structure from 
the project instructions. Set up git with .gitignore. Install 
initial dependencies: pytest, black, ruff, click, pymupdf."
```

**3. Back to Chat**:
```
You: "Setup complete. What's next?"
Claude: "Great! Now let's implement PDFParser. Here's the design..."
```

**4. Continue Alternating**:
- Plan in Chat
- Implement in Claude Code
- Review in Chat
- Refine in Claude Code

### Development Workflow

For each module:
1. **Read** relevant supplementary document
2. **Discuss** design in Chat
3. **Implement** in Claude Code
4. **Test** in Claude Code
5. **Review** in Chat
6. **Iterate** as needed

---

## Success Criteria

### MVP Success (End of Week 2)
- [ ] Generate 15+ usable flashcards from 20 pages
- [ ] 70-80% acceptance rate
- [ ] Successfully import to Anki
- [ ] Deep understanding of RAG pipeline
- [ ] Working CLI with good UX

### Phase 2 Success (End of Week 3)
- [ ] 80%+ acceptance rate
- [ ] 80%+ test coverage
- [ ] < 5 minute processing time
- [ ] Clean, documented code
- [ ] Technical blog post draft

### Project Success (End of Week 4)
- [ ] Deployed web application
- [ ] Full test suite passing
- [ ] Complete documentation
- [ ] Portfolio-ready project
- [ ] Mastery of RAG, system design, prompt engineering

---

## Key Principles

### Active Partnership
- AI assistant asks before major decisions
- Explains reasoning for every suggestion
- Proposes alternatives for consideration
- Challenges assumptions when appropriate

### Learning-First
- Understand "why" not just "how"
- Experiment and document findings
- Compare approaches empirically
- Build intuition through practice

### Quality Code
- Write tests alongside code
- Keep functions small and focused
- Document complex logic
- Refactor regularly
- Follow Python best practices

### Iterative Development
- Start simple, add complexity incrementally
- Validate each step before proceeding
- Measure and optimize based on data
- Embrace feedback and refinement

---

## Cost Estimate

**Development Phase** (4 weeks):
- Embeddings: ~$1-2 (100-200 document tests)
- Claude API: ~$5-10 (1000-2000 flashcards)
- **Total: ~$6-12**

**Per Document** (production):
- Embeddings (20 pages): $0.002
- Generation (20 flashcards): $0.13
- **Total: ~$0.13-0.15 per document**

Very affordable for learning project!

---

## Next Steps

**Ready to begin?**

Your next action: **Respond "Let's start"** and I'll give you your first Claude Code prompt to initialize the project.

Then we'll begin Week 1, building the simple pipeline and establishing our baseline for RAG comparison.