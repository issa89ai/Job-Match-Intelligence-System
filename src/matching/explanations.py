from __future__ import annotations

from typing import Dict, List


def _to_set(values) -> set:
    if not values:
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def build_match_explanation(job_features: Dict, candidate_features: Dict) -> Dict:
    required = _to_set(job_features.get("required_skills", []))
    preferred = _to_set(job_features.get("preferred_skills", []))
    candidate_skills = _to_set(candidate_features.get("skills", []))

    matched_required = sorted(required & candidate_skills)
    missing_required = sorted(required - candidate_skills)
    matched_preferred = sorted(preferred & candidate_skills)
    missing_preferred = sorted(preferred - candidate_skills)

    gaps = []
    recommendations = []

    job_years = job_features.get("years_experience_extracted")
    candidate_years = candidate_features.get("years_experience")

    if missing_required:
        gaps.append(f"Missing required skills: {', '.join(missing_required)}")
        recommendations.append(f"Develop or highlight these required skills: {', '.join(missing_required)}")

    if missing_preferred:
        recommendations.append(f"Strengthen preferred skills: {', '.join(missing_preferred)}")

    if job_years is not None and candidate_years is not None and candidate_years < job_years:
        gaps.append(f"Experience gap: candidate has {candidate_years} years vs required {job_years}")
        recommendations.append("Target roles with slightly lower experience requirements or strengthen project evidence.")

    if job_years is not None and candidate_years is None:
        gaps.append("Candidate experience is not specified.")
        recommendations.append("Add clear years of experience to the candidate profile.")

    job_education = job_features.get("education_extracted")
    candidate_education = candidate_features.get("education")
    if job_education and not candidate_education:
        gaps.append("Education requirement exists but candidate education is missing.")
        recommendations.append("Add education details to candidate profile.")

    return {
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "gaps": gaps,
        "recommendations": recommendations,
    }