# This should run after the ingestion script-
# take the displayname and make a new field in the JSON thats "Company: "
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import re


# Runtime settings for faster but still safe page extraction.
MAX_WORKERS = 6
REQUEST_TIMEOUT_SECONDS = 15
SAVE_RAW_HTML = False
BLOCKED_TEXT_MARKERS = [
    "Our systems have detected suspicious behaviour",
    "Login to continue",
]

thread_local = threading.local()



def find_jobs_file():
    candidates = []
    for file in os.listdir():
        if file.startswith("jobs_") and (file.endswith(".txt") or file.endswith(".json")):
            candidates.append(file)

    if not candidates:
        raise FileNotFoundError("No jobs_*.txt or jobs_*.json file found")

    # Prefer the most recently modified file.
    candidates.sort(key=lambda file_name: os.path.getmtime(file_name), reverse=True)
    return candidates[0]




# citation : help of an LLM was used to help generate the set of known skills as well as regex patterns : https://chatgpt.com/share/69f40421-eae4-83ea-8174-5259e6bf35bc
# read in static file of known skillsets : 
with open("KNOWN SKILLS.txt", "r", encoding="utf-8") as file:
    text = file.read()
    skills = re.findall(r'"([^"]+)"', text)

print(f"Skills to search for: {len(skills)}")
skills = [element.lower() for element in skills]
    
def extract_skills(description, skills):
    if not description:
        return []
    
    # lowercase all text to make matching simpler
    description = description.lower()

    # place extracted skills into a set for uniqueness
    extracted_skills = set()

    for skill in skills:
        # escape special regex characters in skills like c++, c#, .net, node.js, ci/cd
        escaped_skill = re.escape(skill)

        # match skill as its own phrase, not inside another word
        pattern = r'(?<![a-z0-9+#./-])' + escaped_skill + r'(?![a-z0-9+#./-])'

        # search the entirety of the description for the skill
        if re.search(pattern, description):
            extracted_skills.add(skill)

    return sorted(extracted_skills)




def build_session():
    session = requests.Session()
    retry_policy = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(
        max_retries=retry_policy,
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; JobHunterEnrichment/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        }
    )
    return session


def get_thread_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = build_session()
    return thread_local.session


def clean_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def parse_description(full_html):
    soup = BeautifulSoup(full_html, "html.parser")
    selectors = [
        "section.adp-body",
        "article",
        "main",
        "div[itemprop='description']",
    ]

    for selector in selectors:
        node = soup.select_one(selector)
        if not node:
            continue

        text = clean_text(node.get_text("\n", strip=True))
        if text:
            return node, text, selector

    body = soup.select_one("body")
    if body:
        text = clean_text(body.get_text("\n", strip=True))
        if text:
            return None, text, "body_fallback"

    return None, None, "no_text_found"


def fetch_and_extract(url):
    session = get_thread_session()

    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS, allow_redirects=True)
        full_html = response.text
        node, description_text, parse_source = parse_description(full_html)

        if response.status_code == 403:
            status = "blocked"
        elif description_text:
            status = "body returned"
        else:
            status = "adp body not available"

        result = {
            "html": str(node) if (SAVE_RAW_HTML and node is not None) else None,
            "job_description_text": description_text,
            "html_parse_status": parse_source,
            "final_url": response.url,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type"),
            "request_error": None,
            "status": status,
        }

    except requests.exceptions.RequestException as error:
        result = {
            "html": None,
            "job_description_text": None,
            "html_parse_status": "request_exception",
            "final_url": None,
            "status_code": None,
            "content_type": None,
            "request_error": str(error),
            "status": "request_failed",
        }

    return result


def is_blocked_response(result):
    if result.get("status_code") == 403:
        return True

    text = result.get("job_description_text")
    if not isinstance(text, str):
        return False

    return any(marker in text for marker in BLOCKED_TEXT_MARKERS)



jobs_data_file = find_jobs_file()
with open(jobs_data_file, "r", encoding="utf-8") as file:
    jobs = json.load(file)

# Group by redirect_url to avoid duplicate HTTP fetches.
jobs_by_url = {}
for index, job in enumerate(jobs):
    url = job.get("redirect_url")
    if not url:
        job["html"] = None
        job["job_description_text"] = None
        job["html_parse_status"] = "no_redirect_url"
        job["request_error"] = "No redirect_url found"
        continue

    jobs_by_url.setdefault(url, []).append(index)

