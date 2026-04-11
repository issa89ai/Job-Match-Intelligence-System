from __future__ import annotations

from typing import Dict, List


def evaluate_matching(predictions: List[Dict]) -> Dict:
    """
    predictions format:
    [
        {
            "predicted_label": "Good Fit",
            "true_label": "Good Fit"
        }
    ]
    """

    correct = 0

    for item in predictions:
        if item["predicted_label"] == item["true_label"]:
            correct += 1

    accuracy = correct / len(predictions)

    return {
        "accuracy": round(accuracy, 4),
        "total_samples": len(predictions),
        "correct": correct,
    }