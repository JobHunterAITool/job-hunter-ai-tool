"""
Author: Michael Mart, Carl Ikai
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Resume parsing + structured extraction for ML pipeline.
"""

from io import BytesIO
from typing import Optional, List, Dict
import re
import logging

logger = logging.getLogger(__name__)


def _extract_pdf_text(file_bytes: bytes) -> Optional[str]:
    """Extract plain text from a PDF file."""

    try:
        import pdfplumber
    except ImportError:
        return None

    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            return text.strip() or None
    except Exception:
        return None


def _extract_docx_text(file_bytes: bytes) -> Optional[str]:
    """Extract plain text from a DOCX file."""

    try:
        from docx import Document
    except ImportError:
        return None

    try:
        document = Document(BytesIO(file_bytes))

        text = "\n".join(
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

        return text.strip() or None

    except Exception:
        return None


def extract_full_text(filename: str, file_bytes: bytes) -> Optional[str]:
    """Route file extraction based on file extension."""

    lowered = filename.lower()

    if lowered.endswith(".pdf"):
        return _extract_pdf_text(file_bytes)

    if lowered.endswith(".docx"):
        return _extract_docx_text(file_bytes)

    return None


KNOWN_SKILLS = [
    "Python", "JavaScript", "React", "FastAPI", "SQL", "MongoDB", "AWS",
    "Docker", "Git", "REST API", "HTML", "CSS", "Node", "Express",
    "Java", "C++", "Django", "Flask", "PostgreSQL", "Redis",
    "Kubernetes", "Linux", "GraphQL", "CI/CD", "Terraform",
    "TypeScript", "Vue.js", "Next.js", "Tailwind CSS", "Redux", "Vite",
    "Figma", "Jest", "Cypress", "REST APIs", "Pandas", "NumPy",
    "Scikit-learn", "TensorFlow", "PyTorch", "Matplotlib", "Jupyter",
    "Apache Spark", "Airflow", "Tableau", "Swift", "SwiftUI", "Kotlin",
    "Android Studio", "Firebase", "React Native", "Xcode", "SQLite",
    "Azure", "Google Cloud Platform", "Jenkins", "Ansible", "Prometheus",
    "Grafana", "Nginx", "Bash", "Linux Administration", "Helm",
    "Wireshark", "Metasploit", "Burp Suite", "Kali Linux", "SIEM",
    "Network Security", "Penetration Testing", "Incident Response",
    "Splunk", "Cryptography", "Spring Boot", "Oracle SQL", "SOAP APIs",
    "JSP", "Hibernate", "Maven", "Apache Tomcat", "XML", "SVN",
]

JOB_TITLE_KEYWORDS = [
    "software engineer", "software developer", "frontend developer",
    "front end developer", "backend developer", "back end developer",
    "full stack developer", "full-stack developer", "web developer",
    "data analyst", "data engineer", "machine learning engineer",
    "devops engineer", "mobile developer", "ios developer",
    "android developer", "cybersecurity analyst", "security analyst",
    "systems administrator", "cloud engineer",
]

US_STATE_PATTERN = r"\b[A-Z][a-zA-Z .'-]+,\s*[A-Z]{2}\b"


def extract_skills(text: str) -> List[str]:
    """Find matching skills from skills list."""

    found_skills = []
    text_lower = text.lower()

    for skill in KNOWN_SKILLS:
        escaped_skill = re.escape(skill.lower())

        pattern = (
            r"(?<![a-zA-Z0-9])"
            + escaped_skill +
            r"(?![a-zA-Z0-9])"
        )

        if re.search(pattern, text_lower):
            found_skills.append(skill)

    return found_skills


def extract_job_title(text: str) -> str:
    """Extract a job title."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text_lower = text.lower()

    # Check for labeled role sections first
    for line in lines:
        lowered = line.lower()

        if lowered.startswith("target role:"):
            return line.split(":", 1)[1].strip()

        if lowered.startswith("desired role:"):
            return line.split(":", 1)[1].strip()

        if lowered.startswith("job title:"):
            return line.split(":", 1)[1].strip()

        if lowered.startswith("position:"):
            return line.split(":", 1)[1].strip()

        if lowered.startswith("role:"):
            return line.split(":", 1)[1].strip()

        if lowered.startswith("seeking:"):
            return line.split(":", 1)[1].strip()

    # Check software related job titles
    for keyword in JOB_TITLE_KEYWORDS:
        if keyword in text_lower:
            return keyword.title().replace("Devops", "DevOps")

    # Look for lines containing role related words
    for line in lines[:20]:
        lowered = line.lower()

        if (
            "engineer" in lowered
            or "developer" in lowered
            or "analyst" in lowered
            or "administrator" in lowered
        ):
            return line

    return "Unknown"


def extract_location(text: str) -> str:
    """Extract location from resume."""

    lines = [line.strip() for line in text.splitlines() if line.strip()]

    for line in lines:
        lowered = line.lower()

        if lowered.startswith("location:"):
            possible_location = line.split(":", 1)[1].strip()

            match = re.search(
                US_STATE_PATTERN,
                possible_location
            )

            if match:
                return match.group(0)

        if lowered.startswith("address:"):
            possible_location = line.split(":", 1)[1].strip()

            match = re.search(
                US_STATE_PATTERN,
                possible_location
            )

            if match:
                return match.group(0)

        if lowered.startswith("based in"):
            match = re.search(
                US_STATE_PATTERN,
                line
            )

            if match:
                return match.group(0)

    # Fallback search through full resume text
    match = re.search(US_STATE_PATTERN, text)

    if match:
        return match.group(0).strip()

    return "Unknown"


def extract_experience_years(text: str) -> int:
    """Extract years of experience."""

    text_lower = text.lower()

    # Check for direct mentions e.g. "3 years experience"
    year_matches = re.findall(
        r"(\d+)\+?\s*(?:years|yrs)",
        text_lower
    )

    if year_matches:
        return max(int(year) for year in year_matches)

    current_year = 2026

    # Check for date ranges
    date_ranges = re.findall(
        r"(20\d{2}|19\d{2})\s*[-–—]\s*"
        r"(present|current|now|20\d{2}|19\d{2})",
        text_lower
    )

    total_years = 0

    for start, end in date_ranges:
        start_year = int(start)

        if end in ["present", "current", "now"]:
            end_year = current_year
        else:
            end_year = int(end)

        if end_year >= start_year:
            total_years += end_year - start_year

    return total_years


def parse_resume_profile(
    filename: str,
    file_bytes: bytes
) -> Optional[Dict]:
    """Build resume profile."""

    text = extract_full_text(filename, file_bytes)

    if not text:
        return None

    profile = {
        "job_title": extract_job_title(text),
        "skills": extract_skills(text),
        "location": extract_location(text),
        "experience_level": extract_experience_years(text),
    }

    logger.info("Parsed resume profile: %s", profile)

    return profile


def build_text_preview(
    profile: Dict,
    max_chars: int = 350,
) -> str:
    """Create frontend preview from parsed resume profile."""

    skills = profile.get("skills", [])
    skills_text = ", ".join(skills) if skills else "None found"

    preview = (
        f"• Job title: {profile.get('job_title', 'Unknown')}\n"
        f"• Skills: {skills_text}\n"
        f"• Location: {profile.get('location', 'Unknown')}\n"
        f"• Years of experience: "
        f"{profile.get('experience_level', '0')}"
    )

    return preview[:max_chars]