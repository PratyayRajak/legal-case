"""Stub pipeline nodes for Phase 1.

Each node listed in Section 6 of the spec is stubbed here.
Full implementations are built in Phases 3-6.
"""
from __future__ import annotations

from pipeline.assembler import assemble_revenue_brief
from pipeline.chunker import StructureAwareChunker
from pipeline.classifier import CourtDocumentClassifier
from pipeline.conflicts import CrossDocumentConflictDetector
from pipeline.extractor import CanonicalFieldExtractor
from pipeline.ingest import ingest_pdf
from pipeline.nodes.base import PipelineNode, PipelineState
from pipeline.normalizer import CanonicalNormalizer
from pipeline.ocr_engine import HybridCourtOCREngine
from pipeline.pii_masker import IndianCourtPIIMasker
from pipeline.retriever import HybridRetriever
from rules.engine import RulesEngine


class IngestNode(PipelineNode):
    """Validate PDF, detect corruption, split pages and record metadata. Phase 3."""

    node_name = "ingest"

    async def run(self, state: PipelineState) -> PipelineState:
        pdf_path = state.get("pdf_path")
        doc_id = state.get("doc_id", "unnamed_doc")
        if not pdf_path:
            return {**state, "ingest_status": "skipped", "error": "No pdf_path in state"}

        ingest_res = ingest_pdf(pdf_path, doc_id)
        return {
            **state,
            "doc_id": doc_id,
            "doc_hash": ingest_res.doc_hash,
            "total_pages": ingest_res.total_pages,
            "pages_meta": ingest_res.pages_meta,
            "file_size_bytes": ingest_res.file_size_bytes,
            "ingest_status": "completed",
        }


class OCRNode(PipelineNode):
    """Per-page OCR with word confidence, bounding boxes, and language detection. Phase 3."""

    node_name = "ocr"

    def __init__(self, ocr_engine: HybridCourtOCREngine | None = None) -> None:
        self.ocr_engine = ocr_engine or HybridCourtOCREngine()

    async def run(self, state: PipelineState) -> PipelineState:
        pdf_path = state.get("pdf_path")
        doc_id = state.get("doc_id", "unnamed_doc")
        if not pdf_path:
            return {**state, "ocr_status": "skipped"}

        ocr_result = self.ocr_engine.process_document(pdf_path, doc_id)
        return {
            **state,
            "ocr_result": ocr_result,
            "overall_language": ocr_result.overall_language,
            "ocr_status": "completed",
        }


class PIIMaskNode(PipelineNode):
    """PII masking with custom Indian recognizers before any model or log call. Phase 3."""

    node_name = "pii_mask"

    def __init__(self, masker: IndianCourtPIIMasker | None = None) -> None:
        self.masker = masker or IndianCourtPIIMasker()

    async def run(self, state: PipelineState) -> PipelineState:
        ocr_result = state.get("ocr_result")
        doc_id = state.get("doc_id", "unnamed_doc")
        if not ocr_result:
            return {**state, "pii_status": "skipped"}

        masked_pages = []
        all_entities = []

        for page_res in ocr_result.page_results:
            masked_doc = self.masker.mask(
                text=page_res.full_text,
                page_number=page_res.page_number,
                doc_id=doc_id,
            )
            masked_pages.append(masked_doc)
            all_entities.extend(masked_doc.entities_found)

        return {
            **state,
            "masked_pages": masked_pages,
            "pii_entities_detected": list(set(all_entities)),
            "pii_status": "completed",
        }


class ClassifyNode(PipelineNode):
    """Case type, document types, language mix classification. Phase 4."""

    node_name = "classify"

    def __init__(self, classifier: CourtDocumentClassifier | None = None) -> None:
        self.classifier = classifier or CourtDocumentClassifier()

    async def run(self, state: PipelineState) -> PipelineState:
        masked_pages = state.get("masked_pages")
        ocr_result = state.get("ocr_result")
        doc_id = str(state.get("doc_id", "doc"))

        combined_text = ""
        if masked_pages:
            combined_text = "\n\n".join(mp.masked_text for mp in masked_pages)
        elif ocr_result:
            combined_text = "\n\n".join(pr.full_text for pr in ocr_result.page_results)

        if not combined_text:
            return {**state, "classify_status": "skipped", "error": "No text available for classification"}

        result = self.classifier.classify_text(combined_text, doc_id=doc_id)
        return {
            **state,
            "document_type": result.document_type,
            "court_level": result.court_level,
            "case_type": result.case_type,
            "classification_language": result.language,
            "classification_confidence": result.confidence,
            "indicators_found": result.indicators_found,
            "classify_status": "completed",
        }


class ChunkIndexNode(PipelineNode):
    """Structure-aware chunking and BM25+vector indexing. Phase 4."""

    node_name = "chunk_index"

    def __init__(
        self,
        chunker: StructureAwareChunker | None = None,
        retriever: HybridRetriever | None = None,
    ) -> None:
        self.chunker = chunker or StructureAwareChunker()
        self.retriever = retriever or HybridRetriever()

    async def run(self, state: PipelineState) -> PipelineState:
        masked_pages = state.get("masked_pages")
        ocr_result = state.get("ocr_result")
        doc_id = str(state.get("doc_id", "doc"))

        pages: list[str] = []
        if masked_pages:
            pages = [mp.masked_text for mp in masked_pages]
        elif ocr_result:
            pages = [pr.full_text for pr in ocr_result.page_results]

        if not pages:
            return {**state, "chunk_status": "skipped", "error": "No pages to chunk"}

        chunks = self.chunker.chunk_document(pages, doc_id=doc_id)
        await self.retriever.index_chunks(chunks)

        return {
            **state,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "retriever": self.retriever,
            "chunk_status": "completed",
        }


