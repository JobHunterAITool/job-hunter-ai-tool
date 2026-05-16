import json
import unittest
from pathlib import Path

from ml.rank_jobs import rank_jobs


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MONGODB_FIXTURE_PATHS = [
    PROJECT_ROOT / "pipeline" / "pulled_jobs_from_mongodb.json",
]
OUTPUT_PATH = PROJECT_ROOT / "tests" / "outputs" / "ranked_jobs_mongodb_response.json"


def _load_mongodb_jobs() -> list[dict]:
    for fixture_path in MONGODB_FIXTURE_PATHS:
        if fixture_path.exists():
            jobs = json.loads(fixture_path.read_text(encoding="utf-8"))
            if not isinstance(jobs, list):
                raise TypeError(f"{fixture_path.name} must contain a JSON list")
            return jobs

    expected_paths = ", ".join(path.name for path in MONGODB_FIXTURE_PATHS)
    raise FileNotFoundError(f"Expected one of these fixtures: {expected_paths}")


class RankJobsMongoDBDataTests(unittest.TestCase):
    MONGODB_JOBS = _load_mongodb_jobs()

    def test_mongodb_data_loads_with_rankable_fields(self) -> None:
        """Real MongoDB data loads and includes fields consumed by rank_jobs."""
        self.assertTrue(self.MONGODB_JOBS)
        self.assertIsInstance(self.MONGODB_JOBS, list)
        self.assertTrue(any(job.get("title") for job in self.MONGODB_JOBS))
        self.assertTrue(any(job.get("job_description_text") for job in self.MONGODB_JOBS))
        self.assertTrue(any(job.get("skills") for job in self.MONGODB_JOBS))

    def test_ranks_real_mongodb_jobs_and_writes_json_response(self) -> None:
        """Ranking real MongoDB jobs returns scored results and saves JSON output."""
        ranked = rank_jobs(
            {
                "job_title": "Software Engineer Intern",
                "skills": [
                    "computer science",
                    "python",
                    "data analysis",
                    "software engineering",
                ],
                "location": "Remote",
                "experience_level": 0,
            },
            self.MONGODB_JOBS,
        )

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(
            json.dumps(ranked, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        self.assertEqual(len(ranked), min(len(self.MONGODB_JOBS), 200))
        self.assertTrue(OUTPUT_PATH.exists())
        self.assertTrue(all("score" in job for job in ranked))
        self.assertTrue(all(isinstance(job["score"], float) for job in ranked))
        self.assertTrue(all(0.0 <= job["score"] <= 1.0 for job in ranked))
        self.assertEqual(
            [job["score"] for job in ranked],
            sorted((job["score"] for job in ranked), reverse=True),
        )

        top_result = ranked[0]
        self.assertIn("tfidf_score", top_result)
        self.assertIn("raw_final_score", top_result)
        self.assertIn("skill_score", top_result)
        self.assertIn("matched_skills", top_result)

    def test_accepts_user_text_profile_with_real_mongodb_jobs(self) -> None:
        """A user_text-only happy path works against real MongoDB documents."""
        ranked = rank_jobs(
            {"user_text": "computer science intern python software data analysis"},
            self.MONGODB_JOBS,
        )

        self.assertEqual(len(ranked), min(len(self.MONGODB_JOBS), 200))
        self.assertGreaterEqual(ranked[0]["score"], ranked[-1]["score"])
        self.assertTrue(any(job["score"] > 0.0 for job in ranked))

    def test_accepts_resume_text_profile_with_real_mongodb_jobs(self) -> None:
        """A resume_text-only happy path works against real MongoDB documents."""
        ranked = rank_jobs(
            {
                "resume_text": (
                    "Computer science student with Python, database, reporting, "
                    "and software development internship experience."
                )
            },
            self.MONGODB_JOBS,
        )

        self.assertEqual(len(ranked), min(len(self.MONGODB_JOBS), 200))
        self.assertTrue(all("matched_skills_count" in job for job in ranked))
        self.assertTrue(any(job["score"] > 0.0 for job in ranked))

    def test_ranking_real_mongodb_jobs_is_deterministic(self) -> None:
        """Real MongoDB ranking is deterministic for repeated happy-path calls."""
        profile = {
            "job_title": "Software Engineer",
            "skills": "computer science, python, data analysis",
            "experience_level": 0,
        }

        ranked_once = rank_jobs(profile, self.MONGODB_JOBS)
        ranked_twice = rank_jobs(profile, self.MONGODB_JOBS)

        ids_once = [job.get("_id") for job in ranked_once]
        ids_twice = [job.get("_id") for job in ranked_twice]
        self.assertEqual(ids_once, ids_twice)


if __name__ == "__main__":
    unittest.main()
