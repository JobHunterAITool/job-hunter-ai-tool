import unittest

from ml.rank_jobs import rank_jobs


class RankJobsTests(unittest.TestCase):
    def test_returns_jobs_in_ranked_order(self) -> None:
        jobs = [
            {"_id": "1", "title": "Backend Engineer", "description": "Python APIs"},
            {"_id": "2", "title": "Data Analyst", "description": "SQL dashboards"},
            {"_id": "3", "title": "ML Engineer", "description": "NLP ranking"},
        ]

        ranked = rank_jobs({"user_text": "python ml"}, jobs)
        print("\nranked order:", ranked)

        self.assertEqual({job["_id"] for job in ranked}, {"1", "2", "3"})
        self.assertTrue(all("score" in job for job in ranked))
        self.assertEqual(
            [job["score"] for job in ranked],
            sorted((job["score"] for job in ranked), reverse=True),
        )

    def test_adds_score_field_to_each_result(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        ranked = rank_jobs({"user_text": "backend"}, jobs)
        print("\nscore field added:", ranked)

        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertIsInstance(ranked[0]["score"], float)
        self.assertGreaterEqual(ranked[0]["score"], 0.0)
        self.assertLessEqual(ranked[0]["score"], 1.0)
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_does_not_mutate_input_job_dicts(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        ranked = rank_jobs({"user_text": "backend"}, jobs)
        print("\ninput jobs:", jobs)
        print("ranked output:", ranked)

        self.assertNotIn("score", jobs[0])

    def test_raises_for_empty_user_text(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        with self.assertRaises(ValueError) as err:
            rank_jobs({"user_text": ""}, jobs)
        print("\nerr.exception:", err.exception)

    def test_accepts_structured_user_fields_without_user_text(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer", "description": "Python APIs"}]

        ranked = rank_jobs(
            {
                "job_title": "Backend Engineer",
                "skills": ["Python", "FastAPI"],
                "location": "Remote",
                "experience_level": "Mid",
            },
            jobs,
        )
        print("\nranked from structured fields:", ranked)

        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_accepts_comma_separated_skills_string(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer", "description": "Python APIs"}]

        ranked = rank_jobs(
            {
                "job_title": "Backend Engineer",
                "skills": "Python, FastAPI, SQL",
                "location": "Remote",
                "experience_level": "Mid",
            },
            jobs,
        )
        print("\nranked from comma-separated skills:", ranked)

        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_raises_for_empty_user_profile(self) -> None:
        jobs = [{"_id": "1", "title": "Backend Engineer"}]

        with self.assertRaises(ValueError) as err:
            rank_jobs({}, jobs)
        print("\nerr.exception:", err.exception)

    def test_raises_for_empty_jobs(self) -> None:
        with self.assertRaises(ValueError) as err:
            rank_jobs({"user_text": "backend"}, [])
        print("\nerr.exception:", err.exception)

    def test_tolerates_missing_fields(self) -> None:
        jobs = [
            {"_id": "1"},
            {"title": "No id field"},
            {},
        ]

        ranked = rank_jobs({"user_text": "backend"}, jobs)
        print("\nranked:", ranked)

        self.assertEqual(len(ranked), 3)
        self.assertTrue(all("score" in job for job in ranked))

    def test_skill_phrase_match_survives_prefilter_with_skill_ngrams(self) -> None:
        jobs = [
            {
                "_id": f"{index}",
                "title": "Tooling Analyst",
                "description": "machine tooling and learning platforms",
                "skills": ["python"],
            }
            for index in range(200)
        ]
        jobs.append(
            {
                "_id": "skill-phrase-match",
                "title": "Machine Learning Engineer",
                "description": "models and pipelines",
                "skills": ["machine learning"],
            }
        )

        ranked = rank_jobs({"skills": ["machine learning"]}, jobs)
        ranked_ids = [job["_id"] for job in ranked]
        print("\nranked ids:", ranked_ids[:5], "...", ranked_ids[-5:])

        self.assertEqual(len(ranked), 200)
        self.assertIn("skill-phrase-match", ranked_ids)
        self.assertEqual(ranked[0]["_id"], "skill-phrase-match")


if __name__ == "__main__":
    unittest.main()
