# 💼 Job Match Intelligence System

An end-to-end intelligent job matching platform that collects real-world job postings, matches them against candidate profiles using an explainable scoring engine, and serves everything through a live web application.

🔗 **Live App:** [job-match-intelligence-system-m7srotvkvxfkmwhm9e35kv.streamlit.app](https://job-match-intelligence-system-m7srotvkvxfkmwhm9e35kv.streamlit.app)

---

## 🚀 What It Does

- Collects live job postings via the **JSearch API** (LinkedIn, Indeed, Glassdoor, and more)
- Extracts job requirements — skills, experience, education, seniority
- Parses candidate profiles (manual input or **resume upload** — PDF/DOCX)
- Computes **explainable match scores** with component breakdowns
- Generates **personalized job recommendations** ranked by fit
- Full **authentication system** — register, login, JWT, password reset via email
- **Multi-profile support** — manage multiple candidate profiles per account
- **Google Analytics 4** tracking with UTM attribution

---

## 🏗️ Architecture

```
Raw Jobs → Staging → Curated → Extracted → Matching Engine → FastAPI → Streamlit UI
```

**Backend:** FastAPI + SQLAlchemy + SQLite — deployed on [Render](https://render.com)  
**Frontend:** Streamlit — deployed on [Streamlit Cloud](https://streamlit.io/cloud)

---

## 📁 Project Structure

```
Job-Match-Intelligence-System/
│
├── app/
│   └── streamlit_app.py        # Full Streamlit frontend
│
├── configs/
│   ├── sources.yaml            # API keys & email config
│   ├── skills.yaml             # Skill taxonomy
│   └── scoring.yaml            # Scoring weights
│
├── src/
│   ├── api/
│   │   ├── main.py             # FastAPI app + all endpoints
│   │   └── email_service.py    # SMTP password reset emails
│   ├── auth/                   # JWT authentication
│   ├── candidate/
│   │   └── resume_extractor.py # PDF/DOCX resume parser
│   ├── db/                     # SQLAlchemy models
│   ├── extraction/             # Job requirement extraction
│   ├── ingestion/
│   │   └── jsearch.py          # Live JSearch API client
│   ├── matching/
│   │   ├── scoring.py          # Weighted match scoring engine
│   │   ├── ranker.py           # Job ranking
│   │   └── job_templates.py    # 150+ job title skill map
│   └── normalization/          # Data cleaning & structuring
│
├── requirements.txt            # Frontend deps (Streamlit Cloud)
├── requirements-backend.txt    # Backend deps (Render)
├── render.yaml                 # Render deployment config
├── .python-version             # Python 3.11.9
└── DEPLOY.md                   # Full deployment guide
```

---

## ⚙️ System Components

### ✔ Phase 1–4 — Data Pipeline
- Config-driven YAML architecture
- Job ingestion from Greenhouse & Lever (~747 real postings)
- Title, location, and text normalization
- Deduplication via hashing
- Requirement extraction: skills, experience, education, seniority

### ✔ Phase 5 — Candidate Understanding
- Structured candidate profile schema
- Skill, tool, domain, education normalization
- Seniority inference & keyword aggregation
- Resume parsing from PDF and DOCX files

### ✔ Phase 6 — Matching Engine
**Hard Filters:** required skills · experience · education

**Weighted Scoring:**
| Component | Weight |
|-----------|--------|
| Required Skills | High |
| Preferred Skills | Medium |
| Experience | Medium |
| Education | Low |
| Seniority | Medium |
| Domain Alignment | Medium |

**Output per job:**
- Match score (0–100) + Fit label (Strong / Good / Partial / Weak)
- Matched skills, missing skills, component breakdown

### ✔ Phase 7 — API Layer (FastAPI)

| Category | Endpoints |
|----------|-----------|
| Auth | `POST /register` · `POST /login` · `POST /password-reset` |
| Profiles | `GET/POST /profiles` · `PUT/DELETE /profiles/{id}` |
| Matching | `POST /match` · `POST /recommendations` |
| Live Jobs | `POST /recommendations/live` (JSearch) |
| Resume | `POST /resume/parse` |

Swagger docs: `https://job-match-api-iibv.onrender.com/docs`

### ✔ Phase 8 — Frontend (Streamlit)
- Dark theme UI with colorful job cards
- Login / Register / Forgot Password / Change Password
- Candidate profile builder + resume upload
- Profile completeness progress bar
- Job Matches tab — dataset-based recommendations
- Live Jobs tab — real-time JSearch results with match scoring
- Score rings, skill chips (matched/missing), apply buttons

### ✔ Phase 9 — Evaluation
| Metric | Score |
|--------|-------|
| Extraction Precision | 0.75 |
| Extraction Recall | 0.625 |
| Extraction F1 | 0.679 |
| Matching Accuracy | 66.7% |

---

## 🖥️ Local Development

```bash
# Terminal 1 — Backend
uvicorn src.api.main:app --reload

# Terminal 2 — Frontend
streamlit run app/streamlit_app.py
```

Open `http://localhost:8501` in your browser.

See [DEPLOY.md](DEPLOY.md) for full deployment instructions.

---

## 💡 Key Strengths

- ✔ End-to-end system — data pipeline → matching engine → API → live web app
- ✔ Explainable AI — transparent, component-level scoring
- ✔ Real-world job data — live JSearch integration (LinkedIn, Indeed, Glassdoor)
- ✔ Resume parsing — upload PDF or DOCX to auto-fill profile
- ✔ Production deployed — Render (backend) + Streamlit Cloud (frontend)
- ✔ Analytics — GA4 + UTM tracking for visitor attribution

---

## 👨‍💻 Author

**Ahmad Issa**  
Machine Learning Engineer | Data Science & AI Systems  
[GitHub](https://github.com/issa89ai) · [LinkedIn](https://linkedin.com/in/ahmadissa)
