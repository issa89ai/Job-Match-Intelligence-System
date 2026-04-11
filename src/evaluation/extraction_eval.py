from __future__ import annotations

from typing import Dict, List, Tuple


def _to_set(values: List[str]) -> set:
    if not values:
        return set()
    return {str(v).strip().lower() for v in values if str(v).strip()}


def compute_precision_recall_f1(predicted: List[str], ground_truth: List[str]) -> Dict:
    pred = _to_set(predicted)
    truth = _to_set(ground_truth)

    if not pred and not truth:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    if not pred:
        return {"precision": 0.0, "recall": 0.0, "f1": 0.0}

    tp = len(pred & truth)

    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(truth) if truth else 0.0

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def evaluate_extraction(predictions: List[Dict], ground_truths: List[Dict]) -> Dict:
    results = []

    for pred, truth in zip(predictions, ground_truths):
        skill_metrics = compute_precision_recall_f1(
            pred.get("required_skills", []),
            truth.get("required_skills", []),
        )

        results.append(skill_metrics)

    avg_precision = sum(r["precision"] for r in results) / len(results)
    avg_recall = sum(r["recall"] for r in results) / len(results)
    avg_f1 = sum(r["f1"] for r in results) / len(results)

    return {
        "avg_precision": round(avg_precision, 4),
        "avg_recall": round(avg_recall, 4),
        "avg_f1": round(avg_f1, 4),
        "details": results,
    }