"""Tests for Hybrid Retriever with BM25, Dense Embeddings, and RRF."""
from __future__ import annotations

import pytest

from pipeline.chunker import Chunk
from pipeline.interfaces.embedder import Embedder
from pipeline.retriever import (
    BM25Index,
    HybridRetriever,
    cosine_similarity,
    tokenize_bilingual,
)
from tests.conftest import run_coro


class MockSemanticEmbedder(Embedder):
    """Deterministic mock embedder assigning vectors based on keyword presence."""

    def __init__(self) -> None:
        self.keywords = ["खारिज", "dismissed", "नामांतरण", "mutation", "order", "आदेश"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vec = [1.0 if kw in text.lower() else 0.0 for kw in self.keywords]
            # Ensure non-zero vector
            if sum(vec) == 0:
                vec = [0.1] * len(self.keywords)
            vectors.append(vec)
        return vectors

    def get_model_name(self) -> str:
        return "MockSemanticEmbedder/1.0"

    def get_dimension(self) -> int:
        return len(self.keywords)


class TestRetriever:
    def test_bilingual_tokenizer(self):
        text = "न्यायालय उप-जिलाधिकारी (SDM) Court No. 12"
        tokens = tokenize_bilingual(text)
        assert "न्यायालय" in tokens
        assert "sdm" in tokens
        assert "court" in tokens
        assert "12" in tokens

    def test_bm25_search_hindi(self):
        chunks = [
            Chunk("c1", "d1", 1, 0, 50, None, "hi", "नामान्तरण प्रार्थना पत्र खारिज किया गया।", 6),
            Chunk("c2", "d1", 1, 50, 100, None, "hi", "वादी राम कुमार उपस्थित रहे।", 5),
            Chunk("c3", "d1", 1, 100, 150, None, "hi", "पत्रावली वास्ते साक्ष्य नियत की गई।", 6),
        ]
        bm25 = BM25Index()
        bm25.index(chunks)

        results = bm25.search("खारिज प्रार्थना पत्र", top_k=2)
        assert len(results) > 0
        best_chunk_idx, score = results[0]
        assert best_chunk_idx == 0
        assert score > 0

    def test_cosine_similarity(self):
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        v3 = [0.0, 1.0, 0.0]
        assert pytest.approx(cosine_similarity(v1, v2)) == 1.0
        assert pytest.approx(cosine_similarity(v1, v3)) == 0.0

    def test_hybrid_rrf_retrieval(self):
        chunks = [
            Chunk("c1", "d1", 1, 0, 50, None, "hi", "प्रार्थना पत्र खारिज किया जाता है।", 6),
            Chunk("c2", "d1", 2, 0, 50, None, "en", "The mutation petition is dismissed.", 6),
            Chunk("c3", "d1", 3, 0, 50, None, "hi", "वादी का नाम खतौनी में दर्ज किया जाए।", 8),
        ]
        retriever = HybridRetriever(embedder=MockSemanticEmbedder())
        run_coro(retriever.index_chunks(chunks))

        # Search in Hindi
        hits_hi = run_coro(retriever.search("खारिज आदेश", top_k=2))
        assert len(hits_hi) > 0
        top_ids = [h.chunk.chunk_id for h in hits_hi]
        assert "c1" in top_ids

        # Search in English
        hits_en = run_coro(retriever.search("dismissed petition", top_k=2))
        assert len(hits_en) > 0
        top_ids_en = [h.chunk.chunk_id for h in hits_en]
        assert "c2" in top_ids_en
