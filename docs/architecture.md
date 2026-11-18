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
| 4 | Chunking + retrieval | ✅ Done |
| 5 | Field extraction | ✅ Done |
| 6 | Normalization + conflicts | ✅ Done |
| 7 | Rules engine + import | ✅ Done |
| 8 | API + background jobs | ✅ Done |
| 9 | Frontend | 🔲 Next |
| 10 | Q&A + eval | 🔲 Planned |
| 11 | Hardening + deployment | 🔲 Planned |

## Phase 8 Implementation Summary

- **FastAPI Endpoints (`app/routers/`)**:
  - `POST /api/v1/documents/upload`: PDF magic byte validation, SHA-256 calculation, disk storage, and background processing task queue.
  - `GET /api/v1/documents/{doc_id}`: Document status, progress %, and pipeline step.
  - `GET /api/v1/documents/{doc_id}/brief`: Structured `RevenueCaseBrief` retrieval.
  - `GET /api/v1/documents/{doc_id}/rules`: Versioned rule compliance report.
  - `GET /api/v1/documents/{doc_id}/conflicts`: Cross-document conflict report with dual citations.
  - `GET /api/v1/jobs/{job_id}`: Background job progress tracking.
  - `POST /api/v1/qa/ask`: Follow-up Q&A grounded exclusively in source file.
  - `GET /api/v1/admin/rules` & `POST /api/v1/admin/rules/verify`: Rule lifecycle management & legal expert verification gate.
  - `GET /api/v1/admin/audit-logs`: Query immutable audit trail.
- **Background Pipeline Orchestrator (`app/services/job_runner.py`)**:
  - Sequentially coordinates all 10 pipeline stages with progress tracking (10% to 100%).
- **Tamper-Evident Audit Service (`app/services/audit.py`)**:
  - Tracks document hashes, actions, user identifiers, and timestamps.

## Phase 7 Implementation Summary

- **Declarative Logic Evaluator (`rules/evaluator.py`)**:
  - Language-neutral logic evaluator running on canonical field dictionaries.
  - Supports atomic operators (`equals`, `not_equals`, `in`, `not_in`, `exists`, `is_null`), comparisons (`greater_than`, `less_than`, `between`), combinators (`and`, `or`, `not`), and rule implications (`if: <cond>, require: <cond>`).
- **Rules Engine Integration (`rules/engine.py`)**:
  - Fallback from hardcoded checks to declarative rule logic.
  - Missing or unverified fields strictly return `cannot_evaluate`.
- **Hindi Rule Importer & Legal Review Sheet (`scripts/import_rules.py`)**:
  - Ingests raw Hindi procedural rules from CSV / Markdown.
  - Drafts structured language-neutral logic with bilingual messages.
  - Generates Markdown review sheets for legal expert verification.
  - Strict promotion gate: rules require legal expert verification (`verified_by`), complete test cases covering `pass`, `fail`, and `cannot_evaluate`, and glossary concept validation.

## Phase 6 Implementation Summary

- **Canonical Normalizer (`pipeline/normalizer.py`)**:
  - Maps Hindi and English surface forms to canonical concept IDs in `glossary/concepts.yaml`.
  - Validates and coerces enums (`CaseStatus`, `CourtLevel`, `ProceedingType`).
  - Dates and person names enriched with phonetic transliteration keys (`create_person_name`).
  - Unmappable or ambiguous terms are flagged with `needs_review = True`, never guessed.
- **Cross-Document Conflict Detector (`pipeline/conflicts.py`)**:
  - Scans multi-page case records to detect:
    - Case number mismatches/typos across orders and annexures (`blocking`).
    - Contradictory filing/hearing dates across petition and order sheets (`warning`).
    - Status contradictions (e.g., active stay vs. dismissal) across dates (`warning`).
    - Party name variations across documents using `fuzzy_name_match` (`warning`).
  - Generates structured bilingual conflict items with dual citations (`evidence_a`, `evidence_b`).

## Phase 4 Implementation Summary

- **Document Classifier (`pipeline/classifier.py`)**:
  - Classifies document types (`petition`, `order_sheet`, `judgment`, `notice`, `annexure`) and court levels (`district`, `high`, `supreme`, `tribunal`).
- **Structure-Aware Chunker (`pipeline/chunker.py`)**:
  - Respects page and legal section boundaries ("न्यायालय", "आदेश", "ORDER SHEET", "तथ्य", "निर्णय").
  - Ensures citations never cross page boundaries.
- **Hybrid Retriever (`pipeline/retriever.py`)**:
  - Bilingual BM25Okapi lexical index + dense vector search combined via Reciprocal Rank Fusion (RRF, $k=60$).

## Phase 5 Implementation Summary

- **Prompts & Security (`pipeline/prompts.py`)**:
  - Strict untrusted data enclosure (`<document_text>`), zero-temperature determinism, strict JSON schema.
- **Two-Pass Canonical Field Extractor (`pipeline/extractor.py`)**:
  - Pass 1: Deterministic regex and concept matching for case numbers, dates, parties, status, and rejection grounds.
  - Pass 2: Semantic extraction via `LLMClient` with fallback consensus.
  - Verbatim citation verification matching snippet presence in page OCR text via Unicode NFKC normalization.
  - Strict "not found" preference over hallucination.
- **Brief Assembler (`pipeline/assembler.py`)**:
  - Assembles `RevenueCaseBrief` attaching pipeline/rules/glossary provenance and the mandatory legal disclaimer.

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
