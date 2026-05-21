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

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ml.skills_parser import match_skills_by_section


_MAX_CANDIDATES = 200
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


# Load spaCy (lightweight config)
_nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])


def _spacy_preprocess(text: str) -> str:
    doc = _nlp(text.lower())
    tokens = [
        token.lemma_
        for token in doc
        if not token.is_stop
        and not token.is_punct
        and token.is_alpha
    ]
    return " ".join(tokens)


def _normalize_skills(skills: Any) -> list[str]:
    if skills is None:
        return []
    if isinstance(skills, str):
        return [part.strip() for part in skills.split(",") if part.strip()]
    if isinstance(skills, Iterable):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    return [str(skills).strip()] if str(skills).strip() else []


def _normalize_experience_level(experience_level: Any) -> int | None:
    """Normalize experience_level to years of experience as an int."""
    if experience_level is None or experience_level == "":
        return None
    if isinstance(experience_level, bool):
        return None
    if isinstance(experience_level, int):
        return experience_level
    if isinstance(experience_level, float) and experience_level.is_integer():
        return int(experience_level)
    if isinstance(experience_level, str):
        stripped = experience_level.strip()
        if not stripped:
            return None
        try:
            return int(stripped)
        except ValueError:
            legacy_levels = {
                "entry": 0,
                "junior": 1,
                "mid": 3,
                "senior": 5,
                "lead": 8,
            }
            return legacy_levels.get(stripped.lower())
    return None


def _l2_normalize(scores: list[float]) -> list[float]:
    norm = np.linalg.norm(scores)
    if norm == 0:
        return [0.0 for _ in scores]
    return (np.array(scores) / norm).tolist()


def build_user_text(user_profile: dict[str, Any]) -> str:
    """Build ranking text from a user profile dictionary.
    Supported keys: user_text, resume_text, job_title, skills, location,
    experience_level.
    """
    normalized_skills = _normalize_skills(user_profile.get("skills"))
    skill_text = " ".join(normalized_skills)
    experience_level = _normalize_experience_level(user_profile.get("experience_level"))

    parts = [
        user_profile.get("user_text", "") or user_profile.get("resume_text", ""),
        user_profile.get("job_title", ""),
        skill_text,
        user_profile.get("location", ""),
        (
            f"{experience_level} years experience"
            if experience_level is not None else ""
        ),
    ]

    return " ".join(str(part).strip() for part in parts if str(part).strip())


def _tokenize(text: str) -> set[str]:
    return set(_spacy_preprocess(text).split())


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


def _sectioned_skill_score(
    user_skills: set[str],
    job: dict[str, Any],
) -> tuple[float, float, float, list[str], list[str], list[str]]:
    if not user_skills:
        return 0.0, 0.0, 0.0, [], [], []

    job_skills = _normalized_skill_set(job.get("skills"))

    description = (
        job.get("job_description_text", "")
        or job.get("description", "")
    )

    section_matches = match_skills_by_section(
        user_skills,
        description,
    )

    required_matches = set(section_matches["required"])
    preferred_matches = set(section_matches["preferred"])

    sectioned_matches = required_matches | preferred_matches
    general_matches = job_skills & user_skills
    general_only_matches = general_matches - sectioned_matches

    required_skill_score = len(required_matches) / len(user_skills)
    preferred_skill_score = len(preferred_matches) / len(user_skills)

    required_count = len(required_matches)
    preferred_count = len(preferred_matches)
    general_count = len(general_only_matches)

    weighted_components = []
    weight_total = 0.0

    # Only include populated categories
    if required_count > 0:
        weighted_components.append(0.75 * required_count)
        weight_total += 0.75

    if preferred_count > 0:
        weighted_components.append(0.25 * preferred_count)
        weight_total += 0.25

    if general_count > 0:
        weighted_components.append(0.50 * general_count)
        weight_total += 0.50

    if weight_total > 0:
        weighted_match_count = sum(weighted_components)

        normalized_match_count = (
            weighted_match_count / weight_total
        )

        skill_score = min(
            normalized_match_count / len(user_skills),
            1.0,
        )
    else:
        skill_score = 0.0

    matched_skills = sorted(general_matches | sectioned_matches)

    return (
        skill_score,
        required_skill_score,
        preferred_skill_score,
        matched_skills,
        sorted(required_matches),
        sorted(preferred_matches),
    )


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
    debug: bool = True,
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
            "experience_level": int  # years of experience
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

            "score": float   # L2-normalized cosine similarity in [0.0, 1.0]

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

    query_text = _spacy_preprocess(query_text_raw)

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
        _spacy_preprocess(_job_to_text(job))
        for job in candidate_jobs
    ]

    corpus = [query_text, *candidate_texts]

    try:
        tfidf_matrix = TfidfVectorizer(stop_words="english").fit_transform(corpus)
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten().tolist()
    except ValueError:
        scores = [0.0] * len(candidate_jobs)

    user_skills = _normalized_skill_set(user_profile.get("skills"))

    alpha = 0.8  # weight for skill score

    scored_jobs = []
    raw_final_scores = []
    for job, score in zip(candidate_jobs, scores):
        job_copy = dict(job)

        (
            skill_score,
            required_skill_score,
            preferred_skill_score,
            matched_skills,
            matched_required_skills,
            matched_preferred_skills,
        ) = _sectioned_skill_score(user_skills, job)

        final_score = (1 - alpha) * score + alpha * skill_score

        job_copy["matched_skills"] = matched_skills
        job_copy["matched_required_skills"] = matched_required_skills
        job_copy["matched_preferred_skills"] = matched_preferred_skills
        job_copy["matched_skills_count"] = len(matched_skills)

        job_copy["tfidf_score"] = float(score)
        job_copy["skill_score"] = float(skill_score)
        job_copy["required_skill_score"] = float(required_skill_score)
        job_copy["preferred_skill_score"] = float(preferred_skill_score)
        job_copy["raw_final_score"] = float(final_score)

        scored_jobs.append(job_copy)
        raw_final_scores.append(float(final_score))

    normalized_final_scores = _l2_normalize(raw_final_scores)
    for job, normalized_score in zip(scored_jobs, normalized_final_scores):
        job["score"] = float(normalized_score)

    ranked_sorted = sorted(scored_jobs, key=lambda job: job["score"], reverse=True)

    # debug AFTER final scores are computed
    if debug:
        _print_debug_overlaps(
            user_terms,
            ranked_sorted,
            limit=max(0, debug_top_n),
        )

    return ranked_sorted
