import logging
from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import backend.routes.jobs as jobs_route
import backend.routes.search as search_route
import backend.routes.upload_resume as upload_route
from backend.routes.jobs import router as jobs_router
from backend.routes.search import router as search_router
from backend.routes.upload_resume import router as upload_router


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
        window = self._docs[self._skip :]
        if self._limit is not None:
            window = window[: self._limit]
        return iter(window)


class FakeCollection:
    def __init__(self, docs: list[dict]):
        self._docs = list(docs)

    def find(self, _query: dict | None = None, projection: dict | None = None) -> FakeCursor:
        projected_docs: list[dict] = []
        for original in self._docs:
            row = dict(original)
            if projection and projection.get("_id") == 0:
                row.pop("_id", None)
            projected_docs.append(row)
        return FakeCursor(projected_docs)

    def count_documents(self, _query: dict | None = None) -> int:
        return len(self._docs)


class BrokenCollection:
    def find(self, *_args, **_kwargs):
        raise RuntimeError("db read failed")

    def count_documents(self, *_args, **_kwargs):
        raise RuntimeError("db count failed")


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(jobs_router)
    app.include_router(search_router)
    app.include_router(upload_router)
    with TestClient(app) as test_client:
        yield test_client


def _job_doc(index: int) -> dict:
    return {
        "_id": f"id-{index}",
        "title": f"Backend Engineer {index}",
        "company": f"Company {index}",
        "location": "Remote",
        "skills": ["Python", "FastAPI"],
        "experience_level": "Mid",
    }


def _search_payload() -> dict:
    return {
        "job_title": "Backend Engineer",
        "skills": ["Python", "FastAPI"],
        "location": "Remote",
        "experience_level": "Mid",
    }


def test_search_happy_path_returns_ranked_results(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_job_doc(i) for i in range(12)])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    response = client.post("/search", json=_search_payload())
    assert response.status_code == 200

    body = response.json()
    assert len(body["results"]) == 10
    scores = [job["score"] for job in body["results"]]
    assert scores == sorted(scores, reverse=True)


def test_search_empty_result_when_no_jobs(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    response = client.post("/search", json=_search_payload())
    assert response.status_code == 200
    assert response.json() == {"results": []}


def test_search_returns_422_for_invalid_payload(client: TestClient) -> None:
    payload = {
        "job_title": "   ",
        "skills": [],
        "location": "Remote",
        "experience_level": "Mid",
    }
    response = client.post("/search", json=payload)
    assert response.status_code == 422
    detail_text = str(response.json().get("detail", ""))
    assert "skills" in detail_text or "job_title" in detail_text


def test_search_returns_400_for_value_error_from_ranker(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_job_doc(1)])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    def raise_value_error(*_args, **_kwargs):
        raise ValueError("bad ranking input")

    monkeypatch.setattr(search_route, "rank_jobs_stub", raise_value_error)

    response = client.post("/search", json=_search_payload())
    assert response.status_code == 400
    assert "Invalid search input" in response.json()["detail"]


def test_search_returns_500_and_logs_when_ranker_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_collection = FakeCollection([_job_doc(1)])
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: fake_collection)

    def raise_runtime_error(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(search_route, "rank_jobs_stub", raise_runtime_error)

    with caplog.at_level(logging.ERROR):
        response = client.post("/search", json=_search_payload())

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to rank jobs."
    assert any(
        "Unexpected ranking failure in /search" in record.message
        for record in caplog.records
    )


def test_search_returns_500_and_logs_when_db_read_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(search_route, "get_jobs_collection", lambda: BrokenCollection())

    with caplog.at_level(logging.ERROR):
        response = client.post("/search", json=_search_payload())

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch jobs from the database."
    assert any(
        "Failed to read jobs from MongoDB for /search" in record.message
        for record in caplog.records
    )


def test_jobs_happy_path_returns_page_window(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([_job_doc(i) for i in range(25)])
    monkeypatch.setattr(jobs_route, "get_jobs_collection", lambda: fake_collection)

    response = client.get("/jobs?page=2&limit=10")
    assert response.status_code == 200

    body = response.json()
    assert body["page"] == 2
    assert body["limit"] == 10
    assert body["total"] == 25
    assert len(body["results"]) == 10


def test_jobs_empty_result_set(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_collection = FakeCollection([])
    monkeypatch.setattr(jobs_route, "get_jobs_collection", lambda: fake_collection)

    response = client.get("/jobs?page=1&limit=20")
    assert response.status_code == 200

    body = response.json()
    assert body["total"] == 0
    assert body["results"] == []


def test_jobs_returns_422_for_invalid_query(client: TestClient) -> None:
    assert client.get("/jobs?page=0&limit=20").status_code == 422
    assert client.get("/jobs?page=1&limit=101").status_code == 422


def test_jobs_returns_500_and_logs_when_db_fails(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(jobs_route, "get_jobs_collection", lambda: BrokenCollection())

    with caplog.at_level(logging.ERROR):
        response = client.get("/jobs?page=1&limit=20")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to fetch jobs from the database."
    assert any(
        "Failed to fetch paginated jobs for /jobs" in record.message
        for record in caplog.records
    )


def test_upload_resume_happy_path(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        upload_route,
        "extract_text_preview",
        lambda _filename, _bytes: "Backend Engineer Python FastAPI",
    )
    response = client.post(
        "/upload-resume",
        files={"file": ("resume.pdf", b"fake bytes", "application/pdf")},
    )
    assert response.status_code == 200

    body = response.json()
    assert body["filename"] == "resume.pdf"
    assert body["extracted_text_preview"] == "Backend Engineer Python FastAPI"


def test_upload_resume_empty_preview_result(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(upload_route, "extract_text_preview", lambda _filename, _bytes: None)
    response = client.post(
        "/upload-resume",
        files={"file": ("resume.docx", b"fake bytes", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert response.status_code == 200
    assert response.json()["extracted_text_preview"] is None


def test_upload_resume_returns_415_for_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/upload-resume",
        files={"file": ("resume.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 415
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_resume_returns_400_for_empty_file(client: TestClient) -> None:
    response = client.post(
        "/upload-resume",
        files={"file": ("resume.pdf", b"", "application/pdf")},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_upload_resume_returns_500_and_logs_on_parser_error(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def raise_parser_error(_filename: str, _file_bytes: bytes):
        raise RuntimeError("parser crashed")

    monkeypatch.setattr(upload_route, "extract_text_preview", raise_parser_error)
    with caplog.at_level(logging.ERROR):
        response = client.post(
            "/upload-resume",
            files={"file": ("resume.pdf", b"fake bytes", "application/pdf")},
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to parse uploaded resume."
    assert any(
        "Resume parsing failed for file" in record.message
        for record in caplog.records
    )
