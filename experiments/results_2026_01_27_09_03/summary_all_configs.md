# Experiment Summary

**PDF:** tests/sample_data/DDIA.pdf
**Pages:** 222-228
**Cards per page:** 1
**Difficulty:** intermediate
**Run date:** 2026-01-27T09:06:16.096404

## Results Comparison

| Config | Flashcards | Tokens | Cost ($) | Time (s) | Status |
|--------|------------|--------|----------|----------|--------|
| baseline | 7 | 6477 | 0.0283 | 23.1 | success |
| rag_k1 | 7 | 9156 | 0.0368 | 29.6 | success |
| rag_k3 | 7 | 19479 | 0.0688 | 28.2 | success |
| rag_k5 | 7 | 24125 | 0.0824 | 28.7 | success |
| rag_k10 | 7 | 24136 | 0.0826 | 26.4 | success |

## Configuration Details

- **baseline**: Baseline: Full page text without RAG
- **rag_k1**: RAG with top_k=1 (single most relevant chunk)
- **rag_k3**: RAG with top_k=3 (three most relevant chunks)
- **rag_k5**: RAG with top_k=5 (default, five most relevant chunks)
- **rag_k10**: RAG with top_k=10 (ten most relevant chunks)

## Notes

- Review flashcards manually to assess quality
- Consider acceptance rate (% of cards you would keep)
- Note any patterns in RAG vs baseline quality
