"""
Author: Richard Hsiao
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Baseline ML ranking module that normalizes a user profile into a
query string, applies TF-IDF vectorization, computes cosine similarity against
job text, and returns deterministic score-sorted results.
"""

import re
import numpy as np
from collections.abc import Iterable
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_MAX_CANDIDATES = 200
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize_text(text: str) -> str:
    return " ".join(_TOKEN_RE.findall(str(text or "").lower()))


def _normalize_skills(skills: Any) -> list[str]:
    if skills is None:
        return []
    if isinstance(skills, str):
        return [part.strip() for part in skills.split(",") if part.strip()]
    if isinstance(skills, Iterable):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    return [str(skills).strip()] if str(skills).strip() else []


def _l2_normalize(scores: list[float]) -> list[float]:
    norm = np.linalg.norm(scores)
    if norm == 0:
        return [0.0 for _ in scores]
    return (np.array(scores) / norm).tolist()


def build_user_text(user_profile: dict[str, Any]) -> str:
    """Build ranking text from a user profile dictionary.
    Supported keys: user_text, resume_text, job_title, skills, location.
    """
    normalized_skills = _normalize_skills(user_profile.get("skills"))
    skill_text = " ".join(normalized_skills)

    parts = [
        user_profile.get("user_text", "") or user_profile.get("resume_text", ""),
        user_profile.get("job_title", ""),
        skill_text,
        user_profile.get("location", ""),
    ]

    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _tokenize(text: str) -> set[str]:
    return set(_normalize_text(text).split())


def _job_to_text(job: dict[str, Any]) -> str:
    skills = job.get("skills", [])
    normalized_skills = _normalize_skills(skills)
    skills_text = " ".join(normalized_skills)

    parts = [
        job.get("title", ""),
        job.get("job_description_text", ""),
        skills_text,
    ]

    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _keyword_overlap_score(user_terms: set[str], job_text: str) -> int:
    return len(user_terms & _tokenize(job_text))


def _normalized_skill_set(skills: Any) -> set[str]:
    return {skill.lower() for skill in _normalize_skills(skills)}


def _skill_score(user_skills: set[str], job: dict[str, Any]) -> tuple[float, list[str]]:
    if not user_skills:
        return 0.0, []

    job_skills = _normalized_skill_set(job.get("skills", []))
    if not job_skills:
        return 0.0, []

    matched_skills = sorted(user_skills & job_skills)
    skill_score = len(matched_skills) / len(job_skills)
    return skill_score, matched_skills


def _print_debug_overlaps(
    user_terms: set[str],
    ranked_jobs: list[dict[str, Any]],
    limit: int,
) -> None:
    print("[rank_jobs debug] user_terms:", sorted(user_terms))

    if not ranked_jobs:
        print("[rank_jobs debug] no candidate jobs")
        return

    for index, job in enumerate(ranked_jobs[:limit], start=1):
        job_text = _job_to_text(job)
        overlap = sorted(user_terms & _tokenize(job_text))

        print(
            "[rank_jobs debug]",
            {
                "rank": index,
                "job_id": job.get("_id"),
                "title": job.get("title", ""),
                "score": float(job.get("score", 0.0)),
                "matched_skills": job.get("matched_skills", []),
                "matched_terms": overlap,
            },
        )


def rank_jobs(
    user_profile: dict[str, Any],
    jobs: list[dict[str, Any]],
    debug: bool = False,
    debug_top_n: int = 5,
) -> list[dict[str, Any]]:
    """Rank a list of job documents by relevance to the user's profile text.

    Parameters
    ----------
    user_profile : dict[str, str | int]
        User inputs for ranking, including any combination of:

        {
            "user_text": str,
            "resume_text": str,
            "job_title": str,
            "skills": list[str] or comma-separated str,
            "location": str,

        }

    jobs : list[dict]
        Job postings retrieved from MongoDB. Each posting is expected to
        contain at least the following fields:

        {
            "_id":             str,        # MongoDB ObjectId
            "title":           str,
            "company":         str,        # company.display_name (Adzuna)
            "location":        str,        # location.display_name (Adzuna)
            "description":     str,        # Truncated to 500 chars
            "category":        str,        # category.label (Adzuna)
            "skills":          list[str],  # Parsed by Pipeline
            "created":         str,        # ISO 8601 timestamp string
            "redirect_url":    str,    # URL to full job description (Adzuna)
            "job_description_text": str,   # Plain text extracted by Pipeline
        }

        Absent fields are treated as empty strings during scoring.
    debug : bool, optional
        If True, print matched token overlaps for top candidate jobs.
    debug_top_n : int, optional
        Number of top-ranked candidate jobs to include in debug output.

    Returns
    -------
    list[dict]
        A *new* list of job postings sorted in descending order by relevance
        score. Each posting is a shallow copy of the input posting with one
        additional field injected::

            "score": float   # blended relevance score in [0.0, 1.0]

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

    query_text_raw = build_user_text(user_profile)

    if not query_text_raw:
        raise ValueError("user_profile must include non-empty ranking fields")

    query_text = _normalize_text(query_text_raw)

    if not jobs:
        raise ValueError("jobs list must not be empty")

    user_terms = set(query_text.split())

    candidate_jobs = list(jobs)
    if len(candidate_jobs) > _MAX_CANDIDATES:
        candidate_jobs = sorted(
            enumerate(candidate_jobs),
            key=lambda item: (
                -_keyword_overlap_score(user_terms, _job_to_text(item[1])),
                item[0],
            ),
        )[:_MAX_CANDIDATES]
        candidate_jobs = [job for _, job in candidate_jobs]

    candidate_texts = [
        _normalize_text(_job_to_text(job))
        for job in candidate_jobs
    ]

    corpus = [query_text, *candidate_texts]

    try:
        tfidf_matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
        raw_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten().tolist()
    except ValueError:
        raw_scores = [0.0] * len(candidate_jobs)

    tfidf_scores = _l2_normalize(raw_scores)
    user_skills = _normalized_skill_set(user_profile.get("skills"))

    alpha = 0.8  # weight for skill score

    scored_jobs = []
    for job, tfidf_score in zip(candidate_jobs, tfidf_scores):
        job_copy = dict(job)

        skill_score, matched_skills = _skill_score(user_skills, job)
        final_score = (1 - alpha) * tfidf_score + alpha * skill_score

        job_copy["matched_skills"] = matched_skills
        job_copy["matched_skills_count"] = len(matched_skills)

        job_copy["tfidf_score"] = float(tfidf_score)
        job_copy["skill_score"] = float(skill_score)
        job_copy["raw_final_score"] = float(final_score)
        job_copy["score"] = float(final_score)

        scored_jobs.append(job_copy)

    ranked_sorted = sorted(scored_jobs, key=lambda job: job["score"], reverse=True)

    # debug AFTER final scores are computed
    if debug:
        _print_debug_overlaps(
            user_terms,
            ranked_sorted,
            limit=max(0, debug_top_n),
        )

    return ranked_sorted
