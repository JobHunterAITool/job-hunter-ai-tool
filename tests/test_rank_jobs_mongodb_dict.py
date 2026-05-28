import json
from pathlib import Path

from backend.models.schemas import SearchRequest
from backend.services.ranking import (
    _search_request_to_user_profile,
    rank_jobs as backend_rank_jobs,
)
from ml.rank_jobs import rank_jobs as ml_rank_jobs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MONGODB_FIXTURE_PATHS = [
    PROJECT_ROOT / "pipeline" / "pulled_jobs_from_mongodb.json",
    PROJECT_ROOT / "pulled_jobs_from_mongodb.json",
]
OUTPUT_PATH = (
    PROJECT_ROOT
    / "tests"
    / "outputs"
    / "ranked_jobs_mongodb_backend_integration.json"
)
APPENDED_RANKER_FIELDS = (
    "score",
    "matched_skills",
    "matched_skills_count",
)


def _load_mongodb_jobs() -> list[dict]:
    for fixture_path in MONGODB_FIXTURE_PATHS:
        if fixture_path.exists():
            payload = json.loads(fixture_path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                return payload
            if isinstance(payload, dict):
                return payload.get("results", [])
            return []

    expected_paths = ", ".join(path.name for path in MONGODB_FIXTURE_PATHS)
    raise FileNotFoundError(f"Expected one of these fixtures: {expected_paths}")


def _job_identity(job: dict) -> dict:
    return {
        "_id": job.get("_id"),
        "id": job.get("id"),
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
    }


def _appended_ranker_fields(job: dict) -> dict:
    return {
        field: job.get(field)
        for field in APPENDED_RANKER_FIELDS
        if field in job
    }


def _ranker_export_payload(
    search_request: SearchRequest,
    candidate_count: int,
    ranked_jobs: list[dict],
) -> dict:
    return {
        "search_request": search_request.model_dump(),
        "candidate_count": candidate_count,
        "returned_to_backend_count": len(ranked_jobs),
        "appended_ranker_fields": list(APPENDED_RANKER_FIELDS),
        "jobs_before_backend_return": [
            {
                **_job_identity(job),
                "appended_fields": _appended_ranker_fields(job),
            }
            for job in ranked_jobs
        ],
    }


def test_backend_adapter_ranks_mongodb_jobs_without_mongo() -> None:
    jobs = _load_mongodb_jobs()
    assert jobs, "Expected pulled_jobs_from_mongodb.json to contain job records"

    search_request = SearchRequest(
        job_title="Software Engineer Intern",
        skills=["Computer Science", "Python", "Data Analysis"],
        location="Remote",
        experience_level=0,
    )

    print("\nINPUT (SearchRequest):")
    print(search_request.model_dump())

    print("\nINPUT (MongoDB jobs count):", len(jobs))

    user_profile = _search_request_to_user_profile(search_request)
    ml_ranked_jobs = ml_rank_jobs(user_profile, jobs)
    ranked_jobs = backend_rank_jobs(search_request, jobs, top_n=10)
    ml_jobs_returned_to_backend = ml_ranked_jobs[:10]

    assert ranked_jobs == ml_jobs_returned_to_backend

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(
            _ranker_export_payload(
                search_request,
                candidate_count=len(jobs),
                ranked_jobs=ml_jobs_returned_to_backend,
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # print("\nOUTPUT (top 5 ranked MongoDB jobs):")
    # print(json.dumps(ml_jobs_returned_to_backend[:5], indent=2))

    assert ranked_jobs, "Expected ranked results from backend adapter"
    assert len(ranked_jobs) <= 10
    assert OUTPUT_PATH.exists()
    assert all("score" in job for job in ranked_jobs)
    assert all(isinstance(job["score"], float) for job in ranked_jobs)
    assert all(0.0 <= job["score"] <= 1.0 for job in ranked_jobs)
    assert all("matched_skills" in job for job in ranked_jobs)
    assert all("matched_skills_count" in job for job in ranked_jobs)

    print("RETURNED SCORES:", [job["score"] for job in ranked_jobs])

    scores = [job["score"] for job in ranked_jobs]
    assert scores == sorted(scores, reverse=True), "Expected descending score order"

    required_fields = {"title", "company", "location", "score"}
    for job in ranked_jobs:
        assert required_fields.issubset(job.keys())
