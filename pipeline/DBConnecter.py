import json
import os
from functools import lru_cache
from pathlib import Path

import certifi
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / "backend" / ".env")
load_dotenv()

DEFAULT_MONGO_URI = (
    "mongodb+srv://rjalija_db_user:"
    "Rsi1T8mBvNOtBQAI@cluster0.xmvpzab.mongodb.net/?appName=Cluster0"
)
MONGO_URI = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "job_hunter_ai")
JOBS_COLLECTION_NAME = os.getenv("JOBS_COLLECTION_NAME", "job_postings")
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "10000")
)


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Return a shared MongoDB client configured from environment variables."""
    client_options = {
        "serverSelectionTimeoutMS": MONGO_SERVER_SELECTION_TIMEOUT_MS,
    }
    if MONGO_URI.startswith("mongodb+srv://"):
        client_options["tlsCAFile"] = certifi.where()

    return MongoClient(MONGO_URI, **client_options)


def get_jobs_collection() -> Collection:
    """Return the configured jobs collection."""
    return get_mongo_client()[MONGO_DB_NAME][JOBS_COLLECTION_NAME]


# find the most recent enriched jobs file from the local folder
def find_enriched_jobs_file():
    candidates = []

    for file in os.listdir(PIPELINE_DIR):
        if file.startswith("enriched_jobs_") and file.endswith(".json"):
            candidates.append(PIPELINE_DIR / file)

    if not candidates:
        raise FileNotFoundError("No enriched_jobs_*.json file found")

    # sort by most recently modified file first
    candidates.sort(key=lambda file_name: file_name.stat().st_mtime, reverse=True)
    return candidates[0]


def load_latest_enriched_jobs() -> None:
    """Load the newest enriched jobs JSON file into MongoDB."""
    client = get_mongo_client()
    client.admin.command("ping")
    print("Connected to MongoDB")

    jobs_collection = get_jobs_collection()
    jobs_file = find_enriched_jobs_file()

    with jobs_file.open("r", encoding="utf-8") as file:
        jobs = json.load(file)

    print(f"Loaded {len(jobs)} jobs from {jobs_file}")

    # This stops us from inserting the same job over and over again.
    jobs_collection.create_index("id", unique=True)

    operations = []
    for job in jobs:
        job_id = job.get("id")

        if not job_id:
            continue

        # Upsert means: update the existing document or insert it if missing.
        operations.append(
            UpdateOne(
                {"id": job_id},
                {"$set": job},
                upsert=True,
            )
        )

    if operations:
        result = jobs_collection.bulk_write(operations)

        print(f"Matched existing jobs: {result.matched_count}")
        print(f"Inserted new jobs: {result.upserted_count}")
        print(f"Updated jobs: {result.modified_count}")
    else:
        print("No valid jobs found to insert.")


if __name__ == "__main__":
    load_latest_enriched_jobs()
