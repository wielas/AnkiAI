"""Prompt building for flashcard generation using Claude."""

import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """Builds prompts for Claude to generate educational flashcards.

    This is Version 1.0 - a simple template for Week 1. We'll iterate on this
    in Weeks 2-3 based on quality analysis.

    Design decisions:
    - Stateless: All state passed via parameters
    - Few-shot learning: Includes 1-2 example flashcards
    - JSON output: Structured format for easy parsing
    - Quality focus: Emphasizes clear questions and concise answers
    """

    # Prompt version for tracking quality improvements over time
    VERSION = "1.0"

    # Example flashcards for few-shot learning
    EXAMPLE_FLASHCARDS = [
        {
            "question": "What is the main responsibility of the leader node in leader-based replication?",
            "answer": "The leader accepts all write operations from clients and propagates these changes to follower nodes, ensuring data consistency across the cluster.",
        },
        {
            "question": "What is the key difference between synchronous and asynchronous replication?",
            "answer": "Synchronous replication waits for confirmation from replicas before confirming a write (strong consistency, higher latency), while asynchronous replication confirms writes immediately without waiting (eventual consistency, lower latency).",
        },
    ]

    @staticmethod
    def build_flashcard_prompt(
        context: str,
        difficulty: str = "intermediate",
        num_cards: int = 1,
    ) -> str:
        """Build a prompt for generating flashcards from context.

        Args:
            context: The text content to generate flashcards from
            difficulty: Target difficulty level (beginner/intermediate/advanced)
            num_cards: Number of flashcards to generate (default: 1)

        Returns:
            Formatted prompt string for Claude API

        Notes:
            - Requests JSON output format for easy parsing
            - Includes quality criteria and examples
            - Week 1 version - will be enhanced in Week 2-3
        """
        # Validate difficulty
        valid_difficulties = ["beginner", "intermediate", "advanced"]
        if difficulty not in valid_difficulties:
            logger.warning(
                f"Invalid difficulty '{difficulty}', using 'intermediate'. "
                f"Valid values: {valid_difficulties}"
            )
            difficulty = "intermediate"

        # Build difficulty description
        difficulty_guidance = {
            "beginner": "Focus on basic definitions and fundamental concepts. Keep questions simple and straightforward.",
            "intermediate": "Test understanding of concepts and their relationships. Questions should require comprehension, not just memorization.",
            "advanced": "Test deep understanding, edge cases, and practical applications. Questions should be challenging and thought-provoking.",
        }

        # Format example flashcards
        examples_text = "\n\n".join(
            [
                f"Example {i+1}:\n{{\n"
                f'  "question": "{ex["question"]}",\n'
                f'  "answer": "{ex["answer"]}"\n}}'
                for i, ex in enumerate(PromptBuilder.EXAMPLE_FLASHCARDS[:2])
            ]
        )

        # Build the prompt
        prompt = f"""You are an expert educational content creator specializing in technical flashcards for spaced repetition learning (Anki).

Your task is to generate {num_cards} high-quality flashcard{"s" if num_cards > 1 else ""} from the provided text.

DIFFICULTY LEVEL: {difficulty}
{difficulty_guidance[difficulty]}

QUALITY CRITERIA:
1. Question should be:
   - Clear and specific (no ambiguity)
   - Test understanding, not just memorization
   - Self-contained (understandable without the source text)
   - Concise (1-2 sentences maximum)

2. Answer should be:
   - Accurate and technically correct
   - Concise but complete (2-3 sentences ideal)
   - Focus on key points, avoid unnecessary details
   - Use precise technical terminology

3. General guidelines:
   - Avoid yes/no questions
   - Avoid "list all" questions (too broad)
   - Focus on concepts, not trivial facts
   - Each flashcard should test one clear concept

EXAMPLES OF GOOD FLASHCARDS:
{examples_text}

SOURCE TEXT:
{context}

OUTPUT FORMAT:
Generate exactly {num_cards} flashcard{"s" if num_cards > 1 else ""} in JSON format. {"If generating multiple cards, return a JSON array." if num_cards > 1 else "Return a single JSON object."}

{"For multiple cards:" if num_cards > 1 else "Format:"}
{'''[
  {
    "question": "Your question here",
    "answer": "Your answer here"
  },
  {
    "question": "Second question here",
    "answer": "Second answer here"
  }
]''' if num_cards > 1 else '''{
  "question": "Your question here",
  "answer": "Your answer here"
}'''}

Generate the flashcard{"s" if num_cards > 1 else ""} now:"""

        logger.debug(
            f"Built prompt for {num_cards} flashcard(s) at {difficulty} difficulty "
            f"({len(context)} chars context)"
        )

        return prompt

    @staticmethod
    def estimate_prompt_tokens(prompt: str) -> int:
        """Estimate number of tokens in a prompt.

        Uses rough approximation: 1 token ≈ 4 characters for English text.
        This is good enough for cost estimation.

        Args:
            prompt: The prompt text

        Returns:
            Estimated token count
        """
        # Claude's tokenizer is roughly 3.5-4 chars per token for English
        # We use 4 for conservative estimation
        return len(prompt) // 4

    @staticmethod
    def get_version() -> str:
        """Get the current prompt template version.

        Returns:
            Version string (e.g., "1.0")

        Notes:
            Use this to track which prompt version generated which flashcards.
            Essential for A/B testing and quality analysis in Week 3.
        """
        return PromptBuilder.VERSION
