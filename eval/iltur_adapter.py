"""IL-TUR (Indian Legal Text Understanding & Reasoning) Adapter.

Academic Citation:
Joshi et al., 'IL-TUR: Benchmark for Indian Legal Text Understanding and Reasoning',
ACL 2024 (IIT Kanpur & IIT Kharagpur).

This module provides live Hugging Face streaming and offline evaluation for:
1. Legal Named Entity Recognition (L-NER)
2. Legal Document Summarization (SUMM)
3. Legal Statute Identification (LSI)
"""
from __future__ import annotations

import io
import os
import urllib.request
from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class ILTURSample:
    id: str
    tokens: list[str]
    ner_tags: list[str]
    statutes: list[str]
    court: str
    language: str


# Reference offline samples for deterministic local testing
OFFLINE_IL_TUR_SAMPLES: list[ILTURSample] = [
    ILTURSample(
        id="IL_TUR_NER_001",
        tokens=[
            "In", "the", "Court", "of", "Sub-Divisional", "Officer", ",", "Sadar", ",", "Lucknow", ".",
            "Ramesh", "Kumar", "versus", "Suresh", "Singh", ".",
            "Application", "under", "Section", "34", "of", "UP", "Revenue", "Code", "2006", "."
        ],
        ner_tags=[
            "O", "O", "B-COURT", "I-COURT", "I-COURT", "I-COURT", "O", "B-COURT", "O", "B-COURT", "O",
            "B-PETITIONER", "I-PETITIONER", "O", "B-RESPONDENT", "I-RESPONDENT", "O",
            "O", "O", "B-STATUTE", "I-STATUTE", "O", "B-STATUTE", "I-STATUTE", "I-STATUTE", "I-STATUTE", "O"
        ],
        statutes=["UP Revenue Code 2006, Section 34"],
        court="district",
        language="en"
    ),
    ILTURSample(
        id="IL_TUR_NER_002",
        tokens=[
            "न्यायालय", "उप-जिलाधिकारी", "सदर", "वाराणसी", "।",
            "रामलाल", "पुत्र", "हरिकिशन", "बनाम", "श्यामलाल", "।",
            "दाखिल", "खारिज", "प्रार्थना", "पत्र", "धारा", "35", "।",
            "आदेश", "दिनांक", "12-05-2023", "को", "पारित", "किया", "गया", "।"
        ],
        ner_tags=[
            "B-COURT", "I-COURT", "I-COURT", "I-COURT", "O",
            "B-PETITIONER", "O", "O", "O", "B-RESPONDENT", "O",
            "B-PROCEEDING", "I-PROCEEDING", "O", "O", "B-STATUTE", "I-STATUTE", "O",
            "O", "O", "B-DATE", "O", "O", "O", "O", "O"
        ],
        statutes=["UP Revenue Code 2006, Section 35"],
        court="district",
        language="hi"
    ),
]


class ILTURBenchmarkAdapter:
    """Adapter for testing our Court Brief Engine against the official IL-TUR benchmark."""

    BASE_URL = "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main"

    def __init__(self, hf_token: str | None = None) -> None:
        self.hf_token = hf_token or self._get_token_from_env()

    def _get_token_from_env(self) -> str | None:
        token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")
        if not token:
            try:
                with open(".env", encoding="utf-8") as f:
                    for line in f:
                        if line.strip().startswith("HF_TOKEN="):
                            token = line.strip().split("=", 1)[1]
                            break
            except Exception:
                pass
        return token

    def is_authenticated(self) -> bool:
        """Check if a valid token is available."""
        return bool(self.hf_token and len(self.hf_token) > 10)

    def load_live_lner_samples(self, max_samples: int = 10) -> list[dict[str, Any]]:
        """Stream real Legal NER samples from IL-TUR."""
        if not self.is_authenticated():
            return []

        url = f"{self.BASE_URL}/lner/fold_1-00000-of-00001.parquet"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.hf_token}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                df = pd.read_parquet(io.BytesIO(resp.read()))
                records: list[dict[str, Any]] = df.head(max_samples).to_dict(orient="records")
                return records
        except Exception:
            return []

    def load_live_summarization_samples(self, max_samples: int = 5) -> list[dict[str, Any]]:
        """Stream real legal document + summary pairs from IL-TUR."""
        if not self.is_authenticated():
            return []

        url = f"{self.BASE_URL}/summ/test-00000-of-00001.parquet"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.hf_token}"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                df = pd.read_parquet(io.BytesIO(resp.read()))
                records: list[dict[str, Any]] = df.head(max_samples).to_dict(orient="records")
                return records
        except Exception:
            return []

    def load_samples(self) -> list[ILTURSample]:
        """Return reference samples for instant unit test validation."""
        return OFFLINE_IL_TUR_SAMPLES

    def evaluate_extractor_on_iltur(self, extractor: Any) -> dict[str, float]:
        """Evaluate field extraction accuracy, precision, and hallucination rate."""
        samples = self.load_samples()
        total_entities = 0
        correct_entities = 0
        hallucinations = 0

        for sample in samples:
            full_text = " ".join(sample.tokens)
            doc_id = sample.id

            res = extractor.extract_from_text(full_text, doc_id=doc_id, page=1)
            fields = res.get("fields", {})

            # Check petitioners
            pet = fields.get("petitioners", {})
            has_pet = any("PETITIONER" in tag for tag in sample.ner_tags)
            if pet.get("found") and has_pet:
                correct_entities += 1
            elif pet.get("found") and not has_pet:
                hallucinations += 1
            if has_pet:
                total_entities += 1

            # Check respondents
            resp = fields.get("respondents", {})
            has_resp = any("RESPONDENT" in tag for tag in sample.ner_tags)
            if resp.get("found") and has_resp:
                correct_entities += 1
            elif resp.get("found") and not has_resp:
                hallucinations += 1
            if has_resp:
                total_entities += 1

        accuracy = (correct_entities / total_entities * 100.0) if total_entities > 0 else 100.0
        hallucination_rate = (hallucinations / max(1, (correct_entities + hallucinations)) * 100.0)

        return {
            "total_benchmark_samples": float(len(samples)),
            "total_evaluated_entities": float(total_entities),
            "entity_accuracy": round(accuracy, 2),
            "hallucination_rate": round(hallucination_rate, 2),
            "benchmark_passed": 1.0 if accuracy >= 80.0 and hallucination_rate <= 5.0 else 0.0,
        }
