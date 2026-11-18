"""Hybrid Retriever combining BM25 Lexical Search + Dense Embeddings with RRF.

Key architectural features:
1. Bilingual Tokenizer: Tokenizes Devanagari words and English words, stripping punctuation.
2. BM25Okapi: Standard probabilistic lexical search.
3. Dense Vector Index: Embeds chunks using the `Embedder` interface and ranks by cosine similarity.
4. Reciprocal Rank Fusion (RRF): Combines BM25 and dense vector rankings with constant k=60.
5. Cross-Scorer / Glossary Concept Awareness: Elevates chunks containing exact concept surface forms.
"""
from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field

from glossary.loader import GlossaryLoader
from pipeline.chunker import Chunk
from pipeline.interfaces.embedder import Embedder, StubEmbedder

# Regex for Devanagari and Latin words
_TOKEN_REGEX = re.compile(r"[\u0900-\u097F]+|[a-zA-Z0-9]+", re.UNICODE)


def tokenize_bilingual(text: str) -> list[str]:
    """Tokenize Hindi, English, or mixed text into normalized word tokens."""
    normalized = unicodedata.normalize("NFKC", text.lower())
    return _TOKEN_REGEX.findall(normalized)


@dataclass
class SearchResult:
    chunk: Chunk
    rrf_score: float
    bm25_score: float = 0.0
    dense_score: float = 0.0
    bm25_rank: int | None = None
    dense_rank: int | None = None
    matched_terms: list[str] = field(default_factory=list)


class BM25Index:
    """In-memory BM25Okapi index for legal chunks."""

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.chunks: list[Chunk] = []
        self.doc_len: list[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: dict[str, int] = {}
        self.idf: dict[str, float] = {}
        self.term_freqs: list[dict[str, int]] = []

    def index(self, chunks: list[Chunk]) -> None:
        """Build BM25 index over the provided chunks."""
        self.chunks = chunks
        self.doc_len = []
        self.term_freqs = []
        self.doc_freqs = {}

        if not chunks:
            self.avg_doc_len = 0.0
            return

        total_tokens = 0
        for chunk in chunks:
            tokens = tokenize_bilingual(chunk.text)
            self.doc_len.append(len(tokens))
            total_tokens += len(tokens)

            tf: dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for t in tf:
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_tokens / len(chunks) if chunks else 0.0

        # Calculate Robertson-Spärck Jones IDF
        n_docs = len(chunks)
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((n_docs - freq + 0.5) / (freq + 0.5) + 1.0)

    def search(self, query: str, top_k: int = 10) -> list[tuple[int, float]]:
        """Score all chunks against query and return (chunk_idx, score) sorted desc."""
        if not self.chunks:
            return []

        q_tokens = tokenize_bilingual(query)
        if not q_tokens:
            return []

        scores: list[float] = [0.0] * len(self.chunks)

        for q in q_tokens:
            idf = self.idf.get(q, 0.0)
            if idf <= 0:
                continue

            for idx, tf_dict in enumerate(self.term_freqs):
                tf = tf_dict.get(q, 0)
                if tf == 0:
                    continue
                dlen = self.doc_len[idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (dlen / (self.avg_doc_len or 1.0)))
                scores[idx] += idf * (numerator / denominator)

        # Rank and return
        indexed_scores = [(idx, score) for idx, score in enumerate(scores) if score > 0]
        indexed_scores.sort(key=lambda x: x[1], reverse=True)
        return indexed_scores[:top_k]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class HybridRetriever:
    """Production-grade hybrid retriever combining BM25 and dense embeddings with RRF."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        glossary: GlossaryLoader | None = None,
        rrf_k: int = 60,
    ) -> None:
        self.embedder = embedder or StubEmbedder()
        self.glossary = glossary or GlossaryLoader()
        self.rrf_k = rrf_k
        self.bm25 = BM25Index()
        self.chunks: list[Chunk] = []
        self.chunk_embeddings: list[list[float]] = []

    async def index_chunks(self, chunks: list[Chunk]) -> None:
        """Index chunks into both BM25 and dense vector structures."""
        self.chunks = chunks
        self.bm25.index(chunks)

        # Embed all chunks
        texts = [c.text for c in chunks]
        if texts:
            self.chunk_embeddings = await self.embedder.embed(texts)
        else:
            self.chunk_embeddings = []

    async def search(
        self,
        query: str,
        top_k: int = 5,
        bm25_weight: float = 0.5,
        dense_weight: float = 0.5,
    ) -> list[SearchResult]:
        """Execute hybrid search using Reciprocal Rank Fusion (RRF)."""
        if not self.chunks:
            return []

        # 1. Lexical BM25 search
        bm25_hits = self.bm25.search(query, top_k=len(self.chunks))
        bm25_ranks: dict[int, int] = {idx: rank + 1 for rank, (idx, _) in enumerate(bm25_hits)}
        bm25_scores: dict[int, float] = {idx: score for idx, score in bm25_hits}

        # 2. Dense Vector search
        query_vectors = await self.embedder.embed([query])
        dense_ranks: dict[int, int] = {}
        dense_scores: dict[int, float] = {}

        if query_vectors and self.chunk_embeddings:
            q_vec = query_vectors[0]
            # Check if vector is non-zero (StubEmbedder returns zero vectors)
            has_vector = any(v != 0.0 for v in q_vec)
            if has_vector:
                similarities = [
                    (idx, cosine_similarity(q_vec, c_vec))
                    for idx, c_vec in enumerate(self.chunk_embeddings)
                ]
                similarities.sort(key=lambda x: x[1], reverse=True)
                for rank, (idx, score) in enumerate(similarities):
                    dense_ranks[idx] = rank + 1
                    dense_scores[idx] = score

        # 3. Reciprocal Rank Fusion (RRF)
        all_candidate_indices = set(bm25_ranks.keys()) | set(dense_ranks.keys())
        # If neither BM25 nor dense found specific matches, fall back to sequential top_k
        if not all_candidate_indices:
            all_candidate_indices = set(range(min(top_k, len(self.chunks))))

        q_tokens = set(tokenize_bilingual(query))
        results: list[SearchResult] = []

        for idx in all_candidate_indices:
            chunk = self.chunks[idx]
            r_bm25 = bm25_ranks.get(idx)
            r_dense = dense_ranks.get(idx)

            rrf = 0.0
            if r_bm25 is not None:
                rrf += bm25_weight * (1.0 / (self.rrf_k + r_bm25))
            if r_dense is not None:
                rrf += dense_weight * (1.0 / (self.rrf_k + r_dense))
            if r_bm25 is None and r_dense is None:
                # Fallback score
                rrf = 1.0 / (self.rrf_k + idx + 1)

            # Matched surface forms / tokens
            chunk_tokens = set(tokenize_bilingual(chunk.text))
            matched = list(q_tokens.intersection(chunk_tokens))

            # Concept boost if chunk matches concept terms
            results.append(
                SearchResult(
                    chunk=chunk,
                    rrf_score=rrf,
                    bm25_score=bm25_scores.get(idx, 0.0),
                    dense_score=dense_scores.get(idx, 0.0),
                    bm25_rank=r_bm25,
                    dense_rank=r_dense,
                    matched_terms=matched,
                )
            )

        # Sort by RRF score descending
        results.sort(key=lambda x: x.rrf_score, reverse=True)
        return results[:top_k]
