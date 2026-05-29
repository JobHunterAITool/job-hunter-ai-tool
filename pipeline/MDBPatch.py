# temporary_patch_mongodb_jobs.py
# pip install "pymongo[srv]" certifi python-dotenv

import os
import re
import json
import certifi
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne


load_dotenv()

connection_str = "mongodb+srv://rjalija_db_user:Rsi1T8mBvNOtBQAI@cluster0.xmvpzab.mongodb.net/?appName=Cluster0"


if not connection_str:
    raise ValueError("Missing MONGO_URI. Add it to your .env file before running this script.")


client = MongoClient(
    connection_str,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

client.admin.command("ping")
print("Connected to MongoDB Atlas")


# database and collection
db = client["job_hunter_ai"]
jobs_collection = db["job_postings"]


YOE_REGEX = r"""
(?:minimum|at\s+least|required|requires|preferred)?
[^\n.;:]{0,40}?
(?P<years>\d{1,2})\s*\+?\s*
(?:-|to\s+)?\s*
(?:\d{1,2}\s*)?
(?:years?|yrs?)\s+
(?:of\s+)?
(?:
    (?:professional\s+)?experience |
    working\s+experience |
    hands[-\s]?on\s+experience |
    working\s+with
)
"""


# this pulls out years of experience from the job description if it is available
def extract_yoe(description):
    if not isinstance(description, str) or not description.strip():
        return None

    match = re.search(YOE_REGEX, description, re.IGNORECASE | re.VERBOSE)

    if not match:
        return None

    return int(match.group("years"))


def extract_city_and_state(job):
    location = job.get("location", {})

    if not isinstance(location, dict):
        return None, job.get("state")

    area = location.get("area", [])

    if not isinstance(area, list):
        area = []

    # Adzuna area usually looks like:
    # ["US", "State", "County", "City"]
    state = area[1] if len(area) > 1 else job.get("state")
    city = area[3] if len(area) > 3 else None

    # fallback if area does not include city
    # example display_name: "San Diego, San Diego County"
    if not city:
        display_name = location.get("display_name")

        if isinstance(display_name, str) and display_name.strip():
            first_part = display_name.split(",")[0].strip()

            # avoid setting city to "Illinois" when the display is just "Illinois, US"
            if first_part and first_part != state:
                city = first_part

    return city, state


# pull all documents
jobs = list(jobs_collection.find({}))
print(f"Pulled {len(jobs)} jobs from MongoDB")


# backup before updating or deleting anything
backup_file = f"mongodb_backup_before_patch_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.json"

backup_jobs = []

for job in jobs:
    job_copy = dict(job)
    job_copy["_id"] = str(job_copy["_id"])
    backup_jobs.append(job_copy)

with open(backup_file, "w", encoding="utf-8") as file:
    json.dump(backup_jobs, file, indent=2)

print(f"Backup written to {backup_file}")


# delete all jobs where the scrape/enrichment got blocked with 403
delete_result = jobs_collection.delete_many({"status_code": 403})

print(f"Deleted 403 blocked jobs: {delete_result.deleted_count}")


# pull remaining documents after deleting 403 records
jobs = list(jobs_collection.find({}))
print(f"Remaining jobs after deleting 403s: {len(jobs)}")


operations = []
yoe_count = 0
city_count = 0
state_count = 0

for job in jobs:
    mongo_id = job.get("_id")

    # prefer the enriched scraped text, but fallback to regular Adzuna description
    description_for_yoe = job.get("job_description_text")

    if not isinstance(description_for_yoe, str) or not description_for_yoe.strip():
        description_for_yoe = job.get("description")

    yoe = extract_yoe(description_for_yoe)
    city, state = extract_city_and_state(job)

    update_fields = {
        "YOE": yoe,
        "city": city,
        "state": state
    }

    if yoe is not None:
        yoe_count += 1

    if city is not None:
        city_count += 1

    if state is not None:
        state_count += 1

    operations.append(
        UpdateOne(
            {"_id": mongo_id},
            {"$set": update_fields}
        )
    )


if operations:
    result = jobs_collection.bulk_write(operations)

    print("Patch complete.")
    print(f"Deleted 403 blocked jobs: {delete_result.deleted_count}")
    print(f"Matched jobs: {result.matched_count}")
    print(f"Modified jobs: {result.modified_count}")
    print(f"YOE found: {yoe_count}")
    print(f"City found: {city_count}")
    print(f"State found: {state_count}")
else:
    print("No jobs found to update.")
    print(f"Deleted 403 blocked jobs: {delete_result.deleted_count}")
