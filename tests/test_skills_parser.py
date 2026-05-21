import json
from pathlib import Path

from ml.rank_jobs import rank_jobs
from ml.skills_parser import (
    extract_skill_sections,
    find_skills_in_text,
    match_skills_by_section,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "tests" / "outputs" / "skills_parser_ranked_jobs_debug.json"
APPENDED_SKILL_FIELDS = (
    "matched_skills",
    "matched_required_skills",
    "matched_preferred_skills",
    "matched_skills_count",
    "skill_score",
    "required_skill_score",
    "preferred_skill_score",
)


def test_extract_skill_sections_splits_required_and_preferred_text() -> None:
    description = """
    Required Skills:
    Python, SQL, and production API experience.

    Preferred Qualifications:
    Docker and Kubernetes are a plus.
    """

    sections = extract_skill_sections(description)

    assert "Python" in sections["required"]
    assert "Docker" not in sections["required"]
    assert "Docker" in sections["preferred"]


def test_extract_skill_sections_accepts_inline_heading_text() -> None:
    description = """
    Requirements: Python and SQL.
    Preferred Skills: AWS.
    """

    sections = extract_skill_sections(description)

    assert sections["required"] == "Python and SQL."
    assert sections["preferred"] == "AWS."


def test_match_skills_by_section_returns_normalized_matches() -> None:
    description = """
    Requirements:
    Python and machine-learning experience.

    Nice to Have:
    AWS or Docker.
    """

    matches = match_skills_by_section(
        ["Python", "Machine Learning", "AWS", "React"],
        description,
    )

    assert matches == {
        "required": ["machine learning", "python"],
        "preferred": ["aws"],
    }


def test_find_skills_in_text_matches_whole_terms_only() -> None:
    matches = find_skills_in_text(["R", "React"], "React applications")

    assert matches == ["react"]


def test_exports_ranked_job_skill_scores_debug_json() -> None:
    jobs = [
        {
            "_id": "sectioned",
            "title": "Platform Engineer",
            "job_description_text": """
            Requirements:
            Python and SQL experience.

            Nice to Have:
            Docker experience.
            """,
        }
    ]
    user_profile = {"skills": ["Python", "SQL", "Docker"]}

    ranked_jobs = rank_jobs(user_profile, jobs, debug=False)
    debug_payload = {
        "user_profile": user_profile,
        "jobs_before_backend_return": [
            {
                "_id": job.get("_id"),
                "title": job.get("title"),
                "appended_skill_fields": {
                    field: job.get(field)
                    for field in APPENDED_SKILL_FIELDS
                    if field in job
                },
            }
            for job in ranked_jobs
        ],
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(debug_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    exported_payload = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    appended_fields = exported_payload["jobs_before_backend_return"][0][
        "appended_skill_fields"
    ]

    assert OUTPUT_PATH.exists()
    assert appended_fields["matched_required_skills"] == ["python", "sql"]
    assert appended_fields["matched_preferred_skills"] == ["docker"]
    assert appended_fields["required_skill_score"] == 2 / 3
    assert appended_fields["preferred_skill_score"] == 1 / 3
