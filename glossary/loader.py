"""Glossary loader — loads concepts.yaml and provides lookup utilities."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import yaml


@lru_cache(maxsize=1)
def load_glossary(path: str | None = None) -> dict[str, Any]:
    """Load and cache the glossary. Returns the full data dict."""
    p = Path(path) if path else Path(__file__).parent / "concepts.yaml"
    with open(p, encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return cast(dict[str, Any], data if isinstance(data, dict) else {})


def get_concept(concept_id: str) -> dict[str, Any] | None:
    """Look up a concept by ID."""
    glossary = load_glossary()
    concepts = cast(list[dict[str, Any]], glossary.get("concepts", []))
    for concept in concepts:
        if concept.get("concept_id") == concept_id:
            return concept
    return None


def get_surface_forms(concept_id: str, language: str) -> list[str]:
    """Get surface forms for a concept in a given language."""
    concept = get_concept(concept_id)
    if not concept:
        return []
    forms = concept.get("surface_forms", {}).get(language, [])
    return cast(list[str], forms if isinstance(forms, list) else [])


def all_concept_ids() -> list[str]:
    """Return all concept IDs in the glossary."""
    glossary = load_glossary()
    concepts = cast(list[dict[str, Any]], glossary.get("concepts", []))
    return [str(c["concept_id"]) for c in concepts if "concept_id" in c]


def glossary_version() -> str:
    """Return the glossary version string."""
    return str(load_glossary().get("version", "unknown"))
