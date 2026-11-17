# Data Handling Policy

## Purpose and Consent

This system is used for official court proceedings. Users (judges and lawyers)
are court officials operating under their professional duties.

Data is processed for:
1. Generating case briefs to assist court proceedings.
2. Rule compliance checking.
3. Conflict detection across case documents.

## Data Categories

| Category | Examples | Retention | Encrypted |
|----------|----------|-----------|-----------|
| Case documents | PDFs | Per case lifecycle | Yes |
| Extracted fields | Dates, names, case numbers | Per case lifecycle | Yes |
| Audit logs | Actions, timestamps | 7 years | Yes |
| PII mappings | Aadhaar, PAN masked values | Per case lifecycle | Yes (Fernet) |
| User corrections | Field corrections | Per case lifecycle | Yes |

## No Training on User Data

This system does **not** use uploaded documents to train any AI model.
Documents are processed in-memory and stored only for case management.

## Delete on Request

The `/api/v1/admin/documents/{id}` DELETE endpoint removes all data
associated with a document, including extracted fields, audit log entries
(anonymized, action recorded), and PII mappings.

## DPDP Act 2023 Compliance

- Purpose limitation: data used only for the stated purpose.
- Data minimization: only fields needed for the brief are extracted.
- Retention limits: documents deleted after case closure + 90 days.
- Rights: authorized users may request data deletion.
- Security: encryption, access control, audit log.
