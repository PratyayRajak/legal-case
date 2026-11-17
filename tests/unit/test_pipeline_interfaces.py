"""Tests for pipeline interface stubs."""
from __future__ import annotations

from pipeline.interfaces.embedder import StubEmbedder
from pipeline.interfaces.llm import LLMMessage, StubLLMClient
from pipeline.interfaces.ocr import StubOCREngine
from pipeline.interfaces.pii import StubPIIMasker
from pipeline.interfaces.translator import TRANSLATION_DISCLAIMER, StubTranslator
from pipeline.nodes.stubs import AssembleBriefNode, IngestNode, OCRNode
from tests.conftest import run_coro


class TestStubLLMClient:
    def test_complete_returns_response(self):
        client = StubLLMClient()
        msg = LLMMessage(role="user", content="test")
        resp = run_coro(client.complete([msg]))
        assert resp.content == '{"result": "stub"}'
        assert resp.model == "stub"

    def test_is_available(self):
        assert StubLLMClient().is_available() is True

    def test_custom_response(self):
        client = StubLLMClient(fixed_response='{"field": "value"}')
        msg = LLMMessage(role="user", content="x")
        resp = run_coro(client.complete([msg]))
        assert resp.content == '{"field": "value"}'


class TestStubOCREngine:
    def test_process_document(self):
        engine = StubOCREngine()
        result = engine.process_document("fake.pdf", "doc1")
        assert result.doc_id == "doc1"
        assert result.total_pages == 1
        assert len(result.page_results) == 1

    def test_process_page(self):
        engine = StubOCREngine()
        page = engine.process_page("fake.pdf", 1)
        assert page.page_number == 1
        assert page.full_text == "[STUB OCR TEXT]"

    def test_get_engine_name(self):
        assert "Stub" in StubOCREngine().get_engine_name()


class TestStubEmbedder:
    def test_embed_returns_vectors(self):
        embedder = StubEmbedder()
        vecs = run_coro(embedder.embed(["hello", "world"]))
        assert len(vecs) == 2
        assert len(vecs[0]) == embedder.get_dimension()

    def test_dimension(self):
        assert StubEmbedder().get_dimension() == 128


class TestStubPIIMasker:
    def test_mask_returns_same_text(self):
        masker = StubPIIMasker()
        result = masker.mask("My Aadhaar is 1234", page_number=1, doc_id="doc1")
        assert result.masked_text == "My Aadhaar is 1234"
        assert result.entities_found == []

    def test_unmask_returns_text(self):
        masker = StubPIIMasker()
        assert masker.unmask("text", "mapping-1", "user-1") == "text"


class TestStubTranslator:
    def test_translate_adds_disclaimer(self):
        t = StubTranslator()
        result = run_coro(t.translate("hello", "en", "hi"))
        assert TRANSLATION_DISCLAIMER in result

    def test_supported_pairs(self):
        pairs = StubTranslator().supported_language_pairs()
        assert ("hi", "en") in pairs
        assert ("en", "hi") in pairs


class TestPipelineNodes:
    def test_ingest_node(self):
        node = IngestNode()
        result = run_coro(node.run({"doc_id": "test"}))
        assert "ingest_status" in result

    def test_ocr_node(self):
        node = OCRNode()
        result = run_coro(node.run({}))
        assert "ocr_status" in result

    def test_assemble_brief_node(self):
        node = AssembleBriefNode()
        result = run_coro(node.run({}))
        assert "brief_status" in result
