# The Job Hunting AI Web Tool

> This is the 'production' repo for the Job Hunter AI Tool.

## Project Requirements

> Source: https://eecs.engineering.oregonstate.edu/capstone/submission/pages/viewSingleProject.php?id=UqHibY35MJbhf0ba

Develop the ultimate smart AI-based job searching tool. This project will be done by capstone students who are also interested in Data Science, Machine Learning, Text Mining, Web Development, Python Programming, Web Applications, and related tools and models. The goal here is to envision, plan, and develop this open-source platform which could be deployed via the web world-wide. 

> **IMPORTANT:** This project does not have a “mentor”. If you choose this project, you and your team will elect a Team Leader from your group of learners. You will direct your project, determine methods and models, and independently decide directions, goals, ideas, and results. 

### Objectives
1. Explore data, criteria, and goals related to technical job searches. 
2. Understand the problem domain, the challenges, the stakeholders, the use cases, and the potential clients. 
3. Use data, such as via web scraping, APIs, and other methods to gather data and through this data information about all aspects of web-based job searching from the perspectives of both the searcher as well as the advertiser. Include correlations and analytics that can discover as well as model or predict relationships between academic credentials, key words, locations, skills, and related. 
4. Develop a web site that interacts with Users to gather User job search criteria and to return a list of a given number of highly connected, relevant, and correlated job opportunities. 
5. Use machine learning and text mining models and methods to evaluate, analyze, predict/model, describe various patterns, correlations, and eventual suggestions. 
 
The final deliverable is a deployed and fully functional web site that interacts with Users, gathers information from the User, and delivers a solution that includes a list of highly correlated job application opportunities. 

> **IMPORTANT:** This project does not have a “mentor”. If you choose this project, you and your team will elect a Team Leader from your group of learners. You will direct your project, determine methods and models, and independently decide directions, goals, ideas, and results. 

Great Project Resource: https://gatesboltonanalytics.com/

Please note that is project does not have a formal mentor and is student team managed and directed. If you choose this project for a short summer class such as CS 467, make sure to manage the deliverables for that time frame. Alternatively, if you choose this project for a 3-term capstone (such as CS 461, 462, and 463) you will be expected to make the project more robust (and to determine how best to do this). 

### Motivations
Job searching can be time consuming and challenging, especially for students or new job hunters. Our goal is to envision, plan, develop, and deploy a job search site that utilizes AI methods and models. Methods and models might include web development, client-server interaction, data gathering via web scraping and APIs (application programming interfaces), text mining, data analytics, machine learning, visualization, classification, and related. 

An example use-case might include a User engaging with the web site, entering critical information related to job search goals, interests, areas, locations, etc., and then receiving a list of a given number of highly matched and correlated opportunities. 

### Qualifications

#### Minimum Qualifications:

- A considerable interest in using AI/Machine Learning, and Data Science tools, methods, and models. 
- A strong desire to improve job search outcomes and to assist Users (and especially students and new seekers). 
- A willingness to learn new methods and models and to to apply and interpret results.
- An interest in data science, web development, text mining, AI/machine learning, and analytics.
 
#### Preferred Qualifications:

Intermediate (or better) abilities in programming (such as in Python) and in Web Development (such as via HTML/JS, and related.)

## Quick Start Commands

```bash
python -m venv .venv
source .venv/bin/activate   # or .\.venv\Scripts\Activate.ps1 on Windows
python -m pip install -r ml/requirements.txt
python -m pytest
```

## Naming Conventions

To keep this repository consistent across backend, frontend, ML, and pipeline code, use the following naming rules.

### Python Backend and ML (PEP 8)

- Packages and directories: lowercase.
	- Preferred: short lowercase names.
	- Allowed when helpful: lowercase_with_underscores.
- Python files (modules): lowercase_with_underscores.py.
- Classes and exception types: PascalCase.
- Functions, methods, variables, and parameters: lowercase_with_underscores.
- Constants: UPPERCASE_WITH_UNDERSCORES.
- Private/internal helpers: prefix with a single underscore.

### FastAPI Project Structure

- routes directory: one file per route domain.
	- Examples: search.py, jobs.py, upload_resume.py.
- services directory: business logic only.
	- Examples: ranking.py, resume_parser.py.
- models directory: request/response/data schemas.
	- Example: schemas.py.

### Frontend (React + JavaScript)

- React component files: PascalCase.jsx.
	- Examples: SearchForm.jsx, JobResults.jsx.
- Non-component JavaScript files: camelCase.js.
	- Examples: apiClient.js, mockApi.js.
- Functions and variables in JavaScript: camelCase.
- Constants in JavaScript: UPPER_SNAKE_CASE when truly constant.
- CSS files:
	- Component-scoped styles: match component name where practical (PascalCase.css), or use a documented local pattern.
	- Global styles: lowercase (for example index.css).

### Docs and Config Files

- Markdown docs: lowercase_with_underscores.md.
	- Examples: api_contract.md, design_architecture.md.
- Keep naming readable and descriptive over abbreviated names.

### Repository-Wide Rules

- Avoid mixed styles for the same category (for example, do not mix mockAPI.js and mock_api.js).
- Do not use capitalized directory names for Python package-like folders.
- Use one naming style per layer and keep it stable to reduce churn and merge conflicts.

### Suggested Normalization Targets in This Repo

- [ ] Rename `Pipeline` directory to `pipeline`.
- [ ] Rename `ml_README.md` to `ml_readme.md` (or merge into `README.md` inside `ml`).
- [ ] Keep Python backend files in lowercase_with_underscores.
- [ ] Keep React component files in PascalCase and frontend utility files in camelCase.

