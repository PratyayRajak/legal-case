"""Tests for PDF ingestion and hardening."""
from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from pipeline.ingest import (
    DocumentLimitExceededError,
    EncryptedPDFError,
    InvalidPDFError,
    calculate_file_hash,
    ingest_pdf,
    validate_pdf_bytes,
)


class TestPDFIngest:
    def test_valid_pdf_magic_bytes(self):
        valid = b"%PDF-1.7\n1 0 obj\n..."
        validate_pdf_bytes(valid)  # Should not raise

    def test_invalid_magic_bytes_raises(self):
        invalid = b"PK\x03\x04something_else"
        with pytest.raises(InvalidPDFError):
            validate_pdf_bytes(invalid)

    def test_calculate_file_hash(self):
        data = b"%PDF-test content"
        h1 = calculate_file_hash(data)
        h2 = calculate_file_hash(data)
        assert h1 == h2
        assert len(h1) == 64

    def test_ingest_synthetic_pdf(self):
        pdf_path = "eval/data/docs/REV_001_HI.pdf"
        result = ingest_pdf(pdf_path, doc_id="REV_001_HI")
        assert result.doc_id == "REV_001_HI"
        assert result.total_pages == 1
        assert len(result.doc_hash) == 64
        assert result.file_size_bytes > 0
        assert len(result.pages_meta) == 1
        assert result.pages_meta[0].char_count > 0

    def test_page_limit_exceeded(self, tmp_path: Path):
        doc = fitz.open()
        for _ in range(5):
            doc.new_page(width=500, height=700)
        out_file = tmp_path / "multi_page.pdf"
        doc.save(str(out_file))
        doc.close()

        with pytest.raises(DocumentLimitExceededError):
            ingest_pdf(out_file, doc_id="large_doc", max_pages=3)

    def test_size_limit_exceeded(self, tmp_path: Path):
        doc = fitz.open()
        doc.new_page()
        out_file = tmp_path / "tiny.pdf"
        doc.save(str(out_file))
        doc.close()

        with pytest.raises(DocumentLimitExceededError):
            ingest_pdf(out_file, doc_id="tiny_doc", max_size_mb=0)

    def test_encrypted_pdf_rejected(self, tmp_path: Path):
        doc = fitz.open()
        doc.new_page()
        out_file = tmp_path / "encrypted.pdf"
        # Save with encryption password
        doc.save(
            str(out_file),
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="secret123",
            user_pw="secret123",
        )
        doc.close()

        with pytest.raises(EncryptedPDFError):
            ingest_pdf(out_file, doc_id="enc_doc")
