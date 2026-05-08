from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple


# Words/phrases that suggest a skill is required.
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


# Words/phrases that suggest a skill is preferred, not mandatory.
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


# Words/phrases that indicate a skill should not be treated as required.
NEGATION_HINTS = [
    "not required",
    "no experience required",
    "optional",
]


def _normalize_text(text: str) -> str:
    """
    Normalize text before skill matching.
    """
    if not isinstance(text, str):
        return ""

    text = text.lower()

    # Collapse multiple spaces into one.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def _compile_skill_patterns(skill_aliases: Dict[str, List[str]]) -> Dict[str, List[re.Pattern]]:
    """
    Convert skill aliases into compiled regex patterns.
    """

    compiled = {}

    for canonical_skill, aliases in skill_aliases.items():
        patterns = []

        for alias in aliases:
            # Escape alias so special characters are treated literally.
            alias_escaped = re.escape(alias.lower())

            # Match alias only as a standalone term.
            # (?<!\w) means not preceded by word character.
            # (?!\w) means not followed by word character.
            pattern = re.compile(
                rf"(?<!\w){alias_escaped}(?!\w)",
                re.IGNORECASE,
            )

            patterns.append(pattern)

        compiled[canonical_skill] = patterns

    return compiled


def _find_context_window(text: str, start: int, end: int, window: int = 120) -> str:
    """
    Extract surrounding text around a matched skill.
    """

    # Start 120 characters before the match.
    left = max(0, start - window)

    # End 120 characters after the match.
    right = min(len(text), end + window)

    return text[left:right].lower()


def _classify_context(context: str) -> str:
    """
    Classify a matched skill based on surrounding context.
    """

    # If negation appears, ignore this skill.
    for hint in NEGATION_HINTS:
        if hint in context:
            return "ignore"

    # If required hint appears nearby, classify as required.
    for hint in REQUIRED_HINTS:
        if hint in context:
            return "required"

    # If preferred hint appears nearby, classify as preferred.
    for hint in PREFERRED_HINTS:
        if hint in context:
            return "preferred"

    # If no clear signal, classify as unspecified.
    return "unspecified"


def split_sections(text: str) -> dict:
    """
    Split job description into requirement, preferred, and other sections.
    """

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

    # Try to split text after requirement-related headings.
    req_match = re.split(
        r"(minimum requirements|requirements|minimum qualifications|qualifications)",
        text,
        maxsplit=1,
    )

    # Try to split text after preferred-related headings.
    pref_match = re.split(
        r"(preferred qualifications|preferred|nice to have|nice-to-have)",
        text,
        maxsplit=1,
    )

    # If a requirements section was found, keep text after that heading.
    if len(req_match) >= 3:
        sections["requirements"] = req_match[2]

    # If a preferred section was found, keep text after that heading.
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

    # Compile all aliases into regex patterns.
    compiled_patterns = _compile_skill_patterns(skill_aliases)

    required: Set[str] = set()
    preferred: Set[str] = set()
    unspecified: Set[str] = set()

    # For every canonical skill, search all aliases.
    for canonical_skill, patterns in compiled_patterns.items():
        skill_found = False
        best_label = "unspecified"

        for pattern in patterns:
            for match in pattern.finditer(normalized_text):
                skill_found = True

                # Look around the matched skill to classify it.
                context = _find_context_window(
                    normalized_text,
                    match.start(),
                    match.end(),
                )

                label = _classify_context(context)

                if label == "ignore":
                    continue

                # Required has highest priority.
                if label == "required":
                    best_label = "required"
                    break

                # Preferred is second priority.
                if label == "preferred" and best_label != "required":
                    best_label = "preferred"

            # Stop checking aliases once required is detected.
            if best_label == "required":
                break

        # Add skill to correct category.
        if skill_found:
            if best_label == "required":
                required.add(canonical_skill)

            elif best_label == "preferred":
                preferred.add(canonical_skill)

            else:
                unspecified.add(canonical_skill)

    # Remove overlaps.
    # Required wins over preferred and unspecified.
    preferred -= required
    unspecified -= required
    unspecified -= preferred

    return sorted(required), sorted(preferred), sorted(unspecified)


def extract_skills_section_aware(
    text: str,
    skill_aliases: Dict[str, List[str]],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Extract skills by looking at description sections.
    """

    # Split job description into logical sections.
    sections = split_sections(text)

    # Extract required skills from requirements section.
    req_skills, _, _ = extract_skills(
        sections["requirements"],
        skill_aliases,
    )

    # Extract preferred skills from preferred section.
    _, pref_skills, _ = extract_skills(
        sections["preferred"],
        skill_aliases,
    )

    # Extract other skills from full text.
    _, _, other_skills = extract_skills(
        sections["other"],
        skill_aliases,
    )

    req_set = set(req_skills)

    # Preferred cannot duplicate required.
    pref_set = set(pref_skills) - req_set

    # Other cannot duplicate required or preferred.
    other_set = set(other_skills) - req_set - pref_set

    return sorted(req_set), sorted(pref_set), sorted(other_set)