from __future__ import annotations

from typing import Any

from src.utils.io import read_yaml
from src.utils.text import normalize_text_basic, unique_preserve_order


def load_skill_taxonomy(config_path: str = "configs/skills.yaml") -> dict[str, Any]:
    """
    Load the canonical skill taxonomy from YAML.
    """

    # Reads configs/skills.yaml and returns it as a Python dictionary.
    return read_yaml(config_path)


def build_alias_to_skill_map(skills_config: dict[str, Any]) -> dict[str, str]:
    """
    Build a reverse map from alias -> canonical skill key.
    """

    # This dictionary maps each alias to the canonical skill.
    # Example:
    # "ml" -> "machine_learning"
    # "postgresql" -> "sql"
    alias_to_skill: dict[str, str] = {}

    # Get the skills section from the YAML config.
    skills_section = skills_config.get("skills", {})

    for canonical_skill, payload in skills_section.items():

        # Expected structure:
        # python:
        #   aliases:
        #     - python
        aliases = payload.get("aliases", [])

        # Also map the canonical skill name to itself.
        alias_to_skill[normalize_text_basic(canonical_skill)] = canonical_skill

        # Map each alias to the canonical skill.
        for alias in aliases:
            alias_to_skill[normalize_text_basic(alias)] = canonical_skill

    return alias_to_skill


def normalize_skill_terms(skill_terms: list[str], alias_to_skill: dict[str, str]) -> list[str]:
    """
    Normalize free-text skill terms to canonical skills where possible.
    """

    normalized: list[str] = []

    for term in skill_terms:

        # Normalize skill text for lookup.
        key = normalize_text_basic(term)

        # If skill exists in alias map, use canonical form.
        # Otherwise convert text to snake_case as fallback.
        canonical = alias_to_skill.get(key, key.replace(" ", "_"))

        normalized.append(canonical)

    # Remove duplicates while preserving order.
    return unique_preserve_order(normalized)