class ExtractFieldsNode(PipelineNode):
    """Canonical field extraction with citations and two-pass consensus. Phase 5."""

    node_name = "extract_fields"

    def __init__(self, extractor: CanonicalFieldExtractor | None = None) -> None:
        self.extractor = extractor or CanonicalFieldExtractor()

    async def run(self, state: PipelineState) -> PipelineState:
        masked_pages = state.get("masked_pages")
        ocr_result = state.get("ocr_result")
        doc_id = str(state.get("doc_id", "doc"))
        lang = str(state.get("overall_language") or state.get("classification_language") or "hi")

        pages_text: dict[int, str] = {}
        if masked_pages:
            for mp in masked_pages:
                pages_text[mp.page_number] = mp.masked_text
        elif ocr_result:
            for pr in ocr_result.page_results:
                pages_text[pr.page_number] = pr.full_text

        if not pages_text:
            return {**state, "extract_status": "skipped", "error": "No page text available for extraction"}

        extracted_fields = await self.extractor.extract_fields(
            pages_text=pages_text,
            doc_id=doc_id,
            overall_lang=lang,
        )

        return {
            **state,
            "extracted_fields": extracted_fields,
            "extract_status": "completed",
        }


class NormalizeNode(PipelineNode):
    """Date normalization, name transliteration, glossary mapping. Phase 6."""

    node_name = "normalize"

    def __init__(self, normalizer: CanonicalNormalizer | None = None) -> None:
        self.normalizer = normalizer or CanonicalNormalizer()

    async def run(self, state: PipelineState) -> PipelineState:
        extracted = state.get("extracted_fields", {})
        if not extracted:
            return {**state, "normalize_status": "skipped", "error": "No extracted_fields in state"}

        normalized = self.normalizer.normalize_all(extracted)
        return {
            **state,
            "extracted_fields": normalized,
            "normalize_status": "completed",
        }


class ConflictCheckNode(PipelineNode):
    """Cross-document conflict detection. Phase 6."""

    node_name = "conflict_check"

    def __init__(self, detector: CrossDocumentConflictDetector | None = None) -> None:
        self.detector = detector or CrossDocumentConflictDetector()

    async def run(self, state: PipelineState) -> PipelineState:
        masked_pages = state.get("masked_pages")
        ocr_result = state.get("ocr_result")
        extracted_fields = state.get("extracted_fields", {})
        doc_id = str(state.get("doc_id", "doc"))

        pages_text: dict[int, str] = {}
        if masked_pages:
            for mp in masked_pages:
                pages_text[mp.page_number] = mp.masked_text
        elif ocr_result:
            for pr in ocr_result.page_results:
                pages_text[pr.page_number] = pr.full_text

        report = self.detector.detect_conflicts(
            pages_text=pages_text,
            extracted_fields=extracted_fields,
            doc_id=doc_id,
        )

        return {
            **state,
            "conflict_report": report,
            "conflicts": report.conflicts,
            "total_conflicts": report.total_conflicts,
            "has_blocking_conflicts": report.has_blocking,
            "conflict_status": "completed",
        }


class RulesCheckNode(PipelineNode):
    """Deterministic rule evaluation on canonical fields. Phase 7."""

    node_name = "rules_check"

    def __init__(self, engine: RulesEngine | None = None) -> None:
        self.engine = engine or RulesEngine()

    async def run(self, state: PipelineState) -> PipelineState:
        extracted = state.get("extracted_fields", {})
        if not extracted:
            return {**state, "rules_results": [], "rules_status": "skipped"}

        rule_results = self.engine.evaluate(
            canonical_fields=extracted, active_only=False
        )
        return {
            **state,
            "rules_results": rule_results,
            "total_rules_evaluated": len(rule_results),
            "rules_status": "completed",
        }


class ConfidenceScoreNode(PipelineNode):
    """Combine OCR, retrieval, and extraction agreement scores. Phase 5."""

    node_name = "confidence_score"

    async def run(self, state: PipelineState) -> PipelineState:
        extracted = state.get("extracted_fields", {})
        if not extracted:
            return {**state, "confidence_score": 0.0, "confidence_status": "skipped"}

        found_confs = [
            f.confidence for f in extracted.values() if hasattr(f, "confidence") and f.found
        ]
        avg_conf = sum(found_confs) / len(found_confs) if found_confs else 1.0
        return {
            **state,
            "overall_confidence": round(avg_conf, 2),
            "confidence_status": "completed",
        }


class AssembleBriefNode(PipelineNode):
    """Assemble final RevenueCaseBrief with audit provenance and disclaimer. Phase 5."""

    node_name = "assemble_brief"

    async def run(self, state: PipelineState) -> PipelineState:
        doc_id = str(state.get("doc_id", "doc"))
        extracted_fields = state.get("extracted_fields", {})

        brief = assemble_revenue_brief(
            doc_id=doc_id,
            extracted_fields=extracted_fields,
        )

        return {
            **state,
            "case_brief": brief,
            "brief_status": "completed",
            "disclaimer": brief.disclaimer,
        }
