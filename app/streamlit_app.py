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
        "profiles_loaded": False,
        "preferences_loaded": False,
        "all_profiles": [],          # list of ProfileListItem dicts
        "active_profile_id": None,   # candidate_id of selected profile
        "saved_profile": {},         # full profile data for active profile
        "saved_preferences": {},
        "jobs": [],
        "jobs_dataset_path": "",
        "last_match_result": None,
        "last_recommendations": None,
        "last_live_recommendations": None,
        "resume_extracted": None,
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


def api_post(endpoint: str, payload: Dict[str, Any], method: str = "POST") -> Dict[str, Any]:
    url = f"{st.session_state.api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    fn = requests.put if method == "PUT" else requests.post
    response = fn(url, headers=get_headers(), json=payload, timeout=90)
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
    st.session_state.profiles_loaded = False
    st.session_state.preferences_loaded = False
    st.session_state.all_profiles = []
    st.session_state.active_profile_id = None
    st.session_state.saved_profile = {}
    st.session_state.saved_preferences = {}
    st.session_state.last_match_result = None
    st.session_state.last_recommendations = None
    st.session_state.last_live_recommendations = None
    st.rerun()


def load_profiles_silently() -> None:
    """Load all profiles for the current user on first login."""
    if not st.session_state.is_logged_in or st.session_state.profiles_loaded:
        return

    try:
        result = api_get("/profiles")
        st.session_state.all_profiles = result.get("profiles", [])
        # Auto-select first profile if available
        if st.session_state.all_profiles and not st.session_state.active_profile_id:
            first_id = st.session_state.all_profiles[0]["candidate_id"]
            st.session_state.active_profile_id = first_id
            try:
                profile = api_get(f"/profiles/{first_id}")
                st.session_state.saved_profile = profile
            except Exception:
                st.session_state.saved_profile = {}
    except Exception:
        st.session_state.all_profiles = []

    st.session_state.profiles_loaded = True


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
        "candidate_id": st.session_state.get("active_profile_id") or "candidate_001",
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
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
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
            with st.form("register_form"):
                full_name = st.text_input("Full Name", key="register_full_name")
                email = st.text_input("Email", key="register_email")
                password = st.text_input("Password", type="password", key="register_password")
                submitted = st.form_submit_button("Register", use_container_width=True)

            if submitted:
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
    load_profiles_silently()
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
        "Live Jobs",
        "Preferences",
    ]
)


