"""Tests for the download endpoint."""

import pytest

from src.api.services.file_storage import FileStorage


@pytest.mark.unit
class TestDownloadEndpoint:
    """Tests for GET /api/download/{job_id}."""

    def test_download_not_found(self, client):
        """Return 404 for non-existent job."""
        response = client.get("/api/download/nonexistent-job-id")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_download_job_not_completed(self, client, temp_dirs, job_manager):
        """Return 400 when trying to download incomplete job."""
        # Create a job that is still processing
        job = await job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 5}
        )

        # Update to processing state but don't complete
        await job_manager.update_progress(job.job_id, 50, 100, "Processing...")

        # Patch the job manager
        import src.api.services.job_manager as jm

        jm._job_manager = job_manager

        # Try to download - should fail because job is not completed
        response = client.get(f"/api/download/{job.job_id}")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_download_completed_job(self, client, temp_dirs, job_manager):
        """Download result when job is completed."""
        upload_dir, output_dir = temp_dirs

        # Create a completed job manually
        job = await job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 1}
        )

        # Create a fake output file
        output_path = FileStorage.get_output_path(job.job_id)
        output_path.write_bytes(b"fake apkg content")

        # Mark job as completed
        await job_manager.complete_job(job.job_id, str(output_path))

        # Patch the job manager to use our instance
        import src.api.services.job_manager as jm

        jm._job_manager = job_manager

        # Download should work now
        response = client.get(f"/api/download/{job.job_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == b"fake apkg content"

    @pytest.mark.asyncio
    async def test_download_failed_job(self, client, temp_dirs, job_manager):
        """Return error when trying to download failed job."""
        # Create and fail a job
        job = await job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 1}
        )
        await job_manager.fail_job(job.job_id, "Test error message")

        # Patch the job manager
        import src.api.services.job_manager as jm

        jm._job_manager = job_manager

        response = client.get(f"/api/download/{job.job_id}")

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower()
        assert "Test error message" in response.json()["detail"]
