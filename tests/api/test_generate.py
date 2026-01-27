"""Tests for the generate endpoint."""

import pytest


@pytest.mark.unit
class TestGenerateEndpoint:
    """Tests for POST /api/generate/{file_id}."""

    def test_generate_returns_job_id(self, client, sample_pdf, mock_flashcard_service):
        """Starting generation returns a job ID."""
        # First upload a file
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        # Start generation
        response = client.post(
            f"/api/generate/{file_id}",
            json={
                "start_page": 1,
                "end_page": 1,
                "difficulty": "intermediate",
                "cards_per_page": 1,
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["file_id"] == file_id
        assert data["status"] == "pending"
        assert data["progress"] == 0.0

    def test_generate_file_not_found(self, client):
        """Return 404 for non-existent file."""
        response = client.post(
            "/api/generate/nonexistent-file-id",
            json={
                "start_page": 1,
                "end_page": 1,
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_invalid_page_range(self, client, sample_pdf):
        """Reject invalid page range (start > end)."""
        # Upload file first
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        response = client.post(
            f"/api/generate/{file_id}",
            json={
                "start_page": 10,
                "end_page": 5,
            },
        )

        assert response.status_code == 422  # Validation error

    def test_generate_invalid_difficulty(self, client, sample_pdf):
        """Reject invalid difficulty level."""
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        response = client.post(
            f"/api/generate/{file_id}",
            json={
                "start_page": 1,
                "end_page": 1,
                "difficulty": "impossible",
            },
        )

        assert response.status_code == 422

    def test_generate_cards_per_page_validation(self, client, sample_pdf):
        """Validate cards_per_page range (1-10)."""
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        # Test too low
        response = client.post(
            f"/api/generate/{file_id}",
            json={"start_page": 1, "end_page": 1, "cards_per_page": 0},
        )
        assert response.status_code == 422

        # Test too high
        response = client.post(
            f"/api/generate/{file_id}",
            json={"start_page": 1, "end_page": 1, "cards_per_page": 11},
        )
        assert response.status_code == 422

    def test_generate_default_values(self, client, sample_pdf, mock_flashcard_service):
        """Test that default values are applied correctly."""
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        # Only provide required fields
        response = client.post(
            f"/api/generate/{file_id}",
            json={"start_page": 1, "end_page": 5},
        )

        assert response.status_code == 202
        # Defaults should be applied
        data = response.json()
        assert data["total_pages"] == 5
