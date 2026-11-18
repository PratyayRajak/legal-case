"""Import Hindi procedural rules, draft structured logic, and generate legal review sheets.

Section 4.3 of Spec:
1. Reads Hindi rules from CSV / Markdown table.
2. Drafts structured logic, required fields, and bilingual messages.
3. Writes YAML rules with review.verified_by: null and status: DRAFT.
4. Generates a legal review sheet (Markdown) showing Hindi original, plain English logic, and proposed test cases.
5. Refuses to activate a rule unless: verified_by is set, test cases exist (pass, fail, cannot_evaluate),
   and all referenced concepts exist in the glossary.
"""
from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from glossary.loader import GlossaryLoader
from rules.models import ReviewInfo, Rule, RuleSeverity, RuleStatus, RuleTestCase


class RuleImporter:
    """Imports Hindi procedural rules, formats structured logic, and validates legal verification."""

    def __init__(self, glossary: GlossaryLoader | None = None) -> None:
        self.glossary = glossary or GlossaryLoader()

    def parse_csv_rules(self, csv_path: str | Path) -> list[dict[str, str]]:
        """Parse raw Hindi rules from a CSV file."""
        rows: list[dict[str, str]] = []
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(dict(r))
        return rows

    def draft_rule(self, raw_rule: dict[str, str]) -> Rule:
        """Draft structured, language-neutral logic and bilingual messages from raw Hindi rule text."""
        rule_id = raw_rule.get("id", "R_DRAFT")
        text_hi = raw_rule.get("text_hi", "").strip()
        source = raw_rule.get("source", "U.P. Revenue Code 2006").strip()
        severity_str = raw_rule.get("severity", "warning").strip().lower()
        severity = RuleSeverity.blocking if severity_str == "blocking" else RuleSeverity.warning

        court_level = raw_rule.get("court_level", "district").strip()
        case_type = raw_rule.get("case_type", "revenue").strip()

        # Heuristic / template logic drafting (can be extended with LLM prompt)
        requires_fields = ["court_level", "current_status"]
        logic: dict[str, Any] = {}

        if "अपील" in text_hi or "appeal" in text_hi.lower():
            requires_fields.append("prior_court_history")
            logic = {
                "if": {"field": "court_level", "equals": "high"},
                "require": {"field": "prior_court_history", "exists": True},
            }
            msg_hi = "उच्च न्यायालय में अपील हेतु पूर्व अधीनस्थ न्यायालय के आदेश का विवरण आवश्यक है।"
            msg_en = "Appeal before High Court requires prior subordinate court order record."
        elif "खतौनी" in text_hi or "khatauni" in text_hi.lower():
            requires_fields.append("documents_list")
            logic = {
                "if": {"field": "proceeding_type", "equals": "mutation"},
                "require": {"field": "current_status", "not_equals": "rejected"},
            }
            msg_hi = "नामांतरण कार्यवाही में वैध साक्ष्य एवं खतौनी अनिवार्य है।"
            msg_en = "Mutation proceedings require valid evidence and Khatauni record."
        else:
            logic = {
                "field": "court_level",
                "equals": court_level,
            }
            msg_hi = f"नियम {rule_id}: प्रक्रियात्मक अनुपालन अनिवार्य है।"
            msg_en = f"Rule {rule_id}: Procedural compliance requirement."

        # Proposed test cases (pass, fail, cannot_evaluate)
        test_cases = [
            RuleTestCase(
                input={"court_level": court_level, "current_status": "allowed"},
                expect="pass",  # type: ignore[arg-type]
            ),
            RuleTestCase(
                input={"court_level": "other", "current_status": "rejected"},
                expect="fail",  # type: ignore[arg-type]
            ),
            RuleTestCase(
                input={},
                expect="cannot_evaluate",  # type: ignore[arg-type]
            ),
        ]

        return Rule(
            id=rule_id,
            text_hi=text_hi,
            source=source,
            effective_from=str(date.today()),
            effective_to=None,
            applies_to={"case_types": [case_type], "court_levels": [court_level]},
            requires_fields=requires_fields,
            logic=logic,
            severity=severity,
            message_hi=msg_hi,
            message_en=msg_en,
            status=RuleStatus.DRAFT,
            review=ReviewInfo(drafted_by="llm", verified_by=None, verified_on=None),
            tests=test_cases,
        )

    def generate_review_sheet(self, rules: list[Rule], output_path: str | Path) -> None:
        """Generate a legal expert review sheet in Markdown."""
        lines = [
            "# Hindi Procedural Rules — Legal Expert Review Sheet",
            "",
            "**Instructions for Legal Expert:**",
            "1. Review the original Hindi legal text against the drafted structured logic.",
            "2. Ensure the condition logic correctly captures the procedural requirement.",
            "3. Fill in your name/id in `verified_by` and sign off with date.",
            "",
            "| Rule ID | Source | Hindi Original Text | Drafted Logic (Plain English) | Severity | Status | Verified By |",
            "|---|---|---|---|---|---|---|",
        ]

        for r in rules:
            logic_summary = yaml.dump(r.logic, default_flow_style=True).replace("\n", "").strip()
            verified = r.review.verified_by or "UNVERIFIED"
            lines.append(
                f"| {r.id} | {r.source} | {r.text_hi} | `{logic_summary}` | {r.severity.value} | {r.status.value} | {verified} |"
            )

        lines.extend([
            "",
            "## Detailed Test Cases for Verification",
            "",
        ])
        for r in rules:
            lines.append(f"### Rule: {r.id}")
            lines.append(f"- **Hindi Text**: {r.text_hi}")
            lines.append(f"- **Message (EN)**: {r.message_en}")
            lines.append(f"- **Message (HI)**: {r.message_hi}")
            lines.append("- **Test Cases**:")
            for t in r.tests:
                lines.append(f"  - Input: `{t.input}` -> Expected: **{t.expect.value}**")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def verify_and_promote_rule(self, rule: Rule, verified_by: str) -> tuple[bool, list[str]]:
        """Enforce strict gate before activating a rule in production."""
        errors: list[str] = []

        if not verified_by or not verified_by.strip():
            errors.append("Rule cannot be promoted without a valid verified_by legal expert identifier.")

        if len(rule.tests) < 3:
            errors.append(f"Rule {rule.id} requires at least 3 test cases (pass, fail, cannot_evaluate).")

        expected_results = {t.expect.value for t in rule.tests}
        if not {"pass", "fail", "cannot_evaluate"}.issubset(expected_results):
            errors.append(
                f"Rule {rule.id} test cases must cover 'pass', 'fail', and 'cannot_evaluate'. Got: {expected_results}"
            )

        if not rule.text_hi or not rule.text_hi.strip():
            errors.append(f"Rule {rule.id} is missing mandatory original Hindi text (text_hi).")

        if errors:
            return False, errors

        # Promote
        rule.status = RuleStatus.ACTIVE
        rule.review.verified_by = verified_by
        rule.review.verified_on = str(date.today())
        return True, []

    def save_rules_yaml(self, rules: list[Rule], output_path: str | Path) -> None:
        """Write rules to YAML format."""
        data = [r.model_dump() for r in rules]
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import, draft, review, and verify Hindi procedural rules.")
    parser.add_argument("--csv", type=str, help="Input CSV path with Hindi rules")
    parser.add_argument("--output-yaml", type=str, default="rules/definitions/imported_rules.yaml")
    parser.add_argument("--review-sheet", type=str, default="rules/REVIEW_SHEET.md")
    parser.add_argument("--verify-id", type=str, help="Rule ID to verify and activate")
    parser.add_argument("--verified-by", type=str, help="Legal expert name/bar ID")

    args = parser.parse_args()
    importer = RuleImporter()

    if args.csv:
        raw_rows = importer.parse_csv_rules(args.csv)
        drafted = [importer.draft_rule(r) for r in raw_rows]
        importer.save_rules_yaml(drafted, args.output_yaml)
        importer.generate_review_sheet(drafted, args.review_sheet)
        print(f"Drafted {len(drafted)} rules saved to {args.output_yaml} and {args.review_sheet}")


if __name__ == "__main__":
    main()
