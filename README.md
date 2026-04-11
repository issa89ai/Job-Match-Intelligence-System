Job Match Intelligence System

A production-style data pipeline and intelligent matching system that collects real job postings, processes them through multiple data layers, extracts structured requirements, and matches them with candidate profiles to generate fit scores and actionable insights.

📌 Overview

This project builds an end-to-end Job Intelligence Platform that:

Collects real job postings from multiple sources
Normalizes and structures job data
Extracts job requirements (skills, experience, education)
Parses and structures candidate profiles
Computes job–candidate match scores
Provides explainable insights, gaps, and recommendations
Exposes the system via a FastAPI backend

Architecture
Raw Data → Staging → Curated → Extracted → Matching → API → (UI)

Project Structure
job-match-intelligence/
│
├── configs/
│   ├── sources.yaml
│   ├── skills.yaml
│   └── scoring.yaml
│
├── data/
│   ├── raw/
│   ├── staging/
│   ├── curated/
│   └── evaluation/
│
├── src/
│   ├── ingestion/        # Job collection pipelines
│   ├── normalization/    # Data cleaning & structuring
│   ├── extraction/       # Requirement extraction
│   ├── candidate/        # Candidate parsing & features
│   ├── matching/         # Scoring + ranking engine
│   ├── api/              # FastAPI service
│   ├── utils/
│   └── evaluation/
│
├── tests/
├── notebooks/
├── requirements.txt
└── README.md

✔ Phase 1 — Foundation
Config-driven architecture (YAML)
Utilities for I/O, logging, and text normalization

✔ Phase 2 — Ingestion Pipeline
Collects jobs from Greenhouse (Stripe, Airbnb)
Stores raw API snapshots
Converts to unified schema
Saves staging datasets

📊 Result:

~747 real job postings collected

✔ Phase 3 — Normalization Pipeline
Job title normalization (family, function, seniority)
Location normalization (country, region, workplace type)
Text cleaning and standardization
Deduplication using hashing

📂 Output:

data/curated/requirements/jobs_curated_*.csv

✔ Phase 4 — Requirement Extraction
Extracts:
Required skills
Preferred skills
Years of experience
Education requirements
Seniority inference

📂 Output:

data/curated/requirements_enriched/

✔ Phase 5 — Candidate Understanding
Structured candidate profile schema
Normalization of:
skills
tools
domains
education
experience
Feature engineering:
seniority inference
ranking features
keyword aggregation

✔ Phase 6 — Matching Engine

Core intelligence layer:

Hard filters:
required skills
experience
education
Weighted scoring system:
required skills
preferred skills
experience
education
seniority
Explainability:
matched skills
missing skills
gaps
recommendations

📊 Example Output:

{
  "score": 52.0,
  "fit_label": "Partial Fit",
  "gaps": [
    "Missing required skills: enterprise, sales",
    "Experience gap: candidate has 6 years vs required 10"
  ],
  "recommendations": [
    "Develop required skills",
    "Target roles with lower experience requirements"
  ]
}

✔ Stage 7 — API Layer (FastAPI)
REST API built using FastAPI
Endpoint:
POST /match
Returns:
hard filters
match score
fit label
skill gaps
recommendations

📄 Swagger UI:

http://127.0.0.1:8000/docs

🧠 Data Layers
1. Raw Layer
Original API responses
Full traceability
2. Staging Layer
Unified schema
Cleaned structure
3. Curated Layer
Normalized and enriched data
Ready for intelligence processing
4. Extracted Layer
Structured requirements from job descriptions

### Stage 8 — UI Layer (Streamlit)
- Professional frontend for job-candidate matching
- Job and candidate input forms
- API-connected scoring workflow
- Visual display of score, filters, gaps, and recommendations
- Demo-ready interface


⚙️ How to Run
1️⃣ Install dependencies
pip install -r requirements.txt
2️⃣ Run Ingestion
python -m src.ingestion.pipeline
3️⃣ Run Normalization
python -m src.normalization.jobs
4️⃣ Run Extraction
python -m src.extraction.requirements
5️⃣ Run API
python -m uvicorn src.api.main:app --reload

Open:

http://127.0.0.1:8000/docs

🧠 Design Principles
Modular architecture
Config-driven system
Layered data pipeline
Reproducibility
Explainability (no black-box logic)
Extensibility (multi-source ready)

 Next Steps


🔹 Stage 9 — Evaluation
Extraction accuracy (precision/recall)
Ranking quality

📈 Future Improvements
Semantic matching (Sentence Transformers)
Embedding-based similarity
ML-based scoring model
Advanced resume parsing
Geo-location enrichment APIs

💡 Key Insight

Most of the system complexity lies in data cleaning, normalization, and structuring — not the model itself.

👨‍💻 Author

Ahmad
Master’s Student — Computer Science (Data Science)
Focused on building real-world ML systems, data pipelines, and AI applications
