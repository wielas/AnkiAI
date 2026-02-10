"""FastAPI application for AnkiAI flashcard generation.

This module provides the main FastAPI application that exposes
flashcard generation functionality through a REST API with
WebSocket support for real-time progress updates.

Usage:
    poetry run uvicorn src.api.main:app --reload

Interactive docs available at:
    http://localhost:8000/docs
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import download, generate, jobs, upload, websocket
from src.api.services.file_storage import FileStorage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown tasks."""
    # Startup
    FileStorage.init_directories()
    logger.info("AnkiAI API started")
    yield
    # Shutdown
    logger.info("AnkiAI API shutting down")


app = FastAPI(
    title="AnkiAI API",
    description="AI-powered PDF to Anki flashcard generation API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS configuration
# NOTE: For production, restrict to specific origins
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8080",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(download.router, prefix="/api")
app.include_router(websocket.router, prefix="/ws")


@app.get("/health")
async def health_check():
    """Health check endpoint.

    Returns:
        Simple status object indicating the API is running
    """
    return {"status": "healthy", "service": "ankiai-api"}


@app.get("/")
async def root():
    """Root endpoint with API information.

    Returns:
        API metadata and documentation links
    """
    return {
        "name": "AnkiAI API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
