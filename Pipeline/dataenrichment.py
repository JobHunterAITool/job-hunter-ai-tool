# This should run after the ingestion script- 
# take the displayname and make a new field in the JSON thats "Company: "
import os
import json
import requests
import time
from bs4 import BeautifulSoup

# find the jobs file
jobs_data_file = None

for file in os.listdir():
    if file.startswith("jobs_") and file.endswith(".txt"):
        jobs_data_file = file
        break

if not jobs_data_file:
    raise FileNotFoundError("No jobs_*.txt file found")

with open(jobs_data_file, "r", encoding="utf-8") as file:
    jobs = json.load(file)


# enrich each job with html from redirect_url
for job in jobs:
    time.sleep(2) # to avoid potentially being rate limited
    url = job.get("redirect_url")

    if not url:
        job["html"] = None
        job["request_error"] = "No redirect_url found"
        continue

    try:
        response = requests.get(url, timeout=15, allow_redirects=True)
        print(f"Requested data from {url}")
        # check status codes to see if we site is identifying this scraper as a bot
        status = None
        if response.status_code == 403:
            status = "blocked"
        else:
            if adp_body:
                status = "body returned"
            else:
                status = "adp body not available"

        print(f"{job.get('id')} | {status}")
        full_html = response.text

        soup = BeautifulSoup(full_html, "html.parser")
        adp_body = soup.select_one("section.adp-body")

        # most redirects go to another adzuna-details page
        # the expanded description is in section class adp_body
        # adp_body has qualifications in it - we can potentially mine this in a future update to this logic. 
        if adp_body:
            job["html"] = str(adp_body)
            job["job_description_text"] = adp_body.get_text("\n", strip=True)
            job["html_parse_status"] = "adp_body_found"
        else:
            job["html"] = None
            job["job_description_text"] = None
            job["html_parse_status"] = "adp_body_not_found"

        job["final_url"] = response.url
        job["status_code"] = response.status_code
        job["content_type"] = response.headers.get("Content-Type")

    except requests.exceptions.RequestException as e:
        job["html"] = None
        job["request_error"] = str(e)

    time.sleep(1)

# write new file for now with enriched data
enriched_file = f"enriched_{jobs_data_file}"

with open(enriched_file, "w", encoding="utf-8") as f:
    json.dump(jobs, f, indent=2)

print(f"Enriched file written to {enriched_file}")


# some sample redirects to look at : 
# https://www.adzuna.com/details/5697687209?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=833DC389F1A448FF318E4545847F9182A2B4256E
# https://www.adzuna.com/details/5649419020?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=0321190A280AEFEF042D4096568297BC3428AB61
# https://www.adzuna.com/details/5629087559?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=46F2976A0DD28D2CCF82B34814C7ACE447ADC647
# https://www.adzuna.com/details/5549172393?se=3KypJ3g68RG7F9FuB7LA2Q&utm_medium=api&utm_source=8e88dd1a&v=52A2BB13A28F880CD3D04AE7110B8DD89DD23D52
# https://www.adzuna.com/details/5692611566?se=3KypJ3g68RG7F9FuB7LA2Q&utm_medium=api&utm_source=8e88dd1a&v=C2A6D0BCB1A80BC0588D2A184C3F1435512DD5EE