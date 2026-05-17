"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Optional resume upload endpoint for PR#1. Right now this returns
a simple extracted-text preview and will be expanded in later milestones.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from backend.models.schemas import UploadResumeResponse
from backend.services.resume_parser import build_text_preview, parse_resume_profile

router = APIRouter(tags=["resume"])
logger = logging.getLogger(__name__)
SUPPORTED_RESUME_EXTENSIONS = {".pdf", ".docx"}


@router.post("/upload-resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume and return a structured parse preview."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a filename.",
        )

    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in SUPPORTED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file type. Please upload a PDF or DOCX resume.",
        )

    try:
        file_bytes = await file.read()
    except Exception:
        logger.exception("Failed to read uploaded resume file: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read uploaded file.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        profile = parse_resume_profile(file.filename, file_bytes)

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from uploaded resume.",
            )

        preview = build_text_preview(profile)

    except HTTPException:
        raise

    except Exception:
        logger.exception("Resume parsing failed for file: %s", file.filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse uploaded resume.",
        )

    return UploadResumeResponse(
        filename=file.filename,
        message=(
            "Resume uploaded successfully. "
            "Document parsing is a placeholder and will be expanded in a later milestone."
        ),
        extracted_text_preview=preview,
        profile=profile,
    )