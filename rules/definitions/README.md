# Rule Definitions

This directory contains YAML rule files. Each file defines one or more rules.

## Status

Only `ACTIVE` rules run in production. `DRAFT` rules are never evaluated.
A rule becomes ACTIVE only after:
1. `review.verified_by` is set by a legal expert
2. At least 3 test cases exist (pass, fail, cannot_evaluate)
3. All referenced concept IDs exist in `glossary/concepts.yaml`
4. `rules validate` passes

## Placeholder Rules

The placeholder rules in `placeholder_rules.yaml` are for pipeline testing only.
They are DRAFT status and will never run in production.
