"""Tests for Grounded Q&A Faithfulness and Refusal Evaluation."""
from __future__ import annotations

from eval.qa_eval import (
    compute_citation_precision,
    evaluate_qa_pair,
    is_proper_refusal,
)
from pipeline.chunker import Chunk


class TestQAEval:
    def test_refusal_detection(self):
        answer_hi = "इस प्रश्न का उत्तर संलग्न पत्रावली में नहीं पाया गया।"
        answer_en = "The answer to this question was not found in the uploaded file."
        answer_hallucinated = "The applicant was granted relief under Section 34."

        assert is_proper_refusal(answer_hi) is True
        assert is_proper_refusal(answer_en) is True
        assert is_proper_refusal(answer_hallucinated) is False

    def test_out_of_file_question_properly_refused(self):
        chunks = [Chunk("c1", "d1", 1, 0, 50, None, "hi", "वाद संख्या 104/2024।", 4)]
        res = evaluate_qa_pair(
            question="भारत की राजधानी क्या है?",
            answer="इस प्रश्न का उत्तर संलग्न पत्रावली में नहीं पाया गया।",
            citations=[],
            chunks=chunks,
            is_out_of_file=True,
        )
        assert res.refused_properly is True
        assert res.faithfulness_score == 1.0
        assert res.hallucination_detected is False

    def test_in_file_question_with_accurate_citation(self):
        chunk_text = "न्यायालय उपजिलाधिकारी सदर द्वारा नामान्तरण प्रार्थना पत्र खारिज किया गया।"
        chunks = [Chunk("c1", "d1", 1, 0, len(chunk_text), None, "hi", chunk_text, 10)]
        citations = [{"page": 1, "snippet": "नामान्तरण प्रार्थना पत्र खारिज किया गया"}]

        res = evaluate_qa_pair(
            question="आवेदन का क्या परिणाम हुआ?",
            answer="दस्तावेज़ के अनुसार: नामान्तरण प्रार्थना पत्र खारिज किया गया।",
            citations=citations,
            chunks=chunks,
            is_out_of_file=False,
        )
        assert res.faithfulness_score == 1.0
        assert res.citation_precision == 1.0
        assert res.hallucination_detected is False

    def test_citation_precision_computation(self):
        chunks = [Chunk("c1", "d1", 1, 0, 50, None, "hi", "वादी राम कुमार उपस्थित रहे।", 5)]
        valid_citations = [{"snippet": "वादी राम कुमार उपस्थित रहे"}]
        invalid_citations = [{"snippet": "प्रतिवादी अनुपस्थित रहे और जुर्माना लगाया गया"}]

        prec_good = compute_citation_precision(valid_citations, chunks)
        prec_bad = compute_citation_precision(invalid_citations, chunks)

        assert prec_good == 1.0
        assert prec_bad < 0.5
