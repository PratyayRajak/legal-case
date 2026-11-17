"""Tests for PII Masker with custom Indian recognizers and reversible encryption."""
from __future__ import annotations

import pytest

from pipeline.pii_masker import IndianCourtPIIMasker


class TestPIIMasker:
    def test_mask_pan_number(self):
        masker = IndianCourtPIIMasker()
        text = "Petitioner PAN is ABCDE1234F recorded on file."
        masked_doc = masker.mask(text, page_number=1, doc_id="test1")

        assert "ABCDE1234F" not in masked_doc.masked_text
        assert "<INDIAN_PAN_" in masked_doc.masked_text
        assert "INDIAN_PAN" in masked_doc.entities_found

        # Test reversible unmasking
        unmasked = masker.unmask(masked_doc.masked_text, masked_doc.mapping_id, authorized_user_id="judge_1")
        assert unmasked == text

    def test_mask_aadhaar_number(self):
        masker = IndianCourtPIIMasker()
        text = "Aadhaar number of applicant: 3456 7890 1234."
        masked_doc = masker.mask(text, page_number=1, doc_id="test2")

        assert "3456 7890 1234" not in masked_doc.masked_text
        assert "<INDIAN_AADHAAR_" in masked_doc.masked_text

        unmasked = masker.unmask(masked_doc.masked_text, masked_doc.mapping_id, authorized_user_id="judge_1")
        assert unmasked == text

    def test_mask_phone_number(self):
        masker = IndianCourtPIIMasker()
        text = "Contact advocate at mobile +91 98765 43210 immediately."
        masked_doc = masker.mask(text, page_number=1, doc_id="test3")

        assert "98765 43210" not in masked_doc.masked_text
        assert "<INDIAN_PHONE_" in masked_doc.masked_text

        unmasked = masker.unmask(masked_doc.masked_text, masked_doc.mapping_id, authorized_user_id="judge_1")
        assert unmasked == text

    def test_unmask_unauthorized_raises(self):
        masker = IndianCourtPIIMasker()
        text = "PAN ABCDE1234F"
        masked_doc = masker.mask(text, page_number=1, doc_id="test4")

        with pytest.raises(PermissionError):
            masker.unmask(masked_doc.masked_text, masked_doc.mapping_id, authorized_user_id="")
