"""Tests for Phase 4 pipeline nodes: ClassifyNode and ChunkIndexNode."""
from __future__ import annotations

from app.schemas.canonical import CourtLevel, DocumentType
from pipeline.interfaces.pii import MaskedDocument
from pipeline.nodes.stubs import ChunkIndexNode, ClassifyNode
from tests.conftest import run_coro


class TestPhase4Nodes:
    def test_classify_node_execution(self):
        node = ClassifyNode()
        state = {
            "doc_id": "test_doc_4",
            "masked_pages": [
                MaskedDocument(
                    masked_text="न्यायालय उप-जिलाधिकारी सदर लखनऊ। वाद पत्र अंतर्गत धारा 34।",
                    mapping_id="m1",
                    entities_found=[],
                    page_number=1,
                )
            ],
        }
        res_state = run_coro(node.run(state))
        assert res_state["classify_status"] == "completed"
        assert res_state["document_type"] == DocumentType.petition
        assert res_state["court_level"] == CourtLevel.district
        assert res_state["classification_language"] == "hi"

    def test_chunk_index_node_execution(self):
        node = ChunkIndexNode()
        state = {
            "doc_id": "test_doc_4",
            "masked_pages": [
                MaskedDocument(
                    masked_text="Page 1: न्यायालय उपजिलाधिकारी सदर। आदेश पत्रक।\n\nदिनांक 10-01-2024।",
                    mapping_id="m1",
                    entities_found=[],
                    page_number=1,
                ),
                MaskedDocument(
                    masked_text="Page 2: अंतिम आदेश। नामान्तरण प्रार्थना पत्र खारिज किया गया।",
                    mapping_id="m2",
                    entities_found=[],
                    page_number=2,
                ),
            ],
        }
        res_state = run_coro(node.run(state))
        assert res_state["chunk_status"] == "completed"
        assert res_state["total_chunks"] >= 2
        assert "retriever" in res_state

        # Query the indexed retriever
        retriever = res_state["retriever"]
        search_res = run_coro(retriever.search("खारिज आदेश", top_k=1))
        assert len(search_res) == 1
        assert search_res[0].chunk.page_number == 2
