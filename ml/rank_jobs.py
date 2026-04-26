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
_SKILL_NGRAM_MAX = 5
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def _normalize_skills(skills: Any) -> list[str]:
    if skills is None:
        return []
    if isinstance(skills, str):
        return [part.strip() for part in skills.split(",") if part.strip()]
    if isinstance(skills, Iterable):
        return [str(skill).strip() for skill in skills if str(skill).strip()]
    return [str(skills).strip()] if str(skills).strip() else []


def _skills_ngram_tokens(skills: Any) -> list[str]:
    tokens: list[str] = []
    normalized_skills = _normalize_skills(skills)

    for skill in normalized_skills:
        words = _TOKEN_RE.findall(skill.lower())
        max_n = min(_SKILL_NGRAM_MAX, len(words))
        for n in range(2, max_n + 1):
            for start in range(len(words) - n + 1):
                # Encode phrase n-grams as single terms so unigram tokenization keeps them intact.
                tokens.append(f"skillng{n}{''.join(words[start : start + n])}")

    return tokens


def _append_skill_ngram_tokens(text: str, skills: Any) -> str:
    skill_features = _skills_ngram_tokens(skills)
    if not skill_features:
        return text
    return f"{text} {' '.join(skill_features)}".strip()


def build_user_text(user_profile: dict[str, Any]) -> str:
    """Build ranking text from a user profile dictionary.

    Supported keys: user_text, resume_text, job_title, skills, location,
    experience_level.
    """
    normalized_skills = _normalize_skills(user_profile.get("skills"))
    skill_text = " ".join(normalized_skills)
    parts = [
        user_profile.get("user_text", "") or user_profile.get("resume_text", ""),
        user_profile.get("job_title", ""),
        skill_text,
        user_profile.get("location", ""),
        user_profile.get("experience_level", ""),
    ]
    base_text = " ".join(str(part).strip() for part in parts if str(part).strip())
    return _append_skill_ngram_tokens(base_text, normalized_skills)


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _job_to_text(job: dict[str, Any]) -> str:
    skills = job.get("skills", [])
    normalized_skills = _normalize_skills(skills)
    skills_text = " ".join(normalized_skills)

    parts = [
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
        job.get("job_description_text", ""),
        skills_text,
    ]
    base_text = " ".join(str(part).strip() for part in parts if str(part).strip())
    return _append_skill_ngram_tokens(base_text, normalized_skills)


def _keyword_overlap_score(user_terms: set[str], job_text: str) -> int:
    return len(user_terms & _tokenize(job_text))


def _print_debug_overlaps(
    user_terms: set[str],
    candidate_jobs: list[dict[str, Any]],
    scores: list[float],
    limit: int,
) -> None:
    print("[rank_jobs debug] user_terms:", sorted(user_terms))
    if not candidate_jobs:
        print("[rank_jobs debug] no candidate jobs")
        return

    ranked_pairs = sorted(
        zip(candidate_jobs, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    for index, (job, score) in enumerate(ranked_pairs[:limit], start=1):
        job_text = _job_to_text(job)
        overlap = sorted(user_terms & _tokenize(job_text))
        print(
            "[rank_jobs debug]",
            {
                "rank": index,
                "job_id": job.get("_id"),
                "title": job.get("title", ""),
                "score": float(score),
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
        scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten().tolist()
    except ValueError:
        scores = [0.0] * len(candidate_jobs)

    if debug:
        _print_debug_overlaps(user_terms, candidate_jobs, scores, limit=max(0, debug_top_n))

    # Normalization helpers
    def minmax_norm(scores):
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0 for _ in scores]
        return [(s - min_score) / (max_score - min_score) for s in scores]

    def zscore_norm(scores):
        mean = np.mean(scores)
        std = np.std(scores)
        if std == 0:
            return [0.0 for _ in scores]
        return [(s - mean) / std for s in scores]

    def softmax_norm(scores):
        exp_scores = np.exp(scores - np.max(scores))
        sum_exp = np.sum(exp_scores)
        if sum_exp == 0:
            return [0.0 for _ in scores]
        return (exp_scores / sum_exp).tolist()

    def l2_norm(scores):
        norm = np.linalg.norm(scores)
        if norm == 0:
            return [0.0 for _ in scores]
        return (np.array(scores) / norm).tolist()


    scores_minmax = minmax_norm(scores)
    scores_zscore = zscore_norm(scores)
    scores_softmax = softmax_norm(scores)
    scores_l2norm = l2_norm(scores)


    ranked = []
    for job, score, s_minmax, s_zscore, s_softmax, s_l2norm in zip(
        candidate_jobs, scores, scores_minmax, scores_zscore, scores_softmax, scores_l2norm
    ):
        job_copy = dict(job)
        job_copy["score"] = float(score)
        job_copy["score_minmax"] = float(s_minmax)
        job_copy["score_zscore"] = float(s_zscore)
        job_copy["score_softmax"] = float(s_softmax)
        job_copy["score_l2norm"] = float(s_l2norm)
        ranked.append(job_copy)

    return sorted(ranked, key=lambda job: job["score"], reverse=True)
