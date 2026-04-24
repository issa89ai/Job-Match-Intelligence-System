from __future__ import annotations

from typing import Any, Dict


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _to_set(values) -> set:
    if not values:
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _safe_float(value: Any):
    try:
        return float(value)
    except Exception:
        return None


def build_match_explanation(job_features: Dict, candidate_features: Dict) -> Dict:
    required = _to_set(job_features.get("required_skills", []))
    preferred = _to_set(job_features.get("preferred_skills", []))
    job_domains = _to_set(job_features.get("domains", []))

    candidate_skills = _to_set(candidate_features.get("skills", []))
    candidate_domains = _to_set(candidate_features.get("domains", []))

    matched_required = sorted(required & candidate_skills)
    missing_required = sorted(required - candidate_skills)

    matched_preferred = sorted(preferred & candidate_skills)
    missing_preferred = sorted(preferred - candidate_skills)

    matched_domains = sorted(job_domains & candidate_domains)
    missing_domains = sorted(job_domains - candidate_domains)

    strengths = []
    gaps = []
    recommendations = []
    summary_points = []

    # -----------------------------
    # Required skills explanation
    # -----------------------------
    if required:
        required_match_ratio = len(matched_required) / len(required)

        if required_match_ratio == 1:
            strengths.append("Candidate matches all required skills.")
            summary_points.append("Strong required-skill alignment.")
        elif required_match_ratio >= 0.5:
            strengths.append(
                f"Candidate matches {len(matched_required)} out of {len(required)} required skills."
            )
            gaps.append(f"Missing required skills: {', '.join(missing_required)}")
            recommendations.append(
                f"Highlight or develop missing required skills: {', '.join(missing_required)}."
            )
            summary_points.append("Partial required-skill alignment.")
        else:
            gaps.append(f"Missing required skills: {', '.join(missing_required)}")
            recommendations.append(
                f"Prioritize these required skills before applying: {', '.join(missing_required)}."
            )
            summary_points.append("Weak required-skill alignment.")
    else:
        strengths.append("No explicit required skills were listed for this job.")
        summary_points.append("No required-skill blocker detected.")

    # -----------------------------
    # Preferred skills explanation
    # -----------------------------
    if preferred:
        preferred_match_ratio = len(matched_preferred) / len(preferred)

        if preferred_match_ratio == 1:
            strengths.append("Candidate matches all preferred skills.")
            summary_points.append("Strong preferred-skill alignment.")
        elif matched_preferred:
            strengths.append(
                f"Candidate matches preferred skills: {', '.join(matched_preferred)}."
            )
            recommendations.append(
                f"Strengthen preferred skills: {', '.join(missing_preferred)}."
            )
        else:
            recommendations.append(
                f"Consider building preferred skills: {', '.join(missing_preferred)}."
            )
    else:
        strengths.append("No preferred skills were listed for this job.")

    # -----------------------------
    # Domain explanation
    # -----------------------------
    if job_domains:
        if matched_domains:
            strengths.append(
                f"Candidate domain background matches job domain(s): {', '.join(matched_domains)}."
            )
            summary_points.append("Relevant domain alignment.")
        else:
            gaps.append(
                f"Candidate does not show direct domain alignment with: {', '.join(missing_domains)}."
            )
            recommendations.append(
                f"Add projects or experience related to: {', '.join(missing_domains)}."
            )
    else:
        strengths.append("No specific job domain was listed.")

    # -----------------------------
    # Experience explanation
    # -----------------------------
    job_years = _first_present(
        job_features.get("years_experience_required"),
        job_features.get("years_experience_extracted"),
    )
    candidate_years = candidate_features.get("years_experience")

    job_years_num = _safe_float(job_years)
    candidate_years_num = _safe_float(candidate_years)

    if job_years_num is not None:
        if candidate_years_num is None:
            gaps.append("Candidate experience is not specified.")
            recommendations.append("Add clear years of experience to the candidate profile.")
        elif candidate_years_num >= job_years_num:
            strengths.append(
                f"Candidate meets the experience requirement ({candidate_years_num:g} years vs required {job_years_num:g})."
            )
            summary_points.append("Experience requirement met.")
        else:
            gap = job_years_num - candidate_years_num
            gaps.append(
                f"Experience gap: candidate has {candidate_years_num:g} years vs required {job_years_num:g}."
            )

            if gap <= 1:
                recommendations.append(
                    "Experience gap is small; strengthen the application with strong project evidence."
                )
            elif gap <= 3:
                recommendations.append(
                    "Target similar roles with slightly lower experience requirements or emphasize advanced project work."
                )
            else:
                recommendations.append(
                    "Consider roles with lower experience requirements before applying to this role."
                )
    else:
        strengths.append("No explicit experience requirement was found.")

    # -----------------------------
    # Education explanation
    # -----------------------------
    job_education = _first_present(
        job_features.get("education_required"),
        job_features.get("education_extracted"),
    )
    candidate_education = candidate_features.get("education")

    if job_education:
        if candidate_education:
            strengths.append(
                f"Candidate education is provided ({candidate_education})."
            )
        else:
            gaps.append("Education requirement exists but candidate education is missing.")
            recommendations.append("Add education details to the candidate profile.")
    else:
        strengths.append("No explicit education requirement was found.")

    # -----------------------------
    # Seniority explanation
    # -----------------------------
    job_seniority = _first_present(
        job_features.get("seniority"),
        job_features.get("seniority_inferred"),
    )
    candidate_seniority = candidate_features.get("seniority")

    if job_seniority:
        if _normalize_text(job_seniority) == _normalize_text(candidate_seniority):
            strengths.append(f"Candidate seniority aligns with the role ({job_seniority}).")
            summary_points.append("Seniority alignment.")
        elif candidate_seniority:
            recommendations.append(
                f"Review seniority fit: job expects {job_seniority}, candidate profile shows {candidate_seniority}."
            )
        else:
            recommendations.append("Add candidate seniority level for better matching.")
    else:
        strengths.append("No explicit seniority requirement was found.")

    # -----------------------------
    # Final summary
    # -----------------------------
    if not gaps:
        recommendation_summary = "Candidate is a strong match for the main job requirements."
    elif missing_required:
        recommendation_summary = "Candidate has important required-skill gaps for this role."
    else:
        recommendation_summary = "Candidate is a partial match with some improvement areas."

    if not recommendations:
        recommendations.append(
            "Candidate profile aligns well with the main job requirements."
        )

    return {
        "recommendation_summary": recommendation_summary,
        "summary_points": summary_points,
        "strengths": strengths,
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "matched_domains": matched_domains,
        "missing_domains": missing_domains,
        "gaps": gaps,
        "recommendations": recommendations,
    }