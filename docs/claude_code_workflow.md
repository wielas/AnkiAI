# Claude Code Workflow Guide

## Overview

This guide explains how to effectively use Claude Code alongside this chat for building the Anki Flashcard Generator. Think of it as having two complementary tools: the chat for thinking and Claude Code for doing.

---

## The Two Interfaces

### This Chat (Planning & Learning)
**Purpose**: Strategic discussions, decisions, explanations

**Use for**:
- 🎯 Making architectural decisions
- 📚 Learning concepts (RAG, embeddings, system design)
- 🤔 Discussing trade-offs and alternatives
- 📋 Planning next steps
- 🔍 Code reviews and design feedback
- 💡 Brainstorming solutions to problems
- 📖 Understanding "why" something works

**Characteristics**:
- Async, thoughtful discussion
- Can reference multiple artifacts
- Good for back-and-forth dialogue
- Preserves conversation history
- Can explain complex concepts

### Claude Code (Implementation & Execution)
**Purpose**: Hands-on coding, file manipulation, terminal operations

**Use for**:
- 💻 Writing code files
- 🏗️ Setting up project structure
- 📦 Installing dependencies
- 🧪 Running tests
- 🐛 Debugging errors
- 🔧 Refactoring code
- 📝 Creating configuration files
- 🚀 Running the application

**Characteristics**:
- Direct file system access
- Can run terminal commands
- Sees actual errors and outputs
- Makes multiple related changes
- Fast iteration cycles

---

## Workflow Patterns

### Pattern 1: Plan → Implement → Review

**Step 1 - Planning (Chat)**:
```
You: "Should we use PyMuPDF or pdfplumber for PDF parsing?"

Claude: [Compares options, recommends PyMuPDF with reasoning]

You: "Let's go with PyMuPDF. What should the PDFParser interface look like?"

Claude: [Discusses interface design, shows example]
```

**Step 2 - Implementation (Claude Code)**:
```
You in Claude Code: 
"Set up the document_processing module with PDFParser class using 
PyMuPDF. Implement the parse() method with page range support as 
we discussed. Add unit tests."

Claude Code:
- Creates folder structure
- Installs pymupdf via poetry
- Writes pdf_parser.py
- Creates test_pdf_parser.py
- Shows you the results
```

**Step 3 - Review (Chat)**:
```
You: "The parser works but feels slow. How can we optimize?"

Claude: [Suggests lazy loading, caching strategies, provides examples]
```

**Step 4 - Refinement (Claude Code)**:
```
You in Claude Code:
"Refactor PDFParser to use lazy loading as discussed"

Claude Code: [Implements optimization]
```

### Pattern 2: Learn → Apply

**Learn (Chat)**:
```
You: "Explain how RAG works with embeddings and vector search"

Claude: [Detailed explanation with diagrams and examples]

You: "How should we architect our RAG engine?"

Claude: [Discusses architecture options]
```

**Apply (Claude Code)**:
```
You in Claude Code:
"Implement the RAG engine with EmbeddingGenerator and ChromaVectorStore 
following the architecture we just discussed"

Claude Code: [Builds the implementation]
```

### Pattern 3: Debug → Fix

**Encounter Error (Claude Code)**:
```
You: "Run the tests"

Claude Code: [Runs pytest, shows failure]
Error: AttributeError: 'Chunk' object has no attribute 'embedding'
```

**Analyze (Chat)**:
```
You: "I'm getting this error: [paste error]. What's causing it?"

Claude: [Analyzes error, explains root cause, suggests fixes]
```

**Fix (Claude Code)**:
```
You: "Implement the fix we discussed"

Claude Code: [Applies fix, reruns tests, confirms success]
```

### Pattern 4: Iterate → Evolve

**Initial Version (Claude Code)**:
```
You: "Create basic prompt template for flashcard generation"

Claude Code: [Creates prompt_builder.py with v1 template]
```

**Test & Evaluate (Both)**:
```
You in Claude Code: "Generate 5 flashcards from sample PDF"

Claude Code: [Runs, shows results]

You in Chat: "The questions are too vague. How can we improve?"

Claude in Chat: [Suggests prompt improvements, provides examples]
```

**Iterate (Claude Code)**:
```
You: "Update prompt template with the improvements"

Claude Code: [Updates, tests again]
```

---

## Effective Claude Code Prompts

### ✅ Good Prompts (Specific & Actionable)

**Setup Tasks**:
```
"Initialize a new Python project named 'AnkiAI' using 
Poetry. Set Python version to ^3.11. Create the folder structure from 
the project instructions document. Add a .gitignore for Python projects."
```

