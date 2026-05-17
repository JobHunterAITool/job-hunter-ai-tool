from ml.skills_parser import (
    extract_skill_sections,
    find_skills_in_text,
    match_skills_by_section,
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
