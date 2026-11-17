# Security Documentation

**Suitable for government procurement review.**

## PII Handling

- All PII (Aadhaar, PAN, phone, voter ID, names) is masked **before** any LLM
  call and **before** any logging or tracing.
- Reversible mapping stored encrypted at rest using Fernet symmetric encryption.
- Only authorized users (judge role) can unmask PII via the API.
- Custom Presidio recognizers for Indian PII types.

## Prompt Injection Defense

- All document text is treated as **untrusted data**, never as instructions.
- Document text is passed in the `data` section of prompts, never in the
  `system` or `instructions` section.
- Adversarial PDF tests: text like "ignore previous instructions" inside
  documents must have no effect (tested in Phase 10).
- LLM responses are validated against strict JSON schemas before use.

## Authentication & Authorization

- JWT-based authentication with configurable expiry (default: 60 minutes).
- Session timeout: 30 minutes of inactivity.
- Roles: `judge`, `lawyer`, `admin`, `auditor`.
- Per-case permissions enforced at the API layer.
- All auth events written to the immutable audit log.

## Encryption

- All secrets via environment variables or a secrets manager. No hardcoded secrets.
- TLS required in production (terminated at load balancer).
- Database encryption at rest (AWS RDS with encryption enabled).
- S3/MinIO server-side encryption.

## Audit Log

- Immutable: append-only, never updated or deleted.
- Records: upload, view, query, export, correction, rule change.
- Exportable by auditors.
- Retention per DPDP Act requirements.

## Upload Hardening

- File type validation (magic bytes, not just extension).
- Size limit: 50 MB, 500 pages.
- Malware scan hook (ClamAV in production).
- Safe PDF parsing (PyMuPDF with sandboxing).
- Password-protected PDFs rejected with clear error.

## Self-Hosted Mode

- `SELF_HOSTED_MODE=true` disables all external API calls.
- All LLM and embedding calls routed to on-premise models.
- No data leaves the premises.
- Documented for air-gapped deployments.

## India Data Residency

- Production deployment: AWS ap-south-1 (Mumbai region).
- No data replication to other regions.
- Compliant with DPDP Act 2023 data localization requirements.
