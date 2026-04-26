import json
import unittest
from pathlib import Path

from ml.rank_jobs import rank_jobs


def _load_seed_jobs() -> list[dict]:
    seed_path = Path(__file__).resolve().parents[1] / "seed_jobs.json"
    return json.loads(seed_path.read_text(encoding="utf-8"))


class RankJobsSeedDataTests(unittest.TestCase):
    SEED_JOBS = _load_seed_jobs()

    def test_seed_data_loads(self) -> None:
        """Seed jobs data loads and is a non-empty list."""
        self.assertTrue(self.SEED_JOBS)
        self.assertIsInstance(self.SEED_JOBS, list)

    def test_ranked_output_has_valid_shape_and_score_range(self) -> None:
        """Ranking seed jobs returns correct shape and score range."""
        ranked = rank_jobs({"user_text": "python backend fastapi sql docker"}, self.SEED_JOBS)
        # Export ranked jobs for debugging
        with open("tests/ranked_jobs_seed_debug.json", "w", encoding="utf-8") as f:
            json.dump(ranked, f, indent=2, ensure_ascii=False)
        self.assertEqual(len(ranked), len(self.SEED_JOBS))
        self.assertTrue(all("score" in job for job in ranked))
        self.assertTrue(all(isinstance(job["score"], float) for job in ranked))
        self.assertTrue(all(0.0 <= job["score"] <= 1.0 for job in ranked))

    def test_backend_profile_surfaces_relevant_top_result(self) -> None:
        """A realistic backend profile query surfaces relevant jobs at the top."""
        ranked = rank_jobs(
            {
                "user_text": "backend engineer python fastapi rest api microservices sql postgresql docker kubernetes"
            },
            self.SEED_JOBS,
        )
        top_text = json.dumps(ranked[0]).lower()
        self.assertTrue(any(term in top_text for term in ["backend", "python", "fastapi", "api"]))

    def test_ranking_is_deterministic_for_same_input(self) -> None:
        """Ranking is deterministic for the same input and seed data."""
        query = "machine learning engineer python pytorch tensorflow nlp"
        ranked_once = rank_jobs({"user_text": query}, self.SEED_JOBS)
        ranked_twice = rank_jobs({"user_text": query}, self.SEED_JOBS)
        ids_once = [job.get("_id") for job in ranked_once]
        ids_twice = [job.get("_id") for job in ranked_twice]
        self.assertEqual(ids_once, ids_twice)


if __name__ == "__main__":
    unittest.main()
