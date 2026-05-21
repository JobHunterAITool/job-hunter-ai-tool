"""
Utilities for extracting required/preferred skill sections from job text.

This module intentionally stays dependency-light so ranking and future pipeline
steps can import it without creating framework or database coupling.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache


SECTION_KEYS = ("required", "preferred")

_HEADING_PATTERNS = {
    "required": (
        "required skills",
        "requirements",
        "required qualifications",
        "minimum qualifications",
        "basic qualifications",
        "must have",
        "must-have",
        "what you need",
    ),
    "preferred": (
        "preferred skills",
        "preferred qualifications",
        "nice to have",
        "nice-to-have",
        "bonus",
        "bonus points",
        "plus",
        "desired skills",
    ),
}

_HEADING_LOOKUP = {
    heading: section
    for section, headings in _HEADING_PATTERNS.items()
    for heading in headings
}
_HEADING_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?"
    r"(?P<heading>"
    + "|".join(re.escape(heading) for heading in _HEADING_LOOKUP)
    + r")(?:\s*:\s*(?P<inline>.*)|\s*)$"
)


def _normalize_skill(skill: object) -> str:
    return str(skill or "").strip().lower()


@lru_cache(maxsize=1024)
def _skill_pattern(skill: str) -> re.Pattern[str]:
    escaped_terms = [re.escape(part) for part in skill.split()]
    phrase = r"[\s\-/]+".join(escaped_terms)
    return re.compile(rf"(?<![A-Za-z0-9]){phrase}(?![A-Za-z0-9])", re.IGNORECASE)


def extract_skill_sections(description: str) -> dict[str, str]:
    """Return required/preferred text sections from a job description.

    If no supported headings are found, both sections are returned as empty
    strings. Text between a required heading and the next recognized heading is
    considered required; same for preferred headings.
    """
    text = str(description or "")
    sections = {section: "" for section in SECTION_KEYS}
    matches = list(_HEADING_RE.finditer(text))

    for index, match in enumerate(matches):
        heading = match.group("heading").strip().lower()
        section = _HEADING_LOOKUP[heading]
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section_text = f"{match.group('inline') or ''} {text[start:end]}".strip()
        if section_text:
            sections[section] = f"{sections[section]} {section_text}".strip()

    return sections


def find_skills_in_text(skills: Iterable[str], text: str) -> list[str]:
    """Return normalized skills that appear as whole terms in text."""
    normalized_skills = sorted(
        {_normalize_skill(skill) for skill in skills if _normalize_skill(skill)}
    )
    return [
        skill
        for skill in normalized_skills
        if _skill_pattern(skill).search(str(text or ""))
    ]


def match_skills_by_section(
    user_skills: Iterable[str],
    description: str,
) -> dict[str, list[str]]:
    """Return normalized user skills found in required/preferred sections."""
    sections = extract_skill_sections(description)
    return {
        section: find_skills_in_text(user_skills, sections[section])
        for section in SECTION_KEYS
    }
