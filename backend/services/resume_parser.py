"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Lightweight resume text extraction helpers (PDF/DOCX) used by the
optional upload endpoint during early backend milestones.
"""

from io import BytesIO
from typing import Optional


def _extract_pdf_text(file_bytes: bytes) -> Optional[str]:
    try:
        # Optional dependency: backend still runs if PDF parsing libs are missing.
        import pdfplumber  # type: ignore
    except ImportError:
        return None

    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            first_page = pdf.pages[0] if pdf.pages else None
            return first_page.extract_text() if first_page else None
    except Exception:
        return None


def _extract_docx_text(file_bytes: bytes) -> Optional[str]:
    try:
        # Optional dependency: DOCX parsing can be installed when needed.
        from docx import Document  # type: ignore
    except ImportError:
        return None

    try:
        document = Document(BytesIO(file_bytes))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs if paragraph.text)
        return text or None
    except Exception:
        return None


def extract_text_preview(filename: str, file_bytes: bytes, max_chars: int = 350) -> Optional[str]:
    """Return a short plain-text preview from a PDF or DOCX resume file."""
    lowered = filename.lower()
    extracted: Optional[str] = None

    # Route parser based on file extension for this milestone.
    if lowered.endswith(".pdf"):
        extracted = _extract_pdf_text(file_bytes)
    elif lowered.endswith(".docx"):
        extracted = _extract_docx_text(file_bytes)

    if not extracted:
        return None

    # Normalize whitespace so preview stays clean in the frontend UI.
    normalized = " ".join(extracted.split())
    return normalized[:max_chars] if normalized else None
