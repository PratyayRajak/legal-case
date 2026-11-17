# Evaluation Harness

## Overview

The evaluation harness measures extraction accuracy, citation accuracy,
rule precision/recall, and cross-language consistency.

## Running Evaluation

```bash
python eval/run_eval.py --data-dir eval/data --output-dir eval/reports
```

## Metrics

All metrics are sliced by: **language** (hi/en/mixed), scan quality, case type.

| Metric | Description | CI Gate |
|--------|-------------|---------|
| Field accuracy | Exact match for dates/enums, fuzzy for names | > 80% |
| Hallucination rate | Fields with values but no verifiable citation | < 5% |
| Citation accuracy | Cited page contains the answer snippet | > 90% |
| Retrieval recall@k | Top-k retrieval contains the answer | > 85% |
| Rule precision/recall | Per rule | No regression |
| Cross-language consistency | Same case in Hindi and English → same fields | > 95% |
| Ragas faithfulness | LLM judge for Q&A | > 0.75 |

## Label Format

See `eval/data/labels/` for the ground truth JSON format.

## Synthetic Data

Run `python scripts/synth_docs.py` to generate synthetic test PDFs
with known ground truth (Hindi, English, mixed, digital, scanned).
