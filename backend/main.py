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


origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

# CORS is required so our React frontend can call this API from localhost.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
