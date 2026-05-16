"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Pydantic schemas for request/response contracts so frontend and
backend stay aligned while the ML ranking module is still in progress.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SearchRequest(BaseModel):
    # Contract expected by /search from frontend.
    job_title: str = Field(..., min_length=1, examples=["Software Engineer"])
    skills: list[str] = Field(..., min_length=1, examples=[["Python", "AWS"]])
    location: str = Field(..., min_length=1, examples=["Remote"])
    experience_level: int = Field(..., ge=0, examples=[3])

    @field_validator("job_title", "location", mode="before")
    @classmethod
    def _validate_non_empty_text(cls, value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("must be a non-empty string")
        return value.strip()

    @field_validator("skills", mode="before")
    @classmethod
    def _validate_skills(cls, value: object) -> list[str]:
        if not isinstance(value, list) or not value:
            raise ValueError("skills must be a non-empty list of strings")

        normalized_skills = []
        for skill in value:
            if not isinstance(skill, str) or not skill.strip():
                raise ValueError("each skill must be a non-empty string")
            normalized_skills.append(skill.strip())
        return normalized_skills


class ResumeProfile(BaseModel):
    job_title: str
    skills: list[str]
    location: str
    experience_level: int


class RankedJobResult(BaseModel):
    title: str
    company: str
    location: str
    score: float
    matched_skills: list[str]


class SearchResponse(BaseModel):
    # Ranked results list returned by the stub (future ML output shape).
    results: list[RankedJobResult]


class JobDocument(BaseModel):
    title: str
    company: str
    location: str
    skills: list[str]
    experience_level: int


class PaginatedJobsResponse(BaseModel):
    # Standard pagination wrapper for /jobs listing endpoint.
    page: int
    limit: int
    total: int
    results: list[JobDocument]


class UploadResumeResponse(BaseModel):
    filename: str
    message: str
    extracted_text_preview: Optional[str] = None
    profile: Optional[ResumeProfile] = None