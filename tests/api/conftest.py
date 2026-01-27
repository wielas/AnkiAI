"""Test fixtures for API tests."""

import asyncio
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.services.file_storage import FileStorage
from src.api.services.job_manager import JobManager


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dirs(tmp_path: Path) -> Generator[tuple[Path, Path], None, None]:
    """Create temporary upload and output directories.

    Yields:
        Tuple of (upload_dir, output_dir) paths
    """
    upload_dir = tmp_path / "uploads"
    output_dir = tmp_path / "outputs"
    upload_dir.mkdir()
    output_dir.mkdir()

    # Patch FileStorage to use temp directories
    original_upload = FileStorage.UPLOAD_DIR
    original_output = FileStorage.OUTPUT_DIR

    FileStorage.UPLOAD_DIR = upload_dir
    FileStorage.OUTPUT_DIR = output_dir

    yield upload_dir, output_dir

    # Restore original paths
    FileStorage.UPLOAD_DIR = original_upload
    FileStorage.OUTPUT_DIR = original_output


@pytest.fixture
def client(temp_dirs) -> Generator[TestClient, None, None]:
    """Create test client with temporary directories.

    Yields:
        FastAPI TestClient
    """
    # Reset job manager singleton for each test
    import src.api.services.job_manager as jm

    jm._job_manager = None

    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_pdf(temp_dirs) -> Path:
    """Create a sample PDF file for testing.

    Returns:
        Path to the sample PDF
    """
    upload_dir, _ = temp_dirs

    # Create a minimal valid PDF
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Test content) Tj ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000206 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
300
%%EOF
"""
    pdf_path = upload_dir / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def mock_flashcard_service():
    """Mock FlashcardGeneratorService for tests that don't need real generation.

    Yields:
        Mock service that simulates successful generation
    """
    with patch("src.api.routes.generate.FlashcardGeneratorService") as mock_class:
        mock_service = MagicMock()
        mock_class.return_value = mock_service

        # Create a mock result
        mock_result = MagicMock()
        mock_result.status.value = "SUCCESS"
        mock_result.total_success = 1
        mock_result.total_attempted = 1
        mock_result.flashcards = [
            {"question": "Test Q", "answer": "Test A", "source_page": 1}
        ]

        def generate_with_callback(*args, **kwargs):
            # Simulate progress callback
            callback = kwargs.get("on_progress")
            if callback:
                callback(50, 100, "Processing page 1...")
                callback(100, 100, "Complete")
            return mock_result

        mock_service.generate_flashcards.side_effect = generate_with_callback

        yield mock_service


@pytest.fixture
def job_manager() -> JobManager:
    """Create a fresh JobManager instance.

    Returns:
        New JobManager instance
    """
    return JobManager()
