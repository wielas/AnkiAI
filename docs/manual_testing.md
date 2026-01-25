# Manual Testing Guide

This guide covers manual testing procedures for the AnkiAI Week 1 pipeline.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Install dependencies
   poetry install

   # Activate virtual environment
   poetry shell
   ```

2. **API Key Configuration**
   - Create a `.env` file in the project root:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```
   - Or export directly:
     ```bash
     export ANTHROPIC_API_KEY=your_api_key_here
     ```

3. **Sample PDF**
   - Place a PDF for testing in `tests/sample_data/`
   - The project includes: `tests/sample_data/023_Transaction Processing or Analytics_.pdf`

## Test 1: Basic Generation (2-3 pages)

Generate flashcards from a small page range for quick verification.

```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-3 \
  --output test_basic.apkg
```

**Expected Output:**
- Progress indicators for each page
- Preview of each generated flashcard (Q: / A:)
- Summary showing success count, tokens, cost
- File `test_basic.apkg` created

**Verify:**
- [ ] Progress shows [1/3], [2/3], [3/3]
- [ ] At least 2-3 flashcards generated
- [ ] Cost is under $0.01
- [ ] File exists: `ls -la test_basic.apkg`

## Test 2: Larger Document (10 pages)

Test with more pages to verify the pipeline handles larger batches.

```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-10 \
  --output test_large.apkg \
  --cards-per-page 1
```

**Expected Output:**
- Progress for 10 pages
- 8-10 flashcards (some pages may be empty or fail)
- Higher token usage and cost

**Verify:**
- [ ] Processing completes for all pages
- [ ] Status is SUCCESS or PARTIAL
- [ ] Cost estimate shown
- [ ] Deck created with multiple cards

## Test 3: Different Difficulty Levels

Test each difficulty level produces appropriate content.

### Beginner Difficulty
```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 3-5 \
  --difficulty beginner \
  --output test_beginner.apkg
```

**Expected:** Simpler questions, basic definitions

### Advanced Difficulty
```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 3-5 \
  --difficulty advanced \
  --output test_advanced.apkg
```

**Expected:** More complex questions requiring deeper understanding

## Test 4: Multiple Cards Per Page

Generate multiple flashcards per page.

```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-3 \
  --cards-per-page 2 \
  --output test_multi.apkg
```

**Expected Output:**
- Up to 6 flashcards (3 pages × 2 cards)
- Higher token usage than single-card mode

## Test 5: Quiet Mode

Minimal output for scripted usage.

```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-2 \
  --quiet \
  --output test_quiet.apkg
```

**Expected Output:**
- Only summary section shown
- No progress or previews

## Test 6: No Preview Mode

Generate without inline flashcard preview.

```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-3 \
  --no-preview \
  --output test_no_preview.apkg
```

**Expected Output:**
- Progress indicators shown
- No Q:/A: content inline
- Summary still shows counts

## Verify in Anki Desktop

1. **Import the Deck**
   - Open Anki desktop application
   - File → Import
   - Select your generated `.apkg` file
   - Click "Import"

2. **Verify Import**
   - Check deck appears with correct name (e.g., "AnkiAI - 023_Transaction...")
   - Card count matches generated flashcards

3. **Review Cards**
   - Browse cards: View → Browse
   - Check question/answer formatting
   - Verify tags are present:
     - `source:*` - Source filename
     - `pages:*` - Page range
     - `difficulty:*` - Difficulty level
     - `generated:*` - Generation date

4. **Study Cards**
   - Click the deck
   - Press "Study Now"
   - Verify front shows question, back shows answer

## Error Cases

### Missing API Key
```bash
unset ANTHROPIC_API_KEY
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 1-2 \
  --output test_error.apkg
```

**Expected:** Error about missing API key

### Invalid Page Range
```bash
poetry run python -m src.interface.cli.main \
  --pdf tests/sample_data/023_Transaction\ Processing\ or\ Analytics_.pdf \
  --pages 10-5 \
  --output test_error.apkg
```

**Expected:** Error about invalid page range

### Non-existent File
```bash
poetry run python -m src.interface.cli.main \
  --pdf nonexistent.pdf \
  --pages 1-3 \
  --output test_error.apkg
```

**Expected:** File not found error

## Cost Tracking Verification

Track costs across multiple runs to verify accuracy:

| Test | Pages | Cards/Page | Expected Cost |
|------|-------|------------|---------------|
| Basic (3 pages) | 3 | 1 | ~$0.003-0.005 |
| Large (10 pages) | 10 | 1 | ~$0.01-0.015 |
| Multi (3 pages) | 3 | 2 | ~$0.006-0.008 |

*Note: Costs vary based on content length and model pricing*

## Troubleshooting

### Pages show as FAILED
- Check if page has extractable text (some PDFs are image-based)
- Check API rate limits haven't been exceeded
- Review logs for specific error messages

### No flashcards generated
- Ensure ANTHROPIC_API_KEY is set correctly
- Try with a different page range
- Check PDF has readable text content

### Cost seems high
- Verify cards-per-page setting
- Check page range isn't too large
- Review token usage in summary

## Cleanup

Remove test output files:
```bash
rm -f test_*.apkg manual_test.apkg
```
