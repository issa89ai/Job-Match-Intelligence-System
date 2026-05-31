"""
Matching Engine Test Script
============================
Run:  python test_matching.py

Edit the JOB and CANDIDATE dicts below to see how scores change.
Try swapping skills in/out, changing seniority, years, education, etc.
"""

from src.ingestion.jsearch import JSearchClient
from src.candidate.parser import parse_candidate_profile
from src.candidate.feature_builder import build_candidate_features
from src.matching.ranking import rank_candidate_for_job

# ─────────────────────────────────────────────────────────────
# 1.  JOB DESCRIPTION  — paste any real job post here
# ─────────────────────────────────────────────────────────────
JOB_DESCRIPTION = """
We are hiring a Senior Data Scientist to join our AI team.

Requirements:
- 5+ years of experience in data science or machine learning
- Proficiency in Python and SQL
- Hands-on experience with TensorFlow or PyTorch
- Experience with scikit-learn, pandas, numpy
- Knowledge of AWS or Azure cloud platforms
- Familiarity with Docker and Kubernetes
- Experience with data visualization tools such as Tableau or Power BI
- Strong knowledge of statistics and machine learning algorithms
- Familiarity with Git and agile workflows

Nice to have:
- Experience with Spark or distributed computing
- Knowledge of MLflow or Kubeflow
- Background in NLP or computer vision

Education: Bachelor's degree in Computer Science, Statistics, or related field.
"""

# ─────────────────────────────────────────────────────────────
# 2.  CANDIDATE PROFILE  — change these to test different scenarios
# ─────────────────────────────────────────────────────────────
CANDIDATE = {
    "candidate_id": "test_001",
    "full_name": "Ahmad Test",
    "current_title": "Senior Data Scientist",   # try: "Junior Data Scientist", "Teacher", "Sales Manager"
    "location": "New York, US",
    "education": "master",                       # options: high_school, associate, bachelor, master, phd
    "years_experience": 6,                       # try: 0, 2, 5, 10
    "seniority": "senior",                       # options: intern, entry, mid, senior, manager
    "skills": [
        # ── Remove or add skills to see score change ──
        "python",
        "sql",
        "machine learning",
        "tensorflow",
        "scikit-learn",
        "pandas",
        "numpy",
        "aws",
        "docker",
        "statistics",
        "git",
        "data visualization",
        # "tableau",          # uncomment to add
        # "pytorch",          # uncomment to add
        # "spark",            # uncomment to add
    ],
    "tools": ["jupyter", "vs code", "github"],
    "domains": ["data science", "machine learning", "artificial intelligence"],
    "certifications": [],
    "projects": [],
    "summary": "Experienced data scientist with ML and cloud background.",
}

# ─────────────────────────────────────────────────────────────
# 3.  SCENARIO PRESETS  — uncomment one to quickly test extremes
# ─────────────────────────────────────────────────────────────

# --- PERFECT MATCH (should score ~90-100%) ---
# CANDIDATE["skills"] = ["python","sql","tensorflow","pytorch","scikit-learn","pandas","numpy","aws","docker","kubernetes","statistics","git","tableau","power bi","spark"]
# CANDIDATE["years_experience"] = 6
# CANDIDATE["seniority"] = "senior"
# CANDIDATE["education"] = "master"

# --- ZERO MATCH — wrong profession (should score ~10-25%) ---
# CANDIDATE["current_title"] = "Primary School Teacher"
# CANDIDATE["skills"] = ["classroom management","lesson planning","child psychology"]
# CANDIDATE["domains"] = ["education"]

# --- PARTIAL MATCH — right field, missing key skills (should score ~50-70%) ---
# CANDIDATE["skills"] = ["python", "sql"]
# CANDIDATE["years_experience"] = 2
# CANDIDATE["seniority"] = "entry"
# CANDIDATE["education"] = "bachelor"


# ─────────────────────────────────────────────────────────────
# Engine — don't touch below this line
# ─────────────────────────────────────────────────────────────

