#!/usr/bin/env python3
"""Experiment runner for comparing RAG configurations.

This script systematically tests different flashcard generation configurations
and saves results for manual analysis.

Configurations tested:
- baseline: No RAG, uses full page text
- rag_k1: RAG with top_k=1
- rag_k3: RAG with top_k=3
- rag_k5: RAG with top_k=5
- rag_k10: RAG with top_k=10

Usage:
    python experiments/run_experiments.py [--pdf-path PATH] [--pages START END]
    poetry run python experiments/run_experiments.py

Example:
    python experiments/run_experiments.py --pdf-path tests/sample_data/DDIA.pdf --pages 1 5
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.application.flashcard_service import (  # noqa: E402
    FlashcardGeneratorService,
    RAGConfig,
)
from src.domain.models.document import GenerationResult  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class ExperimentConfig:
    """Configuration for a single experiment run.

    Attributes:
        name: Configuration name (e.g., "baseline", "rag_k5")
        use_rag: Whether to use RAG mode
        top_k: Number of chunks to retrieve (only used if use_rag=True)
        description: Human-readable description
    """

    name: str
    use_rag: bool
    top_k: int = 5
    description: str = ""


@dataclass
class ExperimentResult:
    """Result from a single experiment run.

    Attributes:
        config_name: Configuration name
        flashcards: Generated flashcards
        generation_result: Full GenerationResult object
        total_time_seconds: Time taken for generation
        setup_time_seconds: Time for RAG setup (if applicable)
        generation_time_seconds: Time for flashcard generation
        error: Error message if experiment failed
    """

    config_name: str
    flashcards: List[Dict[str, Any]]
    generation_result: Optional[GenerationResult]
    total_time_seconds: float
    setup_time_seconds: float = 0.0
    generation_time_seconds: float = 0.0
    error: Optional[str] = None

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary for JSON serialization."""
        result = self.generation_result
        return {
            "config_name": self.config_name,
            "num_flashcards": len(self.flashcards),
            "total_time_seconds": round(self.total_time_seconds, 2),
            "setup_time_seconds": round(self.setup_time_seconds, 2),
            "generation_time_seconds": round(self.generation_time_seconds, 2),
            "total_tokens": result.total_tokens if result else 0,
            "total_cost_usd": result.total_cost_usd if result else 0,
            "success_rate": result.get_success_rate() if result else 0,
            "status": result.status.value if result else "error",
            "error": self.error,
        }


# Define experiment configurations
EXPERIMENT_CONFIGS = [
    ExperimentConfig(
        name="baseline",
        use_rag=False,
        description="Baseline: Full page text without RAG",
    ),
    ExperimentConfig(
        name="rag_k1",
        use_rag=True,
        top_k=1,
        description="RAG with top_k=1 (single most relevant chunk)",
    ),
    ExperimentConfig(
        name="rag_k3",
        use_rag=True,
        top_k=3,
        description="RAG with top_k=3 (three most relevant chunks)",
    ),
    ExperimentConfig(
        name="rag_k5",
        use_rag=True,
        top_k=5,
        description="RAG with top_k=5 (default, five most relevant chunks)",
    ),
    ExperimentConfig(
        name="rag_k10",
        use_rag=True,
        top_k=10,
        description="RAG with top_k=10 (ten most relevant chunks)",
    ),
]


