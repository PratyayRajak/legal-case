"""Tests for Hindi Procedural Rules Import and Verification Gate."""
from __future__ import annotations

import tempfile
from pathlib import Path

from rules.models import RuleSeverity, RuleStatus
from scripts.import_rules import RuleImporter


class TestRuleImporter:
    def test_draft_rule_from_hindi_text(self):
        importer = RuleImporter()
        raw = {
            "id": "R099_TEST",
            "text_hi": "उच्च न्यायालय में अपील हेतु पूर्व आदेश संलग्न होना आवश्यक है।",
            "source": "राजस्व संहिता नियम 20",
            "severity": "blocking",
            "court_level": "high",
            "case_type": "revenue",
        }
        rule = importer.draft_rule(raw)

        assert rule.id == "R099_TEST"
        assert rule.status == RuleStatus.DRAFT
        assert rule.review.verified_by is None
        assert rule.severity == RuleSeverity.blocking
        assert len(rule.tests) >= 3

        # Test implication logic was drafted
        assert "if" in rule.logic
        assert "require" in rule.logic

    def test_generate_review_sheet_creates_file(self):
        importer = RuleImporter()
        raw = {
            "id": "R100_TEST",
            "text_hi": "नामांतरण हेतु खतौनी साक्ष्य आवश्यक है।",
            "source": "धारा 34",
            "severity": "warning",
            "court_level": "district",
            "case_type": "revenue",
        }
        rule = importer.draft_rule(raw)

        with tempfile.TemporaryDirectory() as tmpdir:
            out_md = Path(tmpdir) / "REVIEW_SHEET.md"
            importer.generate_review_sheet([rule], out_md)

            assert out_md.exists()
            content = out_md.read_text(encoding="utf-8")
            assert "Legal Expert Review Sheet" in content
            assert "R100_TEST" in content
            assert "नामांतरण हेतु खतौनी" in content

    def test_verify_and_promote_rule_enforces_gate(self):
        importer = RuleImporter()
        raw = {
            "id": "R101_TEST",
            "text_hi": "वैध आदेश आवश्यक है।",
            "source": "संहिता",
            "severity": "blocking",
            "court_level": "district",
            "case_type": "revenue",
        }
        rule = importer.draft_rule(raw)

        # Gate 1: Empty verified_by fails
        ok, errors = importer.verify_and_promote_rule(rule, verified_by="")
        assert ok is False
        assert any("verified_by" in e for e in errors)

        # Gate 2: Missing expected test outcome fails
        rule.tests = []  # Remove test cases
        ok, errors = importer.verify_and_promote_rule(rule, verified_by="Advocate_Sharma_UP_Bar_1234")
        assert ok is False
        assert any("requires at least 3 test cases" in e for e in errors)

        # Gate 3: Valid verification promotes to ACTIVE
        rule_valid = importer.draft_rule(raw)
        ok, errors = importer.verify_and_promote_rule(rule_valid, verified_by="Advocate_Sharma_UP_Bar_1234")
        assert ok is True
        assert len(errors) == 0
        assert rule_valid.status == RuleStatus.ACTIVE
        assert rule_valid.review.verified_by == "Advocate_Sharma_UP_Bar_1234"
        assert rule_valid.is_active() is True
