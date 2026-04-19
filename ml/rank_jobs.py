"""
Author: Richard Hsiao
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking module stub used for backend integration before the real
ML model is connected. It currently accepts either resume text or structured
user fields and normalizes them into a single query string for scoring.
"""

import re
from collections.abc import Iterable
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_MAX_CANDIDATES = 200
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize_skills(skills: Any) -> list[str]:
    if skills is None:
        return []
    if isinstance(skills, str):
        return [part.strip() for part in skills.split(",") if part.strip()]
    if isinstance(skills, Iterable):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    return [str(skills).strip()] if str(skills).strip() else []


def build_user_text(
    job_title: str = "",
    skills: Any = None,
    location: str = "",
    experience_level: str = "",
) -> str:
    """Build the ranking text representation from structured user fields."""
    skill_text = " ".join(_normalize_skills(skills))
    parts = [job_title, skill_text, location, experience_level]
    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _job_to_text(job: dict[str, Any]) -> str:
    skills = job.get("skills", [])
    if isinstance(skills, list):
        skills_text = " ".join(str(skill) for skill in skills)
    else:
        skills_text = str(skills)

    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
        job.get("job_description_text", ""),
        skills_text,
    ]
    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _keyword_overlap_score(user_terms: set[str], job_text: str) -> int:
    return len(user_terms & _tokenize(job_text))


def rank_jobs(
    user_text: str | None = None,
    jobs: list[dict[str, Any]] | None = None,
    *,
    job_title: str = "",
    skills: Any = None,
    location: str = "",
    experience_level: str = "",
) -> list[dict[str, Any]]:
    """Rank a list of job documents by relevance to the user's profile text.

    Parameters
    ----------
    user_text : str | None
        Plain text extracted from the user's uploaded resume. Optional when
        structured user fields are supplied.
    job_title : str
        Manual profile/job preference title from the frontend form.
    skills : Any
        Manual profile skills from the frontend form. Accepts list[str] or a
        comma-separated string.
    location : str
        Manual profile location from the frontend form.
    experience_level : str
        Manual profile experience level from the frontend form.
    jobs : list[dict]
        Job postings retrieved from MongoDB. Each posting is expected to
        contain at least the following fields:

        {
            "_id":             str,        # MongoDB ObjectId
            "title":           str,
            "company":         str,        # company.display_name (Adzuna)
            "location":        str,        # location.display_name (Adzuna)
            "description":     str,
            "category":        str,        # category.label (Adzuna)
            "skills":          list[str],  # Parsed by Backend
            "created":         str,        # ISO 8601 timestamp string
            "redirect_url":    str,    # URL to full job description (Adzuna)
            "job_description_text": str,   # Plain text extracted by Pipeline
        }

        Absent fields are treated as empty strings during scoring.

    Returns
    -------
    list[dict]
        A *new* list of job postings sorted in descending order by relevance
        score. Each posting is a shallow copy of the input posting with one
        additional field injected::

            "score": float   # cosine similarity in [0.0, 1.0]

        The caller (backend POST /search handler) is responsible for slicing
        the top-N results before returning them to the frontend.

    Raises
    ------
    ValueError
        If no user information is provided or "jobs" is an empty list.

    Notes
    -----
    Current implementation: returns jobs with appended "score" field, sorted in
    descending order.

    """
    if jobs is None:
        jobs = []

    if user_text and user_text.strip():
        query_text = user_text.strip()
    else:
        query_text = build_user_text(
            job_title=job_title,
            skills=skills,
            location=location,
            experience_level=experience_level,
        )

    if not query_text:
        raise ValueError(
            "either user_text or structured profile fields must be provided"
        )

    if not jobs:
        raise ValueError("jobs list must not be empty")

    user_terms = _tokenize(query_text)

    candidate_jobs = list(jobs)
    if len(candidate_jobs) > _MAX_CANDIDATES:
        candidate_jobs = sorted(
            enumerate(candidate_jobs),
            key=lambda item: (-_keyword_overlap_score(user_terms, _job_to_text(item[1])), item[0]),
        )[:_MAX_CANDIDATES]
        candidate_jobs = [job for _, job in candidate_jobs]

    candidate_texts = [_job_to_text(job) for job in candidate_jobs]
    corpus = [user_text, *candidate_texts]

    try:
        tfidf_matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
    except ValueError:
        scores = [0.0] * len(candidate_jobs)

    ranked = []
    for job, score in zip(candidate_jobs, scores):
        job_copy = dict(job)
        job_copy["score"] = float(score)
        ranked.append(job_copy)

    return sorted(ranked, key=lambda job: job["score"], reverse=True)
