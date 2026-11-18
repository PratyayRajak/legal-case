"""Tests for Phase 5 pipeline nodes: ExtractFieldsNode, ConfidenceScoreNode, AssembleBriefNode."""
from __future__ import annotations

from pipeline.interfaces.pii import MaskedDocument
from pipeline.nodes.stubs import (
    AssembleBriefNode,
    ConfidenceScoreNode,
    ExtractFieldsNode,
)
from tests.conftest import run_coro


class TestPhase5Nodes:
    def test_full_phase5_node_flow(self):
        extract_node = ExtractFieldsNode()
        conf_node = ConfidenceScoreNode()
        assemble_node = AssembleBriefNode()

        initial_state = {
            "doc_id": "rev_test_5",
            "overall_language": "hi",
            "masked_pages": [
                MaskedDocument(
                    masked_text=(
                        "न्यायालय उप-जिलाधिकारी, सदर, जनपद लखनऊ\n"
                        "वाद संख्या: 104 / 2024\n"
                        "विषय: नामांतरण प्रार्थना पत्र\n"
                        "वादी: <PERSON_1>\n"
                        "प्रतिवादी: <PERSON_2>\n"
                        "दायर करने की तिथि: 15/01/2024\n"
                        "आवेदन खारिज किया जाता है।"
                    ),
                    mapping_id="m1",
                    entities_found=["PERSON"],
                    page_number=1,
                )
            ],
        }

        # 1. Run ExtractFieldsNode
        state_after_extract = run_coro(extract_node.run(initial_state))
        assert state_after_extract["extract_status"] == "completed"
        extracted = state_after_extract["extracted_fields"]
        assert "case_number" in extracted
        assert extracted["case_number"].found is True

        # 2. Run ConfidenceScoreNode
        state_after_conf = run_coro(conf_node.run(state_after_extract))
        assert state_after_conf["confidence_status"] == "completed"
        assert state_after_conf["overall_confidence"] > 0.70

        # 3. Run AssembleBriefNode
        final_state = run_coro(assemble_node.run(state_after_conf))
        assert final_state["brief_status"] == "completed"
        brief = final_state["case_brief"]
        assert brief.doc_id == "rev_test_5"
        assert brief.case_number.found is True
        assert "AI-assisted summary. Verify against the source document." in brief.disclaimer
