"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Search endpoint route for ranking job results with the integrated
ML model pipeline.
"""

from fastapi import APIRouter

from backend.db import get_jobs_collection
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.ranking import rank_jobs

router = APIRouter(tags=["search"])

MAX_CANDIDATE_JOBS = 200
MAX_RETURNED_RESULTS = 20


@router.post("/search", response_model=SearchResponse)
def search_jobs(search_request: SearchRequest):
    """Search jobs, rank candidates with ML, and return top results."""
    jobs_collection = get_jobs_collection()
    # Pull a bounded candidate pool from MongoDB before ranking.
    candidate_jobs = list(
        jobs_collection.find({}, {"_id": 0}).limit(MAX_CANDIDATE_JOBS)
    )
    if not candidate_jobs:
        return SearchResponse(results=[])

    ranked_jobs = rank_jobs(search_request, candidate_jobs)
    ranked_jobs.sort(key=lambda item: item.get("score", 0.0), reverse=True)

    return SearchResponse(results=ranked_jobs[:MAX_RETURNED_RESULTS])
