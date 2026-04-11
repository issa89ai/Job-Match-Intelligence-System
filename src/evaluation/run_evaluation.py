from __future__ import annotations

import json

from src.evaluation.extraction_eval import evaluate_extraction
from src.evaluation.ranking_eval import evaluate_matching


def main():
    print("===== Stage 9: Evaluation =====")

    # -----------------------------
    # Extraction Evaluation (example)
    # -----------------------------
    extraction_predictions = [
        {"required_skills": ["python", "sql", "machine learning"]},
        {"required_skills": ["sales", "communication"]},
    ]

    extraction_ground_truth = [
        {"required_skills": ["python", "sql", "machine learning", "statistics"]},
        {"required_skills": ["sales", "negotiation"]},
    ]

    extraction_results = evaluate_extraction(
        extraction_predictions,
        extraction_ground_truth,
    )

    print("\n--- Extraction Evaluation ---")
    print(json.dumps(extraction_results, indent=2))

    # -----------------------------
    # Matching Evaluation (example)
    # -----------------------------
    matching_predictions = [
        {"predicted_label": "Good Fit", "true_label": "Good Fit"},
        {"predicted_label": "Partial Fit", "true_label": "Weak Fit"},
        {"predicted_label": "Strong Fit", "true_label": "Strong Fit"},
    ]

    matching_results = evaluate_matching(matching_predictions)

    print("\n--- Matching Evaluation ---")
    print(json.dumps(matching_results, indent=2))


if __name__ == "__main__":
    main()