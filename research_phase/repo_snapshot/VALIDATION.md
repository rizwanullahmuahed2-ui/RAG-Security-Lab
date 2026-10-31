# Validation and measured outcomes

## September 28 update: poisoning levels and seed explanation

- Both requested modes are available: benchmark-wide dose comparisons and a single-question repeated-passage stress test.
- **91 tests passed**, including UI tests for stale-answer invalidation, fixed-seed level comparison and stress-mode selection, plus duplicate-count, provenance, retrieval and filtering checks.
- The benchmark run `20260926T063738Z_c4db3d85` tested 364 questions with seed 42 and no defense. At 10, 20 and 50 injected passages, it measured respectively **10, 17 and 40 successful poisoned answers** among the 104 targeted questions. These are actual offline pipeline outputs, not a forced trend.
- The stress comparison for the default targeted question injected 0, 1, 5, 10, 20 and 50 copies; the final context contained 0, 1, 5, 5, 5 and 5 target copies. This demonstrates the five-passage context limit and explains why an answer can plateau as more poison is added.
- Full stress evidence is saved under `results/question-comparisons/` when a comparison is run; users can download it from the dashboard. The ZIP includes the latest benchmark run, while earlier runs remain available in the local workspace.

The following section records the earlier full-grid validation; its original budgets and results are retained as historical evidence.

Validated locally on Windows with Python 3.13.9 and the versions in `requirements-tested.txt`.

## Completed checks

- Original baseline: 48 existing tests passed before changes.
- Improved implementation: **86 tests passed**, including original tests and regressions for scoring boundaries, attack attribution, boolean parsing, provenance, working-directory independence, reproducible generation, store isolation, exact-search tie handling, candidate starvation, run isolation/failure handling, fallback controls and Streamlit widget interactions.
- Dataset validation: **224 documents, 225 chunks, 364 questions, 104 poisoning passages**. All documents have searchable chunks; every question's document/chunk relationship is checked.
- Offline dataset reconstruction from saved snapshots produced a byte-identical dataset manifest and output hashes.
- Streamlit startup and the question-answer/evidence flow completed without application errors.
- Full offline benchmark: **21,840 observations** = 364 questions × 20 configurations × 3 attack-selection seeds (17, 42, 91).
- Result audit: no duplicate seed/question/condition/defense keys; every successful attack had its linked target poison injected and retrieved; clean and full-budget generated answers matched exactly across seeds.

## Final benchmark

Run: `20260921T061151Z_d1966106`. See `results/runs/20260921T061151Z_d1966106/manifest.json` for the precise configuration, input/source hashes and environment. This run used **hashing:1024d, exact cosine search, TF-IDF reranking, extractive generation**. A prior Chroma trial is retained locally as historical evidence; its approximate-ranking variability motivated the exact-search default. The packaged project includes the final exact-search run only.

Representative measured results (mean across seeds; rounded):

| Poison passages | Defense | Answer containment accuracy | Targeted attack success |
|---:|---|---:|---:|
| 0 | None | 82.42% | 0% |
| 0 | Reranking | 81.32% | 0% |
| 30 | None | 69.60% | 23.08% |
| 30 | Reranking | 71.15% | 17.95% |
| 104 | None | 3.57% | 73.08% |
| 104 | Reranking | 42.03% | 72.12% |
| 104 | Source filtering | 82.42% | 0% |
| 104 | Reranking + source filtering | 81.32% | 0% |

Attack success in this table uses all 104 targeted questions as its denominator. The separate injected-target metric is essential at smaller budgets: for example, at 10 injected passages with no defense, all-target ASR is about 8.97% but ASR among actually attacked targets averages 93.33%. Both denominators are exported.

Interpretation: lexical reranking recovered much of the supporting evidence under heavy poisoning, but did not reliably stop the extractive answerer from repeating the target false claim. Source filtering rejected all deliberately untrusted poisons, as expected under this restricted threat model. It does not establish safety against attacks through trusted sources.

## Not validated here

Neural embedding/reranking downloads, paid API generation, hosted GitHub Actions, and deployment under concurrent production traffic were not run. The inherited factual documents were not all independently reverified. Automatic scoring is still a transparent lexical heuristic; negation and temporal conflicts require review. Correlated years/paraphrases and synthetic attacks limit generalization.