**Implementation Tasks**:
```
"Implement the PDFParser class in src/domain/document_processing/pdf_parser.py.
It should:
- Accept file_path and page_range parameters
- Use PyMuPDF (fitz) for parsing
- Return a Document object
- Handle errors for invalid files/ranges
- Extract basic metadata

Also create unit tests in tests/unit/document_processing/test_pdf_parser.py"
```

**Debugging Tasks**:
```
"Run pytest on the document_processing module. If there are failures, 
analyze the errors and fix them. Show me what went wrong and what you fixed."
```

**Refactoring Tasks**:
```
"Refactor the Chunker class to use semantic chunking by paragraphs 
instead of fixed-size chunks. Update the tests accordingly."
```

### ❌ Poor Prompts (Too Vague)

```
"Set up the project"  
❌ Too vague - what language, structure, dependencies?

"Make it work"
❌ No context - what's broken?

"Add tests"
❌ For what? What kind of tests?

"Improve the code"
❌ Improve how? What's the goal?
```

### 🎯 Optimal Prompt Structure

```
[Action] + [Specific Component] + [Requirements/Constraints] + [Optional: Context]

Examples:

"Create [Action] 
the EmbeddingGenerator class [Specific Component]
that uses OpenAI's text-embedding-3-large model, handles batching, 
and includes error handling [Requirements]
as designed in the RAG architecture document [Context]"

"Debug [Action]
the VectorStore similarity search [Specific Component]
which is returning empty results [Issue]
by checking the embedding dimensions and query format [Direction]"
```

---

## Referencing Project Documents

All the project documents we've created are accessible. You can reference them:

**In Chat**:
```
"Looking at the Data Models document, should we add a 'priority' field 
to the Flashcard class?"
```

**In Claude Code**:
```
"Implement the Flashcard data model exactly as defined in the 
'Core Data Models' document"
```

```
"Follow the testing strategy from the 'Testing Strategy Guide' to 
create unit tests for the PDFParser"
```

```
"Use the prompt template from the 'Prompt Engineering Playbook' 
version 1.0 in the PromptBuilder class"
```

---

## Session Management

### Starting a New Session

**In Chat** (Start here):
```
You: "I'm ready to start implementing the document processing module. 
Let me switch to Claude Code."

Claude: "Great! Here's what to do in Claude Code:
1. Set up the module structure
2. Install PyMuPDF
3. Create the PDFParser class
4. Write initial tests

Your first Claude Code prompt should be: [specific prompt]"
```

**Then in Claude Code**:
```
You: [Use the suggested prompt]
```

### Continuing Work

**Resuming in Chat**:
```
You: "I've implemented the PDFParser in Claude Code. It works but 
I'm wondering about optimization strategies."

Claude: [Discusses optimization approaches]
```

**Back to Claude Code**:
```
You: "Apply the caching optimization we discussed"
```

### Context Switching

**Switching from Code to Chat**:
- When you hit a conceptual question
- When you need to make a decision
- When you want to understand why something works/doesn't work
- When you need architectural guidance

**Switching from Chat to Code**:
- When you're ready to implement
- When you have a clear specification
- When you need to debug a specific error
- When you want to run tests

---

## Common Workflows

### Workflow 1: Starting a New Module

1. **Chat**: Discuss module design and responsibilities
2. **Chat**: Review data models and interfaces needed
3. **Claude Code**: Create folder structure and skeleton files
4. **Claude Code**: Implement core functionality
5. **Claude Code**: Write and run unit tests
6. **Chat**: Review implementation and discuss improvements
7. **Claude Code**: Apply refinements

### Workflow 2: Debugging an Issue

1. **Claude Code**: Run tests/application, encounter error
2. **Chat**: Share error, get analysis and potential solutions
3. **Claude Code**: Try first solution
4. **Claude Code**: If not fixed, try alternative
5. **Chat**: If still stuck, discuss deeper architectural issues
6. **Claude Code**: Implement proper fix

### Workflow 3: Feature Development

1. **Chat**: Define requirements and acceptance criteria
2. **Chat**: Design the feature (data models, interfaces, flow)
3. **Claude Code**: Implement feature in small increments
4. **Claude Code**: Test each increment
5. **Chat**: Review overall implementation
6. **Claude Code**: Polish and optimize
7. **Claude Code**: Write comprehensive tests

### Workflow 4: Learning New Concept

1. **Chat**: "Explain how vector embeddings work"
2. **Chat**: "How do we apply this to our use case?"
3. **Chat**: "What libraries should we use?"
4. **Claude Code**: "Set up embedding generation with [library]"
5. **Claude Code**: "Test embedding generation on sample data"
6. **Chat**: "The results look like [X]. Is this correct?"
7. **Claude Code**: Adjust based on feedback

