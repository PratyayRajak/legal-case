"""Tests for synthetic document and label generation."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.synth_docs import generate_synthetic_data


class TestSynthDocs:
    def test_generate_synthetic_docs_and_labels(self, tmp_path: Path):
        docs_dir = tmp_path / "docs"
        labels_dir = tmp_path / "labels"
        generated_ids = generate_synthetic_data(docs_dir=docs_dir, labels_dir=labels_dir)

        assert len(generated_ids) >= 5
        assert "REV_001_HI" in generated_ids
        assert "REV_001_EN" in generated_ids

        # Check PDF existence
        for doc_id in generated_ids:
            pdf_path = docs_dir / f"{doc_id}.pdf"
            json_path = labels_dir / f"{doc_id}.json"

            assert pdf_path.exists(), f"PDF missing: {pdf_path}"
            assert json_path.exists(), f"JSON label missing: {json_path}"

            with open(json_path, encoding="utf-8") as f:
                label_data = json.load(f)
                assert label_data["doc_id"] == doc_id
                assert "fields" in label_data
                assert "rule_expectations" in label_data
                assert label_data["doc_language"] in ["hi", "en", "mixed"]
