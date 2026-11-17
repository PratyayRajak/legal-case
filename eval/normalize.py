"""Normalization utilities for Indian Court documents.

Handles:
1. Hindi (Devanagari) numerals (०-९) to ASCII (0-9).
2. Bilingual date parsing to ISO YYYY-MM-DD / YYYY-MM / YYYY.
3. Bilingual person names: transliteration key, honorific stripping, fuzzy matching.
4. Court case numbers canonicalization.
"""
from __future__ import annotations

import re
import unicodedata
from typing import NamedTuple

from app.schemas.canonical import CanonicalDate, CaseNumber, DatePrecision, PersonName

# ---------------------------------------------------------------------------
# 1. Hindi Numeral Normalization
# ---------------------------------------------------------------------------

DEVANAGARI_DIGITS = "०१२३४५६७८९"
ASCII_DIGITS = "0123456789"
_HINDI_TO_ASCII_MAP = str.maketrans(DEVANAGARI_DIGITS, ASCII_DIGITS)
_ASCII_TO_HINDI_MAP = str.maketrans(ASCII_DIGITS, DEVANAGARI_DIGITS)


def convert_hindi_digits_to_ascii(text: str) -> str:
    """Convert Devanagari numerals to ASCII digits."""
    return text.translate(_HINDI_TO_ASCII_MAP)


def convert_ascii_digits_to_hindi(text: str) -> str:
    """Convert ASCII digits to Devanagari numerals."""
    return text.translate(_ASCII_TO_HINDI_MAP)


# ---------------------------------------------------------------------------
# 2. Date Normalization
# ---------------------------------------------------------------------------

HINDI_MONTHS: dict[str, int] = {
    "जनवरी": 1,
    "फरवरी": 2,
    "फ़रवरी": 2,
    "मार्च": 3,
    "अप्रैल": 4,
    "मई": 5,
    "जून": 6,
    "जुलाई": 7,
    "अगस्त": 8,
    "सितंबर": 9,
    "सितम्बर": 9,
    "अक्टूबर": 10,
    "अक्तूबर": 10,
    "नवंबर": 11,
    "नवम्बर": 11,
    "दिसंबर": 12,
    "दिसम्बर": 12,
}

ENGLISH_MONTHS: dict[str, int] = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