def extract_job_features(description: str) -> dict:
    """Use JSearch's NLP extractor on raw text."""
    fake_job = {
        "job_id": "test_job",
        "job_title": "Senior Data Scientist",
        "job_description": description,
        "job_required_skills": [],
        "job_highlights": {},
        "job_employment_type": "FULLTIME",
        "employer_name": "Test Corp",
        "job_city": "New York",
        "job_country": "US",
        "job_is_remote": False,
        "job_apply_link": "",
        "employer_logo": "",
        "job_posted_at_datetime_utc": "",
    }
    client = JSearchClient.__new__(JSearchClient)
    jobs = client.normalize_jobs([fake_job])
    return jobs[0] if jobs else {}


def run_test():
    print("\n" + "═" * 60)
    print("  JOB MATCH SCORING TEST")
    print("═" * 60)

    # Build job features from the prose description
    job = extract_job_features(JOB_DESCRIPTION)
    print(f"\n📋  Job Title   : {job.get('title')}")
    print(f"🔑  Extracted Skills ({len(job.get('required_skills', []))}):")
    for s in sorted(job.get("required_skills", [])):
        print(f"      • {s}")

    # Build candidate features
    profile = parse_candidate_profile(CANDIDATE)
    features = build_candidate_features(profile)
    print(f"\n👤  Candidate   : {CANDIDATE['full_name']} — {CANDIDATE['current_title']}")
    print(f"🛠   Skills ({len(features['skills'])})  : {', '.join(features['skills'])}")
    print(f"📅  Experience  : {features['years_experience']} years  |  Seniority: {features['seniority']}")
    print(f"🎓  Education   : {features['education']}")

    # Run full matching pipeline
    result = rank_candidate_for_job(job, features)
    score_data = result["match_score"]
    explanation = result["explanation"]
    components = score_data["component_scores"]
    weights = score_data["weights"]

    # ── Overall result ──────────────────────────────────────
    score = score_data["score"]
    label = score_data["fit_label"]
    bar_len = int(score / 2)
    bar = "█" * bar_len + "░" * (50 - bar_len)
    color = "🟢" if score >= 85 else "🟡" if score >= 70 else "🟠" if score >= 50 else "🔴"

    print(f"\n{'─'*60}")
    print(f"  {color}  MATCH SCORE:  {score:.1f}%   ({label})")
    print(f"  [{bar}]")
    print(f"{'─'*60}")

    # ── Component breakdown ─────────────────────────────────
    print(f"\n  COMPONENT BREAKDOWN")
    print(f"  {'Component':<28} {'Score':>7}   {'Weight':>7}   {'Contribution':>12}")
    print(f"  {'─'*28}   {'─'*7}   {'─'*7}   {'─'*12}")
    total_contrib = 0
    for key, raw_score in components.items():
        w = weights.get(key, 0)
        contrib = raw_score * w * 100
        total_contrib += contrib
        label_name = key.replace("_score", "").replace("_", " ").title()
        bar_mini = "▓" * int(raw_score * 10) + "░" * (10 - int(raw_score * 10))
        print(f"  {label_name:<28}  {raw_score:>6.2f}   {w*100:>6.0f}%   {contrib:>10.1f}pt  [{bar_mini}]")
    print(f"  {'─'*28}   {'─'*7}   {'─'*7}   {'─'*12}")
    print(f"  {'TOTAL':<28}  {'':>7}   {'100%':>7}   {total_contrib:>10.1f}pt")

    # ── Skill analysis ──────────────────────────────────────
    matched = explanation.get("matched_required_skills", [])
    missing = explanation.get("missing_required_skills", [])
    print(f"\n  ✅  MATCHED SKILLS ({len(matched)}):")
    if matched:
        print("      " + ", ".join(matched))
    else:
        print("      (none)")
    print(f"\n  ❌  MISSING SKILLS ({len(missing)}):")
    if missing:
        print("      " + ", ".join(missing))
    else:
        print("      (none — full coverage!)")

    # ── Hard filters ────────────────────────────────────────
    hf = result["hard_filters"]
    hf_pass = hf.get("passed", True)
    print(f"\n  🔒  Hard Filters : {'✅ PASSED' if hf_pass else '❌ FAILED'}")
    if not hf_pass:
        for issue in hf.get("failures", []):
            print(f"      ⚠ {issue}")

    # ── Recommendations ─────────────────────────────────────
    recs = explanation.get("recommendations", [])
    if recs:
        print(f"\n  💡  RECOMMENDATIONS:")
        for r in recs[:3]:
            print(f"      → {r}")

    print(f"\n{'═'*60}\n")


if __name__ == "__main__":
    run_test()
