Ingestion.py :
This script acts as the ingestion step for pulling job data from Adzuna. 
It reads API credentials from a local file, then loops through a set of target job categories and 
sends paginated requests to the search endpoint. A keyword filter (“computer science”) is used to keep the results manageable.
For each response, it extracts job records from the "results" field, removes duplicates using the job ID, and tags each record 
with a timestamp and its category before adding it to a list. It also prints the final request URL for visibility, handles basic
request errors, and includes a small delay between calls to avoid rate limits.

Data_Enrichment.py :
This script runs after ingestion and takes the raw jobs_*.txt file and enriches it with additional fields. It loops through each job and first pulls out the state from the location.area field and stores it as state.
Then it hits each job’s redirect_url and makes an HTTP request to get the full page HTML.
Most of these redirects lead to an Adzuna job details page, so the script parses the HTML using BeautifulSoup and looks
specifically for the section.adp-body element, which contains the full job description.
If that section is found, it stores both the HTML for that section and a cleaned text version of the job description.
If not found then it flags that the description wasn’t found. It also stores some basic metadata like the final resolved URL, status code,
and content type for debugging. There are delays between requests to avoid getting rate limited. The output is written to a new file prefixed with enriched_
so the original ingestion data stays untouched in case there are errors supplementing the data. 


Adzuna API Limits (Free Tier):
Per Minute: 25 requests
Per Day: 250 requests
Per Week: 1000 requests
Per Month: 2500 requests
Maximum Results Per API Call: 1000

Ingestion Guardrails Implemented:
The ingestion script now enforces free-tier pacing and request caps so local runs do not exceed quota accidentally.

Configurable environment variables:
ADZUNA_REQUESTS_PER_RUN_CAP
Defaults to 200 and is clamped to the free-tier daily max (250).

ADZUNA_MAX_PAGES_PER_CATEGORY
Defaults to 2 pages per category.

Example (PowerShell):
$env:ADZUNA_REQUESTS_PER_RUN_CAP = "150"
$env:ADZUNA_MAX_PAGES_PER_CATEGORY = "3"
python ingestion.py



Below is a sample response from the Adzuna API, and then after is the api response schema. The top section contains metadata about the request, including the total number of records available. The mean field represents the average salary across all returned records.
Individual job records are located under the "results" field.
If salary_is_predicted = 1, the salary value is estimated by Adzuna rather than provided directly.
Adzuna returns up to 50 results per page. Broad searches across the three relevant categories can return 500,000+ results, so it’s important to narrow queries using the what parameter.

Example using the what parameter:
https://api.adzuna.com/v1/api/jobs/us/search/1?app_id=8e88dd1a&app_key=501524232a49925c03eec7a276d7fb5f&results_per_page=50&category=scientific-qa-jobs&what=computer+science

{
  "__CLASS__": "Adzuna::API::Response::JobSearchResults",
  "count": 223050,
  "mean": 154364.27,
  "results": [
    {
      "__CLASS__": "Adzuna::API::Response::Job",
      "id": "5701856729",
      "title": "IAM Engineer III",
      "description": "About the Job: We are seeking an IAM Engineer to join our Identity Governance & Administration (IGA) team to design, build, and operate identity governance capabilities, while developing and supporting Java-based applications and services that enable IAM at scale. The ideal candidate has hands-on experience with SailPoint (IdentityIQ and/or ISC) and strong Java development skills to build and maintain custom software solutions. What's the Job: Implement and maintain IGA capabilities including l…",
      "created": "2026-04-16T16:47:43Z",
      "adref": "eyJhbGciOiJIUzI1NiJ9.eyJpIjoiNTcwMTg1NjcyOSIsInMiOiIxSklJSGQwNThSR2M5XzFOc1hKeWRRIn0.wKPKoiwr6yLkJNvCIklM7e7IT-zraVWKtBLoT57hNyU",
      "redirect_url": "https://www.adzuna.com/land/ad/5701856729?se=1JIIHd058RGc9_1NsXJydQ&utm_medium=api&utm_source=8e88dd1a&v=3C8A519DC98ED7FD16382ACDC55305FCF6D0FACB",
      "salary_min": 164398.53,
      "salary_max": 164398.53,
      "salary_is_predicted": "1",
      "latitude": 43.053096,
      "longitude": -87.932603,
      "company": {
        "__CLASS__": "Adzuna::API::Response::Company",
        "display_name": "Northwestern Mutual"
      },
      "category": {
        "__CLASS__": "Adzuna::API::Response::Category",
        "label": "IT Jobs",
        "tag": "it-jobs"
      },
      "location": {
        "__CLASS__": "Adzuna::API::Response::Location",
        "display_name": "Milwaukee, Milwaukee County",
        "area": [
          "US",
          "Wisconsin",
          "Milwaukee County",
          "Milwaukee"
        ]
      }
    }
  ]
}




SCHEMA: 
{
  "type": "object",
  "properties": {
    "location": {
      "type": "object",
      "properties": {
        "area": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "display_name": {
          "type": "string"
        },
        "__CLASS__": {
          "type": "string"
        }
      },
      "required": [
        "area",
        "display_name",
        "__CLASS__"
      ]
    },
    "company": {
      "type": "object",
      "properties": {
        "__CLASS__": {
          "type": "string"
        },
        "display_name": {
          "type": "string"
        }
      },
      "required": [
        "__CLASS__"
      ]
    },
    "created": {
      "type": "string",
      "format": "date-time"
    },
    "adref": {
      "type": "string"
    },
    "title": {
      "type": "string"
    },
    "redirect_url": {
      "type": "string",
      "format": "uri"
    },
    "salary_max": {
      "type": "number"
    },
    "salary_min": {
      "type": "number"
    },
    "id": {
      "type": "string"
    },
    "salary_is_predicted": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "__CLASS__": {
      "type": "string"
    },
    "category": {
      "type": "object",
      "properties": {
        "label": {
          "type": "string"
        },
        "tag": {
          "type": "string"
        },
        "__CLASS__": {
          "type": "string"
        }
      },
      "required": [
        "label",
        "tag",
        "__CLASS__"
      ]
    },
    "TIMESTAMP": {
      "type": "string",
      "format": "date-time"
    },
    "Category": {
      "type": "string"
    },
    "contract_time": {
      "type": "string"
    },
    "contract_type": {
      "type": "string"
    },
    "latitude": {
      "type": "number"
    },
    "longitude": {
      "type": "number"
    }
  },
  "required": [
    "location",
    "company",
    "created",
    "adref",
    "title",
    "redirect_url",
    "salary_max",
    "salary_min",
    "id",
    "salary_is_predicted",
    "description",
    "__CLASS__",
    "category",
    "TIMESTAMP",
    "Category"
  ]
}