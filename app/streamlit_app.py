from __future__ import annotations

from typing import Any, Dict, List

import requests
import streamlit as st


DEFAULT_API_URL = "http://127.0.0.1:8000/match"


st.set_page_config(
    page_title="Job Match Intelligence System",
    page_icon="🎯",
    layout="wide",
)


def load_css() -> None:
    try:
        with open("app/style.css", "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def parse_text_list(text: str) -> List[str]:
    if not text or not text.strip():
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def build_payload(
    job_uid: str,
    job_title: str,
    required_skills: str,
    preferred_skills: str,
    other_skills: str,
    years_experience_extracted: Any,
    education_extracted: str,
    seniority_inferred: str,
    candidate_id: str,
    full_name: str,
    current_title: str,
    location: str,
    education: str,
    years_experience: Any,
    skills: str,
    tools: str,
    domains: str,
    certifications: str,
    projects: str,
    seniority: str,
    summary: str,
) -> Dict[str, Any]:
    job_years = None if years_experience_extracted in ("", None) else int(years_experience_extracted)
    candidate_years = None if years_experience in ("", None) else int(years_experience)

    return {
        "job": {
            "job_uid": job_uid,
            "title_raw": job_title,
            "required_skills": parse_text_list(required_skills),
            "preferred_skills": parse_text_list(preferred_skills),
            "other_skills_found": parse_text_list(other_skills),
            "years_experience_extracted": job_years,
            "education_extracted": education_extracted or None,
            "seniority_inferred": seniority_inferred or None,
        },
        "candidate": {
            "candidate_id": candidate_id,
            "full_name": full_name,
            "current_title": current_title,
            "location": location,
            "education": education or None,
            "years_experience": candidate_years,
            "skills": parse_text_list(skills),
            "tools": parse_text_list(tools),
            "domains": parse_text_list(domains),
            "certifications": parse_text_list(certifications),
            "projects": parse_text_list(projects),
            "seniority": seniority or "",
            "summary": summary,
        },
    }


def render_tag_list(title: str, items: List[str], variant: str = "default") -> None:
    st.markdown(f"#### {title}")
    if not items:
        st.markdown('<div class="muted-text">None</div>', unsafe_allow_html=True)
        return

    html = '<div class="tag-container">'
    for item in items:
        css_class = "tag"
        if variant == "success":
            css_class = "tag tag-success"
        elif variant == "danger":
            css_class = "tag tag-danger"
        elif variant == "warning":
            css_class = "tag tag-warning"
        html += f'<span class="{css_class}">{item}</span>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def render_score_card(score: float, fit_label: str) -> None:
    if score >= 85:
        score_class = "score-strong"
    elif score >= 70:
        score_class = "score-good"
    elif score >= 50:
        score_class = "score-partial"
    else:
        score_class = "score-weak"

    st.markdown(
        f"""
        <div class="score-card">
            <div class="score-title">Overall Match Score</div>
            <div class="score-value {score_class}">{score:.1f}</div>
            <div class="score-label">{fit_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_component_scores(component_scores: Dict[str, float]) -> None:
    st.markdown("### Component Scores")
    cols = st.columns(len(component_scores))
    for col, (key, value) in zip(cols, component_scores.items()):
        label = key.replace("_", " ").replace("score", "").strip().title()
        with col:
            st.markdown(
                f"""
                <div class="mini-card">
                    <div class="mini-card-title">{label}</div>
                    <div class="mini-card-value">{round(value * 100, 1)}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def call_match_api(payload: Dict[str, Any], api_url: str) -> Dict[str, Any]:
    response = requests.post(api_url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def load_demo_data() -> None:
    st.session_state["job_uid"] = "test_job"
    st.session_state["job_title"] = "Account Executive, AI Sales"
    st.session_state["required_skills"] = "enterprise, sales"
    st.session_state["preferred_skills"] = ""
    st.session_state["other_skills"] = "ai, communication"
    st.session_state["job_years"] = 10
    st.session_state["job_education"] = ""
    st.session_state["job_seniority"] = "senior"

    st.session_state["candidate_id"] = "cand_001"
    st.session_state["full_name"] = "Ahmad"
    st.session_state["current_title"] = "Senior Data Scientist"
    st.session_state["location"] = "Ottawa"
    st.session_state["candidate_education"] = "master"
    st.session_state["candidate_years"] = 6
    st.session_state["candidate_skills"] = "python, sql, machine learning, ai"
    st.session_state["candidate_tools"] = "pandas"
    st.session_state["candidate_domains"] = "ai"
    st.session_state["candidate_certifications"] = ""
    st.session_state["candidate_projects"] = ""
    st.session_state["candidate_seniority"] = ""
    st.session_state["candidate_summary"] = "Built end-to-end machine learning and analytics projects."


def main() -> None:
    load_css()

    st.markdown(
        """
        <div class="hero">
            <div class="hero-badge">Stage 8 • Professional UI</div>
            <h1>🎯 Job Match Intelligence System</h1>
            <p>
                Compare a candidate profile against a job profile and generate an explainable
                match score, gaps, and recommendations.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.markdown("## Settings")
        api_url_input = st.text_input("API URL", value=DEFAULT_API_URL)
        st.caption("Keep your FastAPI server running before using this app.")

        st.markdown("---")
        st.markdown("## Quick Demo")
        if st.button("Load Demo Data", use_container_width=True):
            load_demo_data()

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("## Job Profile")

        job_uid = st.text_input("Job ID", key="job_uid")
        job_title = st.text_input("Job Title", key="job_title")
        required_skills = st.text_area(
            "Required Skills (comma-separated)",
            key="required_skills",
            placeholder="enterprise, sales, python",
        )
        preferred_skills = st.text_area(
            "Preferred Skills (comma-separated)",
            key="preferred_skills",
            placeholder="aws, fastapi",
        )
        other_skills = st.text_area(
            "Other Skills Found (comma-separated)",
            key="other_skills",
            placeholder="communication, strategy, ai",
        )

        c1, c2 = st.columns(2)
        with c1:
            years_experience_extracted = st.number_input(
                "Required Years of Experience",
                min_value=0,
                max_value=50,
                step=1,
                key="job_years",
                value=None,
                placeholder="e.g. 5",
            )
        with c2:
            education_extracted = st.selectbox(
                "Required Education",
                options=["", "high_school", "associate", "bachelor", "master", "phd"],
                key="job_education",
            )

        seniority_inferred = st.selectbox(
            "Job Seniority",
            options=["", "intern", "entry", "mid", "senior", "manager"],
            key="job_seniority",
        )

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("## Candidate Profile")

        candidate_id = st.text_input("Candidate ID", key="candidate_id")
        full_name = st.text_input("Full Name", key="full_name")
        current_title = st.text_input("Current Title", key="current_title")
        location = st.text_input("Location", key="location")

        c3, c4 = st.columns(2)
        with c3:
            education = st.selectbox(
                "Education",
                options=["", "high_school", "associate", "bachelor", "master", "phd"],
                key="candidate_education",
            )
        with c4:
            years_experience = st.number_input(
                "Years of Experience",
                min_value=0,
                max_value=50,
                step=1,
                key="candidate_years",
                value=None,
                placeholder="e.g. 6",
            )

        skills = st.text_area(
            "Skills (comma-separated)",
            key="candidate_skills",
            placeholder="python, sql, machine learning",
        )
        tools = st.text_area(
            "Tools (comma-separated)",
            key="candidate_tools",
            placeholder="pandas, scikit-learn, power bi",
        )
        domains = st.text_area(
            "Domains (comma-separated)",
            key="candidate_domains",
            placeholder="ai, analytics, data science",
        )
        certifications = st.text_area(
            "Certifications (comma-separated)",
            key="candidate_certifications",
            placeholder="aws cloud practitioner",
        )
        projects = st.text_area(
            "Projects (comma-separated)",
            key="candidate_projects",
            placeholder="job match intelligence system, churn prediction deployment",
        )
        seniority = st.selectbox(
            "Candidate Seniority",
            options=["", "intern", "entry", "mid", "senior", "manager"],
            key="candidate_seniority",
        )
        summary = st.text_area(
            "Summary",
            key="candidate_summary",
            placeholder="Short professional summary...",
            height=120,
        )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    cta1, cta2, _ = st.columns([1, 1, 3])
    with cta1:
        run_match = st.button("Run Match Analysis", use_container_width=True, type="primary")
    with cta2:
        show_payload = st.button("Preview JSON Payload", use_container_width=True)

    payload = build_payload(
        job_uid,
        job_title,
        required_skills,
        preferred_skills,
        other_skills,
        years_experience_extracted,
        education_extracted,
        seniority_inferred,
        candidate_id,
        full_name,
        current_title,
        location,
        education,
        years_experience,
        skills,
        tools,
        domains,
        certifications,
        projects,
        seniority,
        summary,
    )

    if show_payload:
        st.markdown("## Payload Preview")
        st.json(payload)

    if run_match:
        try:
            with st.spinner("Running intelligent match analysis..."):
                result = call_match_api(payload, api_url_input)

            st.success("Match analysis completed successfully.")

            match_score = result["match_score"]
            explanation = result["explanation"]
            hard_filters = result["hard_filters"]

            score_col, info_col = st.columns([1.2, 1.8], gap="large")

            with score_col:
                render_score_card(match_score["score"], match_score["fit_label"])

            with info_col:
                st.markdown("### Hard Filter Summary")
                hf_cols = st.columns(3)

                with hf_cols[0]:
                    status = "Passed" if hard_filters["passed"] else "Failed"
                    st.markdown(
                        f'<div class="mini-card"><div class="mini-card-title">Overall Filters</div><div class="mini-card-value">{status}</div></div>',
                        unsafe_allow_html=True,
                    )

                with hf_cols[1]:
                    missing_count = len(hard_filters["skill_check"]["required_skills_missing"])
                    st.markdown(
                        f'<div class="mini-card"><div class="mini-card-title">Missing Required Skills</div><div class="mini-card-value">{missing_count}</div></div>',
                        unsafe_allow_html=True,
                    )

                with hf_cols[2]:
                    exp_gap = hard_filters["experience_check"]["gap"]
                    st.markdown(
                        f'<div class="mini-card"><div class="mini-card-title">Experience Gap</div><div class="mini-card-value">{exp_gap}</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("---")
            render_component_scores(match_score["component_scores"])

            st.markdown("---")
            e1, e2 = st.columns(2, gap="large")

            with e1:
                render_tag_list(
                    "Matched Required Skills",
                    explanation["matched_required_skills"],
                    variant="success",
                )
                render_tag_list(
                    "Missing Required Skills",
                    explanation["missing_required_skills"],
                    variant="danger",
                )

            with e2:
                render_tag_list(
                    "Matched Preferred Skills",
                    explanation["matched_preferred_skills"],
                    variant="success",
                )
                render_tag_list(
                    "Missing Preferred Skills",
                    explanation["missing_preferred_skills"],
                    variant="warning",
                )

            st.markdown("---")
            g1, g2 = st.columns(2, gap="large")

            with g1:
                st.markdown("### Gaps")
                if explanation["gaps"]:
                    for gap in explanation["gaps"]:
                        st.markdown(f"- {gap}")
                else:
                    st.markdown('<div class="muted-text">No major gaps detected.</div>', unsafe_allow_html=True)

            with g2:
                st.markdown("### Recommendations")
                if explanation["recommendations"]:
                    for rec in explanation["recommendations"]:
                        st.markdown(f"- {rec}")
                else:
                    st.markdown('<div class="muted-text">No recommendations needed.</div>', unsafe_allow_html=True)

            with st.expander("See Full API Response"):
                st.json(result)

        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Make sure FastAPI is running.")
        except requests.exceptions.HTTPError as e:
            st.error(f"API returned an error: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()