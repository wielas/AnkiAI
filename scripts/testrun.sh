# 1. Unit tests pass
poetry run pytest tests/unit/ -v

# 2. Linting passes
poetry run ruff check src tests && poetry run black src tests --check



# 3. Test verbose vs quiet output
poetry run python -m src.interface.cli.main --pdf tests/fixtures/sample_technical.pdf --pages 1-2
# Expected: Clean output, no logger lines

poetry run python -m src.interface.cli.main --pdf tests/fixtures/sample_technical.pdf --pages 1-2 --verbose
# Expected: Detailed logging visible