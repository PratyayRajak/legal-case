"""Tests for Land Record Table Parser and CPC procedural rules."""
from __future__ import annotations

from pipeline.table_parser import LandRecordTableParser
from rules.engine import RulesEngine


class TestTableParser:
    def test_parse_khatauni_plots_and_areas(self) -> None:
        parser = LandRecordTableParser()
        sample_khatauni_text = """
        ग्राम: रामपुर परगना: सदर
        खतौनी खाता संख्या: 124
        गाटा संख्या: 142/1 क्षेत्रफल: 0.4500 हेक्टेयर
        खातेदार का नाम: रामकुमार पुत्र शिवपाल
        गाटा संख्या: 142/2 क्षेत्रफल: 0.2300 हेक्टेयर
        खातेदार का नाम: सुरेश कुमार
        """
        res = parser.parse_page_table(sample_khatauni_text, doc_id="TEST_KHATAUNI", page_number=1)
        assert res.raw_table_found is True
        assert res.total_plots == 2
        assert res.entries[0].khasra_number == "142/1"
        assert res.entries[0].area_hectares == 0.45
        assert len(res.entries[0].landholders) >= 1
        assert "रामकुमार" in res.entries[0].landholders[0]

    def test_parse_devanagari_numerals_in_land_records(self) -> None:
        parser = LandRecordTableParser()
        # Text with Devanagari numerals: गाटा संख्या: १४५/३ क्षेत्रफल: ०.५२०० हेक्टेयर
        text = "खसरा संख्या: १४५/३ क्षेत्रफल: ०.५२०० हेक्टेयर खातेदार: महेश"
        res = parser.parse_page_table(text)
        assert res.total_plots == 1
        assert res.entries[0].khasra_number == "145/3"
        assert res.entries[0].area_hectares == 0.52


class TestCPCRules:
    def test_cpc_rules_load_and_evaluate(self) -> None:
        engine = RulesEngine()
        # Evaluate with draft CPC rules enabled
        case_data = {
            "case_type": {"value": "civil", "found": True},
            "current_status": {"value": "pending", "found": True},
            "filing_date": {"value": "2023-01-01", "found": True},
            "next_hearing_date": {"value": "2023-04-01", "found": True},
        }
        results = engine.evaluate(case_data, active_only=False)
        rule_ids = [r.rule_id for r in results]
        assert "R_CPC_O7_R11_CAUSE_OF_ACTION" in rule_ids
        assert "R_LIMITATION_ACT_SEC5_CONDONATION" in rule_ids
