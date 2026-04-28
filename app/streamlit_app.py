from __future__ import annotations

from typing import Any, Dict, List, Optional

import requests
import streamlit as st


# ============================================================
# Page setup
# ============================================================
st.set_page_config(
    page_title="Job Match Intelligence System",
    page_icon="💼",
    layout="wide",
)


# ============================================================
# Helpers
# ============================================================
def split_csv(text: str) -> List[str]:
    if not text or not text.strip():
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def join_list(values: Optional[List[str]]) -> str:
    if not values:
        return ""
    return ", ".join(values)


def init_state() -> None:
    defaults = {
        "api_url": "http://127.0.0.1:8000",
        "token": "",
        "user_email": "",
        "full_name": "",
        "is_logged_in": False,
        "profile_loaded": False,
        "preferences_loaded": False,
        "saved_profile": {},
        "saved_preferences": {},
        "jobs": [],
        "jobs_dataset_path": "",
        "last_match_result": None,
        "last_recommendations": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}

    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"

    return headers


def api_get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = f"{st.session_state.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.get(url, headers=get_headers(), params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def api_post(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{st.session_state.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.post(url, headers=get_headers(), json=payload, timeout=90)
    response.raise_for_status()
    return response.json()


def show_api_error(error: Exception) -> None:
    if isinstance(error, requests.exceptions.HTTPError):
        try:
            detail = error.response.json().get("detail", str(error))
            st.error(detail)
        except Exception:
            st.error(str(error))
    else:
        st.error(str(error))


def logout() -> None:
    st.session_state.token = ""
    st.session_state.user_email = ""
    st.session_state.full_name = ""
    st.session_state.is_logged_in = False
    st.session_state.profile_loaded = False
    st.session_state.preferences_loaded = False
    st.session_state.saved_profile = {}
    st.session_state.saved_preferences = {}
    st.session_state.last_match_result = None
    st.session_state.last_recommendations = None
    st.rerun()


def load_profile_silently() -> None:
    if not st.session_state.is_logged_in or st.session_state.profile_loaded:
        return

    try:
        profile = api_get("/profile")
        st.session_state.saved_profile = profile
    except Exception:
        st.session_state.saved_profile = {}

    st.session_state.profile_loaded = True


def load_preferences_silently() -> None:
    if not st.session_state.is_logged_in or st.session_state.preferences_loaded:
        return

    try:
        preferences = api_get("/preferences")
        st.session_state.saved_preferences = preferences
    except Exception:
        st.session_state.saved_preferences = {}

    st.session_state.preferences_loaded = True


def profile_value(key: str, default: Any = "") -> Any:
    return st.session_state.saved_profile.get(key, default)


def preference_value(key: str, default: Any = "") -> Any:
    return st.session_state.saved_preferences.get(key, default)


def build_candidate_payload() -> Dict[str, Any]:
    return {
        "candidate_id": st.session_state.get("candidate_id", "candidate_001"),
        "full_name": st.session_state.get("candidate_full_name", ""),
        "current_title": st.session_state.get("candidate_current_title", ""),
        "location": st.session_state.get("candidate_location", ""),
        "education": st.session_state.get("candidate_education") or None,
        "years_experience": int(st.session_state.get("candidate_years_experience", 0)),
        "skills": split_csv(st.session_state.get("candidate_skills", "")),
        "tools": split_csv(st.session_state.get("candidate_tools", "")),
        "domains": split_csv(st.session_state.get("candidate_domains", "")),
        "certifications": split_csv(st.session_state.get("candidate_certifications", "")),
        "projects": split_csv(st.session_state.get("candidate_projects", "")),
        "seniority": st.session_state.get("candidate_seniority") or None,
        "summary": st.session_state.get("candidate_summary") or None,
    }


