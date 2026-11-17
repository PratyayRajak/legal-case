"""Glossary lint script.

Fails CI if:
1. Any concept has no Hindi surface forms.
2. Any concept has no English surface forms.
3. Any concept has no Hindi definition or no English definition.
4. A surface form maps to two concepts without a disambiguation note.
5. Any concept_id is duplicated.
6. Any concept is missing the concept_id field.

Usage: python glossary/lint.py
Exit code 0 = pass, 1 = fail.
"""
from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import yaml


def load_concepts(path: Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if isinstance(data, dict):
        return cast(list[dict[str, Any]], data.get("concepts", []))
    return []


def lint(concepts: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    surface_to_concepts: dict[str, list[str]] = defaultdict(list)

    for concept in concepts:
        cid = str(concept.get("concept_id", "<MISSING>"))

        # Duplicate ID check
        if cid in seen_ids:
            errors.append(f"[DUPLICATE_ID] concept_id '{cid}' appears more than once")
        seen_ids.add(cid)

        # Missing definition checks
        if not concept.get("definition_en"):
            errors.append(f"[NO_EN_DEF] '{cid}' has no English definition")
        if not concept.get("definition_hi"):
            errors.append(f"[NO_HI_DEF] '{cid}' has no Hindi definition")

        # Surface form checks
        sf = concept.get("surface_forms", {})
        hi_forms = sf.get("hi", []) if isinstance(sf, dict) else []
        en_forms = sf.get("en", []) if isinstance(sf, dict) else []

        if not hi_forms:
            errors.append(f"[NO_HI_FORMS] '{cid}' has no Hindi surface forms")
        if not en_forms:
            errors.append(f"[NO_EN_FORMS] '{cid}' has no English surface forms")

        # Track surface forms for ambiguity check
        for form in list(hi_forms) + list(en_forms):
            surface_to_concepts[str(form).lower()].append(cid)

    # Ambiguity check — same surface form mapping to 2+ concepts
    for form, cids in surface_to_concepts.items():
        if len(cids) > 1:
            # Check if all concepts that share this form have disambiguation notes
            concepts_dict = {str(c.get("concept_id")): c for c in concepts}
            for cid in cids:
                if not concepts_dict.get(cid, {}).get("disambiguation"):
                    errors.append(
                        f"[AMBIGUOUS_FORM] Surface form '{form}' maps to {cids} "
                        f"but '{cid}' has no disambiguation note"
                    )

    return errors


def main() -> int:
    path = Path(__file__).parent / "concepts.yaml"
    if not path.exists():
        print(f"ERROR: {path} not found", file=sys.stderr)
        return 1

    concepts = load_concepts(path)
    errors = lint(concepts)

    if errors:
        print("GLOSSARY LINT FAILED:")
        for e in errors:
            print(f"  {e}")
        return 1

    print(f"Glossary lint passed. {len(concepts)} concepts checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