def normalize_date(raw_date_str: str) -> CanonicalDate | None:
    """Parse various Hindi/English court date strings into CanonicalDate."""
    if not raw_date_str or not raw_date_str.strip():
        return None

    original = raw_date_str.strip()
    # Convert any Hindi digits to standard ascii
    text = convert_hindi_digits_to_ascii(original)
    text = re.sub(r"[\.,]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Pattern 1: ISO full date YYYY-MM-DD
    iso_match = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", text)
    if iso_match:
        year, month, day = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return CanonicalDate(
                iso_date=f"{year:04d}-{month:02d}-{day:02d}",
                precision=DatePrecision.full,
                original_string=original,
            )

    # Pattern 2: DD/MM/YYYY or DD-MM-YYYY
    slash_match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", text)
    if slash_match:
        day, month, year = int(slash_match.group(1)), int(slash_match.group(2)), int(slash_match.group(3))
        if 1 <= month <= 12 and 1 <= day <= 31:
            return CanonicalDate(
                iso_date=f"{year:04d}-{month:02d}-{day:02d}",
                precision=DatePrecision.full,
                original_string=original,
            )

    # Pattern 3: Date with word month, e.g. "15 मार्च 2024" or "15 March 2024" or "March 15, 2024"
    # Format: DD <month> YYYY
    dm_match = re.search(r"(\d{1,2})\s+([^\d\s]+)\s+(\d{4})", text)
    if dm_match:
        day = int(dm_match.group(1))
        month_str = dm_match.group(2).lower()
        year = int(dm_match.group(3))
        month_num = HINDI_MONTHS.get(month_str) or ENGLISH_MONTHS.get(month_str)
        if month_num and 1 <= day <= 31:
            return CanonicalDate(
                iso_date=f"{year:04d}-{month_num:02d}-{day:02d}",
                precision=DatePrecision.full,
                original_string=original,
            )

    # Format: <month> DD, YYYY
    md_match = re.search(r"([^\d\s]+)\s+(\d{1,2})\s+(\d{4})", text)
    if md_match:
        month_str = md_match.group(1).lower()
        day = int(md_match.group(2))
        year = int(md_match.group(3))
        month_num = HINDI_MONTHS.get(month_str) or ENGLISH_MONTHS.get(month_str)
        if month_num and 1 <= day <= 31:
            return CanonicalDate(
                iso_date=f"{year:04d}-{month_num:02d}-{day:02d}",
                precision=DatePrecision.full,
                original_string=original,
            )

    # Pattern 4: Month and Year only, e.g. "मार्च 2024", "March 2024"
    my_match = re.search(r"([^\d\s]+)\s+(\d{4})", text)
    if my_match:
        month_str = my_match.group(1).lower()
        year = int(my_match.group(2))
        month_num = HINDI_MONTHS.get(month_str) or ENGLISH_MONTHS.get(month_str)
        if month_num:
            return CanonicalDate(
                iso_date=f"{year:04d}-{month_num:02d}",
                precision=DatePrecision.month,
                original_string=original,
            )

    # Pattern 5: Year only, e.g. "2024"
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if year_match:
        year = int(year_match.group(1))
        return CanonicalDate(
            iso_date=f"{year:04d}",
            precision=DatePrecision.year,
            original_string=original,
        )

    return None


# ---------------------------------------------------------------------------
# 3. Person Name Normalization & Transliteration
# ---------------------------------------------------------------------------

HONORIFICS = [
    "shri", "shree", "sri", "smt", "shrimati", "smt.", "mr", "mr.", "mrs", "mrs.", "ms", "ms.",
    "adv", "adv.", "advocate", "dr", "dr.", "pandit", "pt", "pt.", "late",
    "श्री", "श्रीमती", "स्व.", "स्वर्गीय", "डॉ.", "डॉक्टर", "अधिवक्ता", "पं.", "पंडित"
]

DEVANAGARI_TO_LATIN = {
    "अ": "a", "आ": "aa", "इ": "i", "ई": "ee", "उ": "u", "ऊ": "oo", "ऋ": "ri",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au", "अं": "am", "अः": "ah",
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ng",
    "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "ny",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh", "ष": "sh", "स": "s", "ह": "h",
    "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "ृ": "ri", "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
    "्": "", "ं": "n", "ः": "h", "ँ": "n", "़": "",
}


def is_devanagari(text: str) -> bool:
    """Return True if text primarily contains Devanagari characters."""
    dev_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    return dev_count > 0 and (dev_count / max(1, len(text.replace(" ", "")))) >= 0.3


def transliterate_devanagari_to_ascii(text: str) -> str:
    """Simple phonetic transliteration of Devanagari text to normalized ASCII."""
    result = []
    i = 0
    while i < len(text):
        char = text[i]
        if char in DEVANAGARI_TO_LATIN:
            result.append(DEVANAGARI_TO_LATIN[char])
        elif "\u0900" <= char <= "\u097F":
            # skip unknown devanagari diacritics
            pass
        elif char.isalnum() or char.isspace():
            result.append(char)
        i += 1
    return "".join(result)


def make_transliteration_key(name: str) -> str:
    """Generate a lowercase, stripped, phonetic key for fuzzy matching."""
    cleaned = unicodedata.normalize("NFKD", name).lower()
    # Strip honorifics
    tokens = cleaned.split()
    filtered = [t for t in tokens if t not in HONORIFICS and t.rstrip(".") not in HONORIFICS]
    cleaned = " ".join(filtered) if filtered else cleaned
    latin_approx = transliterate_devanagari_to_ascii(cleaned) if is_devanagari(cleaned) else cleaned

    # Normalize vowels and consonants that often vary in transliteration
    norm = re.sub(r"[^a-z0-9\s]", "", latin_approx.lower())
    norm = re.sub(r"ee+", "i", norm)
    norm = re.sub(r"oo+", "u", norm)
    norm = re.sub(r"aa+", "a", norm)
    norm = re.sub(r"ph", "f", norm)
    norm = re.sub(r"sh", "s", norm)
    norm = re.sub(r"v", "w", norm)
    norm = re.sub(r"\s+", "_", norm.strip())
    return norm


def create_person_name(original: str, aliases: list[str] | None = None) -> PersonName:
    """Build a canonical PersonName model with transliteration key and script detection."""
    script = "devanagari" if is_devanagari(original) else "latin"
    t_key = make_transliteration_key(original)
    return PersonName(
        original=original.strip(),
        script=script,
        transliteration_key=t_key,
        aliases=aliases or [],
    )


def fuzzy_name_match(name1: str, name2: str, threshold: float = 0.75) -> bool:
    """Transliteration-aware fuzzy comparison between two names across Hindi & English."""
    k1 = make_transliteration_key(name1)
    k2 = make_transliteration_key(name2)
    if not k1 or not k2:
        return False
    if k1 == k2:
        return True

    # Token overlap (Jaccard similarity on tokens)
    tokens1 = set(k1.split("_"))
    tokens2 = set(k2.split("_"))
    overlap = len(tokens1 & tokens2) / max(len(tokens1 | tokens2), 1)
    if overlap >= threshold:
        return True

    # Character n-gram similarity (bigrams)
    def get_bigrams(s: str) -> set[str]:
        return {s[i:i+2] for i in range(len(s) - 1)}

    bg1 = get_bigrams(k1)
    bg2 = get_bigrams(k2)
    if not bg1 or not bg2:
        return False
    dice = (2.0 * len(bg1 & bg2)) / (len(bg1) + len(bg2))
    return dice >= threshold


# ---------------------------------------------------------------------------
# 4. Case Number Normalization
# ---------------------------------------------------------------------------

class ParsedCaseNumber(NamedTuple):
    case_type: str
    number: str
    year: int
    canonical_str: str


def normalize_case_number(raw_case_no: str) -> CaseNumber | None:
    """Canonicalize bilingual court case numbers into structured CaseNumber."""
    if not raw_case_no or not raw_case_no.strip():
        return None

    orig = raw_case_no.strip()
    ascii_text = convert_hindi_digits_to_ascii(orig)

    # Standard patterns:
    # 1. "Case No. 123/2024", "वाद संख्या 123/2024", "Appeal No. 45 of 2023"
    # 2. "123/2024", "45/23"
    pattern = r"(?:([a-zA-Z\u0900-\u097F\.\s]+)\s+)?(?:No\.|संख्या|सं\.)?\s*(\d+)[\s/]+(?:of\s+)?(\d{2,4})"
    match = re.search(pattern, ascii_text, re.IGNORECASE)

    if match:
        case_type_raw = match.group(1) or "general"
        case_type = case_type_raw.strip().lower()
        number = match.group(2)
        year_str = match.group(3)
        year = int(year_str)
        if year < 100:
            year += 2000 if year <= 40 else 1900

        # Canonical case type name
        if any(term in case_type for term in ["appeal", "अपील"]):
            norm_type = "appeal"
        elif any(term in case_type for term in ["mutation", "नामांतरण", "दाखिल खारिज"]):
            norm_type = "mutation"
        elif any(term in case_type for term in ["partition", "बँटवारा"]):
            norm_type = "partition"
        elif any(term in case_type for term in ["revision", "पुनरीक्षण"]):
            norm_type = "revision"
        else:
            norm_type = "case"

        return CaseNumber(
            case_type=norm_type,
            number=number,
            year=year,
            original_string=orig,
        )

    # Fallback pattern for simple "123/2024"
    simple_match = re.search(r"(\d+)/(\d{4})", ascii_text)
    if simple_match:
        return CaseNumber(
            case_type="case",
            number=simple_match.group(1),
            year=int(simple_match.group(2)),
            original_string=orig,
        )

    return None
