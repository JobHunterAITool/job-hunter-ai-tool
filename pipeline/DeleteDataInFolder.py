import os

# delete local job output files from ingestion and enrichment
# this removes:
# jobs_*.txt
# jobs_*.json
# enriched_jobs_*.txt
# enriched_jobs_*.json
# blocked_urls_jobs_*.json

files_deleted = 0

for file in os.listdir():
    should_delete = (
        file.endswith(".json")
        or file.endswith(".jsonl")
        or (file.startswith("jobs_") and file.endswith(".txt"))
        or (file.startswith("enriched_jobs_") and file.endswith(".txt"))
        or (file.startswith("enriched_stream_jobs_") and file.endswith(".txt"))
    )
    if should_delete:
        os.remove(file)
        files_deleted += 1
        print(f"Deleted: {file}")

print(f"Cleanup complete. Files deleted: {files_deleted}")