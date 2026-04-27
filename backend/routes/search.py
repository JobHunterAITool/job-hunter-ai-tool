"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Search endpoint route for ranking job results using current stub
logic. This is where the future ML ranking pipeline will plug in.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from backend.db import get_jobs_collection
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.ranking import rank_jobs_stub

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)


@router.post("/search", response_model=SearchResponse)
def search_jobs(search_request: SearchRequest):
    """Search jobs and return top ranked results."""
    try:
        jobs_collection = get_jobs_collection()
        # Pull raw jobs first, then score/rank in the service layer.
        jobs = list(jobs_collection.find({}, {"_id": 0}))
    except Exception:
        logger.exception("Failed to read jobs from MongoDB for /search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch jobs from the database.",
        )

    if not jobs:
        return SearchResponse(results=[])

    try:
        # Keeping this call isolated makes it easy to swap in the ML model later.
        ranked_jobs = rank_jobs_stub(search_request, jobs, top_n=10)
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

    return SearchResponse(results=ranked_jobs)
