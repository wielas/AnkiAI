"""Tests for the upload endpoint."""


import pytest


@pytest.mark.unit
class TestUploadEndpoint:
    """Tests for POST /api/upload."""

    def test_upload_valid_pdf(self, client, sample_pdf):
        """Upload a valid PDF file."""
        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert data["filename"] == "test.pdf"
        assert data["size"] > 0
        assert "uploaded_at" in data

    def test_upload_invalid_content_type(self, client):
        """Reject non-PDF files by content type."""
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_invalid_extension(self, client):
        """Reject files with non-PDF extension."""
        # Even with PDF content type, wrong extension should fail
        response = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"%PDF-1.4", "application/pdf")},
        )

        assert response.status_code == 400
        assert "Invalid file extension" in response.json()["detail"]

    def test_upload_file_too_large(self, client, temp_dirs):
        """Reject files exceeding size limit."""
        # Create a file just over the 50MB limit
        from src.api.services.file_storage import FileStorage

        original_limit = FileStorage.MAX_FILE_SIZE
        FileStorage.MAX_FILE_SIZE = 100  # 100 bytes for testing

        try:
            large_content = b"%PDF-1.4\n" + b"x" * 200  # Over 100 bytes
            response = client.post(
                "/api/upload",
                files={"file": ("large.pdf", large_content, "application/pdf")},
            )

            assert response.status_code == 400
            assert "too large" in response.json()["detail"].lower()
        finally:
            FileStorage.MAX_FILE_SIZE = original_limit

    def test_upload_creates_file(self, client, sample_pdf, temp_dirs):
        """Verify uploaded file is saved to disk."""
        upload_dir, _ = temp_dirs

        with open(sample_pdf, "rb") as f:
            response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        assert response.status_code == 200
        file_id = response.json()["file_id"]

        # Verify file exists
        saved_path = upload_dir / f"{file_id}.pdf"
        assert saved_path.exists()
