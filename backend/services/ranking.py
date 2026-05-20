"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking service stub used for backend/frontend integration before
the real ML model is connected.
"""

from typing import Any, Dict, List

from backend.models.schemas import SearchRequest
from ml.rank_jobs import rank_jobs as ml_rank_jobs


def _search_request_to_user_profile(search_input: SearchRequest) -> Dict[str, Any]:
    """Convert SearchRequest from frontend to user_profile dict for ML ranking.

    Maps frontend SearchRequest fields to the user_profile dictionary format
    expected by ml.rank_jobs.rank_jobs().
    """
    return {
        "job_title": search_input.job_title,
        "skills": search_input.skills,
        "location": search_input.location,
        "experience_level": search_input.experience_level,
    }


def rank_jobs(
    search_input: SearchRequest,
    jobs: List[Dict[str, Any]],
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """Rank jobs using the ML ranking model.

    Adapter that converts SearchRequest to user_profile dict format and calls
    the real rank_jobs() implementation. Returns top-N ranked results.
    """
    user_profile = _search_request_to_user_profile(search_input)
    ranked_jobs = ml_rank_jobs(user_profile, jobs, debug=False)
    return ranked_jobs[:top_n]
