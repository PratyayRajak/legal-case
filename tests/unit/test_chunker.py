"""Tests for Structure-Aware Document Chunker."""
from __future__ import annotations

from pipeline.chunker import StructureAwareChunker


class TestStructureAwareChunker:
    def test_single_short_page_chunking(self):
        chunker = StructureAwareChunker(max_chunk_chars=1000)
        text = "न्यायालय उपजिलाधिकारी, सदर, लखनऊ। वाद संख्या 101/2024।"
        chunks = chunker.chunk_page(text, page_number=1, doc_id="doc1")

        assert len(chunks) == 1
        c = chunks[0]
        assert c.chunk_id == "doc1-p1-c0"
        assert c.page_number == 1
        assert c.text == text
        assert c.language == "hi"
        assert c.token_count > 0

    def test_long_page_splits_with_overlap(self):
        chunker = StructureAwareChunker(max_chunk_chars=200, overlap_chars=50, min_chunk_chars=30)
        paragraphs = [
            "न्यायालय उपजिलाधिकारी सदर लखनऊ के समक्ष वाद सं 2024 प्रस्तुत हुआ।",
            "वादी राम कुमार ने धारा 34 के अंतर्गत नामान्तरण हेतु आवेदन किया।",
            "प्रतिवादी श्याम लाल ने आपत्ति प्रस्तुत करते हुए कहा कि वसीयत फर्जी है।",
            "अतः उभय पक्षों को सुना गया तथा पत्रावली आदेश हेतु नियत की गई।",
        ]
        page_text = "\n\n".join(paragraphs)
        chunks = chunker.chunk_page(page_text, page_number=1, doc_id="doc2")

        assert len(chunks) >= 2
        for c in chunks:
            assert c.page_number == 1
            assert c.char_end > c.char_start
            assert len(c.text) >= 30

    def test_section_header_detection(self):
        chunker = StructureAwareChunker()
        text = """
        न्यायालय उपजिलाधिकारी सदर
        वादी: राम कुमार

        आदेश पत्रक
        दिनांक 12-04-2024 को पत्रावली पेश हुई।
        """
        chunks = chunker.chunk_page(text, page_number=2, doc_id="doc3")
        assert len(chunks) > 0
        assert chunks[0].section_header is not None
        assert "न्यायालय" in chunks[0].section_header or "आदेश" in chunks[0].section_header

    def test_chunk_document_preserves_page_boundaries(self):
        chunker = StructureAwareChunker()
        pages = [
            "Page 1: Order sheet entry dated 10-01-2024.",
            "Page 2: Plaint filed by petitioner Ram Kumar.",
            "Page 3: Final rejection order dated 15-05-2024.",
        ]
        all_chunks = chunker.chunk_document(pages, doc_id="doc4")

        assert len(all_chunks) == 3
        assert all_chunks[0].page_number == 1
        assert all_chunks[1].page_number == 2
        assert all_chunks[2].page_number == 3
