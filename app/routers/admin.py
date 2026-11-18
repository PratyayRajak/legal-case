"""Admin endpoints for rule management, verification gating, and audit logs."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.services.audit import audit_service
from rules.loader import load_rules_from_file
from scripts.import_rules import RuleImporter

router = APIRouter()


class VerifyRuleRequest(BaseModel):
    rule_id: str
    verified_by: str = Field(..., description="Legal expert name or State Bar registration number")
    file_path: str = Field(default="rules/definitions/placeholder_rules.yaml")


@router.get("/rules")
async def list_rules(status_filter: str | None = Query(default=None)) -> dict[str, Any]:
    """List rules with their Hindi text of record, structured logic, and verification status."""
    rules = load_rules_from_file("rules/definitions/placeholder_rules.yaml")
    if status_filter:
        rules = [r for r in rules if r.status.value.lower() == status_filter.lower()]

    return {
        "rules": [r.model_dump() for r in rules],
        "total": len(rules),
    }


@router.post("/rules/verify")
async def verify_rule(payload: VerifyRuleRequest) -> dict[str, Any]:
    """Verify and promote a rule to ACTIVE status (enforces Section 4.3 gate)."""
    rules = load_rules_from_file(payload.file_path)
    target_rule = next((r for r in rules if r.id == payload.rule_id), None)
    if not target_rule:
        raise HTTPException(
            status_code=404,
            detail=f"Rule {payload.rule_id} not found in {payload.file_path}",
        )

    importer = RuleImporter()
    ok, errors = importer.verify_and_promote_rule(target_rule, verified_by=payload.verified_by)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rule verification failed quality gate: {errors}",
        )

    importer.save_rules_yaml(rules, payload.file_path)

    audit_service.log(
        action="rule_promoted",
        details={
            "rule_id": target_rule.id,
            "verified_by": payload.verified_by,
            "new_status": target_rule.status.value,
        },
    )

    return {
        "status": "success",
        "rule_id": target_rule.id,
        "new_status": target_rule.status.value,
        "verified_by": payload.verified_by,
        "verified_on": target_rule.review.verified_on,
    }


@router.get("/audit-logs")
async def get_audit_logs(
    document_id: str | None = Query(default=None),
    limit: int = Query(default=50, le=500),
) -> dict[str, Any]:
    """Retrieve immutable audit logs."""
    logs = audit_service.get_logs(document_id=document_id, limit=limit)
    return {
        "logs": [rec.__dict__ for rec in logs],
        "total": len(logs),
    }
