"""Document classification for Indian Court files.

Classifies:
1. Document Type: petition, order_sheet, judgment, annexure, notice, other
2. Case Type: revenue, civil, criminal (v1 default: revenue)
3. Court Level: district, high, supreme, tribunal, other
4. Language Mix: hi, en, mixed
"""
from __future__ import annotations

from dataclasses import dataclass

from app.schemas.canonical import CourtLevel, DocumentType
from glossary.loader import GlossaryLoader

# Key legal section markers in Hindi and English
_DOC_TYPE_INDICATORS: dict[DocumentType, list[str]] = {
    DocumentType.petition: [
        "वाद पत्र",
        "प्रार्थना पत्र",
        "याचिका",
        "अर्जी",
        "plaint",
        "petition",
        "application under",
        "written statement",
    ],
    DocumentType.order_sheet: [
        "आदेश पत्रक",
        "आदेश पत्र",
        "कार्यवाही",
        "रोजगार",
        "order sheet",
        "proceedings",
        "minute of order",
    ],
    DocumentType.judgment: [
        "निर्णय",
        "अंतिम आदेश",
        "फैसला",
        "judgment",
        "final order",
        "decree",
    ],
    DocumentType.notice: [
        "सूचना पत्र",
        "नोटिस",
        "समन",
        "इश्तेहार",
        "notice",
        "summons",
        "citation",
    ],
    DocumentType.annexure: [
        "संलग्नक",
        "अनुबंध",
        "खतौनी",
        "नकल",
        "annexure",
        "exhibit",
        "schedule",
    ],
}

_COURT_LEVEL_INDICATORS: dict[CourtLevel, list[str]] = {
    CourtLevel.district: [
        "उप-जिलाधिकारी",
        "उपजिलाधिकारी",
        "तहसीलदार",
        "जिलाधिकारी",
        "कलेक्टर",
        "सदर",
        "sub-divisional magistrate",
        "sdm",
        "tehsildar",
        "district magistrate",
        "collector",
        "district court",
    ],
    CourtLevel.high: [
        "उच्च न्यायालय",
        "हाई कोर्ट",
        "high court",
        "allahabad high court",
    ],
    CourtLevel.supreme: [
        "सर्वोच्च न्यायालय",
        "उच्चतम न्यायालय",
        "सुप्रीम कोर्ट",
        "supreme court of india",
    ],
    CourtLevel.tribunal: [
        "राजस्व परिषद",
        "बोर्ड ऑफ रेवेन्यू",
        "न्यायाधिकरण",
        "board of revenue",
        "tribunal",
    ],
}


@dataclass
class ClassificationResult:
    doc_id: str
    document_type: DocumentType
    court_level: CourtLevel
    case_type: str  # e.g., "revenue"
    language: str  # "hi", "en", "mixed"
    confidence: float
    indicators_found: list[str]


class CourtDocumentClassifier:
    """Heuristic and glossary-anchored classifier for Indian court records."""

    def __init__(self, glossary: GlossaryLoader | None = None) -> None:
        self.glossary = glossary or GlossaryLoader()

    def classify_text(self, text: str, doc_id: str = "doc") -> ClassificationResult:
        """Classify court document based on its initial pages or complete text."""
        # Use first 3000 characters for high-density header classification
        header_text = text[:3000].lower()
        full_lower = text.lower()

        # 1. Detect Document Type
        doc_type = DocumentType.other
        highest_type_matches = 0
        indicators_found: list[str] = []

        for dtype, patterns in _DOC_TYPE_INDICATORS.items():
            matches = [p for p in patterns if p in header_text or p in full_lower]
            if len(matches) > highest_type_matches:
                highest_type_matches = len(matches)
                doc_type = dtype
                indicators_found = matches

        # 2. Detect Court Level
        court_level = CourtLevel.district
        highest_court_matches = 0
        for clevel, patterns in _COURT_LEVEL_INDICATORS.items():
            matches = [p for p in patterns if p in header_text]
            if len(matches) > highest_court_matches:
                highest_court_matches = len(matches)
                court_level = clevel

        # 3. Detect Language Mix
        devanagari_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
        latin_count = sum(1 for ch in text if "a" <= ch.lower() <= "z")
        total = devanagari_count + latin_count

        if total == 0:
            language = "unknown"
        elif devanagari_count / total >= 0.80:
            language = "hi"
        elif latin_count / total >= 0.80:
            language = "en"
        else:
            language = "mixed"

        # Confidence calculation
        confidence = 0.5
        if highest_type_matches > 0:
            confidence += min(0.4, highest_type_matches * 0.15)
        if highest_court_matches > 0:
            confidence += 0.1

        return ClassificationResult(
            doc_id=doc_id,
            document_type=doc_type,
            court_level=court_level,
            case_type="revenue",  # v1 default
            language=language,
            confidence=round(min(1.0, confidence), 2),
            indicators_found=indicators_found,
        )
