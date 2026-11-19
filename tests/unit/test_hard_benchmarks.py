"""Automated Test Runner for the 4 Hard Research Stress Tests."""
from __future__ import annotations

from eval.counterfactual_test import CounterfactualTamperingEvaluator
from eval.formal_verification import LegalRulesFormalVerifier
from eval.invariance_test import CrossLanguageInvarianceTester
from eval.ocr_stress_test import OCRDegradationStressTester


class TestHardResearchBenchmarks:
    def test_ocr_degradation_stress_suite(self) -> None:
        tester = OCRDegradationStressTester()
        results = tester.run_stress_suite()
        assert len(results) == 15
        assert all(r.recovered_successfully for r in results)
        assert all(r.ocr_readability_score >= 50.0 for r in results)

    def test_adversarial_counterfactual_suite(self) -> None:
        tester = CounterfactualTamperingEvaluator()
        outcomes = tester.run_all_counterfactual_attacks()
        assert len(outcomes) == 4
        # All 4 adversarial attacks must be intercepted
        assert all(o.attack_intercepted for o in outcomes)

    def test_cross_language_invariance_suite(self) -> None:
        tester = CrossLanguageInvarianceTester()
        results = tester.run_invariance_benchmarks()
        assert len(results) == 4
        assert all(r.overall_invariance_score == 1.0 for r in results)
        assert all(r.concepts_identical for r in results)

    def test_z3_formal_verification_theorems(self) -> None:
        verifier = LegalRulesFormalVerifier()
        proofs = verifier.run_all_formal_proofs()
        assert len(proofs) == 3
        # All 3 mathematical theorems must be proven (UNSAT on contradiction)
        assert all(p.is_theorem_proven for p in proofs)
        assert all(not p.is_satisfiable for p in proofs)
