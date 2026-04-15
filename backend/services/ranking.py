"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking service stub used for backend/frontend integration before
the real ML model is connected.
"""

from typing import Any, Dict, List

from backend.models.schemas import SearchRequest


def rank_jobs_stub(
    search_input: SearchRequest,
    jobs: List[Dict[str, Any]],
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """Assign fake descending scores and return ranked results for UI integration.

    TODO(ML): Replace this scoring logic with the real model while keeping the
    same function signature so route wiring does not need to change.
    """
    # Normalize user skill inputs for simple case-insensitive matching.
    keywords = {skill.strip().lower() for skill in search_input.skills}
    scored_jobs: List[Dict[str, Any]] = []

    for index, job in enumerate(jobs):
        job_skills = job.get("skills", []) or []
        matched_skills = [skill for skill in job_skills if skill.lower() in keywords]

        # Deterministic descending baseline score for frontend testing.
        base_score = 0.99 - (index * 0.05)
        skill_bonus = 0.05 * len(matched_skills)
        score = max(0.0, min(1.0, base_score + skill_bonus))

        scored_jobs.append(
            {
                "title": job.get("title", "Unknown"),
                "company": job.get("company", "Unknown"),
                "location": job.get("location", "Unknown"),
                "score": round(score, 2),
                "matched_skills": matched_skills,
            }
        )

    # Highest score first so frontend receives already-sorted recommendations.
    scored_jobs.sort(key=lambda item: item["score"], reverse=True)
    return scored_jobs[:top_n]
