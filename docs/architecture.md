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
| 1 | Skeleton + schemas + interfaces | ✅ Done |
| 2 | Glossary + eval harness + synthetic data | ✅ Done |
| 3 | Ingest + OCR + PII | ✅ Done |
| 4 | Chunking + retrieval | 🔲 Next |
| 5 | Field extraction | 🔲 Planned |
| 6 | Normalization + conflicts | 🔲 Planned |
| 7 | Rules engine + import | 🔲 Planned |
| 8 | API + background jobs | 🔲 Planned |
| 9 | Frontend | 🔲 Planned |
| 10 | Q&A + eval | 🔲 Planned |
| 11 | Hardening + deployment | 🔲 Planned |

## Phase 3 Implementation Summary

- **PDF Ingestion & Hardening (`pipeline/ingest.py`)**:
  - Validates magic bytes (`%PDF-`) and checks against corruption.
  - Computes deterministic SHA-256 hash for caching and audit logs.
  - Enforces page count and file size limits from settings.
  - Detects and rejects password-protected/encrypted files with typed exceptions.
  - Extracts per-page geometry (width, height, rotation, char and image count).

- **Hybrid Court OCR Engine (`pipeline/ocr_engine.py`)**:
  - Classifies pages into `digital`, `scanned`, or `mixed`.
  - OpenCV image preprocessing pipeline: CLAHE adaptive contrast, median blur denoising, deskewing (-15° to +15° via `minAreaRect`), and Otsu adaptive binarization.
  - Digital extraction extracts exact word bounding boxes, line numbers, block numbers, and word-level language flags.
  - Script & language classification (`hi`, `en`, `mixed`) with Devanagari Unicode thresholding.

- **Indian Court PII Masker (`pipeline/pii_masker.py`)**:
  - Presidio Analyzer enhanced with custom regex and context recognizers for Indian identifiers:
    - Aadhaar (`INDIAN_AADHAAR`: 12 digits)
    - PAN card (`INDIAN_PAN`: 5 letters + 4 digits + 1 letter)
    - Mobile phone numbers (`INDIAN_PHONE`: +91/10-digit)
    - Voter ID / EPIC (`VOTER_ID`: 3 letters + 7 digits)
    - Person names (`PERSON`)
  - Overlapping entity deduplication by confidence and specificity score.
  - Reversible masking with symmetric Fernet encryption at rest; unmasking requires authorization.
