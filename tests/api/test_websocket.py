"""Tests for the WebSocket endpoint."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from src.api.main import app
from src.api.services.job_manager import JobManager


@pytest.mark.unit
class TestWebSocketEndpoint:
    """Tests for WebSocket /ws/progress/{job_id}."""

    @pytest.mark.asyncio
    async def test_websocket_job_not_found(self, temp_dirs):
        """WebSocket closes with error for non-existent job."""
        # Reset job manager
        import src.api.services.job_manager as jm

        jm._job_manager = None

        with TestClient(app) as client:
            with pytest.raises(WebSocketDisconnect):
                # WebSocket should reject connection for non-existent job
                with client.websocket_connect("/ws/progress/nonexistent-job-id"):
                    pass

    @pytest.mark.asyncio
    async def test_websocket_receives_initial_state(self, temp_dirs):
        """WebSocket sends initial job state on connect."""
        # Reset and create job manager
        import src.api.services.job_manager as jm

        jm._job_manager = JobManager()

        # Create a job
        job = await jm._job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 5}
        )

        with TestClient(app) as client:
            with client.websocket_connect(f"/ws/progress/{job.job_id}") as websocket:
                # Should receive initial state
                data = websocket.receive_json()
                assert data["type"] == "status"
                assert data["job_id"] == job.job_id
                assert "status" in data
                assert "progress" in data

    @pytest.mark.asyncio
    async def test_websocket_receives_progress_updates(self, temp_dirs):
        """WebSocket receives progress updates."""
        import src.api.services.job_manager as jm

        jm._job_manager = JobManager()

        job = await jm._job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 5}
        )

        with TestClient(app) as client:
            with client.websocket_connect(f"/ws/progress/{job.job_id}") as websocket:
                # Receive initial state
                initial = websocket.receive_json()
                assert initial["type"] == "status"

                # Simulate progress update
                await jm._job_manager.update_progress(
                    job.job_id, 50, 100, "Processing page 2..."
                )

                # Should receive progress update
                update = websocket.receive_json()
                assert update["type"] == "progress"
                assert update["progress"] == 0.5
                assert "Processing page 2" in update["message"]

    @pytest.mark.asyncio
    async def test_websocket_receives_completion(self, temp_dirs):
        """WebSocket receives completion notification."""
        import src.api.services.job_manager as jm

        jm._job_manager = JobManager()

        job = await jm._job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 1}
        )

        with TestClient(app) as client:
            with client.websocket_connect(f"/ws/progress/{job.job_id}") as websocket:
                # Receive initial state
                websocket.receive_json()

                # Complete the job
                await jm._job_manager.complete_job(job.job_id, "/fake/output.apkg")

                # Should receive completion
                complete = websocket.receive_json()
                assert complete["type"] == "complete"
                assert complete["status"] == "completed"

    @pytest.mark.asyncio
    async def test_websocket_receives_error(self, temp_dirs):
        """WebSocket receives error notification."""
        import src.api.services.job_manager as jm

        jm._job_manager = JobManager()

        job = await jm._job_manager.create_job(
            "test-file-id", {"start_page": 1, "end_page": 1}
        )

        with TestClient(app) as client:
            with client.websocket_connect(f"/ws/progress/{job.job_id}") as websocket:
                # Receive initial state
                websocket.receive_json()

                # Fail the job
                await jm._job_manager.fail_job(job.job_id, "Test error")

                # Should receive error
                error = websocket.receive_json()
                assert error["type"] == "error"
                assert error["status"] == "failed"
                assert error["error"] == "Test error"


@pytest.mark.unit
class TestJobManager:
    """Tests for JobManager functionality."""

    @pytest.mark.asyncio
    async def test_create_job(self, job_manager):
        """Create a new job."""
        job = await job_manager.create_job(
            "file-123", {"start_page": 1, "end_page": 10, "difficulty": "intermediate"}
        )

        assert job.job_id is not None
        assert job.file_id == "file-123"
        assert job.status == "pending"
        assert job.progress == 0.0
        assert job.total_pages == 10

    @pytest.mark.asyncio
    async def test_get_job(self, job_manager):
        """Retrieve an existing job."""
        job = await job_manager.create_job("file-123", {"start_page": 1, "end_page": 1})

        retrieved = await job_manager.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.job_id == job.job_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, job_manager):
        """Return None for non-existent job."""
        result = await job_manager.get_job("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_progress(self, job_manager):
        """Update job progress."""
        job = await job_manager.create_job("file-123", {"start_page": 1, "end_page": 5})

        await job_manager.update_progress(job.job_id, 50, 100, "Processing page 3...")

        updated = await job_manager.get_job(job.job_id)
        assert updated.status == "processing"
        assert updated.progress == 0.5
        assert updated.message == "Processing page 3..."

    @pytest.mark.asyncio
    async def test_complete_job(self, job_manager):
        """Mark job as completed."""
        job = await job_manager.create_job("file-123", {"start_page": 1, "end_page": 1})

        await job_manager.complete_job(job.job_id, "/path/to/output.apkg")

        completed = await job_manager.get_job(job.job_id)
        assert completed.status == "completed"
        assert completed.progress == 1.0
        assert completed.result_path == "/path/to/output.apkg"
        assert completed.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_job(self, job_manager):
        """Mark job as failed."""
        job = await job_manager.create_job("file-123", {"start_page": 1, "end_page": 1})

        await job_manager.fail_job(job.job_id, "Something went wrong")

        failed = await job_manager.get_job(job.job_id)
        assert failed.status == "failed"
        assert failed.error == "Something went wrong"
        assert failed.completed_at is not None

    @pytest.mark.asyncio
    async def test_job_to_dict(self, job_manager):
        """Convert job to dictionary."""
        job = await job_manager.create_job("file-123", {"start_page": 1, "end_page": 5})

        job_dict = job.to_dict()

        assert job_dict["job_id"] == job.job_id
        assert job_dict["file_id"] == "file-123"
        assert job_dict["status"] == "pending"
        assert job_dict["progress"] == 0.0
        assert "created_at" in job_dict
