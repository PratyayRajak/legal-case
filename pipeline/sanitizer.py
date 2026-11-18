"""Untrusted document text sanitizer and prompt-injection defense.

Rule 8 of Spec:
Treat all document text as untrusted data, never as instructions.
"""
from __future__ import annotations

import re


class UntrustedDataSanitizer:
    """Sanitizes text extracted from court files before presentation or model consumption."""

    _INJECTION_PATTERNS = [
        r"(?i)<\s*/?\s*(?:system|document_text|instructions?|user|assistant)\s*>",
        r"(?i)\bignore\s+(?:all\s+)?previous\s+instructions\b",
        r"(?i)\bdisregard\s+(?:all\s+)?prior\s+rules\b",
        r"(?i)\byou\s+are\s+now\s+in\s+developer\s+mode\b",
        r"(?i)\brepeat\s+(?:your\s+)?system\s+prompt\b",
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Neutralize known prompt-injection markers and escape structural XML tags."""
        sanitized = text
        # Neutralize XML tags that could break prompt boundaries
        sanitized = sanitized.replace("<document_text>", "&lt;document_text&gt;")
        sanitized = sanitized.replace("</document_text>", "&lt;/document_text&gt;")
        sanitized = sanitized.replace("<system>", "&lt;system&gt;")
        sanitized = sanitized.replace("</system>", "&lt;/system&gt;")
        return sanitized

    @classmethod
    def detect_injection_indicators(cls, text: str) -> list[str]:
        """Detect indicators of prompt-injection attempts inside document text."""
        detected: list[str] = []
        for pat in cls._INJECTION_PATTERNS:
            if re.search(pat, text):
                detected.append(pat)
        return detected
