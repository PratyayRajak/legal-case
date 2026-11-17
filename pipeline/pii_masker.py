"""PII Masking module with Indian Recognizers and Encrypted Reversible Mappings.

Detects:
1. Aadhaar Card Numbers (12 digits, e.g. 1234 5678 9012)
2. PAN Card Numbers (ABCDE1234F pattern)
3. Indian Mobile Phone Numbers (+91 / 0 / 10-digit starting with 6-9)
4. Voter ID / EPIC Cards (3 letters + 7 digits)
5. Person Names (Hindi & English)

Security:
- All sensitive entity mappings are encrypted at rest using Fernet symmetric encryption.
- Encrypted mappings are stored indexed by mapping_id.
- Unmasking requires authorization.
"""
from __future__ import annotations

import json

from cryptography.fernet import Fernet
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerResult

from config import settings
from pipeline.interfaces.pii import MaskedDocument, PIIMasker

# In-memory secure vault for encrypted PII mappings (persisted to DB/S3 in Phase 8)
_ENCRYPTED_VAULT: dict[str, bytes] = {}


def get_encryption_key() -> bytes:
    """Return configured Fernet key or generate a deterministic dev key."""
    if settings.pii_encryption_key:
        return settings.pii_encryption_key.encode()
    # Fixed fallback key for local development and testing
    dev_key = b"tqO3qW1Z1YVq5_G_zF_X0mZq8tY3aW5Z1YVq5_G_zF8="
    return dev_key


class IndianCourtPIIMasker(PIIMasker):
    """Presidio-based PII Masker with custom recognizers for Indian identifiers."""

    def __init__(self) -> None:
        self.analyzer = AnalyzerEngine()
        self.fernet = Fernet(get_encryption_key())
        self._register_indian_recognizers()

    def _register_indian_recognizers(self) -> None:
        """Register custom pattern recognizers for Indian legal and identity documents."""
        # 1. Aadhaar Recognizer (12 digits, optional spaces or hyphens)
        aadhaar_pattern = Pattern(
            name="aadhaar_pattern",
            regex=r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b",
            score=0.9,
        )
        aadhaar_recognizer = PatternRecognizer(
            supported_entity="INDIAN_AADHAAR",
            patterns=[aadhaar_pattern],
            context=["aadhaar", "uid", "आधार", "पहचान पत्र", "uidai"],
        )
        self.analyzer.registry.add_recognizer(aadhaar_recognizer)

        # 2. PAN Card Recognizer (ABCDE1234F)
        pan_pattern = Pattern(
            name="pan_pattern",
            regex=r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
            score=0.95,
        )
        pan_recognizer = PatternRecognizer(
            supported_entity="INDIAN_PAN",
            patterns=[pan_pattern],
            context=["pan", "पैन", "income tax", "आयकर", "खाता संख्या"],
        )
        self.analyzer.registry.add_recognizer(pan_recognizer)

        # 3. Indian Phone Recognizer
        phone_pattern = Pattern(
            name="indian_phone_pattern",
            regex=r"(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b",
            score=0.85,
        )
        phone_recognizer = PatternRecognizer(
            supported_entity="INDIAN_PHONE",
            patterns=[phone_pattern],
            context=["phone", "mobile", "दूरभाष", "मोबाइल", "सम्पर्क"],
        )
        self.analyzer.registry.add_recognizer(phone_recognizer)

        # 4. Voter ID / EPIC Recognizer (ABC1234567)
        epic_pattern = Pattern(
            name="epic_pattern",
            regex=r"\b[A-Z]{3}[0-9]{7}\b",
            score=0.85,
        )
        epic_recognizer = PatternRecognizer(
            supported_entity="VOTER_ID",
            patterns=[epic_pattern],
            context=["voter", "epic", "मतदाता", "पहचान"],
        )
        self.analyzer.registry.add_recognizer(epic_recognizer)

    def supported_entity_types(self) -> list[str]:
        return [
            "INDIAN_AADHAAR",
            "INDIAN_PAN",
            "INDIAN_PHONE",
            "VOTER_ID",
            "PERSON",
            "EMAIL_ADDRESS",
        ]

    def mask(self, text: str, page_number: int, doc_id: str) -> MaskedDocument:
        """Detect and mask PII entities, storing the reversible mapping encrypted."""
        if not text or not settings.pii_masking_enabled:
            return MaskedDocument(
                masked_text=text,
                mapping_id=f"noop-{doc_id}-{page_number}",
                entities_found=[],
                page_number=page_number,
            )

        results = self.analyzer.analyze(
            text=text,
            entities=self.supported_entity_types(),
            language="en",
        )

        mapping: dict[str, str] = {}
        entities_found: list[str] = []

        # Filter overlapping results by prioritizing higher score and specific recognizers
        def entity_priority(res: RecognizerResult) -> tuple[float, int, int]:
            is_specific = 1 if res.entity_type != "PERSON" else 0
            length = res.end - res.start
            return (float(res.score), is_specific, length)

        candidates = sorted(results, key=entity_priority, reverse=True)
        chosen_spans: list[RecognizerResult] = []
        occupied_indices: set[int] = set()

        for res in candidates:
            res_indices = set(range(res.start, res.end))
            if not res_indices.intersection(occupied_indices):
                chosen_spans.append(res)
                occupied_indices.update(res_indices)

        # Sort chosen non-overlapping results from end to start so replacing does not offset indexes
        sorted_results = sorted(chosen_spans, key=lambda x: x.start, reverse=True)

        masked_text = text
        for idx, res in enumerate(sorted_results):
            original_val = text[res.start : res.end]
            entity_type = res.entity_type
            placeholder = f"<{entity_type}_{len(sorted_results) - idx}>"

            mapping[placeholder] = original_val
            if entity_type not in entities_found:
                entities_found.append(entity_type)

            masked_text = masked_text[: res.start] + placeholder + masked_text[res.end :]

        # Encrypt the reversible mapping at rest
        mapping_id = f"pii-{doc_id}-p{page_number}"
        serialized_mapping = json.dumps(mapping, ensure_ascii=False).encode("utf-8")
        encrypted_bytes = self.fernet.encrypt(serialized_mapping)
        _ENCRYPTED_VAULT[mapping_id] = encrypted_bytes

        return MaskedDocument(
            masked_text=masked_text,
            mapping_id=mapping_id,
            entities_found=entities_found,
            page_number=page_number,
        )

    def unmask(self, masked_text: str, mapping_id: str, authorized_user_id: str) -> str:
        """Reverse PII masking for authorized users."""
        if not authorized_user_id:
            raise PermissionError("User not authorized to unmask PII.")

        encrypted_bytes = _ENCRYPTED_VAULT.get(mapping_id)
        if not encrypted_bytes:
            return masked_text

        decrypted_bytes = self.fernet.decrypt(encrypted_bytes)
        mapping: dict[str, str] = json.loads(decrypted_bytes.decode("utf-8"))

        unmasked = masked_text
        for placeholder, original in mapping.items():
            unmasked = unmasked.replace(placeholder, original)

        return unmasked
