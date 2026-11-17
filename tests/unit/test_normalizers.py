"""Tests for normalization utilities."""
from __future__ import annotations

from app.schemas.canonical import DatePrecision
from eval.normalize import (
    convert_ascii_digits_to_hindi,
    convert_hindi_digits_to_ascii,
    create_person_name,
    fuzzy_name_match,
    is_devanagari,
    make_transliteration_key,
    normalize_case_number,
    normalize_date,
)


class TestHindiNumerals:
    def test_hindi_to_ascii(self):
        assert convert_hindi_digits_to_ascii("०१२३४५६७८९") == "0123456789"
        assert convert_hindi_digits_to_ascii("वाद सं. १०४/२०२४") == "वाद सं. 104/2024"

    def test_ascii_to_hindi(self):
        assert convert_ascii_digits_to_hindi("0123456789") == "०१२३४५६७८९"
        assert convert_ascii_digits_to_hindi("15/01/2024") == "१५/०१/२०२४"


class TestDateNormalizer:
    def test_iso_date(self):
        d = normalize_date("2024-03-15")
        assert d is not None
        assert d.iso_date == "2024-03-15"
        assert d.precision == DatePrecision.full

    def test_slash_date(self):
        d = normalize_date("15/03/2024")
        assert d is not None
        assert d.iso_date == "2024-03-15"
        assert d.precision == DatePrecision.full

    def test_hindi_date_string(self):
        d = normalize_date("१५ मार्च २०२४")
        assert d is not None
        assert d.iso_date == "2024-03-15"
        assert d.precision == DatePrecision.full

    def test_english_date_string(self):
        d = normalize_date("15 January 2024")
        assert d is not None
        assert d.iso_date == "2024-01-15"

    def test_month_year_only(self):
        d = normalize_date("मार्च 2024")
        assert d is not None
        assert d.iso_date == "2024-03"
        assert d.precision == DatePrecision.month

    def test_year_only(self):
        d = normalize_date("2024")
        assert d is not None
        assert d.iso_date == "2024"
        assert d.precision == DatePrecision.year

    def test_invalid_date_returns_none(self):
        assert normalize_date("invalid date string") is None
        assert normalize_date("") is None


class TestPersonNameNormalizer:
    def test_devanagari_detection(self):
        assert is_devanagari("राम कुमार शर्मा") is True
        assert is_devanagari("Ram Kumar Sharma") is False

    def test_transliteration_key_generation(self):
        k1 = make_transliteration_key("राम कुमार शर्मा")
        k2 = make_transliteration_key("Ram Kumar Sharma")
        assert "ram" in k1
        assert "kumar" in k1
        assert "ram" in k2
        assert "kumar" in k2

    def test_honorific_stripping(self):
        k1 = make_transliteration_key("श्री राम कुमार")
        k2 = make_transliteration_key("Mr. Ram Kumar")
        assert "shri" not in k1
        assert "mr" not in k2
        assert k1 == k2

    def test_fuzzy_name_match_bilingual(self):
        # Cross-script matching: Hindi vs English spelling
        assert fuzzy_name_match("राम कुमार शर्मा", "Ram Kumar Sharma") is True
        assert fuzzy_name_match("मोहन लाल वर्मा", "Mohan Lal Verma") is True
        assert fuzzy_name_match("Suresh Chandra", "सुरेश चंद्र") is True

    def test_fuzzy_name_match_distinct_names(self):
        assert fuzzy_name_match("राम कुमार", "मोहन लाल") is False

    def test_create_person_name(self):
        pn = create_person_name("राम कुमार", aliases=["R.K."])
        assert pn.script == "devanagari"
        assert pn.transliteration_key == "ram_kumar"
        assert pn.aliases == ["R.K."]


class TestCaseNumberNormalizer:
    def test_case_number_hindi(self):
        cn = normalize_case_number("वाद संख्या: १०४ / २०२४")
        assert cn is not None
        assert cn.number == "104"
        assert cn.year == 2024

    def test_case_number_english(self):
        cn = normalize_case_number("Case No. 104 of 2024")
        assert cn is not None
        assert cn.number == "104"
        assert cn.year == 2024

    def test_appeal_number(self):
        cn = normalize_case_number("Appeal No. 55/2022")
        assert cn is not None
        assert cn.case_type == "appeal"
        assert cn.number == "55"
        assert cn.year == 2022

    def test_invalid_case_number(self):
        assert normalize_case_number("not a case number") is None
