"""Flashcard generation service orchestrating the full pipeline."""

import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.domain.document_processing.pdf_parser import PDFParser
from src.domain.generation.claude_client import ClaudeClient
from src.domain.generation.prompt_builder import PromptBuilder
from src.domain.models.document import (
    Document,
    FlashcardResult,
    GenerationResult,
    ProcessingStatus,
)
from src.domain.output.anki_formatter import AnkiFormatter
from src.domain.rag.chunker import Chunker
from src.domain.rag.context_builder import ContextBuilder
from src.domain.rag.embeddings import EmbeddingGenerator
from src.domain.rag.retriever import Retriever
from src.domain.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG-based flashcard generation.

    Attributes:
        top_k: Number of chunks to retrieve for context (default: 5)
        chunk_target_size: Target token size for chunks (default: 800)
        chunk_overlap_size: Overlap between chunks in tokens (default: 100)
        include_metadata: Include source metadata in context (default: False)
    """

    top_k: int = 5
    chunk_target_size: int = 800
    chunk_overlap_size: int = 100
    include_metadata: bool = False


@dataclass
class RAGSetupResult:
    """Result from RAG setup phase.

    Attributes:
        success: Whether setup completed successfully
        num_chunks: Number of chunks created
        embedding_tokens: Tokens used for embedding generation
        embedding_cost: Cost of embedding generation in USD
        collection_name: Name of the vector store collection
        error_message: Error message if setup failed
    """

    success: bool
    num_chunks: int = 0
    embedding_tokens: int = 0
    embedding_cost: float = 0.0
    collection_name: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class RAGGenerationMetadata:
    """Metadata about RAG generation for a single flashcard.

    Attributes:
        chunks_retrieved: Number of chunks retrieved
        top_chunk_scores: Similarity scores of top chunks
        query_used: The query used for retrieval
        context_tokens: Estimated tokens in context
    """

    chunks_retrieved: int = 0
    top_chunk_scores: List[float] = field(default_factory=list)
    query_used: str = ""
    context_tokens: int = 0


# Type alias for progress callback
ProgressCallback = Callable[[int, int, str], None]


class FlashcardGeneratorService:
    """Orchestrates the flashcard generation pipeline.

    This service coordinates:
    1. PDF parsing and text extraction
    2. Prompt building for each page
    3. Claude API calls for flashcard generation
    4. Anki deck creation and export

    Supports two modes:
    - Baseline: Uses full page text for generation (original Week 1 approach)
    - RAG: Uses retrieval-augmented generation with semantic chunking

    Design decisions:
    - Continues on single-page failures (partial results better than none)
    - Tracks costs and tokens across all operations
    - Supports progress callbacks for CLI/UI updates
    - Creates fresh client instance for clean token tracking
    - RAG mode: Parse once, chunk, embed, index, then retrieve per page
    """

    def __init__(self):
        """Initialize the service with fresh component instances."""
        self.claude_client = ClaudeClient()
        self._embedding_generator: Optional[EmbeddingGenerator] = None
        self._vector_store: Optional[VectorStore] = None
        self._retriever: Optional[Retriever] = None
        self._rag_setup_result: Optional[RAGSetupResult] = None
        logger.info("FlashcardGeneratorService initialized")

    def _get_collection_name(self, pdf_path: str) -> str:
        """Generate a unique collection name for a PDF.

        Uses a hash of the file path to create a unique, deterministic name.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Collection name suitable for ChromaDB
        """
        # Use file path hash for uniqueness
        path_hash = hashlib.md5(pdf_path.encode()).hexdigest()[:8]
        filename = Path(pdf_path).stem
        # Sanitize filename for collection name
        safe_name = "".join(c if c.isalnum() else "_" for c in filename)[:20]
        return f"ankiai_{safe_name}_{path_hash}"

    def _setup_rag(
        self,
        document: Document,
        rag_config: RAGConfig,
        on_progress: Optional[ProgressCallback] = None,
    ) -> RAGSetupResult:
        """Set up RAG components: chunk, embed, and index the document.

        This is the "expensive" setup phase that should only be done once
        per document.

        Args:
            document: Parsed document to index
            rag_config: RAG configuration settings
            on_progress: Optional progress callback

        Returns:
            RAGSetupResult with setup outcome and statistics
        """
        try:
            if on_progress:
                on_progress(0, 100, "Starting RAG setup: chunking document...")

            # Step 1: Chunk the document
            logger.info(f"Chunking document: {document.file_path}")
            chunks = Chunker.chunk(
                document=document,
                target_size=rag_config.chunk_target_size,
                overlap_size=rag_config.chunk_overlap_size,
            )

            if not chunks:
                return RAGSetupResult(
                    success=False,
                    error_message="No chunks created from document",
                )

            logger.info(f"Created {len(chunks)} chunks")

            if on_progress:
                on_progress(
                    30,
                    100,
                    f"Chunking complete: {len(chunks)} chunks. Generating embeddings...",
                )

            # Step 2: Generate embeddings
            logger.info("Generating embeddings for chunks")
            self._embedding_generator = EmbeddingGenerator()
            self._embedding_generator.generate_embeddings(chunks)

            embedding_stats = self._embedding_generator.get_usage_stats()
            logger.info(
                f"Embeddings generated. Tokens: {embedding_stats['total_tokens']}, "
                f"Cost: ${embedding_stats['estimated_cost']:.4f}"
            )

            if on_progress:
                on_progress(
                    70, 100, "Embeddings generated. Indexing in vector store..."
                )

            # Step 3: Index in vector store
            collection_name = self._get_collection_name(document.file_path)
            logger.info(f"Creating vector store collection: {collection_name}")

            # Use a temporary directory for experiments to avoid polluting main store
            self._vector_store = VectorStore(collection_name=collection_name)

            # Clear any existing chunks for this document (in case of re-run)
            self._vector_store.delete_by_source(document.file_path)

            # Add chunks to store
            self._vector_store.add_chunks(chunks)
            logger.info(f"Indexed {len(chunks)} chunks in vector store")

            # Step 4: Create retriever
            self._retriever = Retriever(
                vector_store=self._vector_store,
                embedding_generator=self._embedding_generator,
            )

            if on_progress:
                on_progress(100, 100, "RAG setup complete")

            return RAGSetupResult(
                success=True,
                num_chunks=len(chunks),
                embedding_tokens=embedding_stats["total_tokens"],
                embedding_cost=embedding_stats["estimated_cost"],
                collection_name=collection_name,
            )

        except Exception as e:
            logger.error(f"RAG setup failed: {e}")
            return RAGSetupResult(
                success=False,
                error_message=str(e),
            )

    def _build_retrieval_query(self, page_text: str, page_num: int) -> str:
        """Build a query for retrieving relevant chunks.

        Query strategy: Use a combination of explicit page reference and
        a summarized query. The page text itself provides semantic context
        for finding related content.

        Args:
            page_text: Text content from the current page
            page_num: Page number (1-indexed)

        Returns:
            Query string for retrieval
        """
        # Use first ~200 chars of page text as semantic anchor
        # This helps find contextually similar content
        text_preview = page_text[:500].strip()
        if len(page_text) > 500:
            text_preview += "..."

        # Build a query that combines semantic content with explicit context
        query = f"Key concepts and information for creating educational flashcards: {text_preview}"

        return query

    def _retrieve_context_for_page(
        self,
        page_text: str,
        page_num: int,
        rag_config: RAGConfig,
    ) -> tuple[str, RAGGenerationMetadata]:
        """Retrieve relevant context for a page using RAG.

        Args:
            page_text: Text content from the current page
            page_num: Page number (1-indexed)
            rag_config: RAG configuration

        Returns:
            Tuple of (context_string, metadata)
        """
        if self._retriever is None:
            raise RuntimeError("RAG not set up. Call _setup_rag first.")

        # Build query
        query = self._build_retrieval_query(page_text, page_num)

        # Retrieve chunks
        results = self._retriever.retrieve_with_scores(
            query=query,
            top_k=rag_config.top_k,
        )

        if not results:
            logger.warning(f"No chunks retrieved for page {page_num}")
            return page_text, RAGGenerationMetadata(
                chunks_retrieved=0,
                query_used=query,
            )

        # Build context from retrieved chunks
        chunks = [r.chunk for r in results]
        scores = [r.score for r in results]

        context = ContextBuilder.build_context(
            chunks=chunks,
            include_metadata=rag_config.include_metadata,
        )

        # Estimate tokens in context
        context_tokens = ContextBuilder.estimate_tokens(
            chunks=chunks,
            include_metadata=rag_config.include_metadata,
        )

        metadata = RAGGenerationMetadata(
            chunks_retrieved=len(chunks),
            top_chunk_scores=scores,
            query_used=query,
            context_tokens=context_tokens,
        )

        logger.debug(
            f"Retrieved {len(chunks)} chunks for page {page_num} "
            f"(top score: {scores[0]:.3f})"
        )

        return context, metadata

    def _cleanup_rag(self) -> None:
        """Clean up RAG resources after generation."""
        if self._vector_store is not None:
            try:
                self._vector_store.clear()
                logger.debug("Cleared vector store")
            except Exception as e:
                logger.warning(f"Failed to clean up vector store: {e}")

        self._embedding_generator = None
        self._vector_store = None
        self._retriever = None
        self._rag_setup_result = None

    def generate_flashcards(
        self,
        pdf_path: str,
        page_range: tuple,
        cards_per_page: int = 1,
        difficulty: str = "intermediate",
        output_path: str = "flashcards.apkg",
        on_progress: Optional[ProgressCallback] = None,
        use_rag: bool = False,
        rag_config: Optional[RAGConfig] = None,
    ) -> GenerationResult:
        """Generate flashcards from PDF and save to Anki format.

        Supports two modes:
        - Baseline (use_rag=False): Uses full page text for generation
        - RAG (use_rag=True): Uses retrieval-augmented generation

        Args:
            pdf_path: Path to PDF file
            page_range: (start, end) page numbers (1-indexed, inclusive)
            cards_per_page: Number of flashcards per page
            difficulty: Difficulty level for flashcards (beginner/intermediate/advanced)
            output_path: Where to save .apkg file
            on_progress: Optional callback(current, total, message) for progress updates
            use_rag: If True, use RAG mode; if False, use baseline mode
            rag_config: Configuration for RAG mode (optional, uses defaults if None)

        Returns:
            GenerationResult with flashcards, statistics, and status

        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If page range is invalid
        """
        start_page, end_page = page_range
        total_pages = end_page - start_page + 1

        mode_str = "RAG" if use_rag else "baseline"
        logger.info(
            f"Starting flashcard generation ({mode_str} mode): {pdf_path} "
            f"(pages {start_page}-{end_page}, {cards_per_page} cards/page)"
        )

        # Reset token tracking for fresh stats
        self.claude_client.reset_stats()

        # Use default RAG config if not provided
        if use_rag and rag_config is None:
            rag_config = RAGConfig()

        # RAG Setup Phase (if enabled)
        rag_metadata: Dict[str, Any] = {}
        if use_rag:
            if on_progress:
                on_progress(0, 100, "RAG mode: Parsing full document...")

            try:
                # Parse the full document for RAG indexing
                full_doc = PDFParser.parse(
                    pdf_path, start_page=start_page, end_page=end_page
                )

                # Run RAG setup
                def rag_progress(current: int, total: int, msg: str) -> None:
                    # Scale RAG setup progress to 0-30% of total
                    if on_progress:
                        scaled = int(current * 0.3)
                        on_progress(scaled, 100, f"RAG setup: {msg}")

                self._rag_setup_result = self._setup_rag(
                    document=full_doc,
                    rag_config=rag_config,
                    on_progress=rag_progress,
                )

                if not self._rag_setup_result.success:
                    logger.error(
                        f"RAG setup failed: {self._rag_setup_result.error_message}"
                    )
                    # Fall back to baseline mode
                    logger.warning("Falling back to baseline mode")
                    use_rag = False
                else:
                    rag_metadata = {
                        "num_chunks": self._rag_setup_result.num_chunks,
                        "embedding_tokens": self._rag_setup_result.embedding_tokens,
                        "embedding_cost": self._rag_setup_result.embedding_cost,
                        "top_k": rag_config.top_k,
                    }

            except Exception as e:
                logger.error(f"RAG setup failed with exception: {e}")
                logger.warning("Falling back to baseline mode")
                use_rag = False

        # Collect results
        all_flashcards: List[dict] = []
        page_results: List[FlashcardResult] = []
        failed_count = 0
        success_count = 0

        # Calculate progress scaling for generation phase
        # RAG mode: generation is 30-100% (70% of total)
        # Baseline mode: generation is 0-100% (100% of total)
        progress_start = 30 if use_rag else 0
        progress_range = 70 if use_rag else 100

        # Process each page
        for page_idx, page_num in enumerate(range(start_page, end_page + 1)):
            current = page_idx + 1

            # Report progress
            if on_progress:
                progress_pct = progress_start + int(
                    (current / total_pages) * progress_range
                )
                on_progress(progress_pct, 100, f"Processing page {page_num}...")

            # Extract text for this specific page
            try:
                doc = PDFParser.parse(pdf_path, start_page=page_num, end_page=page_num)
                page_text = doc.content
            except Exception as e:
                logger.error(f"Failed to parse page {page_num}: {e}")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message=f"PDF parsing error: {str(e)}",
                    )
                )
                failed_count += 1
                continue

            # Skip empty pages
            if not page_text.strip():
                logger.warning(f"Page {page_num} has no text content, skipping")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message="Page has no text content",
                    )
                )
                failed_count += 1
                continue

            # Get context for generation
            generation_context = page_text
            rag_gen_metadata = None

            if use_rag and self._retriever is not None:
                try:
                    generation_context, rag_gen_metadata = (
                        self._retrieve_context_for_page(
                            page_text=page_text,
                            page_num=page_num,
                            rag_config=rag_config,
                        )
                    )
                except Exception as e:
                    logger.warning(
                        f"RAG retrieval failed for page {page_num}: {e}, using page text"
                    )
                    generation_context = page_text

            # Build prompt and generate flashcard
            try:
                prompt = PromptBuilder.build_flashcard_prompt(
                    context=generation_context,
                    difficulty=difficulty,
                    num_cards=cards_per_page,
                )

                # Get usage stats before call for delta calculation
                stats_before = self.claude_client.get_usage_stats()
                tokens_before = stats_before["total_tokens"]

                # Generate flashcard(s)
                result = self.claude_client.generate_flashcard(prompt)

                # Calculate tokens used for this call
                stats_after = self.claude_client.get_usage_stats()
                tokens_used = stats_after["total_tokens"] - tokens_before

                # Calculate cost for this call
                input_delta = (
                    stats_after["total_input_tokens"]
                    - stats_before["total_input_tokens"]
                )
                output_delta = (
                    stats_after["total_output_tokens"]
                    - stats_before["total_output_tokens"]
                )
                cost = (
                    input_delta / 1_000_000 * ClaudeClient.PRICE_PER_MILLION_INPUT
                    + output_delta / 1_000_000 * ClaudeClient.PRICE_PER_MILLION_OUTPUT
                )

                # Normalize result to list
                if isinstance(result, dict):
                    flashcards = [result]
                else:
                    flashcards = result

                # Add page reference and RAG metadata to each flashcard
                for card in flashcards:
                    card["source_page"] = page_num
                    if rag_gen_metadata:
                        card["rag_metadata"] = {
                            "chunks_retrieved": rag_gen_metadata.chunks_retrieved,
                            "top_scores": rag_gen_metadata.top_chunk_scores[
                                :3
                            ],  # Top 3 scores
                            "context_tokens": rag_gen_metadata.context_tokens,
                        }

                all_flashcards.extend(flashcards)

                page_results.append(
                    FlashcardResult(
                        flashcards=flashcards,
                        page_number=page_num,
                        success=True,
                        tokens_used=tokens_used,
                        cost_usd=round(cost, 6),
                    )
                )
                success_count += 1

                logger.info(
                    f"Generated {len(flashcards)} flashcard(s) for page {page_num}"
                )

            except Exception as e:
                logger.error(f"Failed to generate flashcard for page {page_num}: {e}")
                page_results.append(
                    FlashcardResult(
                        flashcards=[],
                        page_number=page_num,
                        success=False,
                        error_message=str(e),
                    )
                )
                failed_count += 1

        # Clean up RAG resources
        if use_rag:
            self._cleanup_rag()

        # Get final usage stats
        final_stats = self.claude_client.get_usage_stats()

        # Add embedding cost if RAG was used
        total_cost = final_stats["estimated_cost"]
        if rag_metadata.get("embedding_cost"):
            total_cost += rag_metadata["embedding_cost"]

        # Determine overall status
        if success_count == 0:
            status = ProcessingStatus.FAILED
        elif failed_count > 0:
            status = ProcessingStatus.PARTIAL
        else:
            status = ProcessingStatus.SUCCESS

        # Format to Anki if we have any flashcards
        final_output_path = None
        if all_flashcards:
            try:
                # Create tags from metadata
                source_filename = Path(pdf_path).name
                tags = AnkiFormatter.create_tags_from_metadata(
                    source_filename=source_filename,
                    page_range=page_range,
                    difficulty=difficulty,
                )
                # Add RAG tag if applicable
                if use_rag:
                    tags.append(f"rag_k{rag_config.top_k}")

                # Create deck name from filename
                deck_name = f"AnkiAI - {Path(pdf_path).stem}"

                final_output_path = AnkiFormatter.format_flashcards(
                    flashcards=all_flashcards,
                    deck_name=deck_name,
                    tags=tags,
                    output_path=output_path,
                )

                logger.info(f"Created Anki deck: {final_output_path}")

            except Exception as e:
                logger.error(f"Failed to create Anki deck: {e}")
                # Don't fail the whole result, just note the error
                if status == ProcessingStatus.SUCCESS:
                    status = ProcessingStatus.PARTIAL

        result = GenerationResult(
            flashcards=all_flashcards,
            results=page_results,
            total_attempted=total_pages,
            total_success=success_count,
            total_failed=failed_count,
            total_tokens=final_stats["total_tokens"],
            total_cost_usd=round(total_cost, 4),
            status=status,
            output_path=final_output_path,
        )

        logger.info(
            f"Generation complete ({mode_str} mode): {success_count}/{total_pages} successful, "
            f"{len(all_flashcards)} flashcards, ${total_cost:.4f}"
        )

        return result
