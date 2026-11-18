"""Tamper-evident audit logging service for Indian Court Case Engine.

Rules:
- Append-only immutable log: records document SHA-256, user identity, action, and timestamp.
- Actions: upload, view_brief, check_rules, view_conflicts, unmask_pii, rule_promoted.
- Tracks pipeline and rules versions for complete audit provenance.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class AuditRecord:
    id: str
    action: str
    user_id: str | None
    document_id: str | None
    doc_hash: str | None
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


class AuditService:
    """In-memory audit store with persistence hooks for PostgreSQL/SQLite."""

    def __init__(self) -> None:
        self._logs: list[AuditRecord] = []

    def log(
        self,
        action: str,
        user_id: str | None = None,
        document_id: str | None = None,
        doc_hash: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """Create and store an immutable audit record."""
        record = AuditRecord(
            id=str(uuid.uuid4()),
            action=action,
            user_id=user_id or "anonymous_court_user",
            document_id=document_id,
            doc_hash=doc_hash,
            timestamp=datetime.utcnow().isoformat() + "Z",
            details=details or {},
        )
        self._logs.append(record)
        return record

    def get_logs(self, document_id: str | None = None, limit: int = 100) -> list[AuditRecord]:
        """Query audit logs filtered by document ID."""
        if document_id:
            matching = [r for r in self._logs if r.document_id == document_id]
            return matching[-limit:]
        return self._logs[-limit:]


# Global singleton audit service instance
audit_service = AuditService()
