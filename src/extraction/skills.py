from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple


REQUIRED_HINTS = [
    "required",
    "must have",
    "must-have",
    "need to have",
    "needs to have",
    "minimum qualifications",
    "basic qualifications",
    "you have",
    "qualification",
    "qualifications",
    "requirements",
    "minimum requirements",
]

PREFERRED_HINTS = [
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "preferred qualifications",
    "desired",
    "good to have",
]

NEGATION_HINTS = [
    "not required",
    "no experience required",
    "optional",
]


def _normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _compile_skill_patterns(skill_aliases: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
    compiled = {}
    for canonical_skill, aliases in skill_aliases.items():
        patterns = []
        for alias in aliases:
            alias_escaped = re.escape(alias.lower())
            pattern = re.compile(rf"(?<!\w){alias_escaped}(?!\w)", re.IGNORECASE)
            patterns.append(pattern)
        compiled[canonical_skill] = patterns
    return compiled


def _find_context_window(text: str, start: int, end: int, window: int = 120) -> str:
    left = max(0, start - window)
    right = min(len(text), end + window)
    return text[left:right].lower()


def _classify_context(context: str) -> str:
    for hint in NEGATION_HINTS:
        if hint in context:
            return "ignore"

    for hint in REQUIRED_HINTS:
        if hint in context:
            return "required"

    for hint in PREFERRED_HINTS:
        if hint in context:
            return "preferred"

    return "unspecified"


def split_sections(text: str) -> dict:
    if not isinstance(text, str):
        return {
            "requirements": "",
            "preferred": "",
            "other": "",
        }

    text = text.lower()

    sections = {
        "requirements": "",
        "preferred": "",
        "other": text,
    }

    req_match = re.split(r"(minimum requirements|requirements|minimum qualifications|qualifications)", text, maxsplit=1)
    pref_match = re.split(r"(preferred qualifications|preferred|nice to have|nice-to-have)", text, maxsplit=1)

    if len(req_match) >= 3:
        sections["requirements"] = req_match[2]

    if len(pref_match) >= 3:
        sections["preferred"] = pref_match[2]

    return sections


def extract_skills(
    text: str,
    skill_aliases: Dict[str, List[str]],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Returns:
        required_skills, preferred_skills, found_skills_unspecified
    """
    normalized_text = _normalize_text(text)
    if not normalized_text:
        return [], [], []

    compiled_patterns = _compile_skill_patterns(skill_aliases)

    required: Set[str] = set()
    preferred: Set[str] = set()
    unspecified: Set[str] = set()

    for canonical_skill, patterns in compiled_patterns.items():
        skill_found = False
        best_label = "unspecified"

        for pattern in patterns:
            for match in pattern.finditer(normalized_text):
                skill_found = True
                context = _find_context_window(normalized_text, match.start(), match.end())
                label = _classify_context(context)

                if label == "ignore":
                    continue
                if label == "required":
                    best_label = "required"
                    break
                if label == "preferred" and best_label != "required":
                    best_label = "preferred"

            if best_label == "required":
                break

        if skill_found:
            if best_label == "required":
                required.add(canonical_skill)
            elif best_label == "preferred":
                preferred.add(canonical_skill)
            else:
                unspecified.add(canonical_skill)

    preferred -= required
    unspecified -= required
    unspecified -= preferred

    return sorted(required), sorted(preferred), sorted(unspecified)


def extract_skills_section_aware(
    text: str,
    skill_aliases: Dict[str, List[str]],
) -> Tuple[List[str], List[str], List[str]]:
    sections = split_sections(text)

    req_skills, _, _ = extract_skills(sections["requirements"], skill_aliases)
    _, pref_skills, _ = extract_skills(sections["preferred"], skill_aliases)
    _, _, other_skills = extract_skills(sections["other"], skill_aliases)

    req_set = set(req_skills)
    pref_set = set(pref_skills) - req_set
    other_set = set(other_skills) - req_set - pref_set

    return sorted(req_set), sorted(pref_set), sorted(other_set)