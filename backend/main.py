"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Main FastAPI entry point for my CS 467 capstone portfolio backend.
This file configures CORS, registers routes, and seeds starter jobs on startup.
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.routes.jobs import router as jobs_router
from backend.routes.search import router as search_router
from backend.routes.upload_resume import router as upload_resume_router
from backend.seed.seed_jobs import load_seed_jobs

# Load local .env values so teammates can run this without hardcoding secrets/URIs.
load_dotenv()

app = FastAPI(
    title="Job Hunting AI Web Tool Backend",
    description="FastAPI backend skeleton for the Job Hunting AI Web Tool project.",
    version="0.1.0",
)
logger = logging.getLogger(__name__)

DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,"
    "http://127.0.0.1:3000,"
    "http://localhost:5173,"
    "http://127.0.0.1:5173"
)
ALLOWED_CORS_METHODS = ["GET", "POST", "OPTIONS"]
ALLOWED_CORS_HEADERS = ["Authorization", "Content-Type"]


def _parse_cors_origins(raw_origins: str) -> list[str]:
    """Return explicit frontend origins and reject wildcard CORS entries."""
    parsed_origins = []
    for origin in raw_origins.split(","):
        normalized = origin.strip()
        if not normalized:
            continue
        if normalized == "*":
            logger.warning("Ignoring wildcard CORS origin while credentials are enabled.")
            continue
        parsed_origins.append(normalized)
    return parsed_origins


origins = _parse_cors_origins(os.getenv("CORS_ORIGINS", DEFAULT_CORS_ORIGINS))

# CORS is required so our React frontend can call this API from localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=ALLOWED_CORS_METHODS,
    allow_headers=ALLOWED_CORS_HEADERS,
)

app.include_router(jobs_router)
app.include_router(search_router)
app.include_router(upload_resume_router)


@app.on_event("startup")
def startup_event() -> None:
    """Load seed data so frontend can integrate immediately with placeholder jobs."""
    try:
        # If this is a fresh DB, preload example jobs for integration/testing.
        load_seed_jobs()
    except Exception:
        # Keep API bootable even when DB is temporarily unavailable.
        logger.exception("Startup seed failed; continuing without seeded jobs.")


@app.get("/", summary="Health check")
def root():
    # Simple endpoint to verify backend is alive without hitting DB-heavy routes.
    return {
        "status": "ok",
        "message": "Job Hunting AI Web Tool backend is running",
    }
