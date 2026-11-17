"""Tests for glossary loader and lint."""
from __future__ import annotations

from pathlib import Path

from glossary.lint import lint, load_concepts
from glossary.loader import (
    all_concept_ids,
    get_concept,
    get_surface_forms,
    glossary_version,
    load_glossary,
)


class TestGlossaryLoader:
    def test_loads_without_error(self):
        glossary = load_glossary()
        assert "concepts" in glossary

    def test_has_expected_concepts(self):
        ids = all_concept_ids()
        assert "STATUS_REJECTED" in ids
        assert "PROCEEDING_MUTATION" in ids
        assert "PARTY_PETITIONER" in ids

    def test_get_concept_known(self):
        c = get_concept("STATUS_REJECTED")
        assert c is not None
        assert c["concept_id"] == "STATUS_REJECTED"

    def test_get_concept_unknown(self):
        assert get_concept("DOES_NOT_EXIST") is None

    def test_get_surface_forms_hi(self):
        forms = get_surface_forms("STATUS_REJECTED", "hi")
        assert "खारिज" in forms

    def test_get_surface_forms_en(self):
        forms = get_surface_forms("STATUS_REJECTED", "en")
        assert "rejected" in forms

    def test_glossary_version(self):
        v = glossary_version()
        assert v != "unknown"


class TestGlossaryLint:
    def test_lint_passes_on_seed_glossary(self):
        path = Path(__file__).parent.parent.parent / "glossary" / "concepts.yaml"
        concepts = load_concepts(path)
        errors = lint(concepts)
        assert errors == [], f"Glossary lint errors: {errors}"

    def test_lint_catches_missing_hi_def(self):
        bad = [
            {
                "concept_id": "BAD",
                "definition_en": "test",
                "definition_hi": "",
                "surface_forms": {"hi": ["test"], "en": ["test"]},
            }
        ]
        errors = lint(bad)
        assert any("NO_HI_DEF" in e for e in errors)

    def test_lint_catches_missing_en_forms(self):
        bad = [
            {
                "concept_id": "BAD2",
                "definition_en": "test",
                "definition_hi": "परीक्षण",
                "surface_forms": {"hi": ["test"], "en": []},
            }
        ]
        errors = lint(bad)
        assert any("NO_EN_FORMS" in e for e in errors)

    def test_lint_catches_duplicate_ids(self):
        concept = {
            "concept_id": "DUP",
            "definition_en": "d",
            "definition_hi": "d",
            "surface_forms": {"hi": ["x"], "en": ["y"]},
        }
        errors = lint([concept, concept])
        assert any("DUPLICATE_ID" in e for e in errors)
