"""OCR engine interface.

Default implementation uses PyMuPDF for digital pages and
Tesseract (hin+eng) for scanned pages with OpenCV preprocessing.
The interface allows swapping in a better Indic OCR engine later.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class PageType(str, Enum):
    digital = "digital"       # PDF text layer present and trustworthy
    scanned = "scanned"       # Image-only, requires OCR
    mixed = "mixed"           # Partial text layer + image content


@dataclass
class WordBox:
    """A single word with its bounding box and confidence."""

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    confidence: float          # 0.0–100.0, Tesseract scale
    language: str = "unknown"  # "hi", "en", "unknown"


@dataclass
class PageOCRResult:
    """OCR result for a single PDF page."""

    page_number: int           # 1-indexed
    page_type: PageType
    full_text: str             # Complete text of the page
    words: list[WordBox]       # Word-level bounding boxes
    mean_confidence: float     # Average word confidence (0–100)
    language: str              # Dominant language: "hi", "en", "mixed"
    width: float               # Page width in points
    height: float              # Page height in points
    error: str | None = None  # Set if OCR failed for this page


@dataclass
class DocumentOCRResult:
    """Aggregated OCR result for the whole document."""

    doc_id: str
    page_results: list[PageOCRResult]
    overall_language: str
    total_pages: int
    failed_pages: list[int] = field(default_factory=list)


class OCREngine(ABC):
    """Abstract OCR engine interface.

    Implementations must:
    - Return word-level bounding boxes and per-word confidence
    - Detect page type (digital / scanned / mixed) automatically
    - Support Hindi (Devanagari) and English in the same document
    - Report language per page
    """

    @abstractmethod
    def process_document(self, pdf_path: str, doc_id: str) -> DocumentOCRResult:
        """Process an entire PDF and return OCR results for all pages."""
        ...

    @abstractmethod
    def process_page(self, pdf_path: str, page_number: int) -> PageOCRResult:
        """Process a single page (1-indexed)."""
        ...

    @abstractmethod
    def get_engine_name(self) -> str:
        """Return the engine name and version for audit logging."""
        ...


class StubOCREngine(OCREngine):
    """Stub OCR engine for testing. Returns minimal fixed results."""

    def process_document(self, pdf_path: str, doc_id: str) -> DocumentOCRResult:
        page = self.process_page(pdf_path, 1)
        return DocumentOCRResult(
            doc_id=doc_id,
            page_results=[page],
            overall_language="en",
            total_pages=1,
        )

    def process_page(self, pdf_path: str, page_number: int) -> PageOCRResult:
        return PageOCRResult(
            page_number=page_number,
            page_type=PageType.digital,
            full_text="[STUB OCR TEXT]",
            words=[],
            mean_confidence=100.0,
            language="en",
            width=595.0,
            height=842.0,
        )

    def get_engine_name(self) -> str:
        return "StubOCREngine/0.1"
