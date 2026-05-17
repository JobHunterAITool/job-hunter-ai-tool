import json
from pathlib import Path

from backend.models.schemas import SearchRequest
from backend.services.ranking import rank_jobs


def _load_seed_jobs() -> list[dict]:
    seed_path = Path(__file__).resolve().parents[1] / "seed_jobs.json"
    payload = json.loads(seed_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("results", [])
    return []


def test_backend_adapter_ranks_seed_jobs_without_mongo() -> None:
    jobs = _load_seed_jobs()
    assert jobs, "Expected seed_jobs.json to contain job records"

    search_request = SearchRequest(
        job_title="Backend Engineer",
        skills=["Python", "FastAPI", "Docker"],
        location="Remote",
        experience_level=3,
    )

    print("\nINPUT (SearchRequest):")
    print(search_request.model_dump())

    print("\nINPUT (seed jobs count):", len(jobs))

    ranked_jobs = rank_jobs(search_request, jobs, top_n=10)

    print("\nOUTPUT (top 5 ranked jobs):")
    print(json.dumps(ranked_jobs[:5], indent=2))

    assert ranked_jobs, "Expected ranked results from backend adapter"
    assert len(ranked_jobs) <= 10
    assert all("score" in job for job in ranked_jobs)
    assert all(isinstance(job["score"], float) for job in ranked_jobs)

    scores = [job["score"] for job in ranked_jobs]
    assert scores == sorted(scores, reverse=True), "Expected descending score order"

    required_fields = {"title", "company", "location", "score"}
    for job in ranked_jobs:
        assert required_fields.issubset(job.keys())
