from src.matching.recommendation import recommend_jobs_for_candidate


def main():
    candidate = {
        "candidate_id": "c1",
        "full_name": "Ahmad Issa",
        "current_title": "Data Scientist",
        "location": "Canada",
        "education": "Master in CS",
        "years_experience": 6,
        "skills": ["python", "sql", "machine learning"],
        "tools": ["power bi", "pandas"],
        "domains": ["ai"],
        "certifications": ["aws cloud practitioner"],
        "projects": ["job match intelligence system"],
        "seniority": "senior",
        "summary": "Built end-to-end machine learning and analytics projects.",
    }

    preferences = {
        "preferred_locations": ["canada"],
        "preferred_workplace_types": ["remote"],
        "preferred_domains": ["ai"],
        "preferred_seniority": "senior",
        "min_score": 60,
    }

    jobs = [
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

    recommendations = recommend_jobs_for_candidate(
        candidate_payload=candidate,
        jobs_payload=jobs,
        preferences_payload=preferences,
        top_k=5,
    )

    print("\nTop recommendations:\n")
    for idx, item in enumerate(recommendations, start=1):
        print(
            f"{idx}. {item['title']} | {item['company']} | "
            f"score={item['score']} | fit={item['fit_label']}"
        )


if __name__ == "__main__":
    main()