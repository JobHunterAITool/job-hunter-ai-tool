"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking service stub used for backend/frontend integration before
the real ML model is connected.
"""

import logging
import re
from typing import Any, Dict, List

from backend.models.schemas import SearchRequest

logger = logging.getLogger(__name__)
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


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


def _tokenize(text: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_RE.finditer(text or "")}


def _fallback_rank_jobs(
    user_profile: Dict[str, Any],
    jobs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Deterministic local fallback when ML module or deps are unavailable."""
    user_skills = {str(skill).strip().lower() for skill in user_profile.get("skills", []) if str(skill).strip()}
    query_terms = _tokenize(
        " ".join(
            [
                user_profile.get("job_title", ""),
                user_profile.get("location", ""),
                user_profile.get("experience_level", ""),
                " ".join(sorted(user_skills)),
            ]
        )
    )

    ranked: List[Dict[str, Any]] = []
    for original in jobs:
        job = dict(original)
        job_skills = {
            str(skill).strip().lower()
            for skill in job.get("skills", [])
            if str(skill).strip()
        }
        matched_skills = sorted(user_skills & job_skills)

        job_terms = _tokenize(
            " ".join(
                [
                    str(job.get("title", "")),
                    str(job.get("company", "")),
                    str(job.get("location", "")),
                    str(job.get("description", "")),
                    str(job.get("job_description_text", "")),
                    " ".join(sorted(job_skills)),
                ]
            )
        )
        keyword_score = (
            len(query_terms & job_terms) / max(len(query_terms), 1)
            if query_terms
            else 0.0
        )
        skill_score = (
            len(matched_skills) / max(len(user_skills), 1)
            if user_skills
            else 0.0
        )

        # Keep score in [0,1] and stable for frontend contract.
        score = min(1.0, max(0.0, (0.6 * keyword_score) + (0.4 * skill_score)))
        job["matched_skills"] = matched_skills
        job["score"] = float(score)
        ranked.append(job)

    return sorted(ranked, key=lambda item: item["score"], reverse=True)


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

    try:
        from ml.rank_jobs import rank_jobs as ml_rank_jobs  # Lazy import by design.
    except Exception as exc:
        logger.warning(
            "ML ranking module unavailable; using backend fallback ranker. reason=%s",
            exc,
        )
        ranked_jobs = _fallback_rank_jobs(user_profile, jobs)
    else:
        try:
            ranked_jobs = ml_rank_jobs(user_profile, jobs)
        except Exception as exc:
            logger.exception(
                "ML ranking failed at runtime; using backend fallback ranker. reason=%s",
                exc,
            )
            ranked_jobs = _fallback_rank_jobs(user_profile, jobs)

    for ranked_job in ranked_jobs:
        ranked_job.setdefault("matched_skills", [])
        ranked_job["score"] = float(ranked_job.get("score", 0.0))

    return ranked_jobs[:top_n]
