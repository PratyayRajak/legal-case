"""Tests for Canonical Field Extractor and Citation Verification."""
from __future__ import annotations

from pipeline.extractor import (
    CanonicalFieldExtractor,
    DeterministicExtractor,
    verify_citation_in_page,
)
from tests.conftest import run_coro


class TestCitationVerification:
    def test_verbatim_citation_found(self):
        page_text = "न्यायालय उप-जिलाधिकारी, सदर, लखनऊ। वाद संख्या: 104 / 2024।"
        snippet = "वाद संख्या: 104 / 2024"
        assert verify_citation_in_page(snippet, page_text) is True

    def test_whitespace_normalized_citation_found(self):
        page_text = "वादी:   राम   कुमार\nशर्मा"
        snippet = "वादी: राम कुमार शर्मा"
        assert verify_citation_in_page(snippet, page_text) is True

    def test_missing_snippet_returns_false(self):
        page_text = "पत्रावली पेश हुई। आदेश किया गया।"
        snippet = "वाद खारिज किया जाता है।"
        assert verify_citation_in_page(snippet, page_text) is False


class TestDeterministicExtractor:
    def test_extract_hindi_case(self):
        extractor = DeterministicExtractor()
        pages = {
            1: (
                "न्यायालय उप-जिलाधिकारी / परगनाधिकारी, सदर, जनपद लखनऊ\n"
                "वाद संख्या: 104 / 2024\n"
                "विषय: नामांतरण प्रार्थना पत्र\n"
                "वादी: राम कुमार शर्मा\n"
                "प्रतिवादी: मोहन लाल वर्मा\n"
                "दायर करने की तिथि: 15/01/2024\n"
                "आदेश: वादी द्वारा साक्ष्य न देने पर आवेदन खारिज किया जाता है।\n"
            )
        }
        res = extractor.extract(pages, doc_id="rev_001")

        assert res["case_number"]["found"] is True
        assert res["case_number"]["value"]["number"] == "104"
        assert res["case_number"]["value"]["year"] == 2024

        assert res["court_name"]["found"] is True
        assert res["court_level"]["value"] == "district"

        assert res["proceeding_type"]["found"] is True
        assert res["proceeding_type"]["value"] == "mutation"

        assert res["petitioners"]["found"] is True
        assert res["petitioners"]["value"][0]["original"] == "राम कुमार शर्मा"

        assert res["respondents"]["found"] is True
        assert res["respondents"]["value"][0]["original"] == "मोहन लाल वर्मा"

        assert res["filing_date"]["found"] is True
        assert res["filing_date"]["value"]["iso_date"] == "2024-01-15"

        assert res["current_status"]["found"] is True
        assert res["current_status"]["value"] == "rejected"

        assert res["next_hearing_date"]["found"] is False


class TestCanonicalFieldExtractor:
    def test_two_pass_extraction_with_citations(self):
        extractor = CanonicalFieldExtractor()
        pages = {
            1: (
                "In the Court of Sub-Divisional Magistrate, Sadar, Lucknow\n"
                "Case No. 104 / 2024\n"
                "Mutation Proceeding\n"
                "Petitioner: Ram Kumar Sharma\n"
                "Respondent: Mohan Lal Verma\n"
                "Filing Date: 15-01-2024\n"
                "Final Order: The petition is dismissed for default.\n"
            )
        }
        fields = run_coro(extractor.extract_fields(pages, doc_id="rev_002", overall_lang="en"))

        assert "case_number" in fields
        cn = fields["case_number"]
        assert cn.found is True
        assert len(cn.citations) > 0
        assert cn.citations[0].page == 1
        assert "104" in cn.citations[0].snippet

        # Absent field preference
        nhd = fields["next_hearing_date"]
        assert nhd.found is False
        assert nhd.value is None
        assert nhd.confidence == 1.0  # Confident it's absent
        assert len(nhd.citations) == 0
