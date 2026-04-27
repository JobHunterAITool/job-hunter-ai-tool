from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.jobs as jobs_route
import backend.routes.search as search_route
from backend.routes.jobs import router as jobs_router
from backend.routes.search import router as search_router


class FakeCursor:
    def __init__(self, docs: list[dict]):
        self._docs = list(docs)
        self._skip = 0
        self._limit: int | None = None

    def skip(self, amount: int) -> "FakeCursor":
        self._skip = amount
        return self

    def limit(self, amount: int) -> "FakeCursor":
        self._limit = amount
        return self

    def __iter__(self) -> Iterator[dict]:
        sliced_docs = self._docs[self._skip :]
        if self._limit is not None:
            sliced_docs = sliced_docs[: self._limit]
        return iter(sliced_docs)


class FakeCollection:
    def __init__(self, docs: list[dict]):
        self._docs = list(docs)

    def find(self, _query: dict | None = None, projection: dict | None = None) -> FakeCursor:
        projected_docs: list[dict] = []
        for original_doc in self._docs:
            doc_copy = dict(original_doc)
            if projection and projection.get("_id") == 0:
                doc_copy.pop("_id", None)
            projected_docs.append(doc_copy)
        return FakeCursor(projected_docs)

    def count_documents(self, _query: dict | None = None) -> int:
        return len(self._docs)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(search_router)
    app.include_router(jobs_router)
    with TestClient(app) as test_client:
        yield test_client


def _build_search_payload() -> dict:
    return {
        "job_title": "Backend Engineer",
        "skills": ["Python", "FastAPI"],
        "location": "Remote",
        "experience_level": "Mid",
    }


def _build_job_doc(index: int) -> dict:
    return {
        "_id": f"job-{index}",
        "title": f"Job {index}",
        "company": f"Company {index}",
        "location": "Remote",
        "skills": ["Python", "FastAPI"],
        "experience_level": "Mid",
    }


def test_search_caps_candidates_to_200_and_returns_top_20_sorted(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_build_job_doc(i) for i in range(250)])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    observed: dict[str, int] = {}

    def fake_rank_jobs(_search_input: dict, jobs: list[dict]) -> list[dict]:
        observed["candidate_count"] = len(jobs)
        unsorted_results = []
        for index, job in enumerate(jobs):
            unsorted_results.append(
                {
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "score": float(index % 9),
                    "matched_skills": ["python"],
                }
            )
        return list(reversed(unsorted_results))

    monkeypatch.setattr(search_route, "rank_jobs", fake_rank_jobs)

    response = client.post("/search", json=_build_search_payload())
    assert response.status_code == 200

    body = response.json()
    assert observed["candidate_count"] == 200
    assert len(body["results"]) == 20

    scores = [row["score"] for row in body["results"]]
    assert scores == sorted(scores, reverse=True)
    assert set(body["results"][0].keys()) == {
        "title",
        "company",
        "location",
        "score",
        "matched_skills",
    }


def test_search_returns_empty_results_when_no_jobs_in_collection(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    def fail_if_called(*_args, **_kwargs):
        raise AssertionError("rank_jobs should not be called with empty job candidates")

    monkeypatch.setattr(search_route, "rank_jobs", fail_if_called)

    response = client.post("/search", json=_build_search_payload())
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_jobs_pagination_returns_requested_slice(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_build_job_doc(i) for i in range(35)])
    monkeypatch.setattr(jobs_route, "get_jobs_collection", lambda: fake_collection)

    response = client.get("/jobs?page=2&limit=10")
    assert response.status_code == 200

    body = response.json()
    assert body["page"] == 2
    assert body["limit"] == 10
    assert body["total"] == 35
    assert len(body["results"]) == 10
    assert body["results"][0]["title"] == "Job 10"
    assert body["results"][-1]["title"] == "Job 19"


def test_jobs_pagination_validation_errors(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_build_job_doc(i) for i in range(3)])
    monkeypatch.setattr(jobs_route, "get_jobs_collection", lambda: fake_collection)

    assert client.get("/jobs?page=0&limit=10").status_code == 422
    assert client.get("/jobs?page=1&limit=101").status_code == 422
