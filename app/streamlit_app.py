import json
from typing import Any, Dict, List, Optional

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
        timeout=60,
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


def api_get_with_params(api_url: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    response = requests.get(
        f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}",
        headers=get_headers(),
        params=params or {},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def build_candidate_payload() -> Dict[str, Any]:
    return {
        "candidate_id": st.session_state.get("candidate_id", "").strip(),
        "full_name": st.session_state.get("full_name", "").strip(),
        "current_title": st.session_state.get("current_title", "").strip(),
        "location": st.session_state.get("location", "").strip(),
        "education": st.session_state.get("education", "").strip(),
        "years_experience": int(st.session_state.get("years_experience", 0)),
        "skills": split_csv(st.session_state.get("skills", "")),
        "tools": split_csv(st.session_state.get("tools", "")),
        "domains": split_csv(st.session_state.get("domains", "")),
        "certifications": split_csv(st.session_state.get("certifications", "")),
        "projects": split_csv(st.session_state.get("projects", "")),
        "seniority": st.session_state.get("candidate_seniority", "").strip(),
        "summary": st.session_state.get("summary", "").strip(),
    }


def build_job_payload() -> Dict[str, Any]:
    return {
        "job_id": st.session_state.get("job_id", "").strip(),
        "title": st.session_state.get("job_title", "").strip(),
        "company": st.session_state.get("job_company", "").strip(),
        "location": st.session_state.get("job_location", "").strip(),
        "workplace_type": st.session_state.get("job_workplace_type", "").strip(),
        "domains": split_csv(st.session_state.get("job_domains", "")),
        "required_skills": split_csv(st.session_state.get("required_skills", "")),
        "preferred_skills": split_csv(st.session_state.get("preferred_skills", "")),
        "other_skills": split_csv(st.session_state.get("other_skills", "")),
        "years_experience_required": int(st.session_state.get("job_years_required", 0)),
        "education_required": st.session_state.get("job_education", "").strip(),
        "seniority": st.session_state.get("job_seniority", "").strip(),
    }


def build_preferences_payload() -> Dict[str, Any]:
    return {
        "preferred_titles": split_csv(st.session_state.get("pref_titles", "")),
        "preferred_locations": split_csv(st.session_state.get("pref_locations", "")),
        "preferred_workplace_types": split_csv(st.session_state.get("pref_workplace", "")),
        "preferred_domains": split_csv(st.session_state.get("pref_domains", "")),
        "preferred_seniority": st.session_state.get("pref_seniority", "").strip() or None,
        "min_score": int(st.session_state.get("pref_score", 50)),
    }


def candidate_payload_is_ready(candidate_payload: Dict[str, Any]) -> bool:
    required_fields = ["candidate_id", "full_name", "current_title", "location"]
    return all(str(candidate_payload.get(field, "")).strip() for field in required_fields)


def apply_loaded_profile_if_any() -> None:
    profile = st.session_state.pop("_loaded_profile", None)
    if profile:
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


def apply_loaded_preferences_if_any() -> None:
    preferences = st.session_state.pop("_loaded_preferences", None)
    if preferences:
        st.session_state["pref_titles"] = ", ".join(preferences.get("preferred_titles", []))
        st.session_state["pref_locations"] = ", ".join(preferences.get("preferred_locations", []))
        st.session_state["pref_workplace"] = ", ".join(
            preferences.get("preferred_workplace_types", [])
        )
        st.session_state["pref_domains"] = ", ".join(preferences.get("preferred_domains", []))
        st.session_state["pref_seniority"] = preferences.get("preferred_seniority", "") or ""
        st.session_state["pref_score"] = int(preferences.get("min_score", 50) or 50)


def load_demo_data() -> None:
    st.session_state["job_id"] = "job_001"
    st.session_state["job_title"] = "Enterprise Sales Engineer"
    st.session_state["job_company"] = "Demo Company"
    st.session_state["job_location"] = "Ottawa"
    st.session_state["job_workplace_type"] = "hybrid"
    st.session_state["job_domains"] = "sales"
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

    st.session_state["pref_titles"] = "Data Scientist, ML Engineer"
    st.session_state["pref_locations"] = "Canada, Ottawa"
    st.session_state["pref_workplace"] = "remote, hybrid"
    st.session_state["pref_domains"] = "AI, Analytics"
    st.session_state["pref_seniority"] = "senior"
    st.session_state["pref_score"] = 60

    demo_jobs = [
        {
            "job_id": "job_001",
            "title": "Data Scientist",
            "company": "Company A",
            "location": "Canada",
            "workplace_type": "remote",
            "domains": ["ai"],
            "required_skills": ["python", "sql"],
            "preferred_skills": ["machine learning", "power bi"],
            "other_skills": [],
            "years_experience_required": 5,
            "education_required": "Master in CS",
            "seniority": "senior",
        },
        {
            "job_id": "job_002",
            "title": "Enterprise Sales Engineer",
            "company": "Company B",
            "location": "Ottawa",
            "workplace_type": "hybrid",
            "domains": ["sales"],
            "required_skills": ["enterprise", "sales", "python"],
            "preferred_skills": ["aws"],
            "other_skills": [],
            "years_experience_required": 10,
            "education_required": "Master in CS",
            "seniority": "senior",
        },
        {
            "job_id": "job_003",
            "title": "ML Engineer",
            "company": "Company C",
            "location": "Canada",
            "workplace_type": "remote",
            "domains": ["ai"],
            "required_skills": ["python", "machine learning"],
            "preferred_skills": ["sql"],
            "other_skills": [],
            "years_experience_required": 4,
            "education_required": "Master in CS",
            "seniority": "senior",
        },
    ]
    st.session_state["jobs_json"] = json.dumps(demo_jobs, indent=2)


def parse_jobs_json(text: str) -> List[Dict[str, Any]]:
    if not text.strip():
        return []
    try:
        parsed = json.loads(text)
    except Exception as e:
        raise ValueError(f"Invalid JSON format: {e}") from e

    if not isinstance(parsed, list):
        raise ValueError("Jobs JSON must be a list of job objects.")

    for i, job in enumerate(parsed):
        if not isinstance(job, dict):
            raise ValueError(f"Job at index {i} is not a valid object.")

    return parsed


def render_recommendations(result: Dict[str, Any]) -> None:
    count = result.get("count", 0)
    st.success(f"Found {count} recommendation(s).")

    recommendations = result.get("recommendations", [])

    if not recommendations:
        st.warning("No jobs matched the current candidate and preferences.")
        return

    for idx, item in enumerate(recommendations, start=1):
        with st.container():
            st.subheader(f"{idx}. {item.get('title', 'Unknown Title')}")

            info_cols = st.columns(5)
            info_cols[0].metric("Score", item.get("score", 0))
            info_cols[1].metric("Fit", item.get("fit_label", "Unknown"))
            info_cols[2].metric("Company", item.get("company", ""))
            info_cols[3].metric("Location", item.get("location", ""))
            info_cols[4].metric("Workplace", item.get("workplace_type", ""))

            matched = item.get("matched_required_skills", [])
            missing = item.get("missing_required_skills", [])
            recs = item.get("recommendations", [])

            left, right = st.columns(2)

            with left:
                st.markdown("**🟢 Matched Required Skills**")
                if matched:
                    st.success(", ".join(matched))
                else:
                    st.caption("None")

                st.markdown("**🔴 Missing Required Skills**")
                if missing:
                    st.error(", ".join(missing))
                else:
                    st.caption("None")

            with right:
                st.markdown("**💡 Recommendations**")
                if recs:
                    for rec in recs:
                        st.info(rec)
                else:
                    st.caption("None")

            with st.expander("🔍 Full Match Details"):
                st.json(item.get("full_result", {}))

            st.divider()

    with st.expander("📦 Full Recommendations API Response"):
        st.json(result)


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
    "job_company": "",
    "job_location": "",
    "job_workplace_type": "",
    "job_domains": "",
    "required_skills": "",
    "preferred_skills": "",
    "other_skills": "",
    "job_years_required": 0,
    "job_education": "",
    "job_seniority": "",
    "pref_titles": "",
    "pref_locations": "",
    "pref_workplace": "",
    "pref_domains": "",
    "pref_seniority": "",
    "pref_score": 50,
    "jobs_json": "[]",
    "recommendation_mode": "Manual JSON",
    "dataset_limit_jobs": 200,
    "dataset_preview_limit": 20,
    "dataset_path_override": "",
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

apply_loaded_profile_if_any()
apply_loaded_preferences_if_any()


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
                        "email": reg_email.strip(),
                        "password": reg_password,
                        "full_name": reg_full_name.strip(),
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
                        "email": login_email.strip(),
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
                st.success("Authenticated successfully")
                st.json(me)
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
st.write(
    "Register or login, save your profile and preferences, run single-job matching, "
    "or get top job recommendations from many jobs."
)

tab1, tab2 = st.tabs(["Single Match", "Recommendations"])

# -----------------------------
# TAB 1 - SINGLE MATCH
# -----------------------------
with tab1:
    col1, col2 = st.columns(2)

    with col1:
        st.header("Job Profile")
        st.text_input("Job ID", key="job_id")
        st.text_input("Job Title", key="job_title")
        st.text_input("Company", key="job_company")
        st.text_input("Location", key="job_location")
        st.selectbox("Workplace Type", ["", "remote", "hybrid", "onsite"], key="job_workplace_type")
        st.text_input("Domains (comma-separated)", key="job_domains")
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
    st.header("User Preferences")

    pref_col1, pref_col2 = st.columns(2)

    with pref_col1:
        st.text_input("Preferred Titles (comma-separated)", key="pref_titles")
        st.text_input("Preferred Locations (comma-separated)", key="pref_locations")
        st.text_input("Preferred Workplace Types (remote, hybrid, onsite)", key="pref_workplace")

    with pref_col2:
        st.text_input("Preferred Domains (comma-separated)", key="pref_domains")
        st.selectbox("Preferred Seniority", ["", "junior", "mid", "senior"], key="pref_seniority")
        st.slider("Minimum Match Score", 0, 100, key="pref_score")

    st.divider()

    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns([1, 1, 1, 2])

    with row1_col1:
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

    with row1_col2:
        if st.button("Load Profile", use_container_width=True):
            if not st.session_state["token"]:
                st.error("Please login first.")
            else:
                try:
                    profile = api_get(st.session_state["api_url"], "/profile")
                    st.session_state["_loaded_profile"] = profile
                    st.rerun()
                except Exception as e:
                    st.error(f"Load profile failed: {e}")

    with row1_col3:
        if st.button("Preview JSON Payload", use_container_width=True):
            st.json(
                {
                    "candidate": build_candidate_payload(),
                    "job": build_job_payload(),
                }
            )

    with row1_col4:
        run_match = st.button("Run Match Analysis", use_container_width=True)

    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        if st.button("Save Preferences", use_container_width=True):
            if not st.session_state["token"]:
                st.error("Please login first.")
            else:
                try:
                    payload = build_preferences_payload()
                    saved = api_post(st.session_state["api_url"], "/preferences", payload)
                    st.success("Preferences saved successfully.")
                    st.json(saved)
                except Exception as e:
                    st.error(f"Save preferences failed: {e}")

    with row2_col2:
        if st.button("Load Preferences", use_container_width=True):
            if not st.session_state["token"]:
                st.error("Please login first.")
            else:
                try:
                    preferences = api_get(st.session_state["api_url"], "/preferences")
                    st.session_state["_loaded_preferences"] = preferences
                    st.rerun()
                except Exception as e:
                    st.error(f"Load preferences failed: {e}")

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


# -----------------------------
# TAB 2 - RECOMMENDATIONS
# -----------------------------
with tab2:
    st.header("🚀 Top Job Recommendations")

    st.write(
        "Choose recommendation mode. You can either paste job JSON manually "
        "or use the latest processed dataset from the backend."
    )

    recommendation_mode = st.radio(
        "Recommendation Source",
        ["Manual JSON", "Latest Dataset"],
        key="recommendation_mode",
        horizontal=True,
    )

    top_k = st.number_input(
        "Top K Results",
        min_value=1,
        max_value=100,
        value=10,
        step=1,
        key="recommendation_top_k",
    )

    candidate_payload = build_candidate_payload()

    if recommendation_mode == "Manual JSON":
        st.text_area(
            "Jobs JSON (list of job objects)",
            key="jobs_json",
            height=350,
        )

        if st.button("Get Recommendations", use_container_width=True, key="get_manual_recommendations"):
            try:
                try:
                    jobs = parse_jobs_json(st.session_state.get("jobs_json", "[]"))
                except Exception as parse_err:
                    st.error(f"Invalid Jobs JSON: {parse_err}")
                    st.stop()

                if not jobs:
                    st.warning("Please provide at least one job.")
                    st.stop()

                if not candidate_payload_is_ready(candidate_payload):
                    st.warning(
                        "Please fill at least Candidate ID, Full Name, Current Title, and Location "
                        "before running recommendations."
                    )
                    st.stop()

                payload = {
                    "candidate": candidate_payload,
                    "jobs": jobs,
                    "preferences": build_preferences_payload(),
                    "top_k": int(top_k),
                }

                result = api_post(
                    st.session_state["api_url"],
                    "/recommendations",
                    payload,
                )
                render_recommendations(result)

            except Exception as e:
                st.error(f"Recommendations failed: {e}")

    else:
        dataset_col1, dataset_col2 = st.columns(2)

        with dataset_col1:
            st.number_input(
                "Limit Jobs Loaded From Dataset",
                min_value=1,
                max_value=5000,
                step=1,
                key="dataset_limit_jobs",
            )

        with dataset_col2:
            st.number_input(
                "Preview Limit",
                min_value=1,
                max_value=200,
                step=1,
                key="dataset_preview_limit",
            )

        st.text_input(
            "Optional Dataset Path Override",
            key="dataset_path_override",
            help="Leave blank to use the latest dataset automatically.",
        )

        preview_col1, preview_col2 = st.columns([1, 2])

        with preview_col1:
            if st.button("Preview Dataset Jobs", use_container_width=True, key="preview_dataset_jobs"):
                try:
                    params: Dict[str, Any] = {
                        "limit": int(st.session_state.get("dataset_preview_limit", 20)),
                    }
                    dataset_override = st.session_state.get("dataset_path_override", "").strip()
                    if dataset_override:
                        params["dataset_path"] = dataset_override

                    jobs_preview = api_get_with_params(
                        st.session_state["api_url"],
                        "/jobs",
                        params=params,
                    )

                    st.success(
                        f"Loaded {jobs_preview.get('count', 0)} job(s) from dataset preview."
                    )
                    st.caption(f"Dataset path: {jobs_preview.get('dataset_path', 'N/A')}")

                    with st.expander("See Previewed Jobs"):
                        st.json(jobs_preview)

                except Exception as e:
                    st.error(f"Dataset preview failed: {e}")

        with preview_col2:
            st.info(
                "Dataset mode uses the backend endpoint `/recommendations/from_dataset`. "
                "You do not need to paste jobs JSON in this mode."
            )

        if st.button("Get Dataset Recommendations", use_container_width=True, key="get_dataset_recommendations"):
            try:
                if not candidate_payload_is_ready(candidate_payload):
                    st.warning(
                        "Please fill at least Candidate ID, Full Name, Current Title, and Location "
                        "before running recommendations."
                    )
                    st.stop()

                payload: Dict[str, Any] = {
                    "candidate": candidate_payload,
                    "preferences": build_preferences_payload(),
                    "top_k": int(top_k),
                    "limit_jobs": int(st.session_state.get("dataset_limit_jobs", 200)),
                }

                dataset_override = st.session_state.get("dataset_path_override", "").strip()
                if dataset_override:
                    payload["dataset_path"] = dataset_override

                result = api_post(
                    st.session_state["api_url"],
                    "/recommendations/from_dataset",
                    payload,
                )
                render_recommendations(result)

            except Exception as e:
                st.error(f"Dataset recommendations failed: {e}")