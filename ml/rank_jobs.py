"""
Author: Richard Hsiao
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Ranking module stub used for backend integration before the real
ML model is connected.
"""

import re
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_MAX_CANDIDATES = 200
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


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
        skills_text,
    ]
    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _keyword_overlap_score(user_terms: set[str], job_text: str) -> int:
    return len(user_terms & _tokenize(job_text))


def rank_jobs(user_text: str, jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank a list of job documents by relevance to the user's profile text.

    Parameters
    ----------
    user_text : str
        Plain text extracted from the user's uploaded resume, or assembled
        from the manual input form fields (title + skills + location +
        experience level). Must be a non-empty string.
    jobs : list[dict]
        Job postings retrieved from MongoDB. Each posting is expected to
        contain at least the following fields:

        {
            "_id":             str,        # MongoDB ObjectId
            "title":           str,
            "company":         str,        # company.display_name (Adzuna)
            "location":        str,        # location.display_name (Adzuna)
            "description":     str,
            "skills":          list[str],  # Parsed by Backend
            "created":         str,        # ISO 8601 timestamp string
            "redirect_url":    str,    # URL to full job description (Adzuna)
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
        If ``user_text`` is empty or ``jobs`` is an empty list.

    Notes
    -----
    Current implementation: placeholder stub — returns jobs in ranked
    order with a dummy score of 0.0 so that the backend POST /search endpoint
    is testable end-to-end before the real ML logic is wired in.

    """
    if not user_text or not user_text.strip():
        raise ValueError("user_text must be a non-empty string")
    if not jobs:
        raise ValueError("jobs list must not be empty")

    user_text = user_text.strip()
    user_terms = _tokenize(user_text)

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

    # # --- Stub implementation ---
    # # Return a copy of the input list with a placeholder score attached.
    # # Replace this block entirely in Progress Report #2.
    # ranked = []
    # for job in jobs:
    #     job_copy = dict(job)
    #     job_copy["score"] = 0.0
    #     ranked.append(job_copy)
    # # Sort the ranked jobs by their scores in descending order
    # return sorted(ranked, key=lambda job: job["score"], reverse=True)
