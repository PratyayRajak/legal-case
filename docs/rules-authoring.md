# Rules Authoring Guide

## Workflow

1. Legal expert provides Hindi rule text + source reference.
2. Run `python scripts/import_rules.py --input rules.csv` to draft structured rule.
3. Review the generated Markdown review sheet.
4. Expert verifies logic, test cases, and bilingual messages.
5. Set `review.verified_by` and `review.verified_on` in the YAML.
6. Run `python -m rules validate` — must pass.
7. Change `status: DRAFT` to `status: ACTIVE`.
8. Submit PR with the rule file. CI runs all rule tests.
9. After approval, the rule is live.

## Rule YAML Format

See `rules/definitions/placeholder_rules.yaml` for the full format.

## DRAFT Rules Never Run

A rule with `status: DRAFT` is never evaluated in production.
Only `status: ACTIVE` rules with a verified reviewer and ≥3 test cases run.

## Adding a Check Function

For rules with complex logic that cannot be expressed in simple YAML:
1. Add a function in `rules/checks/` decorated with `@register_check("R0XX")`.
2. The function receives canonical fields and returns `pass`, `fail`, or `cannot_evaluate`.
3. It must be a pure function with no side effects.
4. Add unit tests in `tests/unit/test_rules_checks.py`.
