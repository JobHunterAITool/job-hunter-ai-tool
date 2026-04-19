"""
Author: Richard Hsiao
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Baseline ML ranking module that normalizes a user profile into a
query string, applies TF-IDF vectorization, computes cosine similarity against
job text, and returns deterministic score-sorted results.
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


def build_user_text(user_profile: dict[str, Any]) -> str:
    """Build ranking text from a user profile dictionary.

    Supported keys: user_text, resume_text, job_title, skills, location,
    experience_level.
    """
    skill_text = " ".join(_normalize_skills(user_profile.get("skills")))
    parts = [
        user_profile.get("user_text", "") or user_profile.get("resume_text", ""),
        user_profile.get("job_title", ""),
        skill_text,
        user_profile.get("location", ""),
        user_profile.get("experience_level", ""),
    ]
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
    user_profile: dict[str, Any],
    jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Rank a list of job documents by relevance to the user's profile text.

    Parameters
    ----------
    user_profile : dict[str, Any]
        User inputs for ranking, including any combination of:
        user_text, resume_text, job_title, skills, location,
        experience_level.
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
    if not isinstance(user_profile, dict):
        raise ValueError("user_profile must be a dictionary")

    query_text = build_user_text(user_profile)

    if not query_text:
        raise ValueError("user_profile must include non-empty ranking fields")

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
    corpus = [query_text, *candidate_texts]

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
