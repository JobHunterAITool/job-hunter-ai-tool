"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Jobs listing route with pagination for frontend browsing and
testing against local MongoDB data.
"""

from fastapi import APIRouter, Query

from backend.db import get_jobs_collection
from backend.models.schemas import PaginatedJobsResponse

router = APIRouter(tags=["jobs"])


@router.get("/jobs", response_model=PaginatedJobsResponse)
def get_jobs(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    """Return paginated jobs for frontend listing."""
    jobs_collection = get_jobs_collection()

    # Basic pagination math: page 1 starts at index 0.
    skip = (page - 1) * limit
    total = jobs_collection.count_documents({})

    # Return only this page window so frontend can paginate smoothly.
    items = list(
        jobs_collection.find({}, {"_id": 0}).skip(skip).limit(limit)
    )
    return PaginatedJobsResponse(page=page, limit=limit, total=total, results=items)
