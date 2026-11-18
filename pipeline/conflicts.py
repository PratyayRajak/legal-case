"""Cross-Document Conflict Detection for Indian Court Records.

Flags inconsistencies across documents/pages in a case file:
1. Date Mismatches: contradictory filing or hearing dates across petition, order sheets, notices.
2. Party Name Discrepancies: name/spelling variations or contradictory father/alias names.
3. Status Contradictions: conflicting interim and final orders (e.g. stay vs dismissed).
4. Case Number Inconsistencies: typos or mismatched docket numbers across annexures.

Produces bilingual descriptions (English + Hindi) with dual verifiable citations.
"""
from __future__ import annotations

import re

from app.schemas.canonical import (
    Citation,
    ConflictItem,
    ConflictReport,
    ConflictSeverity,
    ConflictType,
    ExtractedField,
    Language,
)
from eval.normalize import (
    convert_hindi_digits_to_ascii,
    fuzzy_name_match,
    normalize_date,
)


class CrossDocumentConflictDetector:
    """Scans multi-page case files to identify cross-document inconsistencies."""

    def __init__(self) -> None:
        pass

    def detect_conflicts(
        self,
        pages_text: dict[int, str],
        extracted_fields: dict[str, ExtractedField],
        doc_id: str = "doc",
    ) -> ConflictReport:
        """Scan all pages and extracted fields for cross-document conflicts."""
        conflicts: list[ConflictItem] = []

        # 1. Check for Case Number Inconsistencies across pages
        case_no_field = extracted_fields.get("case_number")
        if case_no_field and case_no_field.found and isinstance(case_no_field.value, dict):
            primary_num = str(case_no_field.value.get("number", ""))
            primary_year = str(case_no_field.value.get("year", ""))
            primary_citation = (
                case_no_field.citations[0]
                if case_no_field.citations
                else Citation(doc_id=doc_id, page=1, snippet=primary_num, lang=Language.hi)
            )

            # Search all pages for alternative case numbers
            for pno, text in pages_text.items():
                matches = re.finditer(
                    r"(?:वाद\s*संख्या|Case\s*No\.?)[\s:]*([०-९0-9]+)\s*[\/|\-]\s*([०-९0-9]{4})",
                    text,
                    re.IGNORECASE,
                )
                for m in matches:
                    raw_n = convert_hindi_digits_to_ascii(m.group(1).strip())
                    raw_y = convert_hindi_digits_to_ascii(m.group(2).strip())
                    if raw_n != primary_num or raw_y != primary_year:
                        conflicts.append(
                            ConflictItem(
                                conflict_id=f"conf-caseno-p{pno}",
                                conflict_type=ConflictType.case_number_mismatch,
                                field_name="case_number",
                                description_en=(
                                    f"Case number mismatch: page {primary_citation.page} states '{primary_num}/{primary_year}' "
                                    f"but page {pno} mentions '{raw_n}/{raw_y}'."
                                ),
                                description_hi=(
                                    f"वाद संख्या में विसंगति: पृष्ठ {primary_citation.page} पर '{primary_num}/{primary_year}' "
                                    f"है जबकि पृष्ठ {pno} पर '{raw_n}/{raw_y}' अंकित है।"
                                ),
                                evidence_a=primary_citation,
                                evidence_b=Citation(
                                    doc_id=doc_id,
                                    page=pno,
                                    snippet=m.group(0).strip(),
                                    lang=Language.hi if any("\u0900" <= ch <= "\u097F" for ch in m.group(0)) else Language.en,
                                ),
                                severity=ConflictSeverity.blocking,
                            )
                        )

        # 2. Check for Date Mismatches across pages
        filing_field = extracted_fields.get("filing_date")
        if filing_field and filing_field.found and isinstance(filing_field.value, dict):
            primary_iso = filing_field.value.get("iso_date")
            primary_cit = (
                filing_field.citations[0]
                if filing_field.citations
                else Citation(doc_id=doc_id, page=1, snippet=str(primary_iso), lang=Language.hi)
            )

            for pno, text in pages_text.items():
                if pno == primary_cit.page:
                    continue
                matches = re.finditer(
                    r"(?:दायर\s*करने\s*की\s*तिथि|संस्थित\s*दिनांक|filed\s*on)[\s:]*([०-९0-9\/\-\.]+)",
                    text,
                    re.IGNORECASE,
                )
                for m in matches:
                    d_obj = normalize_date(m.group(1).strip())
                    if d_obj and d_obj.iso_date != primary_iso:
                        conflicts.append(
                            ConflictItem(
                                conflict_id=f"conf-date-p{pno}",
                                conflict_type=ConflictType.date_mismatch,
                                field_name="filing_date",
                                description_en=(
                                    f"Filing date mismatch: page {primary_cit.page} records '{primary_iso}' "
                                    f"while page {pno} indicates '{d_obj.iso_date}'."
                                ),
                                description_hi=(
                                    f"दायर करने की तिथि में विसंगति: पृष्ठ {primary_cit.page} पर '{primary_iso}' "
                                    f"है जबकि पृष्ठ {pno} पर '{d_obj.iso_date}' दर्ज है।"
                                ),
                                evidence_a=primary_cit,
                                evidence_b=Citation(
                                    doc_id=doc_id,
                                    page=pno,
                                    snippet=m.group(0).strip(),
                                    lang=Language.hi if any("\u0900" <= ch <= "\u097F" for ch in m.group(0)) else Language.en,
                                ),
                                severity=ConflictSeverity.warning,
                            )
                        )

        # 3. Check for Status Contradictions (e.g. Stayed vs Dismissed)
        status_field = extracted_fields.get("current_status")
        if status_field and status_field.found:
            curr_status = str(status_field.value)
            curr_cit = (
                status_field.citations[0]
                if status_field.citations
                else Citation(doc_id=doc_id, page=1, snippet=curr_status, lang=Language.hi)
            )

            # Check if an earlier or later order sheet contradicts the current status
            for pno, text in pages_text.items():
                if pno == curr_cit.page:
                    continue
                if curr_status == "rejected" and ("स्थगन" in text or "stay granted" in text.lower()):
                    snippet = "अंतरिम स्थगन" if "अंतरिम स्थगन" in text else "स्थगन आदेश"
                    conflicts.append(
                        ConflictItem(
                            conflict_id=f"conf-status-p{pno}",
                            conflict_type=ConflictType.status_contradiction,
                            field_name="current_status",
                            description_en=(
                                f"Status contradiction: page {curr_cit.page} concludes rejection, "
                                f"but page {pno} mentions an active stay order."
                            ),
                            description_hi=(
                                f"स्थिति में विरोधाभास: पृष्ठ {curr_cit.page} पर वाद खारिज है, "
                                f"परंतु पृष्ठ {pno} पर स्थगन आदेश का उल्लेख है।"
                            ),
                            evidence_a=curr_cit,
                            evidence_b=Citation(
                                doc_id=doc_id,
                                page=pno,
                                snippet=snippet,
                                lang=Language.hi,
                            ),
                            severity=ConflictSeverity.warning,
                        )
                    )

        # 4. Check for Party Name Discrepancies
        pet_field = extracted_fields.get("petitioners")
        if pet_field and pet_field.found and isinstance(pet_field.value, list) and pet_field.value:
            first_pet = pet_field.value[0]
            if isinstance(first_pet, dict):
                pet_name = first_pet.get("original", "")
                pet_cit = (
                    pet_field.citations[0]
                    if pet_field.citations
                    else Citation(doc_id=doc_id, page=1, snippet=pet_name, lang=Language.hi)
                )

                for pno, text in pages_text.items():
                    if pno == pet_cit.page:
                        continue
                    m_pet = re.search(r"(?:वादी|Petitioner)[\s:]*([^\n\r,]+)", text, re.IGNORECASE)
                    if m_pet:
                        other_name = m_pet.group(1).strip()
                        if other_name and not fuzzy_name_match(pet_name, other_name):
                            conflicts.append(
                                ConflictItem(
                                    conflict_id=f"conf-name-p{pno}",
                                    conflict_type=ConflictType.name_discrepancy,
                                    field_name="petitioners",
                                    description_en=(
                                        f"Petitioner name variation: page {pet_cit.page} states '{pet_name}' "
                                        f"while page {pno} lists '{other_name}'."
                                    ),
                                    description_hi=(
                                        f"वादी के नाम में भिन्नता: पृष्ठ {pet_cit.page} पर '{pet_name}' "
                                        f"है जबकि पृष्ठ {pno} पर '{other_name}' है।"
                                    ),
                                    evidence_a=pet_cit,
                                    evidence_b=Citation(
                                        doc_id=doc_id,
                                        page=pno,
                                        snippet=m_pet.group(0).strip(),
                                        lang=Language.hi if any("\u0900" <= ch <= "\u097F" for ch in other_name) else Language.en,
                                    ),
                                    severity=ConflictSeverity.warning,
                                )
                            )

        has_blocking = any(c.severity == ConflictSeverity.blocking for c in conflicts)
        return ConflictReport(
            doc_id=doc_id,
            conflicts=conflicts,
            total_conflicts=len(conflicts),
            has_blocking=has_blocking,
        )
