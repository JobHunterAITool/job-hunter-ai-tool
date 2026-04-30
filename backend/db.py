"""
Author: Michael Mart
Class: CS 467
Project: The Job Hunting AI Web Tool
Description: MongoDB helper module that centralizes database configuration and
shared collection access for the FastAPI routes/services.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

# Local defaults make first-time setup easier for the team.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "job_ai_tool")
JOBS_COLLECTION_NAME = os.getenv("JOBS_COLLECTION_NAME", "jobs")
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(
    os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000")
)


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Return a shared Mongo client instance for the app process."""
    # Cache client so we do not reconnect to MongoDB on every request.
    return MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
    )


def get_database() -> Database:
    """Return the configured MongoDB database."""
    return get_mongo_client()[MONGO_DB_NAME]


def get_jobs_collection() -> Collection:
    """Return the jobs collection used by search and listing endpoints."""
    return get_database()[JOBS_COLLECTION_NAME]
