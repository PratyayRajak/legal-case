"""Tests for Phase 7 pipeline node: RulesCheckNode."""
from __future__ import annotations

from app.schemas.canonical import Citation, ExtractedField, Language
from pipeline.nodes.stubs import RulesCheckNode
from tests.conftest import run_coro


class TestPhase7Nodes:
    def test_rules_check_node_execution(self):
        node = RulesCheckNode()
        state = {
            "doc_id": "test_rules_doc",
            "extracted_fields": {
                "court_level": ExtractedField(
                    field="court_level",
                    value="district",
                    found=True,
                    confidence=0.95,
                    citations=[Citation(doc_id="test", page=1, snippet="जिलाधिकारी", lang=Language.hi)],
                ),
                "case_type": ExtractedField(
                    field="case_type",
                    value="revenue",
                    found=True,
                    confidence=0.95,
                    citations=[Citation(doc_id="test", page=1, snippet="राजस्व", lang=Language.hi)],
                ),
            },
        }
        res_state = run_coro(node.run(state))
        assert res_state["rules_status"] == "completed"
        assert "rules_results" in res_state
