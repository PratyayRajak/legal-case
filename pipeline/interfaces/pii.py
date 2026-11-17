"""PII masking interface.

Implements: Microsoft Presidio with custom recognizers for Indian PII:
- Aadhaar number (12-digit)
- PAN card number (ABCDE1234F pattern)
- Indian phone numbers
- Voter ID
- Optional: Devanagari name recognizer (Phase 3)

Masking happens BEFORE any LLM call and BEFORE any logging.
Reversible mapping is stored encrypted at rest for authorized users.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MaskedDocument:
    """Result of PII masking."""

    masked_text: str
    mapping_id: str           # Key to retrieve the reversible mapping
    entities_found: list[str]  # Types of PII found, e.g. ["AADHAAR", "PHONE"]
    page_number: int


class PIIMasker(ABC):
    """Abstract PII masking interface."""

    @abstractmethod
    def mask(self, text: str, page_number: int, doc_id: str) -> MaskedDocument:
        """Mask PII in text. Returns masked text and a mapping reference."""
        ...

    @abstractmethod
    def unmask(self, masked_text: str, mapping_id: str, authorized_user_id: str) -> str:
        """Reverse PII masking for authorized users only."""
        ...

    @abstractmethod
    def supported_entity_types(self) -> list[str]:
        """Return the list of PII entity types this masker detects."""
        ...


class StubPIIMasker(PIIMasker):
    """Stub PII masker for testing. Returns text unchanged."""

    def mask(self, text: str, page_number: int, doc_id: str) -> MaskedDocument:
        return MaskedDocument(
            masked_text=text,
            mapping_id=f"stub-mapping-{doc_id}-{page_number}",
            entities_found=[],
            page_number=page_number,
        )

    def unmask(self, masked_text: str, mapping_id: str, authorized_user_id: str) -> str:
        return masked_text

    def supported_entity_types(self) -> list[str]:
        return ["AADHAAR", "PAN", "PHONE", "VOTER_ID", "PERSON"]
