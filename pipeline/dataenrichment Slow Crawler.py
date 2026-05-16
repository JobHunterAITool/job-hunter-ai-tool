# This should run after the ingestion script.
# It enriches job records with better job description text when possible.
# Main idea:
# 1. Try to scrape the full job description from the redirect URL.
# 2. If scraping works, use the scraped description.
# 3. If scraping does not work but the request was not blocked, use the Adzuna API description as fallback.
# 4. Do not write blocked jobs to the enriched output file.
# 5. Write each enriched job immediately as JSONL.
# 6. Track progress after each URL so the script can resume later.
# 7. If 3 blocks happen in a row, sleep for 2 hours and then keep going.
# 8. If the tracker belongs to a different jobs file, start a fresh tracker from position 0.
# 9. Extract skills and years of experience from the final job description text.

import json
import os
import random
import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# -----------------------------
# Settings
# -----------------------------

# Scrape this many URLs, then take a break.
SCRAPES_PER_BATCH = 25

# Break between batches.
BATCH_BREAK_SECONDS = 300

REQUEST_TIMEOUT_SECONDS = 20

# Random delay between each individual request.
MIN_DELAY_SECONDS = 10
MAX_DELAY_SECONDS = 25

# If this many blocks happen in a row, sleep before trying the next scrape.
MAX_BLOCKED_URLS_IN_A_ROW_BEFORE_BREAK = 3

# Two hour break after too many blocks in a row.
BLOCK_BREAK_SECONDS = 2 * 60 * 60

# Do not write raw HTML unless debugging.
SAVE_RAW_HTML = False

# Only accept scraped text if it looks useful.
MIN_SCRAPED_TEXT_LENGTH = 500

# Tracker file used to resume.
TRACKER_FILE = "enrichment_progress_tracker.json"


# see if the text contains common phrases that indicate 403 blocks
BLOCKED_TEXT_MARKERS = [
    "Our systems have detected suspicious behaviour",
    "Login to continue",
    "Access Denied",
    "Checking your browser",
    "verify you are human",
    "captcha",
]


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


# -----------------------------
# File helpers
# -----------------------------

def find_jobs_file():
    candidates = []

    for file in os.listdir():
        if file.startswith("jobs_") and (file.endswith(".txt") or file.endswith(".json")):
            candidates.append(file)

    if not candidates:
        raise FileNotFoundError("No jobs_*.txt or jobs_*.json file found")

    candidates.sort(key=lambda file_name: os.path.getmtime(file_name), reverse=True)
    return candidates[0]


