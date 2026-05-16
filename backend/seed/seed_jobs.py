"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Seed script that inserts starter jobs into local MongoDB from
seed_jobs.json so data can be swapped with Adzuna-style JSON later.
"""

import json
from pathlib import Path
from typing import Any

from backend.db import get_jobs_collection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEED_PATH = PROJECT_ROOT / "seed_jobs.json"


def _extract_company(company_field: Any) -> str:
    if isinstance(company_field, dict):
        return str(company_field.get("display_name", "")).strip()
    return str(company_field or "").strip()


def _extract_location(location_field: Any) -> str:
    if isinstance(location_field, dict):
        return str(location_field.get("display_name", "")).strip()
    return str(location_field or "").strip()


def _normalize_skills(skills_field: Any) -> list[str]:
    if isinstance(skills_field, list):
        return [str(skill).strip() for skill in skills_field if str(skill).strip()]
    if isinstance(skills_field, str):
        return [part.strip() for part in skills_field.split(",") if part.strip()]
    return []


def _normalize_seed_job(job: dict[str, Any], index: int) -> dict[str, Any]:
    company = _extract_company(job.get("company"))
    location = _extract_location(job.get("location"))
    skills = _normalize_skills(job.get("skills"))

    normalized: dict[str, Any] = {
        "_id": str(job.get("_id") or job.get("id") or f"seed_{index:03d}"),
        "title": str(job.get("title", "")).strip(),
        "company": company,
        "location": location,
        "skills": skills,
        # Needed for current /jobs response model compatibility.
        "experience_level": str(job.get("experience_level") or "Mid"),
    }

    if "description" in job:
        normalized["description"] = str(job.get("description") or "")
    if "category" in job:
        category = job.get("category")
        if isinstance(category, dict):
            normalized["category"] = str(category.get("label", "")).strip()
        else:
            normalized["category"] = str(category or "").strip()
    if "created" in job:
        normalized["created"] = str(job.get("created") or "")
    if "redirect_url" in job:
        normalized["redirect_url"] = str(job.get("redirect_url") or "")

    return normalized


def _load_jobs_from_json(seed_path: Path = DEFAULT_SEED_PATH) -> list[dict[str, Any]]:
    if not seed_path.exists():
        return []

    raw_payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if isinstance(raw_payload, dict):
        raw_jobs = raw_payload.get("results", [])
    elif isinstance(raw_payload, list):
        raw_jobs = raw_payload
    else:
        return []

    jobs: list[dict[str, Any]] = []
    for index, item in enumerate(raw_jobs, start=1):
        if isinstance(item, dict):
            jobs.append(_normalize_seed_job(item, index))
    return jobs


def load_seed_jobs():
    """Insert seed jobs from seed_jobs.json if the collection is empty."""
    jobs_collection = get_jobs_collection()
    jobs = _load_jobs_from_json()
    # Idempotent seed behavior: only insert starter jobs on an empty collection.
    if jobs_collection.count_documents({}) == 0 and jobs:
        jobs_collection.insert_many(jobs)


if __name__ == "__main__":
    # Allows running this file directly for quick local seeding.
    load_seed_jobs()
