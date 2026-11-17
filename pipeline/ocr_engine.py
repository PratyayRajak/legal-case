"""Hybrid OCR Engine implementation for Indian Court documents.

Features:
1. Per-page classification: digital, scanned, or mixed.
2. OpenCV preprocessing for scanned pages:
   - Grayscale conversion
   - Noise removal & CLAHE contrast enhancement
   - Automated deskewing
   - Adaptive Otsu binarization
3. Word-level bounding boxes and confidence scores.
4. Per-page and overall language detection (Hindi, English, mixed).
5. PyMuPDF fast digital extraction + Tesseract (hin+eng) fallback.
"""
from __future__ import annotations

import logging
from typing import Any

import cv2
import fitz
import numpy as np

from config import settings
from pipeline.interfaces.ocr import (
    DocumentOCRResult,
    OCREngine,
    PageOCRResult,
    PageType,
    WordBox,
)

logger = logging.getLogger(__name__)


def preprocess_image_for_ocr(img_bgr: np.ndarray[Any, Any]) -> np.ndarray[Any, Any]:
    """Apply OpenCV preprocessing pipeline to enhance degraded scanned court documents."""
    # 1. Grayscale
    if len(img_bgr.shape) == 3 and img_bgr.shape[2] == 3:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    else:
        gray = img_bgr.copy()

    # 2. Contrast Enhancement using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # 3. Denoising
    denoised = cv2.medianBlur(contrast, 3)

    # 4. Deskewing
    coords = np.column_stack(np.where(denoised < 200))
    if coords.shape[0] > 50:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        elif angle > 45:
            angle = 90 - angle
        else:
            angle = -angle

        # Only correct slight skews (between 0.5 and 15 degrees)
        if 0.5 <= abs(angle) <= 15.0:
            (h, w) = denoised.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            denoised = cv2.warpAffine(
                denoised,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )

    # 5. Otsu's adaptive binarization
    _, binarized = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binarized


def detect_language(text: str) -> str:
    """Detect dominant script/language of a text chunk: 'hi', 'en', or 'mixed'."""
    devanagari_count = sum(1 for ch in text if "\u0900" <= ch <= "\u097F")
    latin_count = sum(1 for ch in text if "a" <= ch.lower() <= "z")
    total_letters = devanagari_count + latin_count

    if total_letters == 0:
        return "unknown"

    hi_ratio = devanagari_count / total_letters
    en_ratio = latin_count / total_letters

    if hi_ratio >= 0.80:
        return "hi"
    if en_ratio >= 0.80:
        return "en"
    return "mixed"


