"""Tests for the jobs endpoint."""

import pytest


@pytest.mark.unit
class TestJobsEndpoint:
    """Tests for GET /api/jobs/{job_id}."""

    def test_get_job_status(self, client, sample_pdf, mock_flashcard_service):
        """Get status of an existing job."""
        # Upload and start generation
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        gen_response = client.post(
            f"/api/generate/{file_id}",
            json={"start_page": 1, "end_page": 1},
        )
        job_id = gen_response.json()["job_id"]

        # Check status
        response = client.get(f"/api/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["file_id"] == file_id
        assert "status" in data
        assert "progress" in data
        assert "created_at" in data

    def test_get_job_not_found(self, client):
        """Return 404 for non-existent job."""
        response = client.get("/api/jobs/nonexistent-job-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_job_status_fields(self, client, sample_pdf, mock_flashcard_service):
        """Verify all expected fields are present in job status."""
        with open(sample_pdf, "rb") as f:
            upload_response = client.post(
                "/api/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )
        file_id = upload_response.json()["file_id"]

        gen_response = client.post(
            f"/api/generate/{file_id}",
            json={"start_page": 1, "end_page": 3},
        )
        job_id = gen_response.json()["job_id"]

        response = client.get(f"/api/jobs/{job_id}")
        data = response.json()

        # Check all expected fields
        expected_fields = [
            "job_id",
            "file_id",
            "status",
            "progress",
            "current_page",
            "total_pages",
            "message",
            "created_at",
            "completed_at",
            "error",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
