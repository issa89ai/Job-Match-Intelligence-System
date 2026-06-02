\# 💼 Job Match Intelligence System



An end-to-end intelligent platform that collects real-world job postings, processes them into structured datasets, and matches them with candidate profiles using an explainable scoring and recommendation engine.



\---



\## 📌 Overview



This project implements a \*\*production-style Job Intelligence System\*\* that:



\* Collects real job postings from external sources (Greenhouse, Lever)

\* Processes data through structured pipeline layers

\* Extracts job requirements (skills, experience, education, seniority)

\* Parses and structures candidate profiles

\* Computes explainable job–candidate match scores

\* Generates personalized job recommendations

\* Provides a full API + interactive frontend



\---



\## 🏗️ Architecture



```text

Raw → Staging → Curated → Extracted → Matching → API → UI

```



\---



\## 📁 Project Structure



```text

Job-Match-Intelligence-System/

│

├── app/                    # Streamlit frontend

│   ├── streamlit\_app.py

│   └── style.css

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

│   ├── api/               # FastAPI backend

│   ├── auth/              # Authentication (JWT)

│   ├── candidate/         # Candidate parsing \& features

│   ├── db/                # Database models

│   ├── extraction/        # Requirement extraction

│   ├── ingestion/         # Job ingestion pipelines

│   ├── matching/          # Scoring, ranking, recommendation

│   ├── normalization/     # Data cleaning \& structuring

│   ├── utils/             # Utilities

│   └── evaluation/        # Evaluation scripts

│

├── tests/

├── notebooks/

├── requirements.txt

└── README.md

```



\---



\## ⚙️ System Components



\---



\### ✔ Phase 1 — Foundation



\* Config-driven architecture (YAML)

\* Utility modules (I/O, logging, text processing)



\---



\### ✔ Phase 2 — Ingestion Pipeline



\* Collects jobs from:



&#x20; \* Greenhouse

&#x20; \* Lever

\* Stores raw API responses

\* Converts to unified schema



📊 Result:



\* \~747 real job postings collected 



\---



\### ✔ Phase 3 — Normalization Pipeline



\* Job title normalization (family, function, seniority)

\* Location normalization (country, region, workplace type)

\* Text cleaning

\* Deduplication via hashing



📂 Output:



```

data/curated/requirements/

```



\---



\### ✔ Phase 4 — Requirement Extraction



Extracts:



\* Required skills

\* Preferred skills

\* Years of experience

\* Education requirements

\* Seniority



📂 Output:



```

data/curated/requirements\_enriched/

```



\---



\### ✔ Phase 5 — Candidate Understanding



\* Structured candidate profile schema

\* Normalization of:



&#x20; \* skills

&#x20; \* tools

&#x20; \* domains

&#x20; \* education

\* Feature engineering:



&#x20; \* seniority inference

&#x20; \* keyword aggregation



\---



\### ✔ Phase 6 — Matching Engine (Core Intelligence)



\#### 🔹 Hard Filters



\* Required skills

\* Experience

\* Education



\#### 🔹 Scoring System (Weighted)



\* Required skills

\* Preferred skills

\* Experience

\* Education

\* Seniority

\* Domain alignment



\#### 🔹 Output



\* Match score (0–100)

\* Fit label (Strong / Good / Partial / Weak)

\* Matched skills

\* Missing skills

\* Recommendations



\---



\### ✔ Phase 7 — API Layer (FastAPI)



Provides a complete REST API:



\#### 🔐 Authentication



\* Register

\* Login

\* JWT-based authorization



\#### 👤 User Features



\* Save profile

\* Load profile

\* Save preferences

\* Load preferences



\#### 📊 Core Endpoints



\* `POST /match` → single job matching

\* `GET /jobs` → preview dataset jobs

\* `POST /recommendations` → rank jobs from input

\* `POST /recommendations/from\_dataset` → full dataset ranking



📄 Swagger:



```

http://127.0.0.1:8000/docs

```



\---



\### ✔ Stage 8 — Frontend (Streamlit)



Interactive user interface with:



\* Authentication (login/register)

\* Candidate profile management

\* Single job matching

\* Job explorer (dataset preview)

\* Dataset-based recommendations

\* Preferences filtering system



Displays:



\* Match score

\* Fit label

\* Hard filter results

\* Skill match (matched / missing)

\* Recommendations

\* Component scores



\---



\### ✔ Stage 9 — Evaluation



\#### Extraction Performance



\* Precision: 0.75

\* Recall: 0.625

\* F1 Score: 0.6785 



\#### Matching Performance



\* Accuracy: 66.7% 



\---



\## 🧠 Data Layers



\### Raw Layer



\* Original API responses

\* Full traceability



\### Staging Layer



\* Unified structured schema



\### Curated Layer



\* Cleaned and normalized data



\### Extracted Layer



\* Structured requirements



\---



\## 🚀 How to Run



\### 1️⃣ Install Dependencies



```bash

pip install -r requirements.txt

```



\---



\### 2️⃣ Run Backend (FastAPI)



```bash

python -m uvicorn src.api.main:app --reload

```



👉 Open:



```

http://127.0.0.1:8000/docs

```



\---



\### 3️⃣ Run Frontend (Streamlit)



```bash

python -m streamlit run app/streamlit\_app.py

```



\---



\## 🔄 System Flow



```text

Jobs → Processing → Structured Data

Candidate → Parsing → Features

→ Matching Engine → Score + Explanation

→ Recommendation Engine → Top Jobs

→ UI Display

```



\---



\## 💡 Key Strengths



✔ End-to-end system (data → model → API → UI)

✔ Explainable AI (transparent scoring)

✔ Real-world job data integration

✔ Personalized recommendations

✔ Modular \& scalable architecture



\---



\## 📈 Future Improvements



\* NLP-based skill extraction (transformers)

\* Embedding-based semantic matching

\* Real-time job ingestion

\* Improved UI (job cards, filtering, sorting)

\* Profile strength scoring

\* Deployment (Render / Streamlit Cloud)



\---



\## 💡 Key Insight



Most system complexity lies in:



```text

Data processing, normalization, and structuring — not the model itself

```



\---



\## 👨‍💻 Author



\*\*Ahmad Issa\*\*

Machine Learning Engineer | Data Science \& AI Systems

\---



