"""Translation interface (display only).

IMPORTANT: Translation is NEVER used for rule checking or extraction.
It is used ONLY for displaying snippets to users in their preferred language.
All translated outputs are labeled: 'translation, not original'.

Default: IndicTrans2 (self-hosted, supports Hindi ↔ English).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

TRANSLATION_DISCLAIMER = "translation, not original"


class Translator(ABC):
    """Abstract translation interface.

    Translation outputs must ALWAYS be labeled with TRANSLATION_DISCLAIMER.
    Never use translation output as input to rules or extraction.
    """

    @abstractmethod
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> str:
        """Translate text from source to target language."""
        ...

    @abstractmethod
    def supported_language_pairs(self) -> list[tuple[str, str]]:
        """Return list of (source, target) language code pairs supported."""
        ...


class StubTranslator(Translator):
    """Stub translator for testing. Returns text with a label."""

    async def translate(self, text: str, source_language: str, target_language: str) -> str:
        return f"[{TRANSLATION_DISCLAIMER}: {text}]"

    def supported_language_pairs(self) -> list[tuple[str, str]]:
        return [("hi", "en"), ("en", "hi")]
