# Glossary Authoring Guide

## Adding a New Concept

1. Add an entry to `glossary/concepts.yaml`.
2. Required fields: `concept_id`, `definition_en`, `definition_hi`, surface forms in both languages.
3. Set `review.reviewed_by: null` until a legal expert reviews it.
4. Run `python glossary/lint.py` — must pass with 0 errors.
5. If a surface form is shared with another concept, add a `disambiguation` note to both.

## Ambiguous Words

Some Hindi words map to multiple legal meanings. These require disambiguation:
- **आदेश**: "order" (court order, DOC_ORDER) vs general "instruction".
  → In legal context, always refers to court order.
- **तारीख**: "date" (general) vs "adjournment/next hearing date" (PROC_ADJOURNMENT).

## Preferred Terms

Each concept has a `preferred_term` in both languages. Use this in all UI messages
and translations to ensure consistent terminology.

## Concept Categories

| Category | Description |
|----------|-------------|
| `case_status` | Current status of a case |
| `court_level` | Level of court |
| `proceeding_type` | Type of legal proceeding |
| `document_type` | Type of court document |
| `party_role` | Role of a person in the case |
| `land_record` | Land record types |
| `official_role` | Official roles in revenue administration |
| `land_identifier` | Land parcel identifiers |
| `location` | Administrative locations |
| `procedural` | Procedural concepts |
| `land_right` | Land tenure and rights |
