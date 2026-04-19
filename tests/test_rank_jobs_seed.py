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
        print(f"\nseed job count: {len(self.SEED_JOBS)}")
        self.assertTrue(self.SEED_JOBS)
        self.assertIsInstance(self.SEED_JOBS, list)

    def test_ranked_output_has_valid_shape_and_score_range(self) -> None:
        ranked = rank_jobs({"user_text": "python backend fastapi sql docker"}, self.SEED_JOBS)

        self.assertEqual(len(ranked), len(self.SEED_JOBS))
        self.assertTrue(all("score" in job for job in ranked))
        self.assertTrue(all(isinstance(job["score"], float) for job in ranked))
        self.assertTrue(all(0.0 <= job["score"] <= 1.0 for job in ranked))

        top_preview = [
            {"_id": job.get("_id"), "score": round(job["score"], 4)}
            for job in ranked[:5]
        ]
        print("\ntop 5 (python/backend query):", top_preview)

    def test_backend_profile_surfaces_relevant_top_result(self) -> None:
        ranked = rank_jobs(
            {
                "user_text": "backend engineer python fastapi rest api microservices sql postgresql docker kubernetes"
            },
            self.SEED_JOBS,
        )

        print("\ntop backend result:", {"_id": ranked[0].get("_id"), "title": ranked[0].get("title"), "score": round(ranked[0]["score"], 4)})
        top_text = json.dumps(ranked[0]).lower()
        self.assertTrue(any(term in top_text for term in ["backend", "python", "fastapi", "api"]))

    def test_ranking_is_deterministic_for_same_input(self) -> None:
        query = "machine learning engineer python pytorch tensorflow nlp"

        ranked_once = rank_jobs({"user_text": query}, self.SEED_JOBS)
        ranked_twice = rank_jobs({"user_text": query}, self.SEED_JOBS)

        ids_once = [job.get("_id") for job in ranked_once]
        ids_twice = [job.get("_id") for job in ranked_twice]
        print("\nfirst 10 ids (run 1):", ids_once[:10])
        print("first 10 ids (run 2):", ids_twice[:10])
        self.assertEqual(ids_once, ids_twice)


if __name__ == "__main__":
    unittest.main()
