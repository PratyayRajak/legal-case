# Court Brief Engine

**Bilingual (Hindi/English) AI-assisted case brief and rule-check system for Indian courts.**

> ⚠️ AI-assisted summary. Verify against the source document. This system assists and never decides.

## Overview

Upload a case PDF (Hindi, English, or mixed) and receive:
1. A structured **case brief** with citations
2. A **rule-compliance report** (deterministic rules engine)
3. A **conflict report** across documents
4. **Follow-up Q&A** grounded in the uploaded file

## Quick Start

```bash
# 1. Copy and configure environment
cp .env.example .env
# Edit .env: add your LLM API key and SECRET_KEY

# 2. Run the full stack
docker compose up

# 3. API docs (dev mode only)
# http://localhost:8000/api/docs
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md).

## Adding a Case Type (config only)

1. Add field definitions to `app/schemas/case_types/<type>.yaml`.
2. Add glossary concepts to `glossary/concepts.yaml`.
3. Add rules to `rules/definitions/<type>_rules.yaml`.
4. No code changes required.

## Adding a Rule

See [`docs/rules-authoring.md`](docs/rules-authoring.md).

## Adding a Glossary Concept

See [`docs/glossary-authoring.md`](docs/glossary-authoring.md).

## Development

```bash
pip install -e ".[dev]"
pytest tests/unit/ -v
ruff check .
python glossary/lint.py
```

## Phase Status

Currently in **Phase 1 — Skeleton**. See `docs/architecture.md` for the roadmap.

## Security

See [`docs/security.md`](docs/security.md) and [`docs/data-handling.md`](docs/data-handling.md).

## Known Limitations

See [`docs/known-limitations.md`](docs/known-limitations.md).

## Disclaimer

This system is for research and assistance purposes only. It does not provide
legal advice and must be verified against source documents. All AI outputs
carry the disclaimer: "AI-assisted summary. Verify against the source document."
