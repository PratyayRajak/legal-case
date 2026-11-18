"""Tests for Phase 6 pipeline nodes: NormalizeNode and ConflictCheckNode."""
from __future__ import annotations

from app.schemas.canonical import CaseStatus, Citation, ExtractedField, Language
from pipeline.nodes.stubs import ConflictCheckNode, NormalizeNode
from tests.conftest import run_coro


class TestPhase6Nodes:
    def test_normalize_node_execution(self):
        node = NormalizeNode()
        state = {
            "doc_id": "doc_norm_1",
            "extracted_fields": {
                "current_status": ExtractedField(
                    field="current_status",
                    value="खारिज",
                    found=True,
                    confidence=0.9,
                    citations=[Citation(doc_id="doc_norm_1", page=1, snippet="खारिज", lang=Language.hi)],
                )
            },
        }
        res_state = run_coro(node.run(state))
        assert res_state["normalize_status"] == "completed"
        norm_status = res_state["extracted_fields"]["current_status"].value
        assert norm_status == CaseStatus.rejected

    def test_conflict_node_execution(self):
        node = ConflictCheckNode()
        state = {
            "doc_id": "doc_conf_1",
            "extracted_fields": {
                "case_number": ExtractedField(
                    field="case_number",
                    value={"number": "101", "year": 2024},
                    found=True,
                    citations=[Citation(doc_id="doc_conf_1", page=1, snippet="101/2024", lang=Language.hi)],
                )
            },
            "masked_pages": [
                type("MaskedDoc", (), {"page_number": 1, "masked_text": "वाद संख्या 101/2024"}),
                type("MaskedDoc", (), {"page_number": 2, "masked_text": "वाद संख्या 999/2024"}),
            ],
        }
        res_state = run_coro(node.run(state))
        assert res_state["conflict_status"] == "completed"
        assert res_state["total_conflicts"] >= 1
        assert res_state["has_blocking_conflicts"] is True