# we write records down immediatley after we get an http response so we don't lose data if the script is interrupted or crashes
def append_jsonl(file_name, record):
    with open(file_name, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()
        os.fsync(file.fileno())


# tracker is a json file that keep strack of where we left off in the enrichment process if script is interrupted or crashes
def read_tracker():
    if not os.path.exists(TRACKER_FILE):
        return None

    with open(TRACKER_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


# we write the tracker after every URL attempt so we always know where we left off even if the script is interrupted or crashes
def write_tracker(tracker):
    temp_file = TRACKER_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(tracker, file, indent=2)
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_file, TRACKER_FILE)


# once jsonl file is complete we remake it into a normal json file for MongoDB insertion
# jsonl file is used to write down each record immediately after enrichment
def build_json_from_jsonl(jsonl_file, json_file):
    records = []
    seen_ids = set()

    if not os.path.exists(jsonl_file):
        with open(json_file, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2)
        return records

    with open(jsonl_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            record = json.loads(line)
            record_id = record.get("id")

            if record_id:
                if record_id in seen_ids:
                    continue

                seen_ids.add(record_id)

            records.append(record)

    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(records, file, indent=2)

    return records


# read in the api response
def load_jobs_data(jobs_data_file):
    with open(jobs_data_file, "r", encoding="utf-8") as file:
        jobs = json.load(file)

    if not isinstance(jobs, list):
        raise ValueError("Jobs file must contain a list of job records")

    return jobs


# -----------------------------
# Text extraction
# -----------------------------

# this is a static record of many possible skills we want to extract from the job descriptions
def load_known_skills():
    # citation : help of an LLM was used to help generate the set of known skills as well as regex patterns :
    # https://chatgpt.com/share/69f40421-eae4-83ea-8174-5259e6bf35bc

    with open("KNOWN SKILLS.txt", "r", encoding="utf-8") as file:
        text = file.read()

    skills = re.findall(r'"([^"]+)"', text)
    skills = [skill.lower().strip() for skill in skills if skill.strip()]

    print(f"Skills to search for: {len(skills)}")
    return skills


# this is a regex based skill extractor that looks for whole word matches of the known skills in the job description text
def extract_skills(description, skills):
    if not description:
        return []

    description = description.lower()
    extracted_skills = set()

    for skill in skills:
        escaped_skill = re.escape(skill)
        pattern = r'(?<![a-z0-9+#./-])' + escaped_skill + r'(?![a-z0-9+#./-])'

        if re.search(pattern, description):
            extracted_skills.add(skill)

    return sorted(extracted_skills)


# this pulls out years of experience from the job description if it is available
def extract_yoe(description):
    if not isinstance(description, str) or not description.strip():
        return None

    match = re.search(YOE_REGEX, description, re.IGNORECASE | re.VERBOSE)

    if not match:
        return None

    return int(match.group("years"))


# -----------------------------
# HTTP session
# -----------------------------

# creates a session with retry logic and headers to mimic a real browser to avoid blocks and handle errors
def build_session():
    session = requests.Session()

    # Do not retry 403 or 429.
    # 403 = blocked
    # 429 = slow down or blocked
    retry_policy = Retry(
        total=2,
        connect=2,
        read=2,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,)

    adapter = HTTPAdapter(max_retries=retry_policy, pool_connections=1, pool_maxsize=1)

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    return session


# -----------------------------
# HTML parsing
# -----------------------------

def clean_text(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def remove_junk_tags(soup):
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()


def parse_description(full_html):
    soup = BeautifulSoup(full_html, "html.parser")
    remove_junk_tags(soup)

    selectors = [
        "section.adp-body",
        "div[itemprop='description']",
        "article",
        "main",]

    for selector in selectors:
        node = soup.select_one(selector)

        if not node:
            continue

        text = clean_text(node.get_text("\n", strip=True))

        if text and len(text) >= MIN_SCRAPED_TEXT_LENGTH:
            return node, text, selector

    body = soup.select_one("body")

    if body:
        text = clean_text(body.get_text("\n", strip=True))

        if text and len(text) >= MIN_SCRAPED_TEXT_LENGTH:
            return None, text, "body_fallback"

    return None, None, "no_useful_text_found"


def looks_blocked_text(text):
    if not isinstance(text, str):
        return False

    lower_text = text.lower()

    for marker in BLOCKED_TEXT_MARKERS:
        if marker.lower() in lower_text:
            return True

    return False


# -----------------------------
# Scraping
# -----------------------------

def wait_before_request():
    delay = random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS)
    time.sleep(delay)


def fetch_and_extract(session, url):
    wait_before_request()

    try:
        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=True,
        )

        content_type = response.headers.get("Content-Type", "")
        full_html = response.text or ""

        if response.status_code in [403, 429]:
            return {
                "html": None,
                "job_description_text": None,
                "html_parse_status": "blocked_or_rate_limited",
                "final_url": response.url,
                "status_code": response.status_code,
                "content_type": content_type,
                "request_error": None,
                "status": "blocked",
            }

        if response.status_code != 200:
            return {
                "html": None,
                "job_description_text": None,
                "html_parse_status": "non_200_response",
                "final_url": response.url,
                "status_code": response.status_code,
                "content_type": content_type,
                "request_error": None,
                "status": "non_200",
            }

        if "text/html" not in content_type.lower():
            return {
                "html": None,
                "job_description_text": None,
                "html_parse_status": "not_html",
                "final_url": response.url,
                "status_code": response.status_code,
                "content_type": content_type,
                "request_error": None,
                "status": "not_html",
            }

        node, description_text, parse_source = parse_description(full_html)

        if looks_blocked_text(description_text):
            return {
                "html": None,
                "job_description_text": None,
                "html_parse_status": "blocked_text_detected",
                "final_url": response.url,
                "status_code": response.status_code,
                "content_type": content_type,
                "request_error": None,
                "status": "blocked",
            }

        if description_text:
            return {
                "html": str(node) if (SAVE_RAW_HTML and node is not None) else None,
                "job_description_text": description_text,
                "html_parse_status": parse_source,
                "final_url": response.url,
                "status_code": response.status_code,
                "content_type": content_type,
                "request_error": None,
                "status": "body_returned",
            }

        return {
            "html": None,
            "job_description_text": None,
            "html_parse_status": parse_source,
            "final_url": response.url,
            "status_code": response.status_code,
            "content_type": content_type,
            "request_error": None,
            "status": "no_useful_text",
        }

    except requests.exceptions.RequestException as error:
        return {
            "html": None,
            "job_description_text": None,
            "html_parse_status": "request_exception",
            "final_url": None,
            "status_code": None,
            "content_type": None,
            "request_error": str(error),
            "status": "request_failed",
        }


# -----------------------------
# Job update logic
# -----------------------------

def initialize_job_defaults(job):
    # Start with no enriched description
    # If scraping fails later the API description can be used as fallback
    job["job_description_text"] = None
    job["description_source"] = "not_enriched"
    job["html"] = None
    job["html_parse_status"] = "not_scraped"
    job["final_url"] = None
    job["status_code"] = None
    job["content_type"] = None
    job["request_error"] = None
    job["blocked_by_anti_bot"] = False
    job["skills"] = []
    job["skills_count"] = 0
    job["YOE"] = None


def apply_api_fallback_to_job(job, skills):
    api_description = job.get("description")

    if isinstance(api_description, str) and api_description.strip():
        job["job_description_text"] = api_description.strip()
        job["description_source"] = "adzuna_api_fallback"
        job["blocked_by_anti_bot"] = False
        job["skills"] = extract_skills(job["job_description_text"], skills)
        job["skills_count"] = len(job["skills"])
        job["YOE"] = extract_yoe(job["job_description_text"])

    return job


def apply_scrape_result_to_job(job, result, skills):
    job["html"] = result.get("html")
    job["html_parse_status"] = result.get("html_parse_status")
    job["final_url"] = result.get("final_url")
    job["status_code"] = result.get("status_code")
    job["content_type"] = result.get("content_type")
    job["request_error"] = result.get("request_error")

    if result.get("status") == "blocked":
        job["job_description_text"] = None
        job["description_source"] = "blocked_no_fallback"
        job["blocked_by_anti_bot"] = True
        job["skills"] = []
        job["skills_count"] = 0
        job["YOE"] = None
        return job

    scraped_text = result.get("job_description_text")

    if isinstance(scraped_text, str) and scraped_text.strip():
        job["job_description_text"] = scraped_text.strip()
        job["description_source"] = "scraped_page"
        job["blocked_by_anti_bot"] = False
        job["skills"] = extract_skills(job["job_description_text"], skills)
        job["skills_count"] = len(job["skills"])
        job["YOE"] = extract_yoe(job["job_description_text"])
        return job

    job["job_description_text"] = None
    job["description_source"] = "not_enriched"
    job["blocked_by_anti_bot"] = False
    job["skills"] = []
    job["skills_count"] = 0
    job["YOE"] = None

    return apply_api_fallback_to_job(job, skills)


def should_write_enriched_job(job):
    return job.get("description_source") in ["scraped_page", "adzuna_api_fallback"]


# -----------------------------
# Tracker setup
# -----------------------------

def create_fresh_tracker(jobs_data_file, total_urls):
    timestamp = datetime.now().isoformat().replace(":", "_")
    input_base = os.path.splitext(jobs_data_file)[0]

    tracker = {
        "input_file": jobs_data_file,
        "created_at": timestamp,
        "updated_at": timestamp,
        "resume_position": 0,
        "total_urls": total_urls,
        "enriched_jsonl_file": f"enriched_stream_{input_base}_{timestamp}.jsonl",
        "enriched_json_file": f"enriched_stream_{input_base}_{timestamp}.json",
        "scrape_report_jsonl_file": f"scrape_report_{input_base}_{timestamp}.jsonl",
        "status": "running",
        "last_url": None,
        "last_status": None,
        "last_status_code": None,
        "successful_scrape_urls": 0,
        "api_fallback_jobs": 0,
        "blocked_urls": 0,
        "no_useful_text_urls": 0,
        "not_html_urls": 0,
        "non_200_urls": 0,
        "request_failed_urls": 0,
        "block_breaks_taken": 0,
    }

    write_tracker(tracker)
    print(f"Created tracker: {TRACKER_FILE}")
    return tracker


def create_or_load_tracker(jobs_data_file, total_urls):
    existing_tracker = read_tracker()

    # If there is no tracker yet, create a new one.
    if not existing_tracker:
        return create_fresh_tracker(jobs_data_file, total_urls)

    tracker_input_file = existing_tracker.get("input_file")

    # If tracker exists and belongs to this input file, resume it.
    if tracker_input_file == jobs_data_file:
        print(f"Resuming from tracker: {TRACKER_FILE}")
        print(f"Tracker input file matches current jobs file: {jobs_data_file}")
        return existing_tracker

    # If tracker exists but belongs to a different input file, start over from position 0.
    print("Existing tracker belongs to a different input file.")
    print(f"Tracker input file: {tracker_input_file}")
    print(f"Current input file: {jobs_data_file}")
    print("Starting fresh tracker from position 0.")

    return create_fresh_tracker(jobs_data_file, total_urls)


def update_tracker_after_attempt(tracker, position, url, result, should_resume_from_current=False):
    tracker["updated_at"] = datetime.now().isoformat()
    tracker["last_url"] = url
    tracker["last_status"] = result.get("status")
    tracker["last_status_code"] = result.get("status_code")

    if result.get("status") == "body_returned":
        tracker["successful_scrape_urls"] = tracker.get("successful_scrape_urls", 0) + 1
    elif result.get("status") == "blocked":
        tracker["blocked_urls"] = tracker.get("blocked_urls", 0) + 1
    elif result.get("status") == "no_useful_text":
        tracker["no_useful_text_urls"] = tracker.get("no_useful_text_urls", 0) + 1
    elif result.get("status") == "not_html":
        tracker["not_html_urls"] = tracker.get("not_html_urls", 0) + 1
    elif result.get("status") == "non_200":
        tracker["non_200_urls"] = tracker.get("non_200_urls", 0) + 1
    elif result.get("status") == "request_failed":
        tracker["request_failed_urls"] = tracker.get("request_failed_urls", 0) + 1

    # If needed, resume from this same URL later.
    # Otherwise, resume from the next URL.
    if should_resume_from_current:
        tracker["resume_position"] = position
    else:
        tracker["resume_position"] = position + 1

    write_tracker(tracker)


def sleep_after_too_many_blocks(tracker, position):
    tracker["status"] = "sleeping_after_consecutive_blocks"
    tracker["updated_at"] = datetime.now().isoformat()
    tracker["resume_position"] = position + 1
    tracker["block_breaks_taken"] = tracker.get("block_breaks_taken", 0) + 1
    write_tracker(tracker)

    print("")
    print(
        f"{MAX_BLOCKED_URLS_IN_A_ROW_BEFORE_BREAK} blocked responses happened in a row. "
        f"Sleeping for {BLOCK_BREAK_SECONDS} seconds before trying the next scrape..."
    )
    time.sleep(BLOCK_BREAK_SECONDS)

    tracker["status"] = "running"
    tracker["updated_at"] = datetime.now().isoformat()
    write_tracker(tracker)

    print("")
    print("Block break finished. Continuing scrape...")


# -----------------------------
# Main pipeline
# -----------------------------

def main():
    skills = load_known_skills()
    jobs_data_file = find_jobs_file()
    jobs = load_jobs_data(jobs_data_file)

    print(f"Loaded {len(jobs)} jobs from {jobs_data_file}")

    for job in jobs:
        initialize_job_defaults(job)

    # Group by redirect_url to avoid duplicate HTTP fetches.
    jobs_by_url = {}

    for index, job in enumerate(jobs):
        url = job.get("redirect_url")

        if not isinstance(url, str) or not url.strip():
            continue

        jobs_by_url.setdefault(url, []).append(index)

    urls_to_fetch = list(jobs_by_url.keys())

    tracker = create_or_load_tracker(jobs_data_file, len(urls_to_fetch))

    start_position = tracker.get("resume_position", 0)

    if start_position >= len(urls_to_fetch):
        print("Tracker says all URLs were already completed.")
        final_records = build_json_from_jsonl(
            tracker["enriched_jsonl_file"],
            tracker["enriched_json_file"])

        tracker["status"] = "complete"
        tracker["updated_at"] = datetime.now().isoformat()
        write_tracker(tracker)

        print(f"Final JSON refreshed: {tracker['enriched_json_file']}")
        print(f"Total enriched records: {len(final_records)}")
        return

    print(f"Unique scrape candidates: {len(jobs_by_url)}")
    print(f"Total URLs selected: {len(urls_to_fetch)}")
    print(f"Starting from position: {start_position}")
    print(f"Scrapes per batch: {SCRAPES_PER_BATCH}")
    print(f"Break between batches: {BATCH_BREAK_SECONDS} seconds")
    print(f"Block break after consecutive blocks: {BLOCK_BREAK_SECONDS} seconds")
    print(f"Streaming enriched output to: {tracker['enriched_jsonl_file']}")

    session = build_session()

    consecutive_blocked_url_count = 0

    try:
        for position in range(start_position, len(urls_to_fetch)):
            url = urls_to_fetch[position]
            batch_number = position // SCRAPES_PER_BATCH + 1
            position_in_batch = position % SCRAPES_PER_BATCH

            # Break between batches, but not before the very first request.
            if position != start_position and position_in_batch == 0:
                print("")
                print(f"Batch {batch_number - 1} complete. Sleeping for {BATCH_BREAK_SECONDS} seconds...")
                time.sleep(BATCH_BREAK_SECONDS)
                print("")
                print(f"Starting batch {batch_number}")

            result = fetch_and_extract(session, url)

            # Always write scrape attempt immediately
            scrape_record = {
                "position": position,
                "url": url,
                "status": result.get("status"),
                "status_code": result.get("status_code"),
                "final_url": result.get("final_url"),
                "html_parse_status": result.get("html_parse_status"),
                "batch_number": batch_number,
                "timestamp": datetime.now().isoformat(), }

            append_jsonl(tracker["scrape_report_jsonl_file"], scrape_record)

            if result.get("status") == "blocked":
                consecutive_blocked_url_count += 1

                # save tracker after this blocked URL
                # since the script is continuing the next run should start from the next URL since we already know this one is blocked
                update_tracker_after_attempt(
                    tracker,
                    position,
                    url,
                    result,
                    should_resume_from_current=False,)

                # print the batch status after each URL for visibility into the process especially blocked URLs
                print(f"[{position + 1}/{len(urls_to_fetch)}] "f"Batch {batch_number} | "f"{url} | {result.get('status')} | {result.get('status_code')}")

                # if too many blocks happen in a row take a long break before trying the next URL
                if consecutive_blocked_url_count >= MAX_BLOCKED_URLS_IN_A_ROW_BEFORE_BREAK:
                    # helper function to update tracker status to sleeping and then back to running after the break is over
                    sleep_after_too_many_blocks(tracker, position)
                    consecutive_blocked_url_count = 0

                continue

            # If the request was not blocked, reset the consecutive block count
            consecutive_blocked_url_count = 0

            # For non blocked attempts process jobs mapped to this URL
            for job_index in jobs_by_url[url]:
                job = jobs[job_index]
                updated_job = apply_scrape_result_to_job(job, result, skills)

                # If enriched, immediately append to output file.
                if should_write_enriched_job(updated_job):
                    append_jsonl(tracker["enriched_jsonl_file"], updated_job)

                    if updated_job.get("description_source") == "adzuna_api_fallback":
                        tracker["api_fallback_jobs"] = tracker.get("api_fallback_jobs", 0) + 1

            # For non blocked statuses, resume from the next URL next time.
            # what this does is if the script is interrupted it will not redo the last URL since it already succeeded it will move on to the next one
            update_tracker_after_attempt(
                tracker,
                position,
                url,
                result,
                should_resume_from_current=False,)

            # print the batch status after each URL for visibility into the process
            print( f"[{position + 1}/{len(urls_to_fetch)}] " f"Batch {batch_number} | " f"{url} | {result.get('status')} | {result.get('status_code')}")

        # Build normal JSON file from streamed JSONL for MongoDB
        # tracker status is complete since we finished all URLs
        # tracker picks up where it left off if interrupted so if we got here it means all URLs were processed
        final_records = build_json_from_jsonl(
            tracker["enriched_jsonl_file"],
            tracker["enriched_json_file"])

        if tracker.get("resume_position", 0) >= len(urls_to_fetch):
            tracker["status"] = "complete"
        else:
            tracker["status"] = "paused"

        tracker["updated_at"] = datetime.now().isoformat()
        write_tracker(tracker)

        print("")
        print("Run summary:")
        print(f"Tracker file: {TRACKER_FILE}")
        print(f"Resume position: {tracker.get('resume_position')}/{len(urls_to_fetch)}")
        print(f"Tracker status: {tracker.get('status')}")
        print(f"Streaming enriched JSONL: {tracker['enriched_jsonl_file']}")
        print(f"Mongo-ready enriched JSON: {tracker['enriched_json_file']}")
        print(f"Total enriched records in JSON: {len(final_records)}")
        print(f"Successful scrape URLs total: {tracker.get('successful_scrape_urls')}")
        print(f"API fallback jobs total: {tracker.get('api_fallback_jobs')}")
        print(f"Blocked URLs total: {tracker.get('blocked_urls')}")
        print(f"No useful text URLs total: {tracker.get('no_useful_text_urls')}")
        print(f"Not HTML URLs total: {tracker.get('not_html_urls')}")
        print(f"Non-200 URLs total: {tracker.get('non_200_urls')}")
        print(f"Request failed URLs total: {tracker.get('request_failed_urls')}")
        print(f"Block breaks taken: {tracker.get('block_breaks_taken')}")

    # process can be interrupted by the user and will save progress up to the last URL immediately
    # to interrupt press Ctrl+C in the terminal where this script is running
    except KeyboardInterrupt:
        print("")
        print("Interrupted manually. Saving current JSON file from streamed JSONL")

        final_records = build_json_from_jsonl(
            tracker["enriched_jsonl_file"],
            tracker["enriched_json_file"])

        tracker["status"] = "interrupted"
        tracker["updated_at"] = datetime.now().isoformat()
        write_tracker(tracker)


        print(f"Tracker saved: {TRACKER_FILE}")
        print(f"Resume position: {tracker.get('resume_position')}/{len(urls_to_fetch)}")
        print(f"Mongo-ready enriched JSON refreshed: {tracker['enriched_json_file']}")
        print(f"Total enriched records in JSON: {len(final_records)}")


if __name__ == "__main__":
    main()