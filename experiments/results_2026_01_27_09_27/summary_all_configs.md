# Experiment Summary

**PDF:** tests/sample_data/DDIA.pdf
**Pages:** 205-209
**Cards per page:** 1
**Difficulty:** intermediate
**Run date:** 2026-01-27T09:28:48.305230

## Results Comparison

| Config | Flashcards | Tokens | Cost ($) | Time (s) | Status |
|--------|------------|--------|----------|----------|--------|
| baseline | 5 | 4841 | 0.0205 | 15.9 | success |
| rag_k1 | 5 | 6966 | 0.0277 | 20.4 | success |
| rag_k3 | 5 | 14326 | 0.0508 | 20.6 | success |
| rag_k5 | 5 | 14334 | 0.0510 | 20.9 | success |
| rag_k10 | 5 | 14354 | 0.0513 | 21.9 | success |

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
