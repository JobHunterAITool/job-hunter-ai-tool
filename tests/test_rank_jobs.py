import unittest

from ml.rank_jobs import rank_jobs


class RankJobsTests(unittest.TestCase):
    def test_returns_jobs_in_original_order_for_stub(self) -> None:
        jobs = [
            {"_id": "1", "title": "Backend Engineer", "description": "Python APIs"},
            {"_id": "2", "title": "Data Analyst", "description": "SQL dashboards"},
            {"_id": "3", "title": "ML Engineer", "description": "NLP ranking"},
        ]

        ranked = rank_jobs("python ml", jobs)

        self.assertEqual([job["_id"] for job in ranked], ["1", "2", "3"])

    def test_adds_score_field_to_each_result(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        ranked = rank_jobs("backend", jobs)
        print("\nscore field added:", ranked)

        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertIsInstance(ranked[0]["score"], float)
        self.assertEqual(ranked[0]["score"], 0.0)

    def test_does_not_mutate_input_job_dicts(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        _ = rank_jobs("backend", jobs)

        self.assertNotIn("score", jobs[0])

    def test_raises_for_empty_user_text(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        with self.assertRaises(ValueError):
            rank_jobs("", jobs)

    def test_raises_for_whitespace_user_text(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        with self.assertRaises(ValueError):
            rank_jobs("   ", jobs)

    def test_raises_for_empty_jobs(self) -> None:
        with self.assertRaises(ValueError):
            rank_jobs("backend", [])

    def test_tolerates_missing_fields(self) -> None:
        jobs = [
            {"_id": "1"},
            {"title": "No id field"},
            {},
        ]

        ranked = rank_jobs("backend", jobs)

        self.assertEqual(len(ranked), 3)
        self.assertTrue(all("score" in job for job in ranked))


if __name__ == "__main__":
    unittest.main()