print(f"Unique URLs to fetch: {len(jobs_by_url)} (from {len(jobs)} jobs)")

blocked_report = []
blocked_count = 0
fallback_count = 0
success_count = 0

with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {executor.submit(fetch_and_extract, url): url for url in jobs_by_url}
    completed = 0

    for future in as_completed(futures):
        url = futures[future]
        result = future.result()
        completed += 1

        for job_index in jobs_by_url[url]:
            job = jobs[job_index]
            job["html"] = result["html"]
            job["job_description_text"] = result["job_description_text"]
            job["html_parse_status"] = result["html_parse_status"]
            job["final_url"] = result["final_url"]
            job["status_code"] = result["status_code"]
            job["content_type"] = result["content_type"]

            if is_blocked_response(result):
                blocked_count += 1
                fallback_text = job.get("description")

                if isinstance(fallback_text, str) and fallback_text.strip():
                    job["job_description_text"] = fallback_text
                    job["description_source"] = "adzuna_api_fallback"
                    fallback_count += 1
                else:
                    job["job_description_text"] = None
                    job["description_source"] = "none"

                job["blocked_by_anti_bot"] = True
                job["html_parse_status"] = "blocked_403"

                blocked_report.append(
                    {
                        "id": job.get("id"),
                        "redirect_url": job.get("redirect_url"),
                        "final_url": result.get("final_url"),
                        "status_code": result.get("status_code"),
                        "fallback_used": bool(isinstance(fallback_text, str) and fallback_text.strip()),
                    }
                )

            else:
                job["blocked_by_anti_bot"] = False

                if isinstance(job.get("job_description_text"), str) and job["job_description_text"].strip():
                    job["description_source"] = "scraped_page"
                    success_count += 1
                else:
                    job["description_source"] = "none"

            if result["request_error"]:
                job["request_error"] = result["request_error"]
            elif "request_error" in job:
                del job["request_error"]

            # add in the description field : 
            description_for_skills = job.get("job_description_text")
            job["skills"] = extract_skills(description_for_skills, skills)
            job["skills_count"] = len(job["skills"])


        print(f"[{completed}/{len(futures)}] {url} | {result['status']}")

# write enriched data to both txt and json outputs
input_base = os.path.splitext(jobs_data_file)[0]
enriched_txt_file = f"enriched_{input_base}.txt"
enriched_json_file = f"enriched_{input_base}.json"

with open(enriched_txt_file, "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=2)

with open(enriched_json_file, "w", encoding="utf-8") as file:
    json.dump(jobs, file, indent=2)

print(f"Enriched file written to {enriched_txt_file}")
print(f"Enriched file written to {enriched_json_file}")

blocked_report_file = f"blocked_urls_{os.path.splitext(jobs_data_file)[0]}.json"
with open(blocked_report_file, "w", encoding="utf-8") as file:
    json.dump(blocked_report, file, indent=2)

print(f"Blocked URL report written to {blocked_report_file}")
print(f"Blocked jobs: {blocked_count}; API fallback used: {fallback_count}; Successful scrapes: {success_count}")






# some sample redirects to look at :
# https://www.adzuna.com/details/5697687209?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=833DC389F1A448FF318E4545847F9182A2B4256E
# https://www.adzuna.com/details/5649419020?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=0321190A280AEFEF042D4096568297BC3428AB61
# https://www.adzuna.com/details/5629087559?se=XsfWK3g68RGZ3L9kDetG3g&utm_medium=api&utm_source=8e88dd1a&v=46F2976A0DD28D2CCF82B34814C7ACE447ADC647
# https://www.adzuna.com/details/5549172393?se=3KypJ3g68RG7F9FuB7LA2Q&utm_medium=api&utm_source=8e88dd1a&v=52A2BB13A28F880CD3D04AE7110B8DD89DD23D52
# https://www.adzuna.com/details/5692611566?se=3KypJ3g68RG7F9FuB7LA2Q&utm_medium=api&utm_source=8e88dd1a&v=C2A6D0BCB1A80BC0588D2A184C3F1435512DD5EE