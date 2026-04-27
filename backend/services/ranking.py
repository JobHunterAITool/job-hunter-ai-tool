"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking service integration layer that adapts backend request
models to the shared ML ranker while preserving the frontend response shape.
"""

from typing import Any

from backend.models.schemas import SearchRequest
from ml.rank_jobs import rank_jobs as ml_rank_jobs


def _search_request_to_dict(search_input: SearchRequest | dict[str, Any]) -> dict[str, Any]:
    """Return a plain dict so ML code can consume search input consistently."""
    if isinstance(search_input, dict):
        return dict(search_input)
    if hasattr(search_input, "model_dump"):
        return search_input.model_dump()
    if hasattr(search_input, "dict"):
        return search_input.dict()
    raise ValueError("search_input must be a mapping-compatible object")


def rank_jobs(
    search_input: SearchRequest | dict[str, Any],
    jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Run ML ranking and normalize output fields expected by API consumers."""
    if not jobs:
        return []

    user_profile = _search_request_to_dict(search_input)
    ranked_jobs = ml_rank_jobs(user_profile, jobs, debug=False)

    normalized_results: list[dict[str, Any]] = []
    for job in ranked_jobs:
        normalized_results.append(
            {
                "title": str(job.get("title", "Unknown")),
                "company": str(job.get("company", "Unknown")),
                "location": str(job.get("location", "Unknown")),
                "score": float(job.get("score", 0.0)),
                "matched_skills": [
                    str(skill).strip()
                    for skill in (job.get("matched_skills") or [])
                    if str(skill).strip()
                ],
            }
        )

    return normalized_results
