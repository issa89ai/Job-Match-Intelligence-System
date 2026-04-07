A production-style data pipeline and intelligence system that collects real job postings, normalizes them, extracts requirements, and matches them with candidate profiles to compute fit scores and actionable insights.

---

## 📌 Overview

This project builds an end-to-end **Job Intelligence Platform** that:

- Collects real job postings from public sources
- Normalizes and structures job data
- Extracts job requirements (skills, experience, education)
- Parses candidate profiles
- Computes match scores between jobs and candidates
- Provides explanations and recommendations

The system follows a **multi-stage data pipeline architecture** similar to real-world data platforms.

---

## 🏗️ Architecture


Raw Data → Staging → Curated → Extracted → Matching → API/UI


---

## 📂 Project Structure


job-match-intelligence/
│
├── configs/
│ ├── sources.yaml
│ ├── skills.yaml
│ └── scoring.yaml
│
├── data/
│ ├── raw/
│ ├── staging/
│ ├── curated/
│ └── evaluation/
│
├── src/
│ ├── ingestion/
│ ├── normalization/
│ ├── extraction/
│ ├── candidate/
│ ├── matching/
│ ├── api/
│ ├── utils/
│ └── evaluation/
│
├── tests/
├── notebooks/
├── requirements.txt
└── README.md


---

## ✅ Current System Status

### ✔ Phase 1 — Foundation
- Config-driven architecture (YAML)
- Utilities for I/O, logging, and text processing

### ✔ Phase 2 — Ingestion Pipeline
- Fetches jobs from Greenhouse (Stripe, Airbnb)
- Stores raw snapshots
- Converts data into unified schema
- Saves staging dataset
- Structured logging

📊 Result:
- ~747 real job postings collected

---

### ✔ Phase 3 — Normalization Pipeline
- Title normalization (job family, seniority)
- Location normalization (country, region, workplace type)
- Text cleaning and standardization
- Deduplication using hashes

📂 Output:

data/curated/requirements/jobs_curated_*.csv


---

## 🧠 Data Layers

### 1. Raw Layer
- Original API responses
- Full traceability

### 2. Staging Layer
- Unified schema across sources
- Cleaned structure

### 3. Curated Layer
- Normalized and enriched data
- Ready for intelligence processing

---

## ⚙️ How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
2. Run Ingestion
python -m src.ingestion.pipeline

Outputs:

data/raw/jobs/
data/staging/jobs/
3. Run Normalization

Update input file in:

src/normalization/jobs.py

Then run:

python -m src.normalization.jobs

Outputs:

data/curated/requirements/
📊 Example Output
Normalized Job Record
{
  "title_normalized": "account_executive",
  "job_family": "sales",
  "seniority_level": "",
  "country": "brazil",
  "region": "south_america",
  "workplace_type": "onsite"
}
🚀 Next Phases
🔹 Phase 4 — Requirement Extraction
Extract skills (required vs preferred)
Extract experience requirements
Extract education requirements
🔹 Phase 5 — Candidate Understanding
Parse resumes
Extract skills, experience, education
🔹 Phase 6 — Matching Engine
Hard filters
Scoring system (config-driven)
Ranking
Explainability
🔹 Phase 7 — API (FastAPI)
Expose matching as a service
🔹 Phase 8 — Evaluation
Measure extraction accuracy
Evaluate ranking quality
🔹 Phase 9 — UI (Streamlit)
Resume upload
Job matching visualization
Recommendations
🧠 Design Principles
Modular architecture
Config-driven system
Layered data pipeline
Reproducibility
Explainability (no black-box logic)
Extensibility (multi-source support)
📈 Future Improvements
NLP-based semantic matching
Embedding models (Sentence Transformers)
ML-based scoring
Advanced resume parsing
Geo-location enrichment APIs
💡 Key Insight

Most of the system complexity is in:

Data cleaning, normalization, and structuring — not the model itself.

👨‍💻 Author



Ahmad — Master's student in Computer Science (Data Science focus)

