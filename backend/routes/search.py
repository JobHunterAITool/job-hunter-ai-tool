"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Search endpoint route for ranking job results using current stub
logic. This is where the future ML ranking pipeline will plug in.
"""

from fastapi import APIRouter

from backend.db import get_jobs_collection
from backend.models.schemas import SearchRequest, SearchResponse
from backend.services.ranking import rank_jobs_stub

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search_jobs(search_request: SearchRequest):
    """Search jobs and return top ranked results."""
    jobs_collection = get_jobs_collection()
    # Pull raw jobs first, then score/rank in the service layer.
    jobs = list(jobs_collection.find({}, {"_id": 0}))

    # Keeping this call isolated makes it easy to swap in the ML model later.
    ranked_jobs = rank_jobs_stub(search_request, jobs, top_n=10)
    return SearchResponse(results=ranked_jobs)
