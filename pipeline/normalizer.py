"""Normalization and Glossary Concept Mapping Engine.

Validates and normalizes extracted field values against:
1. `glossary/concepts.yaml` (canonical legal concept IDs and surface forms).
2. Pydantic canonical enums (CaseStatus, CourtLevel, ProceedingType, DocumentType).
3. ISO 8601 date representations with precision flags.
4. Transliterated phonetic keys for person names.

Unmappable terms are set to needs_review=True, NEVER silently guessed.
"""
from __future__ import annotations

from typing import Any

from app.schemas.canonical import (
    CaseStatus,
    ConceptRef,
    CourtLevel,
    ExtractedField,
    Language,
    ProceedingType,
)
from eval.normalize import (
    create_person_name,
    normalize_case_number,
    normalize_date,
)
from glossary.loader import GlossaryLoader


class CanonicalNormalizer:
    """Normalizes extracted field values into canonical concept IDs and enums."""

    def __init__(self, glossary: GlossaryLoader | None = None) -> None:
        self.glossary = glossary or GlossaryLoader()
        self._build_concept_lookup()

    def _build_concept_lookup(self) -> None:
        """Build surface-form to concept_id index from glossary."""
        self.surface_to_concept: dict[str, str] = {}
        for cid in self.glossary.all_concept_ids():
            hi_forms = self.glossary.get_surface_forms(cid, "hi")
            en_forms = self.glossary.get_surface_forms(cid, "en")
            for f in hi_forms:
                self.surface_to_concept[f.strip().lower()] = cid
            for f in en_forms:
                self.surface_to_concept[f.strip().lower()] = cid

    def map_to_concept(self, text: str, lang: Language = Language.hi) -> ConceptRef | None:
        """Map text or surface form to a canonical ConceptRef."""
        cleaned = text.strip().lower()
        cid = self.surface_to_concept.get(cleaned)
        if cid:
            return ConceptRef(
                concept_id=cid,
                surface_form=text.strip(),
                language=lang,
                confidence=1.0,
            )
        return None

    def normalize_status(self, raw_val: Any) -> tuple[CaseStatus | str, bool, str | None]:
        """Map raw status string to canonical CaseStatus enum."""
        if not raw_val:
            return CaseStatus.other, True, "Status value is empty"

        val_str = str(raw_val).strip().lower()

        # Check enum match
        try:
            return CaseStatus(val_str), False, None
        except ValueError:
            pass

        # Check surface form mapping
        if any(term in val_str for term in ["खारिज", "निरस्त", "dismiss", "reject"]):
            return CaseStatus.rejected, False, None
        if any(term in val_str for term in ["स्वीकार", "मंजूर", "allow"]):
            return CaseStatus.allowed, False, None
        if any(term in val_str for term in ["निस्तारित", "फैसला", "dispose"]):
            return CaseStatus.disposed, False, None
        if any(term in val_str for term in ["स्थगन", "स्टे", "stay"]):
            return CaseStatus.stayed, False, None
        if any(term in val_str for term in ["लंबित", "विचाराधीन", "pending"]):
            return CaseStatus.pending, False, None
        if any(term in val_str for term in ["वापस", "withdrawn"]):
            return CaseStatus.withdrawn, False, None

        return val_str, True, f"Unrecognized case status: '{raw_val}'"

    def normalize_court_level(self, raw_val: Any) -> tuple[CourtLevel | str, bool, str | None]:
        """Map raw court level to CourtLevel enum."""
        if not raw_val:
            return CourtLevel.district, True, "Court level value is empty"

        val_str = str(raw_val).strip().lower()
        try:
            return CourtLevel(val_str), False, None
        except ValueError:
            pass

        if any(k in val_str for k in ["high", "उच्च न्यायालय", "हाई कोर्ट"]):
            return CourtLevel.high, False, None
        if any(k in val_str for k in ["supreme", "सर्वोच्च", "उच्चतम", "सुप्रीम"]):
            return CourtLevel.supreme, False, None
        if any(k in val_str for k in ["tribunal", "परिषद", "बोर्ड", "board"]):
            return CourtLevel.tribunal, False, None
        if any(k in val_str for k in ["district", "sdm", "उप-जिलाधिकारी", "तहसील", "कलेक्टर", "सदर"]):
            return CourtLevel.district, False, None

        return val_str, True, f"Unrecognized court level: '{raw_val}'"

    def normalize_proceeding_type(self, raw_val: Any) -> tuple[ProceedingType | str, bool, str | None]:
        """Map proceeding type to ProceedingType enum."""
        if not raw_val:
            return ProceedingType.other, True, "Proceeding type value is empty"

        val_str = str(raw_val).strip().lower()
        try:
            return ProceedingType(val_str), False, None
        except ValueError:
            pass

        if any(k in val_str for k in ["नामांतरण", "नामान्तरण", "mutation"]):
            return ProceedingType.mutation, False, None
        if any(k in val_str for k in ["बंटवारा", "विभाजन", "partition"]):
            return ProceedingType.partition, False, None
        if any(k in val_str for k in ["सीमांकन", "पैमाइश", "boundary"]):
            return ProceedingType.boundary_dispute, False, None
        if any(k in val_str for k in ["अधिग्रहण", "acquisition"]):
            return ProceedingType.land_acquisition, False, None
        if any(k in val_str for k in ["काश्तकारी", "tenancy"]):
            return ProceedingType.tenancy, False, None

        return val_str, True, f"Unrecognized proceeding type: '{raw_val}'"

    def normalize_field(self, field: ExtractedField) -> ExtractedField:
        """Validate and normalize an individual ExtractedField in-place."""
        if not field.found or field.value is None:
            return field

        fname = field.field
        raw_val = field.value
        needs_rev = field.needs_review
        rev_reasons = list(field.review_reasons)
        normalized_val = raw_val

        if fname == "current_status":
            norm_status, rev_flag, reason = self.normalize_status(raw_val)
            normalized_val = norm_status
            if rev_flag:
                needs_rev = True
                if reason:
                    rev_reasons.append(reason)

        elif fname == "court_level":
            norm_cl, rev_flag, reason = self.normalize_court_level(raw_val)
            normalized_val = norm_cl
            if rev_flag:
                needs_rev = True
                if reason:
                    rev_reasons.append(reason)

        elif fname == "proceeding_type":
            norm_proc, rev_flag, reason = self.normalize_proceeding_type(raw_val)
            normalized_val = norm_proc
            if rev_flag:
                needs_rev = True
                if reason:
                    rev_reasons.append(reason)

        elif fname in ["filing_date", "next_hearing_date"]:
            if isinstance(raw_val, dict) and "original_string" in raw_val:
                norm_d = normalize_date(raw_val["original_string"])
                if norm_d:
                    normalized_val = {
                        "iso_date": norm_d.iso_date,
                        "precision": norm_d.precision.value,
                        "original_string": norm_d.original_string,
                    }
                else:
                    needs_rev = True
                    rev_reasons.append(f"Invalid date format in {fname}: {raw_val}")

        elif fname in ["petitioners", "respondents"]:
            if isinstance(raw_val, list):
                norm_names = []
                for item in raw_val:
                    if isinstance(item, dict) and "original" in item:
                        pname = create_person_name(item["original"])
                        norm_names.append(
                            {
                                "original": pname.original,
                                "script": pname.script,
                                "transliteration_key": pname.transliteration_key,
                            }
                        )
                    elif isinstance(item, str):
                        pname = create_person_name(item)
                        norm_names.append(
                            {
                                "original": pname.original,
                                "script": pname.script,
                                "transliteration_key": pname.transliteration_key,
                            }
                        )
                normalized_val = norm_names

        elif fname == "case_number":
            if isinstance(raw_val, dict) and "original_string" in raw_val:
                norm_c = normalize_case_number(raw_val["original_string"])
                if norm_c:
                    normalized_val = {
                        "case_type": norm_c.case_type,
                        "number": norm_c.number,
                        "year": norm_c.year,
                        "original_string": norm_c.original_string,
                    }

        return ExtractedField(
            field=fname,
            value=normalized_val,
            found=field.found,
            confidence=field.confidence,
            citations=field.citations,
            needs_review=needs_rev,
            review_reasons=rev_reasons,
        )

    def normalize_all(self, extracted: dict[str, ExtractedField]) -> dict[str, ExtractedField]:
        """Normalize all fields in an extracted field dictionary."""
        return {fname: self.normalize_field(fld) for fname, fld in extracted.items()}
