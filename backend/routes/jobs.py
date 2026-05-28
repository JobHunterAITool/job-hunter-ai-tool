"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Jobs listing route with pagination for frontend browsing and
testing against local MongoDB data.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from backend.db import get_jobs_collection
from backend.models.schemas import PaginatedJobsResponse

router = APIRouter(tags=["jobs"])
logger = logging.getLogger(__name__)


def _extract_display_name(value: Any, fallback: str) -> str:
    """Convert nested API objects into display strings for the response schema."""
    if isinstance(value, str) and value.strip():
        return value.strip()

    if isinstance(value, dict):
        display_name = value.get("display_name")
        if isinstance(display_name, str) and display_name.strip():
            return display_name.strip()

    return fallback


def _normalize_skills(value: Any) -> list[str]:
    """Return a response-safe skills list from loose MongoDB data."""
    if isinstance(value, list):
        return [str(skill).strip() for skill in value if str(skill).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def _normalize_experience_level(value: Any) -> int:
    """Return an integer experience value even when source data is missing."""
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _normalize_job_for_response(job: dict[str, Any]) -> dict[str, Any]:
    """Normalize MongoDB job documents so they match the /jobs response schema."""
    return {
        "title": str(job.get("title") or "Untitled Job").strip(),
        "company": _extract_display_name(job.get("company"), "Unknown Company"),
        "location": _extract_display_name(job.get("location"), "Unknown Location"),
        "skills": _normalize_skills(job.get("skills")),
        "experience_level": _normalize_experience_level(job.get("experience_level")),
    }


@router.get("/jobs", response_model=PaginatedJobsResponse)
def get_jobs(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100)):
    """Return paginated jobs for frontend listing."""
    try:
        jobs_collection = get_jobs_collection()

        # Basic pagination math: page 1 starts at index 0.
        skip = (page - 1) * limit
        total = jobs_collection.count_documents({})

        # Return only this page window so frontend can paginate smoothly.
        items = list(
            jobs_collection.find({}, {"_id": 0}).skip(skip).limit(limit)
        )
        normalized_items = [_normalize_job_for_response(item) for item in items]
    except Exception:
        logger.exception(
            "Failed to fetch paginated jobs for /jobs page=%s limit=%s",
            page,
            limit,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch jobs from the database.",
        )

    return PaginatedJobsResponse(
        page=page,
        limit=limit,
        total=total,
        results=normalized_items,
    )
