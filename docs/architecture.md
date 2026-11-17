# System Architecture

> AI-assisted summary. Verify against the source document.

## Overview

The Court Brief Engine is a bilingual (Hindi/English) AI-assisted system for
Indian courts that extracts structured information from case PDFs and checks
procedural rule compliance.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                    │
│  Upload │ Brief Viewer │ PDF+Highlights │ Q&A │ Rules Panel  │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────────────┐
│                     FastAPI Backend                           │
│  Auth/RBAC │ Upload │ Jobs │ Q&A │ Admin                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                   LangGraph Pipeline                          │
│  ingest→ocr→pii_mask→classify→chunk_index→extract_fields    │
│  →normalize→conflict_check→rules_check→confidence→brief      │
└──────────┬────────────────────────────────────────┬──────────┘
           │                                        │
┌──────────▼──────────┐              ┌──────────────▼──────────┐
│   OCR Engine        │              │   Rules Engine           │
│ PyMuPDF + Tesseract │              │ Deterministic YAML rules │
│ (swappable)         │              │ on canonical fields only │
└─────────────────────┘              └─────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│   Data Stores                                                 │
│  Postgres │ Redis │ MinIO/S3 │ ChromaDB (vectors)            │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

1. **Bilingual by design**: Rules run on canonical (language-neutral) fields only.
   Language matters only at extraction (in) and display (out).
2. **Never decide, only assist**: Every output carries a disclaimer.
3. **Citations required**: Every field value must have a verifiable citation.
4. **Rules are code**: Deterministic, versioned, auditable. Never in prompts.
5. **Privacy first**: PII masked before any model call.

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Skeleton + schemas + interfaces | ✅ In Progress |
| 2 | Glossary + eval harness | 🔲 Planned |
| 3 | Ingest + OCR + PII | 🔲 Planned |
| 4 | Chunking + retrieval | 🔲 Planned |
| 5 | Field extraction | 🔲 Planned |
| 6 | Normalization + conflicts | 🔲 Planned |
| 7 | Rules engine + import | 🔲 Planned |
| 8 | API + background jobs | 🔲 Planned |
| 9 | Frontend | 🔲 Planned |
| 10 | Q&A + eval | 🔲 Planned |
| 11 | Hardening + deployment | 🔲 Planned |