class HybridCourtOCREngine(OCREngine):
    """Production-grade hybrid OCR engine for Hindi & English Indian Court records."""

    def __init__(self, languages: str | None = None) -> None:
        self.languages = languages or settings.tesseract_languages
        self._tesseract_available: bool | None = None

    def get_engine_name(self) -> str:
        return "HybridCourtOCREngine (PyMuPDF 1.27 + OpenCV 4.9 + Tesseract fallback)"

    def _check_tesseract(self) -> bool:
        if self._tesseract_available is None:
            try:
                import pytesseract
                # Test pytesseract version
                _ = pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available

    def classify_page_type(self, page: fitz.Page) -> PageType:
        """Classify page into digital, scanned, or mixed."""
        text = page.get_text().strip()
        images = page.get_images()
        text_len = len(text)
        has_images = len(images) > 0

        if text_len > 80 and not has_images:
            return PageType.digital
        if text_len <= 30 and has_images:
            return PageType.scanned
        if text_len > 30 and has_images:
            return PageType.mixed
        # Default based on char density
        return PageType.digital if text_len > 30 else PageType.scanned

    def process_page(self, pdf_path: str, page_number: int) -> PageOCRResult:
        """Extract text, word bounding boxes, confidence, and language for a single page."""
        doc = fitz.open(pdf_path)
        pno = page_number - 1
        if pno < 0 or pno >= len(doc):
            doc.close()
            raise ValueError(f"Invalid page number {page_number} for PDF with {len(doc)} pages")

        page = doc[pno]
        rect = page.rect
        width, height = rect.width, rect.height
        page_type = self.classify_page_type(page)

        words: list[WordBox] = []
        full_text = ""
        mean_confidence = 100.0

        if page_type in [PageType.digital, PageType.mixed]:
            full_text = page.get_text()
            # PyMuPDF word tuples: (x0, y0, x1, y1, "word", block_no, line_no, word_no)
            raw_words = page.get_text("words")
            for w in raw_words:
                word_text = str(w[4])
                word_lang = detect_language(word_text)
                words.append(
                    WordBox(
                        text=word_text,
                        x0=float(w[0]),
                        y0=float(w[1]),
                        x1=float(w[2]),
                        y1=float(w[3]),
                        confidence=98.0,
                        language=word_lang,
                    )
                )

        # Scanned processing if scanned or digital yielded negligible text
        if page_type == PageType.scanned or (len(full_text.strip()) < 20 and page_type == PageType.mixed):
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.h, pix.w, pix.n))
            preprocessed = preprocess_image_for_ocr(img)

            if self._check_tesseract():
                try:
                    import pytesseract
                    from pytesseract import Output
                    # Run tesseract data extraction
                    data = pytesseract.image_to_data(
                        preprocessed,
                        lang=self.languages,
                        output_type=Output.DICT,
                    )
                    words = []
                    text_parts = []
                    conf_scores = []
                    n_boxes = len(data["text"])
                    scale_x = width / float(pix.w)
                    scale_y = height / float(pix.h)

                    for i in range(n_boxes):
                        w_text = data["text"][i].strip()
                        conf = float(data["conf"][i])
                        if w_text and conf > 0:
                            bx0 = float(data["left"][i]) * scale_x
                            by0 = float(data["top"][i]) * scale_y
                            bx1 = bx0 + float(data["width"][i]) * scale_x
                            by1 = by0 + float(data["height"][i]) * scale_y
                            w_lang = detect_language(w_text)
                            words.append(
                                WordBox(
                                    text=w_text,
                                    x0=bx0,
                                    y0=by0,
                                    x1=bx1,
                                    y1=by1,
                                    confidence=conf,
                                    language=w_lang,
                                )
                            )
                            text_parts.append(w_text)
                            conf_scores.append(conf)

                    full_text = " ".join(text_parts)
                    mean_confidence = float(np.mean(conf_scores)) if conf_scores else 60.0
                except Exception as exc:
                    logger.warning("Tesseract execution failed on page %d: %s", page_number, exc)

            if not full_text.strip():
                # Fallback: PyMuPDF page text
                full_text = page.get_text()
                mean_confidence = 70.0

        doc.close()

        lang = detect_language(full_text)
        return PageOCRResult(
            page_number=page_number,
            page_type=page_type,
            full_text=full_text,
            words=words,
            mean_confidence=mean_confidence,
            language=lang,
            width=width,
            height=height,
        )

    def process_document(self, pdf_path: str, doc_id: str) -> DocumentOCRResult:
        """Process full document across all pages."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()

        page_results: list[PageOCRResult] = []
        failed_pages: list[int] = []
        all_text_chunks: list[str] = []

        for p in range(1, total_pages + 1):
            try:
                res = self.process_page(pdf_path, p)
                page_results.append(res)
                all_text_chunks.append(res.full_text)
            except Exception as e:
                logger.error("Failed to process page %d of %s: %s", p, doc_id, e)
                failed_pages.append(p)

        overall_lang = detect_language(" ".join(all_text_chunks))
        return DocumentOCRResult(
            doc_id=doc_id,
            page_results=page_results,
            overall_language=overall_lang,
            total_pages=total_pages,
            failed_pages=failed_pages,
        )
