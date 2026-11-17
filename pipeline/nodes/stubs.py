"""Stub pipeline nodes for Phase 1.

Each node listed in Section 6 of the spec is stubbed here.
Full implementations are built in Phases 3-6.
"""
from __future__ import annotations

from pipeline.nodes.base import PipelineNode, PipelineState


class IngestNode(PipelineNode):
    """Validate PDF, detect corruption, split pages. Phase 3."""

    node_name = "ingest"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "ingest_status": "stub"}


class OCRNode(PipelineNode):
    """Per-page OCR with confidence and bboxes. Phase 3."""

    node_name = "ocr"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "ocr_status": "stub"}


class PIIMaskNode(PipelineNode):
    """PII masking before any LLM call. Phase 3."""

    node_name = "pii_mask"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "pii_status": "stub"}


class ClassifyNode(PipelineNode):
    """Case type, document types, language mix classification. Phase 4."""

    node_name = "classify"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "classify_status": "stub"}


class ChunkIndexNode(PipelineNode):
    """Structure-aware chunking and BM25+vector indexing. Phase 4."""

    node_name = "chunk_index"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "chunk_status": "stub"}


class ExtractFieldsNode(PipelineNode):
    """Canonical field extraction with citations. Phase 5."""

    node_name = "extract_fields"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "extract_status": "stub"}


class NormalizeNode(PipelineNode):
    """Date normalization, name transliteration, glossary mapping. Phase 6."""

    node_name = "normalize"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "normalize_status": "stub"}


class ConflictCheckNode(PipelineNode):
    """Cross-document conflict detection. Phase 6."""

    node_name = "conflict_check"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "conflicts": []}


class RulesCheckNode(PipelineNode):
    """Deterministic rule evaluation on canonical fields. Phase 7."""

    node_name = "rules_check"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "rules_results": []}


class ConfidenceScoreNode(PipelineNode):
    """Combine OCR, retrieval, agreement scores. Phase 5."""

    node_name = "confidence_score"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "confidence_status": "stub"}


class AssembleBriefNode(PipelineNode):
    """Assemble final RevenueCaseBrief. Phase 5."""

    node_name = "assemble_brief"

    async def run(self, state: PipelineState) -> PipelineState:
        return {**state, "brief_status": "stub"}