---

## Best Practices

### DO ✅

**In Chat**:
- ✅ Ask "why" questions
- ✅ Discuss multiple approaches before choosing
- ✅ Request explanations of complex concepts
- ✅ Review and critique code design
- ✅ Plan before implementing
- ✅ Discuss trade-offs

**In Claude Code**:
- ✅ Give specific, actionable instructions
- ✅ Reference project documents
- ✅ Ask to see output/results
- ✅ Request to run tests after changes
- ✅ Iterate quickly on implementation
- ✅ Ask for error analysis

### DON'T ❌

**In Chat**:
- ❌ Ask Claude to write full file contents (use Claude Code instead)
- ❌ Paste long code blocks for typing out (use Claude Code)
- ❌ Request file system operations (use Claude Code)

**In Claude Code**:
- ❌ Ask for lengthy conceptual explanations (use Chat)
- ❌ Request multiple unrelated changes at once
- ❌ Expect it to make architectural decisions (discuss in Chat first)

---

## Example: Complete Feature Development

Let's walk through implementing the Chunker module:

### Phase 1: Design (Chat)

**You**:
```
"We need to implement the Chunker. What chunking strategy should we use 
for technical books? Fixed-size or semantic?"
```

**Claude**:
```
For technical books, I recommend semantic chunking because:
1. Preserves context (doesn't split mid-concept)
2. Better for RAG retrieval
3. Respects document structure

We can chunk by:
- Paragraphs (most common)
- Sections (if detectable)
- With overlap for continuity

Let's start with paragraph-based chunking, ~800 tokens per chunk, 
100 token overlap.
```

**You**:
```
"Perfect. What should the interface look like?"
```

**Claude**:
```
Based on our data models:

class Chunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 100)
    def chunk(self, document: Document) -> List[Chunk]
    
Should:
- Preserve page numbers
- Generate unique chunk IDs
- Track position (first/last chunk flags)
- Handle edge cases (empty pages, very long paragraphs)
```

### Phase 2: Implementation (Claude Code)

**You in Claude Code**:
```
"Create the Chunker class in src/domain/document_processing/chunker.py 
following the design we discussed. 

Requirements:
- Chunk by paragraphs
- Default 800 tokens per chunk with 100 token overlap
- Track page numbers and position
- Generate unique chunk IDs
- Use the Chunk model from src/domain/models/chunk.py

Also create comprehensive unit tests."
```

**Claude Code**:
```
[Creates chunker.py with implementation]
[Creates test_chunker.py with tests]
[Runs tests]

✓ All tests pass
✓ Created 15 test cases covering:
  - Basic chunking
  - Overlap verification
  - Edge cases (empty input, single paragraph, etc.)
  - Metadata preservation
```

### Phase 3: Integration (Claude Code)

**You**:
```
"Now test the PDFParser → Chunker pipeline. Parse pages 1-5 from 
tests/fixtures/sample_book.pdf and chunk it. Show me the results."
```

**Claude Code**:
```
[Runs integration test]

Results:
- Parsed 5 pages
- Generated 12 chunks
- Average chunk size: 750 tokens
- All chunks have valid metadata
- Overlap verified between consecutive chunks

Sample chunk:
Chunk 0 (Page 1): "Introduction to Distributed Systems..."
Chunk 1 (Page 1-2): "...Systems. A distributed system is..." [shows overlap]
```

### Phase 4: Review (Chat)

**You**:
```
"The chunker works well but I'm concerned about very long paragraphs. 
What if a single paragraph is 2000 tokens?"
```

**Claude**:
```
Good catch! We should handle this:

Option 1: Split long paragraphs by sentences
Option 2: Hard split at token limit
Option 3: Split at sentence boundaries near limit

I recommend Option 3: respect sentence boundaries but enforce max size.

This requires:
1. Sentence tokenization
2. Token counting per sentence
3. Smart boundary detection
```

### Phase 5: Enhancement (Claude Code)

**You**:
```
"Add long paragraph handling to Chunker using Option 3. 
Split at sentence boundaries when exceeding chunk_size * 1.5"
```

**Claude Code**:
```
[Updates chunker.py]
[Adds new tests for long paragraphs]
[Runs all tests]

✓ All tests pass including new long paragraph cases
✓ Max chunk size now enforced: 1200 tokens (800 * 1.5)
```

### Phase 6: Documentation (Claude Code)

**You**:
```
"Add comprehensive docstrings to the Chunker class explaining 
the chunking strategy and parameters"
```

