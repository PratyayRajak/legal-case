"""Structure-Aware Document Chunker for Indian Court Records.

Design principles:
1. Chunks never cross PDF page boundaries to guarantee that every citation
   has an unambiguous, exact page number.
2. Identifies legal section headings (e.g., "न्यायालय", "आदेश", "तथ्य", "निर्णय", "ORDER")
   to anchor chunks within their procedural context.
3. Respects paragraph and sentence boundaries while maintaining target chunk size
   with configurable overlap.
4. Tags each chunk with language ('hi', 'en', 'mixed') for multilingual retrieval.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from pipeline.ocr_engine import detect_language

# Common legal section headers in Hindi and English
_SECTION_PATTERNS = [
    r"^(?:न्यायालय|COURT OF|IN THE COURT OF)\b.*$",
    r"^(?:वाद संख्या|मुकदमा नं|CASE NO|SUIT NO)\b.*$",
    r"^(?:आदेश पत्रक|आदेश|ORDER SHEET|ORDER|PROCEEDINGS)\b.*$",
    r"^(?:तथ्य|संक्षिप्त विवरण|संक्षिप्त तथ्य|FACTS|BRIEF FACTS)\b.*$",
    r"^(?:वादी|याचिकाकर्ता|PETITIONER|APPLICANT)\b.*$",
    r"^(?:प्रतिवादी|विपक्षी|RESPONDENT|DEFENDANT)\b.*$",
    r"^(?:निष्कर्ष|अंतिम निष्कर्ष|FINDINGS|DECISION|CONCLUSION)\b.*$",
    r"^(?:निर्णय|अंतिम आदेश|JUDGMENT|FINAL ORDER)\b.*$",
]

_SECTION_REGEX = re.compile("|".join(_SECTION_PATTERNS), re.IGNORECASE | re.MULTILINE)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    page_number: int  # 1-indexed
    char_start: int
    char_end: int
    section_header: str | None
    language: str  # "hi", "en", "mixed"
    text: str
    token_count: int


class StructureAwareChunker:
    """Structure-aware chunker respecting page, section, and paragraph boundaries."""

    def __init__(
        self,
        max_chunk_chars: int = 1000,
        overlap_chars: int = 150,
        min_chunk_chars: int = 50,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars
        self.min_chunk_chars = min_chunk_chars

    def _split_into_paragraphs(self, text: str) -> list[tuple[int, int, str]]:
        """Split text into paragraphs with start and end character offsets."""
        paragraphs: list[tuple[int, int, str]] = []
        # Split on double newline or indented blocks
        matches = list(re.finditer(r"\S.*?(?:\n\s*\n|\Z)", text, re.DOTALL))
        if not matches:
            if text.strip():
                paragraphs.append((0, len(text), text.strip()))
            return paragraphs

        for m in matches:
            content = m.group().strip()
            if content:
                start = m.start()
                end = start + len(content)
                paragraphs.append((start, end, content))
        return paragraphs

    def _detect_section_header(self, text: str) -> str | None:
        """Find the earliest legal section heading in the text snippet."""
        match = _SECTION_REGEX.search(text)
        if match:
            return match.group(0).strip()
        return None

    def chunk_page(
        self,
        page_text: str,
        page_number: int,
        doc_id: str,
    ) -> list[Chunk]:
        """Produce structured chunks for a single page."""
        cleaned_page = page_text.strip()
        if not cleaned_page:
            return []

        # If page is small enough, return as a single chunk
        if len(cleaned_page) <= self.max_chunk_chars:
            header = self._detect_section_header(cleaned_page)
            lang = detect_language(cleaned_page)
            words = cleaned_page.split()
            return [
                Chunk(
                    chunk_id=f"{doc_id}-p{page_number}-c0",
                    doc_id=doc_id,
                    page_number=page_number,
                    char_start=0,
                    char_end=len(cleaned_page),
                    section_header=header,
                    language=lang,
                    text=cleaned_page,
                    token_count=len(words),
                )
            ]

        paragraphs = self._split_into_paragraphs(page_text)
        chunks: list[Chunk] = []
        current_chunk_paragraphs: list[tuple[int, int, str]] = []
        current_len = 0
        current_header: str | None = None
        chunk_idx = 0

        for p_start, p_end, p_text in paragraphs:
            # Check if this paragraph introduces a new section header
            detected_h = self._detect_section_header(p_text)
            if detected_h:
                current_header = detected_h

            if current_len + len(p_text) > self.max_chunk_chars and current_chunk_paragraphs:
                # Flush current chunk
                first_start = current_chunk_paragraphs[0][0]
                last_end = current_chunk_paragraphs[-1][1]
                combined_text = "\n\n".join(p[2] for p in current_chunk_paragraphs)

                if len(combined_text) >= self.min_chunk_chars:
                    lang = detect_language(combined_text)
                    chunks.append(
                        Chunk(
                            chunk_id=f"{doc_id}-p{page_number}-c{chunk_idx}",
                            doc_id=doc_id,
                            page_number=page_number,
                            char_start=first_start,
                            char_end=last_end,
                            section_header=current_header,
                            language=lang,
                            text=combined_text,
                            token_count=len(combined_text.split()),
                        )
                    )
                    chunk_idx += 1

                # Maintain overlap from trailing paragraphs
                overlap_paras: list[tuple[int, int, str]] = []
                overlap_len = 0
                for op in reversed(current_chunk_paragraphs):
                    if overlap_len + len(op[2]) <= self.overlap_chars:
                        overlap_paras.insert(0, op)
                        overlap_len += len(op[2])
                    else:
                        break

                current_chunk_paragraphs = overlap_paras
                current_len = overlap_len

            current_chunk_paragraphs.append((p_start, p_end, p_text))
            current_len += len(p_text)

        # Flush any remaining paragraphs
        if current_chunk_paragraphs:
            first_start = current_chunk_paragraphs[0][0]
            last_end = current_chunk_paragraphs[-1][1]
            combined_text = "\n\n".join(p[2] for p in current_chunk_paragraphs)
            if len(combined_text) >= self.min_chunk_chars or not chunks:
                lang = detect_language(combined_text)
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc_id}-p{page_number}-c{chunk_idx}",
                        doc_id=doc_id,
                        page_number=page_number,
                        char_start=first_start,
                        char_end=last_end,
                        section_header=current_header,
                        language=lang,
                        text=combined_text,
                        token_count=len(combined_text.split()),
                    )
                )

        return chunks

    def chunk_document(
        self,
        pages: list[str],
        doc_id: str,
    ) -> list[Chunk]:
        """Chunk all pages of a document."""
        all_chunks: list[Chunk] = []
        for idx, page_text in enumerate(pages, start=1):
            page_chunks = self.chunk_page(
                page_text=page_text,
                page_number=idx,
                doc_id=doc_id,
            )
            all_chunks.extend(page_chunks)
        return all_chunks
