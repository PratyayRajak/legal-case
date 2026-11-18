"""Brief Assembler for Indian Revenue Court Records.

Assembles extracted fields into a canonical RevenueCaseBrief model with:
- Audit metadata and pipeline provenance
- Glossary version and rules version
- Mandatory legal disclaimer: "AI-assisted summary. Verify against the source document."
"""
from __future__ import annotations

from app.schemas.canonical import ExtractedField, RevenueCaseBrief
from glossary.loader import glossary_version


def assemble_revenue_brief(
    doc_id: str,
    extracted_fields: dict[str, ExtractedField],
    pipeline_version: str = "0.1.0",
    rules_version: str = "0.1.0-draft",
) -> RevenueCaseBrief:
    """Assemble all extracted fields into a validated RevenueCaseBrief object."""

    def _get_or_empty(field_name: str) -> ExtractedField:
        return extracted_fields.get(
            field_name,
            ExtractedField(
                field=field_name,
                value=None,
                found=False,
                confidence=1.0,
                citations=[],
                needs_review=False,
            ),
        )

    brief = RevenueCaseBrief(
        doc_id=doc_id,
        pipeline_version=pipeline_version,
        glossary_version=glossary_version(),
        rules_version=rules_version,
        # Core fields
        case_number=_get_or_empty("case_number"),
        court_name=_get_or_empty("court_name"),
        court_level=_get_or_empty("court_level"),
        case_type=_get_or_empty("case_type"),
        proceeding_type=_get_or_empty("proceeding_type"),
        petitioners=_get_or_empty("petitioners"),
        respondents=_get_or_empty("respondents"),
        advocates=_get_or_empty("advocates"),
        filing_date=_get_or_empty("filing_date"),
        previous_hearing_dates=_get_or_empty("previous_hearing_dates"),
        next_hearing_date=_get_or_empty("next_hearing_date"),
        current_status=_get_or_empty("current_status"),
        rejection_reason=_get_or_empty("rejection_reason"),
        orders_summary=_get_or_empty("orders_summary"),
        prior_court_history=_get_or_empty("prior_court_history"),
        documents_list=_get_or_empty("documents_list"),
        disclaimer="AI-assisted summary. Verify against the source document.",
    )
    return brief