**Claude Code**:
```
[Adds detailed docstrings]
[Updates README if needed]

Done! Chunker is now fully documented.
```

---

## Advanced Patterns

### Pattern: Rapid Prototyping

**Goal**: Quickly test an idea

1. **Chat**: "I want to try using sentence-transformers instead of OpenAI embeddings. Thoughts?"
2. **Chat**: [Discussion of pros/cons]
3. **Claude Code**: "Create a prototype SentenceTransformerEmbedder class"
4. **Claude Code**: "Test it on 10 sample chunks and compare results"
5. **Chat**: "Here are the results. Which should we use?"
6. **Chat**: [Decision]
7. **Claude Code**: "Implement the chosen approach properly"

### Pattern: Test-Driven Development

1. **Chat**: "What tests should we write for the QualityChecker?"
2. **Chat**: [Discusses test cases]
3. **Claude Code**: "Write the test cases we discussed (they'll fail)"
4. **Claude Code**: "Now implement QualityChecker to make tests pass"
5. **Claude Code**: "Refactor while keeping tests green"

### Pattern: Performance Optimization

1. **Claude Code**: "Run performance benchmark on embedding generation"
2. **Chat**: "Results show 2 seconds per chunk. That's slow. Ideas?"
3. **Chat**: [Discusses batching, caching, parallelization]
4. **Claude Code**: "Implement batch processing for embeddings"
5. **Claude Code**: "Re-run benchmark"
6. **Chat**: "Now 0.3 seconds per chunk. Good enough or optimize more?"

---

## Troubleshooting

### Issue: Claude Code Can't Find Files

**Problem**: "File not found: src/domain/models/document.py"

**Solution in Claude Code**:
```
"Show me the current directory structure"
[Identifies issue]
"Create the missing file/folder"
```

### Issue: Tests Failing After Change

**In Claude Code**:
```
"Run the full test suite and show me all failures"
[See errors]
```

**In Chat**:
```
"These tests are failing: [paste errors]. What's the root cause?"
[Analysis and solution]
```

**Back in Claude Code**:
```
"Fix the issues we identified"
```

### Issue: Unclear What to Do Next

**In Chat**:
```
"We've implemented PDFParser and Chunker. What should we do next 
according to the roadmap?"

Claude: "According to the learning roadmap, Week 1 Phase 3 is 
'First Integration Test'. You should:
1. Create a test that combines PDFParser + Chunker
2. Verify the full pipeline works
3. Then move to Week 2: RAG implementation

Your next Claude Code prompt should be: [specific prompt]"
```

---

## Quick Reference

### When to Use Chat
- 🤔 Making decisions
- 📚 Learning concepts  
- 🎯 Planning features
- 🔍 Reviewing designs
- ⚖️ Comparing options
- 💭 Understanding "why"

### When to Use Claude Code
- 💻 Writing code
- 🧪 Running tests
- 🐛 Fixing bugs
- 📦 Installing packages
- 🏗️ Creating files/folders
- 🚀 Running programs

### Switching Triggers

**Chat → Claude Code**:
- "Let's implement that"
- "I'm ready to code"
- "Show me if it works"

**Claude Code → Chat**:
- "Why isn't this working?"
- "What's the best approach?"
- "Should we do X or Y?"

---

## Your First Session

### Recommended First Steps

**1. Start in Chat** (this conversation):
```
You: "I'm ready to begin. What should be my first Claude Code prompt?"
```

**2. Go to Claude Code**:
```
Your first prompt: "Initialize the Anki Flashcard Generator project 
using Poetry with Python 3.11+. Create the complete folder structure 
from the project instructions. Set up git with appropriate .gitignore. 
Install initial dependencies: pytest, black, ruff."
```

**3. Back to Chat**:
```
You: "Project setup complete. Ready for next step."

Claude: "Great! Now let's implement the first module: PDFParser..."
```

**4. Continue Alternating**:
- Chat for planning each module
- Claude Code for implementing
- Chat for reviewing
- Claude Code for refining

---

## Success Metrics

You're using the workflow effectively when:

✅ You plan in Chat before coding in Claude Code
✅ You implement in Claude Code after designing in Chat
✅ You debug errors by discussing in Chat, fixing in Claude Code
✅ You iterate quickly between the two interfaces
✅ You reference project documents in both places
✅ Your code is clean because you thought through the design first

---

## Remember

**This Chat**: Your strategic thinking partner
**Claude Code**: Your implementation partner

Together, they form a complete development environment that combines:
- 🧠 Strategic thinking + 💪 Execution power
- 📖 Learning + 🛠️ Building
- 🎨 Design + ⚙️ Implementation

Use both effectively and you'll build better software faster! 🚀