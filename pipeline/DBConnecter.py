# pip install "pymongo[srv]" python-dotenv certifi
import certifi
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
import json
import os

load_dotenv()


# I will make this an environmental variable or mask it in some way, but since repo is private its a string for now
connection_str = "mongodb+srv://rjalija_db_user:Rsi1T8mBvNOtBQAI@cluster0.xmvpzab.mongodb.net/?appName=Cluster0"
#db_user
#J9eKhr9CbGsDfrX6

client = MongoClient(
    connection_str,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

client.admin.command("ping")
print("Connected to MongoDB Atlas")


# name the database and collection here
# these do not need to already exist in Atlas
# MongoDB will create them once we insert data
db = client["job_hunter_ai"]
jobs_collection = db["job_postings"]


# find the most recent enriched jobs file from the local folder
def find_enriched_jobs_file():
    candidates = []

    for file in os.listdir():
        if file.startswith("enriched_stream_jobs_") and file.endswith(".json"):
            candidates.append(file)

    if not candidates:
        raise FileNotFoundError("No enriched_stream_jobs_*.json file found")

    # sort by most recently modified file first
    candidates.sort(key=lambda file_name: os.path.getmtime(file_name), reverse=True)
    return candidates[0]


# read in the enriched jobs file
jobs_file = find_enriched_jobs_file()

with open(jobs_file, "r", encoding="utf-8") as file:
    jobs = json.load(file)

print(f"Loaded {len(jobs)} jobs from {jobs_file}")


# create a unique index on the job id
# this should stop us from inserting the same job over and over again
jobs_collection.create_index("id", unique=True)


# build the list of MongoDB operations
operations = []

for job in jobs:
    job_id = job.get("id")

    # if there is no job id, skip it since we need something unique to match on
    if not job_id:
        continue

    # upsert means: if the job id already exists, update the existing record
    # otherwise insert it as a new record
    operations.append(
        UpdateOne(
            {"id": job_id},
            {"$set": job},
            upsert=True
        )
    )


# push the data to MongoDB Atlas
if operations:
    result = jobs_collection.bulk_write(operations)

    print(f"Matched existing jobs: {result.matched_count}")
    print(f"Inserted new jobs: {result.upserted_count}")
    print(f"Updated jobs: {result.modified_count}")
else:
    print("No valid jobs found to insert.")