class ExperimentRunner:
    """Runs and manages experiments for comparing configurations."""

    def __init__(
        self,
        pdf_path: str,
        page_range: tuple,
        output_dir: Optional[str] = None,
        cards_per_page: int = 1,
        difficulty: str = "intermediate",
    ):
        """Initialize the experiment runner.

        Args:
            pdf_path: Path to PDF file for experiments
            page_range: (start, end) page numbers (1-indexed, inclusive)
            output_dir: Directory to save results (auto-generated if None)
            cards_per_page: Number of flashcards per page
            difficulty: Difficulty level for flashcards
        """
        self.pdf_path = pdf_path
        self.page_range = page_range
        self.cards_per_page = cards_per_page
        self.difficulty = difficulty

        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        if output_dir is None:
            output_dir = str(project_root / "experiments" / f"results_{timestamp}")

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store results
        self.results: List[ExperimentResult] = []

        logger.info("Experiment runner initialized")
        logger.info(f"  PDF: {pdf_path}")
        logger.info(f"  Pages: {page_range[0]}-{page_range[1]}")
        logger.info(f"  Output: {self.output_dir}")

    def run_single_experiment(
        self,
        config: ExperimentConfig,
    ) -> ExperimentResult:
        """Run a single experiment with the given configuration.

        Args:
            config: Experiment configuration

        Returns:
            ExperimentResult with outcomes and metrics
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Running experiment: {config.name}")
        logger.info(f"Description: {config.description}")
        logger.info(f"{'='*60}")

        start_time = time.time()

        try:
            # Create fresh service instance for each experiment
            service = FlashcardGeneratorService()

            # Configure RAG if enabled
            rag_config = None
            if config.use_rag:
                rag_config = RAGConfig(top_k=config.top_k)

            # Progress callback for logging
            def progress_callback(current: int, total: int, message: str) -> None:
                logger.info(f"  [{current}/{total}] {message}")

            # Run generation
            generation_start = time.time()
            result = service.generate_flashcards(
                pdf_path=self.pdf_path,
                page_range=self.page_range,
                cards_per_page=self.cards_per_page,
                difficulty=self.difficulty,
                output_path=str(self.output_dir / config.name / "flashcards.apkg"),
                on_progress=progress_callback,
                use_rag=config.use_rag,
                rag_config=rag_config,
            )
            generation_time = time.time() - generation_start

            total_time = time.time() - start_time

            logger.info(f"\nExperiment {config.name} completed:")
            logger.info(f"  Flashcards: {len(result.flashcards)}")
            logger.info(f"  Status: {result.status.value}")
            logger.info(f"  Tokens: {result.total_tokens}")
            logger.info(f"  Cost: ${result.total_cost_usd:.4f}")
            logger.info(f"  Time: {total_time:.1f}s")

            return ExperimentResult(
                config_name=config.name,
                flashcards=result.flashcards,
                generation_result=result,
                total_time_seconds=total_time,
                generation_time_seconds=generation_time,
            )

        except Exception as e:
            logger.error(f"Experiment {config.name} failed: {e}")
            import traceback

            traceback.print_exc()

            return ExperimentResult(
                config_name=config.name,
                flashcards=[],
                generation_result=None,
                total_time_seconds=time.time() - start_time,
                error=str(e),
            )

    def run_all_experiments(
        self,
        configs: Optional[List[ExperimentConfig]] = None,
    ) -> List[ExperimentResult]:
        """Run all experiment configurations.

        Args:
            configs: List of configurations to run (defaults to EXPERIMENT_CONFIGS)

        Returns:
            List of ExperimentResults
        """
        if configs is None:
            configs = EXPERIMENT_CONFIGS

        logger.info(f"\n{'#'*60}")
        logger.info(f"Starting experiment suite with {len(configs)} configurations")
        logger.info(f"{'#'*60}\n")

        self.results = []

        for i, config in enumerate(configs, 1):
            logger.info(f"\n[Experiment {i}/{len(configs)}]")
            result = self.run_single_experiment(config)
            self.results.append(result)

            # Save intermediate results
            self._save_experiment_result(result, config)

        # Save summary
        self._save_summary()

        logger.info(f"\n{'#'*60}")
        logger.info("All experiments completed!")
        logger.info(f"Results saved to: {self.output_dir}")
        logger.info(f"{'#'*60}")

        return self.results

    def _save_experiment_result(
        self,
        result: ExperimentResult,
        config: ExperimentConfig,
    ) -> None:
        """Save results for a single experiment.

        Args:
            result: Experiment result
            config: Experiment configuration
        """
        config_dir = self.output_dir / config.name
        config_dir.mkdir(parents=True, exist_ok=True)

        # Save flashcards as JSON
        flashcards_path = config_dir / "flashcards.json"
        with open(flashcards_path, "w") as f:
            json.dump(result.flashcards, f, indent=2)

        # Save readable markdown
        markdown_path = config_dir / "flashcards_readable.md"
        with open(markdown_path, "w") as f:
            f.write(f"# Flashcards - {config.name}\n\n")
            f.write(f"**Configuration:** {config.description}\n\n")
            f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
            f.write("---\n\n")

            for i, card in enumerate(result.flashcards, 1):
                f.write(f"## Card {i} (Page {card.get('source_page', 'unknown')})\n\n")
                f.write(f"**Question:**\n{card.get('question', 'N/A')}\n\n")
                f.write(f"**Answer:**\n{card.get('answer', 'N/A')}\n\n")

                # Include RAG metadata if present
                if "rag_metadata" in card:
                    meta = card["rag_metadata"]
                    f.write("**RAG Metadata:**\n")
                    f.write(f"- Chunks retrieved: {meta.get('chunks_retrieved', 0)}\n")
                    f.write(f"- Top scores: {meta.get('top_scores', [])}\n")
                    f.write(f"- Context tokens: {meta.get('context_tokens', 0)}\n")
                    f.write("\n")

                f.write("---\n\n")

        # Save summary for this config
        summary_path = config_dir / "summary.txt"
        summary = result.to_summary_dict()
        with open(summary_path, "w") as f:
            f.write(f"Experiment Summary: {config.name}\n")
            f.write(f"{'='*40}\n\n")
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")

        logger.info(f"Saved results for {config.name} to {config_dir}")

    def _save_summary(self) -> None:
        """Save overall summary comparing all configurations."""
        summary_path = self.output_dir / "summary_all_configs.md"

        with open(summary_path, "w") as f:
            f.write("# Experiment Summary\n\n")
            f.write(f"**PDF:** {self.pdf_path}\n")
            f.write(f"**Pages:** {self.page_range[0]}-{self.page_range[1]}\n")
            f.write(f"**Cards per page:** {self.cards_per_page}\n")
            f.write(f"**Difficulty:** {self.difficulty}\n")
            f.write(f"**Run date:** {datetime.now().isoformat()}\n\n")

            f.write("## Results Comparison\n\n")
            f.write("| Config | Flashcards | Tokens | Cost ($) | Time (s) | Status |\n")
            f.write("|--------|------------|--------|----------|----------|--------|\n")

            for result in self.results:
                summary = result.to_summary_dict()
                f.write(
                    f"| {summary['config_name']} "
                    f"| {summary['num_flashcards']} "
                    f"| {summary['total_tokens']} "
                    f"| {summary['total_cost_usd']:.4f} "
                    f"| {summary['total_time_seconds']:.1f} "
                    f"| {summary['status']} |\n"
                )

            f.write("\n## Configuration Details\n\n")
            for config in EXPERIMENT_CONFIGS:
                f.write(f"- **{config.name}**: {config.description}\n")

            f.write("\n## Notes\n\n")
            f.write("- Review flashcards manually to assess quality\n")
            f.write("- Consider acceptance rate (% of cards you would keep)\n")
            f.write("- Note any patterns in RAG vs baseline quality\n")

        # Also save as JSON for programmatic access
        json_path = self.output_dir / "summary.json"
        summary_data = {
            "experiment_params": {
                "pdf_path": self.pdf_path,
                "page_range": list(self.page_range),
                "cards_per_page": self.cards_per_page,
                "difficulty": self.difficulty,
                "run_date": datetime.now().isoformat(),
            },
            "results": [r.to_summary_dict() for r in self.results],
        }
        with open(json_path, "w") as f:
            json.dump(summary_data, f, indent=2)

        logger.info(f"Saved summary to {summary_path}")


def find_test_pdf() -> Optional[str]:
    """Find a suitable test PDF in the project.

    Returns:
        Path to test PDF if found, None otherwise
    """
    # Check for sample data
    sample_paths = [
        project_root / "tests" / "sample_data" / "DDIA.pdf",
        project_root / "tests" / "fixtures" / "sample_technical.pdf",
    ]

    for path in sample_paths:
        if path.exists():
            return str(path)

    return None


def main():
    """Main entry point for experiment runner."""
    parser = argparse.ArgumentParser(
        description="Run flashcard generation experiments comparing RAG configurations"
    )
    parser.add_argument(
        "--pdf-path",
        type=str,
        help="Path to PDF file for experiments",
    )
    parser.add_argument(
        "--pages",
        type=int,
        nargs=2,
        default=[1, 5],
        metavar=("START", "END"),
        help="Page range to process (default: 1 5)",
    )
    parser.add_argument(
        "--cards-per-page",
        type=int,
        default=1,
        help="Number of flashcards per page (default: 1)",
    )
    parser.add_argument(
        "--difficulty",
        type=str,
        default="intermediate",
        choices=["beginner", "intermediate", "advanced"],
        help="Flashcard difficulty level (default: intermediate)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for results (auto-generated if not specified)",
    )
    parser.add_argument(
        "--configs",
        type=str,
        nargs="+",
        help="Specific configurations to run (default: all)",
    )

    args = parser.parse_args()

    # Find PDF
    pdf_path = args.pdf_path
    if pdf_path is None:
        pdf_path = find_test_pdf()
        if pdf_path is None:
            logger.error(
                "No PDF path specified and no test PDF found. "
                "Use --pdf-path to specify a PDF file."
            )
            sys.exit(1)
        logger.info(f"Using test PDF: {pdf_path}")

    if not Path(pdf_path).exists():
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)

    # Filter configs if specified
    configs = EXPERIMENT_CONFIGS
    if args.configs:
        config_names = set(args.configs)
        configs = [c for c in EXPERIMENT_CONFIGS if c.name in config_names]
        if not configs:
            logger.error(
                f"No valid configurations found. Available: {[c.name for c in EXPERIMENT_CONFIGS]}"
            )
            sys.exit(1)

    # Create runner
    runner = ExperimentRunner(
        pdf_path=pdf_path,
        page_range=tuple(args.pages),
        output_dir=args.output_dir,
        cards_per_page=args.cards_per_page,
        difficulty=args.difficulty,
    )

    # Run experiments
    results = runner.run_all_experiments(configs)

    # Print summary
    print("\n" + "=" * 60)
    print("EXPERIMENT SUMMARY")
    print("=" * 60)
    print(f"\nResults saved to: {runner.output_dir}\n")

    for result in results:
        summary = result.to_summary_dict()
        status_emoji = (
            "✅"
            if summary["status"] == "success"
            else "⚠️" if summary["status"] == "partial" else "❌"
        )
        print(
            f"{status_emoji} {summary['config_name']:12} | "
            f"{summary['num_flashcards']:2} cards | "
            f"${summary['total_cost_usd']:.4f} | "
            f"{summary['total_time_seconds']:.1f}s"
        )

    print("\n" + "=" * 60)
    print("Review flashcards in the results directory for quality analysis")
    print("=" * 60)


if __name__ == "__main__":
    main()
