"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: Seed script that inserts fake starter jobs into local MongoDB so
the app has usable data for demos and frontend integration.
"""

from backend.db import get_jobs_collection

DEFAULT_JOBS = [
    {
        "title": "Software Engineer",
        "company": "Amazon",
        "location": "Remote",
        "skills": ["Python", "AWS", "Docker"],
        "experience_level": "Mid",
    },
    {
        "title": "Backend Developer",
        "company": "Google",
        "location": "Mountain View, CA",
        "skills": ["Python", "Golang", "Kubernetes"],
        "experience_level": "Mid",
    },
    {
        "title": "Data Engineer",
        "company": "Microsoft",
        "location": "Remote",
        "skills": ["Python", "SQL", "Azure"],
        "experience_level": "Mid",
    },
    {
        "title": "DevOps Engineer",
        "company": "Netflix",
        "location": "Los Angeles, CA",
        "skills": ["AWS", "Terraform", "Docker"],
        "experience_level": "Senior",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "Tesla",
        "location": "Austin, TX",
        "skills": ["Python", "TensorFlow", "PyTorch"],
        "experience_level": "Mid",
    },
    {
        "title": "Frontend Engineer",
        "company": "Spotify",
        "location": "Remote",
        "skills": ["React", "TypeScript", "CSS"],
        "experience_level": "Junior",
    },
    {
        "title": "Full Stack Engineer",
        "company": "Airbnb",
        "location": "San Francisco, CA",
        "skills": ["Python", "React", "AWS"],
        "experience_level": "Mid",
    },
    {
        "title": "QA Automation Engineer",
        "company": "Apple",
        "location": "Cupertino, CA",
        "skills": ["Python", "Selenium", "CI/CD"],
        "experience_level": "Mid",
    },
    {
        "title": "Technical Project Manager",
        "company": "Facebook",
        "location": "Remote",
        "skills": ["Scrum", "Communication", "Budgeting"],
        "experience_level": "Senior",
    },
    {
        "title": "Cloud Architect",
        "company": "IBM",
        "location": "New York, NY",
        "skills": ["AWS", "Azure", "Cloud Security"],
        "experience_level": "Senior",
    },
]


def load_seed_jobs():
    """Insert default seed jobs if the collection is empty."""
    jobs_collection = get_jobs_collection()
    # Idempotent seed behavior: only insert starter jobs on an empty collection.
    if jobs_collection.count_documents({}) == 0:
        jobs_collection.insert_many(DEFAULT_JOBS)


if __name__ == "__main__":
    # Allows running this file directly for quick local seeding.
    load_seed_jobs()
