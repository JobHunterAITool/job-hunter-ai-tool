"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Search endpoint route for ranking job results using current stub
logic. This is where the future ML ranking pipeline will plug in.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.db import get_jobs_collection
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.ranking import rank_jobs

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)

MAX_CANDIDATE_JOBS = 200
MAX_RETURNED_RESULTS = 20


def _score_for_sort(job: dict[str, Any]) -> float:
    """Return a safe float score value for sorting ranked jobs."""
    try:
        return float(job.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _extract_display_name(value: Any, fallback: str) -> str:
    """Convert nested API objects into display strings for the response schema."""
    if isinstance(value, str) and value.strip():
        return value

    if isinstance(value, dict):
        display_name = value.get("display_name")
        if isinstance(display_name, str) and display_name.strip():
            return display_name

    return fallback


def _normalize_job_for_response(job: dict[str, Any]) -> dict[str, Any]:
    """Normalize ranked job fields so they match the SearchResponse schema."""
    normalized_job = job.copy()

    normalized_job["company"] = _extract_display_name(
        normalized_job.get("company"),
        "Unknown Company",
    )

    normalized_job["location"] = _extract_display_name(
        normalized_job.get("location"),
        "Unknown Location",
    )

    return normalized_job


@router.post("/search", response_model=SearchResponse)
def search_jobs(search_request: SearchRequest):
    """Search jobs and return top ranked results."""
    try:
        jobs_collection = get_jobs_collection()

        # Pull candidate jobs first, then score/rank in the service layer.
        jobs = list(jobs_collection.find({}, {"_id": 0}).limit(MAX_CANDIDATE_JOBS))

    except Exception:
        logger.exception("Failed to read jobs from MongoDB for /search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch jobs from the database.",
        )

    if not jobs:
        return SearchResponse(results=[])

    try:
        # The ranker may already sort, but the API contract expects score-sorted results.
        ranked_jobs = rank_jobs(search_request, jobs, top_n=MAX_CANDIDATE_JOBS)
        ranked_jobs = sorted(
            ranked_jobs,
            key=_score_for_sort,
            reverse=True,
        )

        normalized_jobs = [
            _normalize_job_for_response(job)
            for job in ranked_jobs[:MAX_RETURNED_RESULTS]
        ]

    except ValueError as exc:
        logger.warning("Invalid ranking input for /search: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid search input: {exc}",
        )

    except Exception:
        logger.exception("Unexpected ranking failure in /search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to rank jobs.",
        )

    return SearchResponse(results=normalized_jobs)