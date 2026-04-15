"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Pydantic schemas for request/response contracts so frontend and
backend stay aligned while the ML ranking module is still in progress.
"""

from typing import Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    # Contract expected by /search from frontend.
    job_title: str = Field(..., examples=["Software Engineer"])
    skills: list[str] = Field(..., examples=[["Python", "AWS"]])
    location: str = Field(..., examples=["Remote"])
    experience_level: str = Field(..., examples=["Mid"])


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
    experience_level: str


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
