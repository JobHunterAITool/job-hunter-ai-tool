"""
ML ranking module for JobHunterAI.

Public interface
----------------
    rank_jobs(user_text: str, jobs: list[dict]) -> list[dict]

The backend calls rank_jobs() from its POST /search handler after
querying MongoDB for candidate job documents and passing them here
together with the user's profile text.
"""


def rank_jobs(user_text: str, jobs: list[dict[str]]) -> list[dict[str]]:
    """Rank a list of job documents by relevance to the user's profile text.

    Parameters
    ----------
    user_text : str
        Plain text extracted from the user's uploaded resume, or assembled
        from the manual input form fields (title + skills + location +
        experience level).  Must be a non-empty string.
    jobs : list[dict]
        Job postings retrieved from MongoDB.  Each posting is expected to
        contain at least the following fields, as documented below::

            {
                "_id":         str,
                "title":       str,
                "company":     str,
                "location":    str,
                "description": str,
                "skills":      list[str],
                "source":      str,
                "fetched_at":  str,   # ISO 8601 timestamp string
                "normalized":  bool,
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
    Current implementation: placeholder stub — returns jobs in their original
    order with a dummy score of 0.0 so that the backend POST /search endpoint
    is testable end-to-end before the real ML logic is wired in.

    """
    if not user_text or not user_text.strip():
        raise ValueError("user_text must be a non-empty string")
    if not jobs:
        raise ValueError("jobs list must not be empty")

    # --- Stub implementation ---
    # Return a copy of the input list with a placeholder score attached.
    # Replace this block entirely in Progress Report #2.
    ranked = []
    for job in jobs:
        job_copy = dict(job)
        job_copy["score"] = 0.0
        ranked.append(job_copy)
    # Sort the ranked jobs by their scores in descending order
    return sorted(ranked, key=lambda job: job["score"], reverse=True)
