"""PDF Ingestion and Hardening module.

Security and hardening rules:
1. Validates magic bytes (%PDF-).
2. Computes SHA-256 document hash for caching and audit logging.
3. Enforces page count and file size limits from settings.
4. Detects encrypted / password-protected PDFs and rejects them safely.
5. Catches corrupted or malformed PDFs with clear typed errors.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import fitz

from config import settings


class IngestError(Exception):
    """Base exception for ingestion errors."""


class InvalidPDFError(IngestError):
    """File is not a valid PDF."""


class EncryptedPDFError(IngestError):
    """PDF is password protected."""


class DocumentLimitExceededError(IngestError):
    """PDF exceeds size or page count limits."""


@dataclass
class PageMetadata:
    page_number: int  # 1-indexed
    width: float
    height: float
    rotation: int
    char_count: int
    image_count: int


@dataclass
class IngestionResult:
    doc_id: str
    file_path: str
    doc_hash: str
    file_size_bytes: int
    total_pages: int
    pages_meta: list[PageMetadata] = field(default_factory=list)
    is_valid: bool = True
    error_message: str | None = None


def validate_pdf_bytes(file_bytes: bytes) -> None:
    """Validate PDF header magic bytes."""
    if not file_bytes.startswith(b"%PDF-"):
        raise InvalidPDFError("File does not start with valid PDF magic bytes (%PDF-)")


def calculate_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of document bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def ingest_pdf(
    pdf_path: str | Path,
    doc_id: str,
    max_pages: int | None = None,
    max_size_mb: int | None = None,
) -> IngestionResult:
    """Validate, inspect, and ingest a PDF file."""
    path = Path(pdf_path)
    if not path.exists():
        raise InvalidPDFError(f"File not found: {path}")

    file_size = path.stat().st_size
    max_mb = settings.max_pdf_size_mb if max_size_mb is None else max_size_mb
    if file_size > max_mb * 1024 * 1024:
        raise DocumentLimitExceededError(
            f"File size {file_size / (1024*1024):.2f}MB exceeds limit of {max_mb}MB"
        )

    with open(path, "rb") as f:
        content = f.read()

    validate_pdf_bytes(content)
    doc_hash = calculate_file_hash(content)

    try:
        doc = fitz.open(stream=content, filetype="pdf")
    except Exception as exc:
        raise InvalidPDFError(f"Failed to parse PDF document: {exc}") from exc

    if doc.is_encrypted:
        doc.close()
        raise EncryptedPDFError("Document is password protected and cannot be processed.")

    total_pages = len(doc)
    max_p = settings.max_pdf_pages if max_pages is None else max_pages
    if total_pages > max_p:
        doc.close()
        raise DocumentLimitExceededError(
            f"Document has {total_pages} pages, exceeding the limit of {max_p} pages."
        )

    pages_meta: list[PageMetadata] = []
    for i in range(total_pages):
        page = doc[i]
        rect = page.rect
        text = page.get_text()
        images = page.get_images()
        pages_meta.append(
            PageMetadata(
                page_number=i + 1,
                width=rect.width,
                height=rect.height,
                rotation=page.rotation,
                char_count=len(text),
                image_count=len(images),
            )
        )

    doc.close()

    return IngestionResult(
        doc_id=doc_id,
        file_path=str(path),
        doc_hash=doc_hash,
        file_size_bytes=file_size,
        total_pages=total_pages,
        pages_meta=pages_meta,
    )
