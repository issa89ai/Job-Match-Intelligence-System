import json
from typing import Any, Dict, List

import requests
import streamlit as st

st.set_page_config(page_title="Job Match Intelligence System", layout="wide")


# -----------------------------
# Helpers
# -----------------------------
def split_csv(text: str) -> List[str]:
    if not text.strip():
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    token = st.session_state.get("token", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_post(api_url: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(
        f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}",
        json=payload,
        headers=get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def api_get(api_url: str, endpoint: str) -> Dict[str, Any]:
    response = requests.get(
        f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}",
        headers=get_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def safe_set_profile_fields(profile: Dict[str, Any]) -> None:
    st.session_state["candidate_id"] = profile.get("candidate_id", "")
    st.session_state["full_name"] = profile.get("full_name", "")
    st.session_state["current_title"] = profile.get("current_title", "")
    st.session_state["location"] = profile.get("location", "")
    st.session_state["education"] = profile.get("education", "")
    st.session_state["years_experience"] = int(profile.get("years_experience", 0) or 0)
    st.session_state["skills"] = ", ".join(profile.get("skills", []))
    st.session_state["tools"] = ", ".join(profile.get("tools", []))
    st.session_state["domains"] = ", ".join(profile.get("domains", []))
    st.session_state["certifications"] = ", ".join(profile.get("certifications", []))
    st.session_state["projects"] = ", ".join(profile.get("projects", []))
    st.session_state["candidate_seniority"] = profile.get("seniority", "")
    st.session_state["summary"] = profile.get("summary", "")


def build_candidate_payload() -> Dict[str, Any]:
    return {
        "candidate_id": st.session_state.get("candidate_id", ""),
        "full_name": st.session_state.get("full_name", ""),
        "current_title": st.session_state.get("current_title", ""),
        "location": st.session_state.get("location", ""),
        "education": st.session_state.get("education", ""),
        "years_experience": int(st.session_state.get("years_experience", 0)),
        "skills": split_csv(st.session_state.get("skills", "")),
        "tools": split_csv(st.session_state.get("tools", "")),
        "domains": split_csv(st.session_state.get("domains", "")),
        "certifications": split_csv(st.session_state.get("certifications", "")),
        "projects": split_csv(st.session_state.get("projects", "")),
        "seniority": st.session_state.get("candidate_seniority", ""),
        "summary": st.session_state.get("summary", ""),
    }


def build_job_payload() -> Dict[str, Any]:
    return {
        "job_id": st.session_state.get("job_id", ""),
        "title": st.session_state.get("job_title", ""),
        "required_skills": split_csv(st.session_state.get("required_skills", "")),
        "preferred_skills": split_csv(st.session_state.get("preferred_skills", "")),
        "other_skills": split_csv(st.session_state.get("other_skills", "")),
        "years_experience_required": int(st.session_state.get("job_years_required", 0)),
        "education_required": st.session_state.get("job_education", ""),
        "seniority": st.session_state.get("job_seniority", ""),
    }


def load_demo_data() -> None:
    st.session_state["job_id"] = "job_001"
    st.session_state["job_title"] = "Enterprise Sales Engineer"
    st.session_state["required_skills"] = "enterprise, sales, python"
    st.session_state["preferred_skills"] = "aws, fastapi"
    st.session_state["other_skills"] = "communication, strategy, ai"
    st.session_state["job_years_required"] = 10
    st.session_state["job_education"] = "Master in CS"
    st.session_state["job_seniority"] = "senior"

    st.session_state["candidate_id"] = "c1"
    st.session_state["full_name"] = "Ahmad Issa"
    st.session_state["current_title"] = "Data Scientist"
    st.session_state["location"] = "Canada"
    st.session_state["education"] = "Master in CS"
    st.session_state["years_experience"] = 6
    st.session_state["skills"] = "python, sql, machine learning"
    st.session_state["tools"] = "power bi, pandas"
    st.session_state["domains"] = "ai"
    st.session_state["certifications"] = "aws cloud practitioner"
    st.session_state["projects"] = "job match intelligence system, churn prediction deployment"
    st.session_state["candidate_seniority"] = "senior"
    st.session_state["summary"] = "Built end-to-end machine learning and analytics projects."


# -----------------------------
# Session defaults
# -----------------------------
defaults = {
    "api_url": "http://127.0.0.1:8000",
    "token": "",
    "logged_in_email": "",
    "candidate_id": "",
    "full_name": "",
    "current_title": "",
    "location": "",
    "education": "",
    "years_experience": 0,
    "skills": "",
    "tools": "",
    "domains": "",
    "certifications": "",
    "projects": "",
    "candidate_seniority": "",
    "summary": "",
    "job_id": "",
    "job_title": "",
    "required_skills": "",
    "preferred_skills": "",
    "other_skills": "",
    "job_years_required": 0,
    "job_education": "",
    "job_seniority": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.title("Settings")
    st.text_input("API URL", key="api_url")
    st.caption("Keep your FastAPI server running before using this app.")

    st.divider()
    st.subheader("Auth")

    auth_mode = st.radio("Mode", ["Login", "Register"], horizontal=True)

    if auth_mode == "Register":
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        reg_full_name = st.text_input("Full Name", key="reg_full_name")
        if st.button("Register"):
            try:
                result = api_post(
                    st.session_state["api_url"],
                    "/auth/register",
                    {
                        "email": reg_email,
                        "password": reg_password,
                        "full_name": reg_full_name,
                    },
                )
                st.session_state["token"] = result["access_token"]
                st.session_state["logged_in_email"] = result.get("user_email", reg_email)
                st.success(f"Registered and logged in as {st.session_state['logged_in_email']}")
            except Exception as e:
                st.error(f"Register failed: {e}")

    else:
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                result = api_post(
                    st.session_state["api_url"],
                    "/auth/login",
                    {
                        "email": login_email,
                        "password": login_password,
                    },
                )
                st.session_state["token"] = result["access_token"]
                st.session_state["logged_in_email"] = result.get("user_email", login_email)
                st.success(f"Logged in as {st.session_state['logged_in_email']}")
            except Exception as e:
                st.error(f"Login failed: {e}")

    if st.session_state["token"]:
        st.caption(f"Current user: {st.session_state['logged_in_email']}")
        if st.button("Check /me"):
            try:
                me = api_get(st.session_state["api_url"], "/me")
                st.success(json.dumps(me, indent=2))
            except Exception as e:
                st.error(f"/me failed: {e}")

        if st.button("Logout"):
            st.session_state["token"] = ""
            st.session_state["logged_in_email"] = ""
            st.success("Logged out.")

    st.divider()
    st.subheader("Quick Demo")
    if st.button("Load Demo Data"):
        load_demo_data()
        st.success("Demo data loaded.")


# -----------------------------
# Main UI
# -----------------------------
st.title("🎯 Job Match Intelligence System")
st.write("Compare a candidate profile against a job profile and generate an explainable match score, gaps, and recommendations.")

col1, col2 = st.columns(2)

with col1:
    st.header("Job Profile")
    st.text_input("Job ID", key="job_id")
    st.text_input("Job Title", key="job_title")
    st.text_area("Required Skills (comma-separated)", key="required_skills", height=100)
    st.text_area("Preferred Skills (comma-separated)", key="preferred_skills", height=100)
    st.text_area("Other Skills Found (comma-separated)", key="other_skills", height=100)
    st.number_input("Years Required", min_value=0, step=1, key="job_years_required")
    st.text_input("Education Required", key="job_education")
    st.selectbox("Job Seniority", ["", "junior", "mid", "senior"], key="job_seniority")

with col2:
    st.header("Candidate Profile")
    st.text_input("Candidate ID", key="candidate_id")
    st.text_input("Full Name", key="full_name")
    st.text_input("Current Title", key="current_title")
    st.text_input("Location", key="location")
    st.text_input("Education", key="education")
    st.number_input("Years of Experience", min_value=0, step=1, key="years_experience")
    st.text_area("Skills (comma-separated)", key="skills", height=100)
    st.text_area("Tools (comma-separated)", key="tools", height=100)
    st.text_area("Domains (comma-separated)", key="domains", height=100)
    st.text_area("Certifications (comma-separated)", key="certifications", height=100)
    st.text_area("Projects (comma-separated)", key="projects", height=100)
    st.selectbox("Candidate Seniority", ["", "junior", "mid", "senior"], key="candidate_seniority")
    st.text_area("Summary", key="summary", height=100)

st.divider()

action_col1, action_col2, action_col3, action_col4 = st.columns([1, 1, 1, 2])

with action_col1:
    if st.button("Save Profile", use_container_width=True):
        if not st.session_state["token"]:
            st.error("Please login first.")
        else:
            try:
                payload = build_candidate_payload()
                saved = api_post(st.session_state["api_url"], "/profile", payload)
                st.success("Profile saved successfully.")
                st.json(saved)
            except Exception as e:
                st.error(f"Save profile failed: {e}")

with action_col2:
    if st.button("Load Profile", use_container_width=True):
        if not st.session_state["token"]:
            st.error("Please login first.")
        else:
            try:
                profile = api_get(st.session_state["api_url"], "/profile")
                safe_set_profile_fields(profile)
                st.success("Profile loaded into the form.")
            except Exception as e:
                st.error(f"Load profile failed: {e}")

with action_col3:
    if st.button("Preview JSON Payload", use_container_width=True):
        st.json(
            {
                "candidate": build_candidate_payload(),
                "job": build_job_payload(),
            }
        )

with action_col4:
    run_match = st.button("Run Match Analysis", use_container_width=True)

if run_match:
    try:
        payload = {
            "candidate": build_candidate_payload(),
            "job": build_job_payload(),
        }
        result = api_post(st.session_state["api_url"], "/match", payload)
        st.success("Match analysis completed successfully.")

        match_score = result.get("match_score", {})
        hard_filters = result.get("hard_filters", {})
        explanation = result.get("explanation", {})

        score_cols = st.columns(4)
        score_cols[0].metric("Overall Match Score", match_score.get("score", 0))
        score_cols[1].metric("Fit Label", match_score.get("fit_label", "N/A"))
        score_cols[2].metric("Overall Filters", "Passed" if hard_filters.get("passed") else "Failed")
        exp_gap = hard_filters.get("experience_check", {}).get("gap", 0)
        score_cols[3].metric("Experience Gap", exp_gap)

        st.subheader("Component Scores")
        comp = match_score.get("component_scores", {})
        comp_cols = st.columns(5)
        comp_cols[0].metric("Required Skill", f"{comp.get('required_skill_score', 0) * 100:.1f}%")
        comp_cols[1].metric("Preferred Skill", f"{comp.get('preferred_skill_score', 0) * 100:.1f}%")
        comp_cols[2].metric("Experience", f"{comp.get('experience_score', 0) * 100:.1f}%")
        comp_cols[3].metric("Education", f"{comp.get('education_score', 0) * 100:.1f}%")
        comp_cols[4].metric("Seniority", f"{comp.get('seniority_score', 0) * 100:.1f}%")

        left, right = st.columns(2)
        with left:
            st.subheader("Matched Required Skills")
            matched_req = explanation.get("matched_required_skills", [])
            if matched_req:
                st.write(", ".join(matched_req))
            else:
                st.caption("None")

            st.subheader("Missing Required Skills")
            missing_req = explanation.get("missing_required_skills", [])
            if missing_req:
                st.write(", ".join(missing_req))
            else:
                st.caption("None")

        with right:
            st.subheader("Matched Preferred Skills")
            matched_pref = explanation.get("matched_preferred_skills", [])
            if matched_pref:
                st.write(", ".join(matched_pref))
            else:
                st.caption("None")

            st.subheader("Missing Preferred Skills")
            missing_pref = explanation.get("missing_preferred_skills", [])
            if missing_pref:
                st.write(", ".join(missing_pref))
            else:
                st.caption("None")

        st.subheader("Gaps")
        gaps = explanation.get("gaps", [])
        if gaps:
            for gap in gaps:
                st.write(f"- {gap}")
        else:
            st.caption("None")

        st.subheader("Recommendations")
        recs = explanation.get("recommendations", [])
        if recs:
            for rec in recs:
                st.write(f"- {rec}")
        else:
            st.caption("None")

        with st.expander("See Full API Response"):
            st.json(result)

    except Exception as e:
        st.error(f"API returned an error: {e}")