# ============================================================
# Candidate Profile
# ============================================================
with page[0]:
    st.header("Candidate Profile")

    # ── Profile selector bar ──────────────────────────────
    profiles = st.session_state.all_profiles
    active_id = st.session_state.active_profile_id

    sel_col, new_col, del_col = st.columns([4, 1, 1])

    with sel_col:
        if profiles:
            profile_labels = [
                f"{p['profile_name']}  ({p['current_title'] or 'No title'})"
                for p in profiles
            ]
            current_index = next(
                (i for i, p in enumerate(profiles) if p["candidate_id"] == active_id),
                0,
            )
            selected_index = st.selectbox(
                "Active Profile",
                range(len(profile_labels)),
                format_func=lambda i: profile_labels[i],
                index=current_index,
                key="profile_selector",
            )
            selected_id = profiles[selected_index]["candidate_id"]

            # Switch profile if user picks a different one
            if selected_id != active_id:
                try:
                    profile = api_get(f"/profiles/{selected_id}")
                    st.session_state.saved_profile = profile
                    st.session_state.active_profile_id = selected_id
                    st.rerun()
                except Exception as e:
                    show_api_error(e)
        else:
            st.info("No profiles yet. Click **New Profile** to create one.")

    with new_col:
        st.write("")  # vertical alignment
        st.write("")
        if st.button("＋ New", use_container_width=True):
            try:
                new_profile = api_post("/profiles", {
                    "profile_name": f"Profile {len(profiles) + 1}",
                    "full_name": st.session_state.full_name,
                    "current_title": "",
                    "location": "",
                    "years_experience": 0,
                    "skills": [], "tools": [], "domains": [],
                    "certifications": [], "projects": [],
                })
                st.session_state.active_profile_id = new_profile["candidate_id"]
                st.session_state.saved_profile = new_profile
                st.session_state.profiles_loaded = False   # force refresh
                st.success("New profile created.")
                st.rerun()
            except Exception as e:
                show_api_error(e)

    with del_col:
        st.write("")
        st.write("")
        if active_id and len(profiles) > 0:
            if st.button("🗑 Delete", use_container_width=True):
                try:
                    api_get(f"/profiles/{active_id}")  # confirm exists
                    requests.delete(
                        f"{st.session_state.api_url}/profiles/{active_id}",
                        headers=get_headers(),
                        timeout=30,
                    )
                    st.session_state.active_profile_id = None
                    st.session_state.saved_profile = {}
                    st.session_state.profiles_loaded = False
                    st.success("Profile deleted.")
                    st.rerun()
                except Exception as e:
                    show_api_error(e)

    # ── Show system-assigned Candidate ID (read-only) ─────
    if active_id:
        st.caption(f"🔑 Candidate ID (system-assigned): `{active_id}`")

    st.divider()

    # ── Profile Completeness Bar ──────────────────────────
    def compute_completeness_local(profile: dict) -> dict:
        """Compute completeness locally without an API call."""
        weights = {
            "skills": 25, "years_experience": 15, "current_title": 15,
            "education": 10, "seniority": 10, "domains": 10,
            "summary": 10, "location": 5,
        }
        labels = {
            "skills": "Skills (at least 3)",
            "years_experience": "Years of experience",
            "current_title": "Current job title",
            "education": "Education level",
            "seniority": "Seniority level",
            "domains": "Domain / industry",
            "summary": "Professional summary",
            "location": "Location",
        }
        score = 0
        missing = []
        for field, weight in weights.items():
            val = profile.get(field)
            ok = False
            if isinstance(val, list):
                ok = len(val) >= (3 if field == "skills" else 1)
            elif isinstance(val, int):
                ok = val > 0
            elif val:
                ok = True
            if ok:
                score += weight
            else:
                missing.append({"label": labels[field], "weight": weight})
        missing.sort(key=lambda x: x["weight"], reverse=True)
        return {"score": score, "missing": missing}

    current_profile_for_score = {
        "skills":           split_csv(st.session_state.get("candidate_skills", "")) or profile_value("skills", []),
        "years_experience": st.session_state.get("candidate_years_experience") or profile_value("years_experience", 0),
        "current_title":    st.session_state.get("candidate_current_title") or profile_value("current_title", ""),
        "education":        st.session_state.get("candidate_education") or profile_value("education", ""),
        "seniority":        st.session_state.get("candidate_seniority") or profile_value("seniority", ""),
        "domains":          split_csv(st.session_state.get("candidate_domains", "")) or profile_value("domains", []),
        "summary":          st.session_state.get("candidate_summary") or profile_value("summary", ""),
        "location":         st.session_state.get("candidate_location") or profile_value("location", ""),
    }
    completeness = compute_completeness_local(current_profile_for_score)
    score = completeness["score"]
    missing_fields = completeness["missing"]

    # Color the bar based on score
    if score >= 80:
        bar_color = "green"
        score_label = "Great"
    elif score >= 50:
        bar_color = "orange"
        score_label = "Good — a few things missing"
    else:
        bar_color = "red"
        score_label = "Incomplete — please fill in more details"

    st.markdown(f"**Profile Completeness: {score}% — {score_label}**")
    st.progress(score / 100)

    if missing_fields:
        with st.expander(f"📋 {len(missing_fields)} field(s) missing — click to see what to add"):
            for item in missing_fields:
                st.write(f"• **{item['label']}** — adds {item['weight']}%")

    st.divider()

    # ── Resume Upload Section ─────────────────────────────
    st.subheader("📄 Upload Resume to Auto-fill")
    st.write("Upload your resume and we'll extract your information automatically.")

    upload_col, info_col = st.columns([2, 3])
    with upload_col:
        uploaded_file = st.file_uploader(
            "Choose your resume",
            type=["pdf", "docx", "txt"],
            key="resume_upload",
            label_visibility="collapsed",
        )

    with info_col:
        st.caption("Supported formats: PDF, DOCX, TXT · Max size: 10 MB")
        st.caption("Your file is only used to fill the form below — it is not stored.")

    if uploaded_file is not None:
        if st.button("Extract & Auto-fill Profile", type="primary", key="extract_resume_btn"):
            with st.spinner("Reading your resume..."):
                try:
                    response = requests.post(
                        f"{st.session_state.api_url}/resume/parse",
                        headers={"Authorization": f"Bearer {st.session_state.token}"},
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                        timeout=60,
                    )
                    response.raise_for_status()
                    parsed = response.json()

                    extracted = parsed.get("extracted_profile", {})
                    comp = parsed.get("completeness", {})

                    # Store extracted data to pre-fill the form
                    st.session_state["resume_extracted"] = extracted

                    score_after = comp.get("score", 0)
                    missing_after = comp.get("missing", [])

                    st.success(f"Resume parsed! Profile completeness from your resume: **{score_after}%**")

                    if missing_after:
                        st.warning(
                            "We couldn't detect the following — please fill them in manually: "
                            + ", ".join(f['label'] for f in missing_after)
                        )
                    else:
                        st.success("All profile fields were detected!")

                except requests.exceptions.HTTPError as e:
                    try:
                        detail = e.response.json().get("detail", str(e))
                    except Exception:
                        detail = str(e)
                    st.error(f"Could not parse resume: {detail}")
                except Exception as e:
                    st.error(f"Error: {e}")

    # If resume was just extracted, pre-fill session state values
    if st.session_state.get("resume_extracted"):
        ex = st.session_state["resume_extracted"]
        if ex.get("full_name"):
            st.session_state["candidate_full_name"] = ex["full_name"]
        if ex.get("current_title"):
            st.session_state["candidate_current_title"] = ex["current_title"]
        if ex.get("location"):
            st.session_state["candidate_location"] = ex["location"]
        if ex.get("years_experience"):
            st.session_state["candidate_years_experience"] = ex["years_experience"]
        if ex.get("education"):
            st.session_state["candidate_education"] = ex["education"]
        if ex.get("seniority"):
            st.session_state["candidate_seniority"] = ex["seniority"]
        if ex.get("skills"):
            st.session_state["candidate_skills"] = ", ".join(ex["skills"])
        if ex.get("tools"):
            st.session_state["candidate_tools"] = ", ".join(ex["tools"])
        if ex.get("domains"):
            st.session_state["candidate_domains"] = ", ".join(ex["domains"])
        if ex.get("summary"):
            st.session_state["candidate_summary"] = ex["summary"]
        if ex.get("certifications"):
            st.session_state["candidate_certifications"] = ", ".join(ex["certifications"])
        if ex.get("projects"):
            st.session_state["candidate_projects"] = ", ".join(ex["projects"])
        # Clear so it doesn't re-apply on every rerun
        st.session_state["resume_extracted"] = None

    st.divider()

    # ── Profile form ──────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.text_input(
            "Profile Name",
            value=profile_value("profile_name", "My Profile"),
            key="candidate_profile_name",
            help="A label for this profile, e.g. 'Data Scientist Profile'",
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

    if st.button("Save Profile", type="primary"):
        if not active_id:
            st.warning("Please create a profile first using the '＋ New' button.")
        else:
            try:
                payload = {
                    "profile_name": st.session_state.get("candidate_profile_name", "My Profile"),
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
                result = api_post(f"/profiles/{active_id}", payload, method="PUT")
                st.session_state.saved_profile = result
                st.session_state.profiles_loaded = False  # refresh selector
                st.success("Profile saved successfully.")
                st.rerun()
            except Exception as e:
                show_api_error(e)


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
# Live Jobs
# ============================================================
with page[4]:
    st.header("🌐 Live Job Search")
    st.write(
        "Search real-time job postings from LinkedIn, Indeed, Glassdoor, and more — "
        "then instantly score them against your candidate profile."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        live_search_query = st.text_input(
            "Job Title / Keywords",
            placeholder="e.g. data scientist, machine learning engineer",
            key="live_search_query",
        )
        live_location = st.text_input(
            "Location (optional)",
            placeholder="e.g. New York, Toronto, remote",
            key="live_location",
        )

    with col2:
        live_top_k = st.number_input(
            "Top K results",
            min_value=1,
            max_value=10,
            value=5,
            key="live_top_k",
        )
        live_date_posted = st.selectbox(
            "Date Posted",
            options=["all", "today", "3days", "week", "month"],
            index=0,
            key="live_date_posted",
        )

    live_use_preferences = st.checkbox(
        "Apply my saved preferences (location, seniority, min score...)",
        value=False,
        key="live_use_preferences",
    )

    st.info(
        "Your **Candidate Profile** tab values are used for matching — "
        "make sure your skills and experience are filled in before searching."
    )

    if st.button("Search Live Jobs", type="primary", key="live_search_btn"):
        if not live_search_query.strip():
            st.warning("Please enter a job title or keywords to search.")
        else:
            try:
                with st.spinner(f"Searching live jobs for '{live_search_query}'..."):
                    live_payload = {
                        "candidate": build_candidate_payload(),
                        "search_query": live_search_query.strip(),
                        "location": live_location.strip(),
                        "top_k": int(live_top_k),
                        "date_posted": live_date_posted,
                        "preferences": build_preferences_payload() if live_use_preferences else None,
                    }
                    live_result = api_post("/recommendations/live", live_payload)
                    st.session_state["last_live_recommendations"] = live_result

                st.success(
                    f"Found and scored {live_result.get('count', 0)} live jobs."
                )

            except Exception as e:
                show_api_error(e)

    # Display live results
    if st.session_state.get("last_live_recommendations"):
        result = st.session_state["last_live_recommendations"]
        recommendations = result.get("recommendations", [])

        if not recommendations:
            st.warning("No matching live jobs found. Try a different search query or location.")
        else:
            st.divider()
            st.subheader(f"Top {len(recommendations)} Live Job Matches")

            for index, item in enumerate(recommendations, start=1):
                full = item.get("full_result", {})
                job_data = full.get("explanation", {})

                with st.container(border=True):
                    # Header row: rank + title
                    title_col, score_col = st.columns([3, 1])
                    with title_col:
                        st.markdown(f"### {index}. {item.get('title', 'Untitled')}")
                        company = item.get("company", "")
                        location = item.get("location", "")
                        wtype = item.get("workplace_type", "")
                        meta_parts = [p for p in [company, location, wtype] if p]
                        st.caption(" · ".join(meta_parts))

                    with score_col:
                        score = item.get("score", 0)
                        fit = item.get("fit_label", "Unknown")
                        st.metric("Match Score", f"{score}%")
                        st.caption(fit)

                    # Hard filter status
                    passed = item.get("hard_filters_passed", False)
                    if passed:
                        st.success("✅ Hard filters passed")
                    else:
                        st.warning("⚠️ Hard filters not fully passed")

                    # Skills
                    skill_c1, skill_c2 = st.columns(2)
                    with skill_c1:
                        matched = item.get("matched_required_skills", [])
                        st.markdown("**Matched Skills**")
                        st.write(", ".join(matched) if matched else "None detected")

                    with skill_c2:
                        missing = item.get("missing_required_skills", [])
                        st.markdown("**Missing Skills**")
                        if missing:
                            st.warning(", ".join(missing))
                        else:
                            st.success("None missing")

                    # Improvement suggestions
                    recs = item.get("recommendations", [])
                    if recs:
                        with st.expander("Improvement Suggestions"):
                            for rec in recs:
                                st.write(f"- {rec}")

                    # Apply link — passed through directly from JSearch
                    apply_link = item.get("source_url", "")
                    if apply_link:
                        st.link_button("Apply on Original Website", apply_link)



# ============================================================
# Preferences
# ============================================================
with page[5]:
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