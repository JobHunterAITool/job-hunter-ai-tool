import unittest

from ml.rank_jobs import rank_jobs


class RankJobsTests(unittest.TestCase):
    def test_returns_jobs_in_ranked_order(self) -> None:
        """Jobs are returned in ranked order by score."""
        jobs = [
            {"_id": "1", "title": "Backend Engineer", "description": "Python APIs"},
            {"_id": "2", "title": "Data Analyst", "description": "SQL dashboards"},
            {"_id": "3", "title": "ML Engineer", "description": "NLP ranking"},
        ]
        ranked = rank_jobs({"user_text": "python ml"}, jobs)
        self.assertEqual({job["_id"] for job in ranked}, {"1", "2", "3"})
        self.assertTrue(all("score" in job for job in ranked))
        self.assertEqual(
            [job["score"] for job in ranked],
            sorted((job["score"] for job in ranked), reverse=True),
        )

    def test_adds_score_field_to_each_result(self) -> None:
        """Each job gets a score field between 0 and 1."""
        jobs = [{"_id": "1", "title": "Backend Engineer"}]
        ranked = rank_jobs({"user_text": "backend"}, jobs)
        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertIsInstance(ranked[0]["score"], float)
        self.assertGreaterEqual(ranked[0]["score"], 0.0)
        self.assertLessEqual(ranked[0]["score"], 1.0)
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_does_not_mutate_input_job_dicts(self) -> None:
        """Input job dicts are not mutated (no score field added)."""
        jobs = [{"_id": "1", "title": "Backend Engineer"}]
        ranked = rank_jobs({"user_text": "backend"}, jobs)
        self.assertNotIn("score", jobs[0])

    def test_raises_for_empty_user_text(self) -> None:
        """Raises ValueError if user_text is empty."""
        jobs = [{"_id": "1", "title": "Backend Engineer"}]
        with self.assertRaises(ValueError):
            rank_jobs({"user_text": ""}, jobs)

    def test_accepts_structured_user_fields_without_user_text(self) -> None:
        """Accepts structured user profile fields instead of user_text."""
        jobs = [{"_id": "1", "title": "Backend Engineer", "description": "Python APIs"}]
        ranked = rank_jobs(
            {
                "job_title": "Backend Engineer",
                "skills": ["Python", "FastAPI"],
                "location": "Remote",
                "experience_level": 3,
            },
            jobs,
        )
        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_accepts_comma_separated_skills_string(self) -> None:
        """Accepts skills as a comma-separated string."""
        jobs = [{"_id": "1", "title": "Backend Engineer", "description": "Python APIs"}]
        ranked = rank_jobs(
            {
                "job_title": "Backend Engineer",
                "skills": "Python, FastAPI, SQL",
                "location": "Remote",
                "experience_level": 3,
            },
            jobs,
        )
        self.assertEqual(len(ranked), 1)
        self.assertIn("score", ranked[0])
        self.assertGreater(ranked[0]["score"], 0.0)

    def test_final_scores_are_l2_normalized(self) -> None:
        """Returned scores are L2-normalized after final score blending."""
        jobs = [
            {"_id": "1", "title": "Backend Engineer", "skills": ["Python"]},
            {"_id": "2", "title": "API Engineer", "skills": ["FastAPI"]},
        ]
        ranked = rank_jobs({"skills": ["Python", "FastAPI"]}, jobs)
        score_norm = sum(job["score"] ** 2 for job in ranked) ** 0.5
        self.assertAlmostEqual(score_norm, 1.0)

    def test_raises_for_empty_user_profile(self) -> None:
        """Raises ValueError if user profile is empty."""
        jobs = [{"_id": "1", "title": "Backend Engineer"}]
        with self.assertRaises(ValueError):
            rank_jobs({}, jobs)

    def test_raises_for_empty_jobs(self) -> None:
        """Raises ValueError if jobs list is empty."""
        with self.assertRaises(ValueError):
            rank_jobs({"user_text": "backend"}, [])

    def test_tolerates_missing_fields(self) -> None:
        """Handles jobs with missing fields gracefully."""
        jobs = [
            {"_id": "1"},
            {"title": "No id field"},
            {},
        ]
        result = rank_jobs({"user_text": "backend"}, jobs)
        self.assertEqual(len(result), 3)
        self.assertTrue(all("score" in job for job in result))

    def test_skill_phrase_match_survives_prefilter_with_skill_ngrams(self) -> None:
        """Skill phrase match survives prefiltering with skill ngrams."""
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
        result = rank_jobs({"skills": ["machine learning"]}, jobs)
        ranked_ids = [job["_id"] for job in result]
        self.assertEqual(len(result), 200)
        self.assertIn("skill-phrase-match", ranked_ids)
        self.assertEqual(result[0]["_id"], "skill-phrase-match")

    def test_matches_required_and_preferred_skills_from_description_sections(self) -> None:
        """Required/preferred sections contribute separate skill match fields."""
        jobs = [
            {
                "_id": "sectioned",
                "title": "Platform Engineer",
                "job_description_text": """
                Requirements:
                Python and SQL experience.

                Nice to Have:
                Docker experience.
                """,
            }
        ]

        result = rank_jobs({"skills": ["Python", "SQL", "Docker"]}, jobs)

        self.assertEqual(result[0]["matched_required_skills"], ["python", "sql"])
        self.assertEqual(result[0]["matched_preferred_skills"], ["docker"])
        self.assertEqual(
            result[0]["matched_skills"],
            ["docker", "python", "sql"],
        )
        self.assertAlmostEqual(result[0]["skill_score"], 7 / 12)



if __name__ == "__main__":
    unittest.main()
