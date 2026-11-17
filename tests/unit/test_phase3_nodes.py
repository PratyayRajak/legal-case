"""Integration tests for Phase 3 pipeline nodes (Ingest, OCR, PII Mask)."""
from __future__ import annotations

from pipeline.nodes.stubs import IngestNode, OCRNode, PIIMaskNode
from tests.conftest import run_coro


class TestPhase3Nodes:
    def test_ingest_node_execution(self):
        node = IngestNode()
        state = {
            "pdf_path": "eval/data/docs/REV_001_HI.pdf",
            "doc_id": "REV_001_HI",
        }
        res = run_coro(node.run(state))
        assert res["ingest_status"] == "completed"
        assert res["total_pages"] == 1
        assert len(res["doc_hash"]) == 64

    def test_ocr_node_execution(self):
        node = OCRNode()
        state = {
            "pdf_path": "eval/data/docs/REV_001_EN.pdf",
            "doc_id": "REV_001_EN",
        }
        res = run_coro(node.run(state))
        assert res["ocr_status"] == "completed"
        assert res["ocr_result"].total_pages == 1
        assert res["overall_language"] == "en"

    def test_pii_node_execution(self):
        ocr_node = OCRNode()
        pii_node = PIIMaskNode()

        # Step 1: Run OCR on mixed document
        state = {
            "pdf_path": "eval/data/docs/REV_002_MIXED.pdf",
            "doc_id": "REV_002_MIXED",
        }
        ocr_state = run_coro(ocr_node.run(state))

        # Step 2: Run PII mask
        pii_state = run_coro(pii_node.run(ocr_state))
        assert pii_state["pii_status"] == "completed"
        assert len(pii_state["masked_pages"]) == 1
