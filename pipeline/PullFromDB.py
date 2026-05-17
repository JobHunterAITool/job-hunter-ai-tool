# pip install "pymongo[srv]" certifi

import certifi
from pymongo import MongoClient
import json


# MongoDB Atlas credentials
username = "JobSearchDBUser"
password = "HairyBeaver2026"

# cluster connection string
connection_str = f"mongodb+srv://{username}:{password}@cluster0.xmvpzab.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


client = MongoClient(
    connection_str,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000
)

# test connection
client.admin.command("ping")
print("Connected to MongoDB Atlas")


# choose the database and collection we inserted into
db = client["job_hunter_ai"]
jobs_collection = db["job_postings"]


# pull all documents from the collection
jobs = list(jobs_collection.find({}))

print(f"Pulled {len(jobs)} jobs from MongoDB")


# MongoDB adds an _id field that Python's json module cannot write by default
# convert it to a string so we can save it locally
for job in jobs:
    job["_id"] = str(job["_id"])


# save the pulled data locally
output_file = "pulled_jobs_from_mongodb.json"

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=2)

print(f"Data written to {output_file}")