def build_job_payload() -> Dict[str, Any]:
    years_required = st.session_state.get("job_years_required")

    return {
        "job_id": st.session_state.get("job_id", "job_001"),
        "title": st.session_state.get("job_title", ""),
        "company": st.session_state.get("job_company", ""),
        "location": st.session_state.get("job_location", ""),
        "workplace_type": st.session_state.get("job_workplace_type", ""),
        "domains": split_csv(st.session_state.get("job_domains", "")),
        "required_skills": split_csv(st.session_state.get("job_required_skills", "")),
        "preferred_skills": split_csv(st.session_state.get("job_preferred_skills", "")),
        "other_skills": split_csv(st.session_state.get("job_other_skills", "")),
        "years_experience_required": int(years_required) if years_required is not None else None,
        "education_required": st.session_state.get("job_education_required") or None,
        "seniority": st.session_state.get("job_seniority") or None,
    }


def build_preferences_payload() -> Dict[str, Any]:
    return {
        "preferred_titles": split_csv(st.session_state.get("preferred_titles", "")),
        "preferred_locations": split_csv(st.session_state.get("preferred_locations", "")),
        "preferred_workplace_types": split_csv(st.session_state.get("preferred_workplace_types", "")),
        "preferred_domains": split_csv(st.session_state.get("preferred_domains", "")),
        "preferred_seniority": st.session_state.get("preferred_seniority") or None,
        "min_score": int(st.session_state.get("min_score", 50)),
    }


def display_match_result(result: Dict[str, Any]) -> None:
    match_score = result.get("match_score", {})
    hard_filters = result.get("hard_filters", {})
    explanation = result.get("explanation", {})

    score = match_score.get("score", 0)
    fit_label = match_score.get("fit_label", "Unknown")

    col1, col2, col3 = st.columns(3)
    col1.metric("Match Score", f"{score}%")
    col2.metric("Fit Label", fit_label)
    col3.metric("Hard Filters", "Passed" if hard_filters.get("passed") else "Not Passed")

    st.subheader("Skill Match")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("**Matched Required Skills**")
        matched = explanation.get("matched_required_skills", [])
        if matched:
            st.success(", ".join(matched))
        else:
            st.info("No matched required skills found.")

    with c2:
        st.markdown("**Missing Required Skills**")
        missing = explanation.get("missing_required_skills", [])
        if missing:
            st.warning(", ".join(missing))
        else:
            st.success("No missing required skills.")

    st.subheader("Recommendations")
    recommendations = explanation.get("recommendations", [])
    if recommendations:
        for item in recommendations:
            st.write(f"- {item}")
    else:
        st.info("No recommendations returned by the backend.")

    st.subheader("Component Scores")
    st.json(match_score.get("component_scores", {}))

    with st.expander("Full API Response"):
        st.json(result)


def display_recommendations(result: Dict[str, Any]) -> None:
    recommendations = result.get("recommendations", [])

    if not recommendations:
        st.warning("No recommendations found.")
        return

    st.success(f"Found {len(recommendations)} recommended jobs.")

    for index, item in enumerate(recommendations, start=1):
        with st.container(border=True):
            st.markdown(f"### {index}. {item.get('title', 'Untitled Job')}")
            st.write(f"**Company:** {item.get('company', '')}")
            st.write(f"**Location:** {item.get('location', '')}")
            st.write(f"**Workplace Type:** {item.get('workplace_type', '')}")

            c1, c2, c3 = st.columns(3)
            c1.metric("Score", f"{item.get('score', 0)}%")
            c2.metric("Fit", item.get("fit_label", "Unknown"))
            c3.metric(
                "Hard Filters",
                "Passed" if item.get("hard_filters_passed") else "Not Passed",
            )

            matched = item.get("matched_required_skills", [])
            missing = item.get("missing_required_skills", [])

            st.write("**Matched Required Skills:**", ", ".join(matched) if matched else "None")
            st.write("**Missing Required Skills:**", ", ".join(missing) if missing else "None")

            recs = item.get("recommendations", [])
            if recs:
                st.write("**Improvement Suggestions:**")
                for rec in recs:
                    st.write(f"- {rec}")

            with st.expander("Full Result"):
                st.json(item.get("full_result", item))


