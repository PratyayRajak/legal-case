"""Tests for Court Document Classifier."""
from __future__ import annotations

from app.schemas.canonical import CourtLevel, DocumentType
from pipeline.classifier import CourtDocumentClassifier


class TestCourtDocumentClassifier:
    def test_classify_petition_hindi(self):
        classifier = CourtDocumentClassifier()
        text = """
        न्यायालय उप-जिलाधिकारी, सदर, लखनऊ
        वाद पत्र अंतर्गत धारा 34/35 उ०प्र० राजस्व संहिता 2006
        वादी: राम कुमार
        प्रतिवादी: श्याम लाल
        प्रार्थना पत्र प्रस्तुत कर निवेदन है कि...
        """
        res = classifier.classify_text(text, doc_id="rev_001")
        assert res.document_type == DocumentType.petition
        assert res.court_level == CourtLevel.district
        assert res.case_type == "revenue"
        assert res.language == "hi"
        assert res.confidence >= 0.7

    def test_classify_order_sheet_english(self):
        classifier = CourtDocumentClassifier()
        text = """
        In the Court of Sub-Divisional Magistrate, Lucknow
        Order Sheet
        Case No. REV/2024/001
        Matter called. Parties present. Case adjourned to 15-05-2024 for framing of issues.
        """
        res = classifier.classify_text(text, doc_id="rev_002")
        assert res.document_type == DocumentType.order_sheet
        assert res.court_level == CourtLevel.district
        assert res.language == "en"

    def test_classify_judgment_hindi(self):
        classifier = CourtDocumentClassifier()
        text = """
        न्यायालय उपजिलाधिकारी, सदर
        अंतिम आदेश / निर्णय
        उपरोक्त विवेचना के आधार पर नामान्तरण प्रार्थना पत्र खारिज किया जाता है।
        """
        res = classifier.classify_text(text, doc_id="rev_003")
        assert res.document_type == DocumentType.judgment
        assert res.language == "hi"

    def test_classify_high_court_level(self):
        classifier = CourtDocumentClassifier()
        text = """
        In the High Court of Judicature at Allahabad
        Writ Petition No. 1234 of 2024
        """
        res = classifier.classify_text(text, doc_id="hc_001")
        assert res.court_level == CourtLevel.high
        assert res.document_type == DocumentType.petition
