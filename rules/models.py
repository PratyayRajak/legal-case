"""Rule data models.

Rules are stored with the Hindi original as the legal text of record
plus a structured, language-neutral logic block.
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RuleStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class RuleSeverity(str, Enum):
    warning = "warning"
    blocking = "blocking"


class RuleResult(str, Enum):
    pass_ = "pass"
    fail = "fail"
    cannot_evaluate = "cannot_evaluate"


class ReviewInfo(BaseModel):
    drafted_by: str = "llm"
    verified_by: str | None = None
    verified_on: str | None = None


class RuleTestCase(BaseModel):
    input: dict[str, Any]
    expect: RuleResult


class Rule(BaseModel):
    """A structured rule with the Hindi original as the text of record."""

    id: str
    text_hi: str = Field(..., description="Original Hindi rule text — never altered")
    source: str = Field(..., description="Act / section / order reference")
    effective_from: str
    effective_to: str | None = None
    applies_to: dict[str, list[str]] = Field(
        default_factory=dict,
        description="e.g. {case_types: [revenue], court_levels: [district]}",
    )
    requires_fields: list[str] = Field(
        default_factory=list,
        description="Canonical fields required to evaluate this rule",
    )
    logic: dict[str, Any] = Field(
        default_factory=dict,
        description="Language-neutral logic block using canonical fields",
    )
    severity: RuleSeverity
    message_hi: str
    message_en: str
    status: RuleStatus = RuleStatus.DRAFT
    review: ReviewInfo = Field(default_factory=ReviewInfo)
    tests: list[RuleTestCase] = Field(default_factory=list)

    def is_active(self) -> bool:
        return self.status == RuleStatus.ACTIVE

    def can_run_in_production(self) -> bool:
        """A rule runs in production only if ACTIVE and verified."""
        return (
            self.status == RuleStatus.ACTIVE
            and self.review.verified_by is not None
            and len(self.tests) >= 3  # must have pass, fail, cannot_evaluate tests
        )


class RuleCheckResult(BaseModel):
    """Result of evaluating a single rule against a case."""

    rule_id: str
    rule_version: str
    result: RuleResult
    severity: RuleSeverity
    message_hi: str
    message_en: str
    evidence_citations: list[dict[str, Any]] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
