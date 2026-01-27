"""WebSocket endpoint for real-time progress updates."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.services.job_manager import get_job_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


@router.websocket("/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for streaming job progress updates.

    Clients connect to this endpoint to receive real-time updates
    about job progress. Messages are sent as JSON with the following
    structure:

    Progress update:
    {
        "type": "progress",
        "progress": 0.45,
        "current_page": 9,
        "total_pages": 20,
        "message": "Processing page 9..."
    }

    Completion:
    {
        "type": "complete",
        "status": "completed",
        "progress": 1.0,
        "message": "Generation complete"
    }

    Error:
    {
        "type": "error",
        "status": "failed",
        "error": "Error message"
    }

    Args:
        websocket: The WebSocket connection
        job_id: The job to monitor
    """
    job_manager = get_job_manager()
    job = await job_manager.get_job(job_id)

    # Check if job exists before accepting connection
    if not job:
        await websocket.close(code=4004, reason="Job not found")
        return

    await websocket.accept()
    logger.info(f"WebSocket connected for job: {job_id}")

    await job_manager.register_websocket(job_id, websocket)

    try:
        # Send current state immediately
        await websocket.send_json(
            {
                "type": "status",
                "job_id": job.job_id,
                "status": job.status,
                "progress": job.progress,
                "current_page": job.current_page,
                "total_pages": job.total_pages,
                "message": job.message,
                "error": job.error,
            }
        )

        # If job is already done, send final state and close
        if job.status in ("completed", "failed"):
            msg_type = "complete" if job.status == "completed" else "error"
            await websocket.send_json(
                {
                    "type": msg_type,
                    "status": job.status,
                    "progress": job.progress,
                    "message": job.message,
                    "error": job.error,
                }
            )
            return

        # Keep connection alive until job completes or client disconnects
        # The job_manager will push updates as they happen
        while True:
            try:
                # Wait for messages from client (ping/pong or close)
                # This keeps the connection alive and detects disconnects
                await websocket.receive_text()
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for job: {job_id}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        await job_manager.unregister_websocket(job_id, websocket)
        logger.debug(f"WebSocket cleanup complete for job: {job_id}")
