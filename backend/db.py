"""
MongoDB helper module for backend routes.

The backend reuses the Pipeline Mongo connector so API reads and Pipeline writes
target the same database and collection.
"""

from pathlib import Path

from dotenv import load_dotenv
from pymongo.collection import Collection
from pymongo.database import Database

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

from Pipeline.DBConnecter import MONGO_DB_NAME  # noqa: E402
from Pipeline.DBConnecter import get_jobs_collection as get_pipeline_jobs_collection  # noqa: E402
from Pipeline.DBConnecter import get_mongo_client  # noqa: E402


def get_database() -> Database:
    """Return the configured MongoDB database."""
    return get_mongo_client()[MONGO_DB_NAME]


def get_jobs_collection() -> Collection:
    """Return the jobs collection used by search and listing endpoints."""
    return get_pipeline_jobs_collection()