# ============================================================
# App start
# ============================================================
init_state()

st.title("💼 Job Match Intelligence System")
st.caption("Candidate profile, job matching, and dataset-based recommendations.")


# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.header("Settings")

    st.session_state.api_url = st.text_input(
        "FastAPI URL",
        value=st.session_state.api_url,
    )

    st.divider()

    if not st.session_state.is_logged_in:
        auth_tab = st.radio("Account", ["Login", "Register"])

        if auth_tab == "Login":
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")

            if st.button("Login", use_container_width=True):
                try:
                    result = api_post(
                        "/auth/login",
                        {"email": email, "password": password},
                    )
                    st.session_state.token = result["access_token"]
                    st.session_state.user_email = result["user_email"]
                    st.session_state.full_name = result.get("full_name", "")
                    st.session_state.is_logged_in = True
                    st.session_state.profile_loaded = False
                    st.session_state.preferences_loaded = False
                    st.success("Logged in successfully.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

        else:
            full_name = st.text_input("Full Name", key="register_full_name")
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")

            if st.button("Register", use_container_width=True):
                try:
                    result = api_post(
                        "/auth/register",
                        {
                            "full_name": full_name,
                            "email": email,
                            "password": password,
                        },
                    )
                    st.session_state.token = result["access_token"]
                    st.session_state.user_email = result["user_email"]
                    st.session_state.full_name = result.get("full_name", "")
                    st.session_state.is_logged_in = True
                    st.session_state.profile_loaded = False
                    st.session_state.preferences_loaded = False
                    st.success("Account created successfully.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

    else:
        st.success("Logged in")
        st.write(st.session_state.full_name)
        st.caption(st.session_state.user_email)

        if st.button("Logout", use_container_width=True):
            logout()


if st.session_state.is_logged_in:
    load_profile_silently()
    load_preferences_silently()


# ============================================================
# Main app
# ============================================================
if not st.session_state.is_logged_in:
    st.info("Please login or register from the sidebar to use the app.")
    st.stop()


page = st.tabs(
    [
        "Candidate Profile",
        "Single Match",
        "Job Explorer",
        "Recommendations",
        "Preferences",
    ]
)


# ============================================================
# Candidate Profile
# ============================================================
with page[0]:
    st.header("Candidate Profile")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Candidate ID",
            value=profile_value("candidate_id", "candidate_001"),
            key="candidate_id",
        )
        st.text_input(
            "Full Name",
            value=profile_value("full_name", st.session_state.full_name),
            key="candidate_full_name",
        )
        st.text_input(
            "Current Title",
            value=profile_value("current_title", ""),
            key="candidate_current_title",
        )
        st.text_input(
            "Location",
            value=profile_value("location", ""),
            key="candidate_location",
        )
        st.selectbox(
            "Education",
            ["", "high_school", "associate", "bachelor", "master", "phd"],
            index=["", "high_school", "associate", "bachelor", "master", "phd"].index(
                profile_value("education", "") or ""
            )
            if (profile_value("education", "") or "") in ["", "high_school", "associate", "bachelor", "master", "phd"]
            else 0,
            key="candidate_education",
        )
        st.number_input(
            "Years of Experience",
            min_value=0,
            max_value=60,
            value=int(profile_value("years_experience", 0) or 0),
            key="candidate_years_experience",
        )

    with col2:
        st.selectbox(
            "Seniority",
            ["", "intern", "entry", "junior", "mid", "senior", "manager"],
            index=["", "intern", "entry", "junior", "mid", "senior", "manager"].index(
                profile_value("seniority", "") or ""
            )
            if (profile_value("seniority", "") or "") in ["", "intern", "entry", "junior", "mid", "senior", "manager"]
            else 0,
            key="candidate_seniority",
        )
        st.text_area(
            "Skills",
            value=join_list(profile_value("skills", [])),
            key="candidate_skills",
            help="Comma-separated values",
        )
        st.text_area(
            "Tools",
            value=join_list(profile_value("tools", [])),
            key="candidate_tools",
            help="Comma-separated values",
        )
        st.text_area(
            "Domains",
            value=join_list(profile_value("domains", [])),
            key="candidate_domains",
            help="Comma-separated values",
        )

    st.text_area(
        "Certifications",
        value=join_list(profile_value("certifications", [])),
        key="candidate_certifications",
        help="Comma-separated values",
    )
    st.text_area(
        "Projects",
        value=join_list(profile_value("projects", [])),
        key="candidate_projects",
        help="Comma-separated values",
    )
    st.text_area(
        "Summary",
        value=profile_value("summary", "") or "",
        key="candidate_summary",
    )

    if st.button("Save Candidate Profile", type="primary"):
        try:
            payload = build_candidate_payload()
            result = api_post("/profile", payload)
            st.session_state.saved_profile = result
            st.success("Profile saved successfully.")
        except Exception as e:
            show_api_error(e)

    with st.expander("Candidate JSON Preview"):
        st.json(build_candidate_payload())


# ============================================================
# Single Match
# ============================================================
with page[1]:
    st.header("Single Job Match")

    col1, col2 = st.columns(2)

    with col1:
        st.text_input("Job ID", value="job_001", key="job_id")
        st.text_input("Job Title", key="job_title")
        st.text_input("Company", key="job_company")
        st.text_input("Job Location", key="job_location")
        st.selectbox(
            "Workplace Type",
            ["", "remote", "hybrid", "onsite"],
            key="job_workplace_type",
        )
        st.number_input(
            "Years Experience Required",
            min_value=0,
            max_value=60,
            value=0,
            key="job_years_required",
        )

    with col2:
        st.selectbox(
            "Education Required",
            ["", "high_school", "associate", "bachelor", "master", "phd"],
            key="job_education_required",
        )
        st.selectbox(
            "Job Seniority",
            ["", "intern", "entry", "junior", "mid", "senior", "manager"],
            key="job_seniority",
        )
        st.text_area("Required Skills", key="job_required_skills")
        st.text_area("Preferred Skills", key="job_preferred_skills")
        st.text_area("Other Skills", key="job_other_skills")
        st.text_area("Job Domains", key="job_domains")

    if st.button("Run Match Analysis", type="primary"):
        try:
            payload = {
                "candidate": build_candidate_payload(),
                "job": build_job_payload(),
            }
            result = api_post("/match", payload)
            st.session_state.last_match_result = result
            st.success("Match completed.")
        except Exception as e:
            show_api_error(e)

    if st.session_state.last_match_result:
        display_match_result(st.session_state.last_match_result)

    with st.expander("Match Request JSON Preview"):
        st.json(
            {
                "candidate": build_candidate_payload(),
                "job": build_job_payload(),
            }
        )


# ============================================================
# Job Explorer
# ============================================================
with page[2]:
    st.header("Job Explorer")

    col1, col2 = st.columns([1, 2])

    with col1:
        limit = st.number_input(
            "Number of jobs to load",
            min_value=1,
            max_value=500,
            value=20,
        )

        if st.button("Load Jobs from Dataset", type="primary"):
            try:
                result = api_get("/jobs", params={"limit": limit})
                st.session_state.jobs = result.get("jobs", [])
                st.session_state.jobs_dataset_path = result.get("dataset_path", "")
                st.success(f"Loaded {len(st.session_state.jobs)} jobs.")
            except Exception as e:
                show_api_error(e)

    with col2:
        if st.session_state.jobs_dataset_path:
            st.info(f"Dataset: {st.session_state.jobs_dataset_path}")

    if st.session_state.jobs:
        st.subheader("Loaded Jobs")

        for job in st.session_state.jobs:
            with st.container(border=True):
                st.markdown(f"### {job.get('title', '')}")
                st.write(f"**Company:** {job.get('company', '')}")
                st.write(f"**Location:** {job.get('location', '')}")
                st.write(f"**Workplace Type:** {job.get('workplace_type', '')}")
                st.write(f"**Required Skills:** {', '.join(job.get('required_skills', []))}")
                st.write(f"**Preferred Skills:** {', '.join(job.get('preferred_skills', []))}")

                with st.expander("Full Job JSON"):
                    st.json(job)


# ============================================================
# Recommendations
# ============================================================
with page[3]:
    st.header("Dataset-Based Job Recommendations")

    st.write(
        "This uses your saved or current candidate profile and ranks jobs from the backend dataset."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        top_k = st.number_input("Top K", min_value=1, max_value=100, value=10)

    with col2:
        limit_jobs = st.number_input(
            "Limit jobs scanned",
            min_value=1,
            max_value=5000,
            value=200,
        )

    with col3:
        use_preferences = st.checkbox("Use saved/current preferences", value=True)

    if st.button("Get Recommendations", type="primary"):
        try:
            payload = {
                "candidate": build_candidate_payload(),
                "preferences": build_preferences_payload() if use_preferences else None,
                "top_k": int(top_k),
                "limit_jobs": int(limit_jobs),
                "dataset_path": None,
            }

            result = api_post("/recommendations/from_dataset", payload)
            st.session_state.last_recommendations = result
            st.success("Recommendations generated.")
        except Exception as e:
            show_api_error(e)

    if st.session_state.last_recommendations:
        display_recommendations(st.session_state.last_recommendations)

    with st.expander("Recommendation Request JSON Preview"):
        st.json(
            {
                "candidate": build_candidate_payload(),
                "preferences": build_preferences_payload() if use_preferences else None,
                "top_k": int(top_k),
                "limit_jobs": int(limit_jobs),
                "dataset_path": None,
            }
        )


# ============================================================
# Preferences
# ============================================================
with page[4]:
    st.header("Job Preferences")

    st.text_area(
        "Preferred Titles",
        value=join_list(preference_value("preferred_titles", [])),
        key="preferred_titles",
        help="Example: data scientist, machine learning engineer",
    )

    st.text_area(
        "Preferred Locations",
        value=join_list(preference_value("preferred_locations", [])),
        key="preferred_locations",
        help="Example: ottawa, toronto, remote",
    )

    st.text_area(
        "Preferred Workplace Types",
        value=join_list(preference_value("preferred_workplace_types", [])),
        key="preferred_workplace_types",
        help="Example: remote, hybrid, onsite",
    )

    st.text_area(
        "Preferred Domains",
        value=join_list(preference_value("preferred_domains", [])),
        key="preferred_domains",
        help="Example: machine learning, data science, analytics",
    )

    st.selectbox(
        "Preferred Seniority",
        ["", "intern", "entry", "junior", "mid", "senior", "manager"],
        index=["", "intern", "entry", "junior", "mid", "senior", "manager"].index(
            preference_value("preferred_seniority", "") or ""
        )
        if (preference_value("preferred_seniority", "") or "") in ["", "intern", "entry", "junior", "mid", "senior", "manager"]
        else 0,
        key="preferred_seniority",
    )

    st.slider(
        "Minimum Match Score",
        min_value=0,
        max_value=100,
        value=int(preference_value("min_score", 50) or 50),
        key="min_score",
    )

    if st.button("Save Preferences", type="primary"):
        try:
            payload = build_preferences_payload()
            result = api_post("/preferences", payload)
            st.session_state.saved_preferences = result
            st.success("Preferences saved successfully.")
        except Exception as e:
            show_api_error(e)

    with st.expander("Preferences JSON Preview"):
        st.json(build_preferences_payload())