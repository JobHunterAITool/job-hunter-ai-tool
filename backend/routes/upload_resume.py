"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Optional resume upload endpoint for PR#1. Right now this returns
a simple extracted-text preview and will be expanded in later milestones.
"""

from fastapi import APIRouter, File, UploadFile

from backend.models.schemas import UploadResumeResponse
from backend.services.resume_parser import extract_text_preview

router = APIRouter(tags=["resume"])


@router.post("/upload-resume", response_model=UploadResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume and return a placeholder parse preview for PR#1."""
    # Read uploaded file bytes so parser service can handle PDF or DOCX formats.
    file_bytes = await file.read()

    # This is intentionally lightweight for PR#1 and will expand in later sprints.
    preview = extract_text_preview(file.filename, file_bytes)

    return UploadResumeResponse(
        filename=file.filename,
        message=(
            "Resume uploaded successfully. "
            "Document parsing is a placeholder and will be expanded in a later milestone."
        ),
        extracted_text_preview=preview,
    )
