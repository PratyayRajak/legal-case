"""Tests for Hybrid OCR Engine."""
from __future__ import annotations

import numpy as np

from pipeline.interfaces.ocr import PageType
from pipeline.ocr_engine import (
    HybridCourtOCREngine,
    detect_language,
    preprocess_image_for_ocr,
)


class TestOCREngine:
    def test_language_detection(self):
        assert detect_language("न्यायालय उप-जिलाधिकारी, सदर, लखनऊ") == "hi"
        assert detect_language("In the Court of District Magistrate, Lucknow") == "en"
        assert detect_language("Case No. 123/2024 वाद संख्या लखनऊ") == "mixed"

    def test_image_preprocessing_pipeline(self):
        # Create synthetic noisy BGR image
        img = np.ones((100, 200, 3), dtype=np.uint8) * 240
        # Draw some dark text-like patterns
        img[30:70, 50:150] = 30
        preprocessed = preprocess_image_for_ocr(img)

        assert preprocessed.shape == (100, 200)
        assert preprocessed.dtype == np.uint8
        # Output should be binarized (values 0 or 255)
        unique_vals = set(np.unique(preprocessed))
        assert unique_vals.issubset({0, 255})

    def test_process_digital_page(self):
        engine = HybridCourtOCREngine()
        res = engine.process_page("eval/data/docs/REV_001_HI.pdf", page_number=1)
        assert res.page_number == 1
        assert res.page_type == PageType.digital
        assert len(res.words) > 0
        assert res.mean_confidence > 90.0
        assert res.language == "hi"
        assert "लखनऊ" in res.full_text

        # Verify word bounding boxes
        w0 = res.words[0]
        assert w0.x1 > w0.x0
        assert w0.y1 > w0.y0
        assert w0.confidence > 0

    def test_process_scanned_page(self):
        engine = HybridCourtOCREngine()
        res = engine.process_page("eval/data/docs/REV_003_SCAN_GOOD.pdf", page_number=1)
        assert res.page_number == 1
        assert res.page_type == PageType.scanned
        assert res.width == 595.0
        assert res.height == 842.0

    def test_process_document(self):
        engine = HybridCourtOCREngine()
        doc_res = engine.process_document("eval/data/docs/REV_002_MIXED.pdf", doc_id="REV_002_MIXED")
        assert doc_res.doc_id == "REV_002_MIXED"
        assert doc_res.total_pages == 1
        assert len(doc_res.page_results) == 1
        assert doc_res.overall_language in ["en", "mixed"]
        assert len(doc_res.failed_pages) == 0
