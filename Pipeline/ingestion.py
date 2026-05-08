import requests
import datetime
import time
import json
import os

# Adzuna free-tier guardrails.
FREE_TIER_PER_MINUTE = 25
FREE_TIER_PER_DAY = 250
FREE_TIER_PER_WEEK = 1000
FREE_TIER_PER_MONTH = 2500

# Keep some daily headroom by default so repeated local runs do not consume the full quota.
REQUESTS_PER_RUN_CAP = int(os.getenv("ADZUNA_REQUESTS_PER_RUN_CAP", "200"))
REQUESTS_PER_RUN_CAP = min(REQUESTS_PER_RUN_CAP, FREE_TIER_PER_DAY)
REQUEST_INTERVAL_SECONDS = 60.0 / FREE_TIER_PER_MINUTE
MAX_PAGES_PER_CATEGORY = int(os.getenv("ADZUNA_MAX_PAGES_PER_CATEGORY", "2"))

# Adzuna API endpoints : 

# /jobs/{country}/search/{page}
# This is the main endpoint that actually returns job listings. It gives us all the core data like title, description, company, location, salary, and link, and supports filters like keywords and category

# /jobs/{country}/histogram
# This gives a breakdown of how many jobs fall into different salary ranges

# /jobs/{country}/history
# This returns historical average salary data over time

# /jobs/{country}/geodata
# This provides salary data by location

# /jobs/{country}/top_companies
# This shows which companies are posting the most jobs for a given search

# /version
# This just returns the API version info


# categories  :  returns the predefined list of job categories adzuna uses, we will use this for our industry filter. 
# you can see them all in this response : https://api.adzuna.com/v1/api/jobs/us/categories?app_id=8e88dd1a&app_key=501524232a49925c03eec7a276d7fb5f
# below are the filters in scope for this project. 



categories = [
    "it-jobs",
    "engineering-jobs",
    "scientific-qa-jobs",
]

# read credentials in so theyre not harded coded 
with open("cred.txt", "r") as file: 
    line = file.read().strip()
id, key  = [x.strip().strip('"') for x in line.split(",")]


# main loop logic : 
# We will request one category at a time, since adzuna supports pagination we will continue requesting for that one category until no results return. 
# FOR NOW : Ill stop at page 10 for each category, for later progress reports we can go past that. 

seen_ids = set()
all_jobs = []
category = ""
results_per_page = 50
base_url = "https://api.adzuna.com/v1/api/jobs/us/search/{}"
request_count = 0
last_request_at = None


# 50 is the max results per page per the api response
def send_HTTP_request(url, id, key, category, results_per_page=50, page=1, what = ""):
        url = base_url.format(page)
        params = {
            "app_id": id,
            "app_key": key,
            "results_per_page": results_per_page, 
            'category' : category, 
            'what' : what
            }

        try:
            response = requests.get(url, params=params)
            return response, response.json() # return the response and statuscode. 
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None, {}

# create timestamp variable and convert it to string.
TIMESTAMP = datetime.datetime.now().isoformat()

print(
    f"Adzuna free-tier guardrails active: "
    f"{FREE_TIER_PER_MINUTE}/min, {FREE_TIER_PER_DAY}/day, "
    f"{FREE_TIER_PER_WEEK}/week, {FREE_TIER_PER_MONTH}/month"
)
print(
    f"This run cap: {REQUESTS_PER_RUN_CAP} requests, "
    f"max pages/category: {MAX_PAGES_PER_CATEGORY}"
)

# start making requests : 
# loop through each of our job industry categories. 
for category in categories:
    if request_count >= REQUESTS_PER_RUN_CAP:
        print("Reached per-run request cap before finishing all categories.")
        break

    print(f"\nJob category: {category}")

    # pagination - 50 results per response. We can limit where to stop here, or continue until we reach the end. 
    for page in range(1, MAX_PAGES_PER_CATEGORY + 1):
        if request_count >= REQUESTS_PER_RUN_CAP:
            print("Reached per-run request cap. Stopping pagination.")
            break

        if last_request_at is not None:
            elapsed = time.time() - last_request_at
            wait_seconds = REQUEST_INTERVAL_SECONDS - elapsed
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        request_count += 1
        last_request_at = time.time()

        # the send_HTTP_requests returns the status code, and then the actual data in a set. 
        response, data = send_HTTP_request(
            base_url,
            id=id,
            key=key,
            category=category,
            results_per_page=results_per_page,
            page=page,
            what="computer science"  # <- we can change this, but without it we return 400,000+ jobs
        )

        if response is None:
            print(f"Request failed for category={category}, page={page}")
            break

        print(f"[{request_count}/{REQUESTS_PER_RUN_CAP}] {response.url}")

        if response.status_code != 200:
            print(f"Request failed for category={category}, page={page}")
            print(f"Status code: {response.status_code}")
            print(f"Error: {response.text}")
            break

        # return the results, or if it doesnt exist an empty list (to avoid erroring out)
        results = data.get("results", [])

        if not results:
            print(f"No more results for {category} on page {page}. Stopping this category.")
            break

        print(f"Retrieved {len(results)} jobs from category={category}, page={page}")

        # check for duplications
        for job in results:
            job_id = job.get("id")
            if job_id not in seen_ids:
                seen_ids.add(job_id)
                job["TIMESTAMP"] = TIMESTAMP
                job["Category"] = category
                area = job.get("location", {}).get("area", [])
                job["state"] = area[1] if len(area) > 1 else None
                all_jobs.append(job)

print(f"\nUnique jobs entered: {len(all_jobs)}")
print(f"Total API requests this run: {request_count}")

# printing all jobs just prints the python representation of the data structure which is a dict
print(all_jobs)
# json module converts to valid json string
print(json.dumps(all_jobs, indent=2))


# delete already existing jobs_*.txt and jobs_*.json files, we will overwrite them each time (for now)
# update this logic to insert data into MongoDB in the next progress report. 
for file in os.listdir():
    if file.startswith("jobs_") and (file.endswith(".txt") or file.endswith(".json")):
        os.remove(file)

base_filename = f"jobs_{TIMESTAMP.replace(':', '_')}"
txt_filename = f"{base_filename}.txt"
json_filename = f"{base_filename}.json"
payload = json.dumps(all_jobs, indent=2)

with open(txt_filename, "w", encoding="utf-8") as f:
    f.write(payload)

with open(json_filename, "w", encoding="utf-8") as f:
    f.write(payload)

print(f"Results written to: {txt_filename}")
print(f"Results written to: {json_filename}")
