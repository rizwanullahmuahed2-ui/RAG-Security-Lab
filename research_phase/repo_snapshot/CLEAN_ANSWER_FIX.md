# Clean-answer correction — 28 September 2026

The configured system uses an offline extractive answerer, not a generative LLM. Previously the capital question returned Herat or a provincial capital even though the Kabul passage was present. Raw token overlap discarded the country name and accepted the first sentence sharing the word capital. Hashing retrieval also ranked some paraphrases poorly.

## Changes

- Offline lexical normalization handles possessives, common inflections, source-attribution boilerplate and two domain aliases (Afghan/Afghanistan and WDI/World Development Indicators).
- Offline retrieval examines all eligible passages in this small corpus and ranks their best sentence by weighted query-term coverage, proximity and density, using cosine similarity as a tie-breaker. Filtering still applies before ranking. This is not scalable neural retrieval.
- Sentence selection retains entity terms, respects explicit years and expects a number for numeric questions. It abstains on insufficient lexical support. These are heuristics, not guaranteed semantic entailment or conflict detection.
- No answers, question IDs, ground truth, poison IDs or trust labels are used by the relevance scorer. A synthetic poisoned sentence can still cause a false answer in attack experiments.
- The dashboard invalidates cached resources and displayed answers when source code changes, and names the offline engine more clearly.
- New backend identifiers are `hashing-lexical-v2:1024d` and `extractive-evidence-v2`. Existing run files and the earlier paper results are historical measurements of the old backend and have not been rewritten. Rerun experiments before updating paper claims.

## Validation

105 tests passed, including 14 new regressions for national/provincial capitals, paraphrases, dates, totals versus per-capita values, missing-country evidence, poisoned evidence and the actual Streamlit custom-question flow at zero poison.

On the unchanged 364-question clean benchmark, lexical answer matches improved from 300/364 (82.4%) to 355/364 (97.5%). Labeled relevant-chunk recall improved from 340/364 (93.4%) to 361/364 (99.2%). These are diagnostic benchmark metrics, not independently adjudicated factual accuracy. Nine answer-match failures remain, including insufficient-evidence responses, abbreviation/label differences and ambiguous or conflicting inherited source material. No dataset facts were changed.

## Use

Stop the running Streamlit server with Ctrl+C and restart it from this project directory:

```powershell
python -m streamlit run app.py
```

Set Injected passages to 0, choose no defense, and run `what is capital of afghanistan`. The first retrieved passage should be `CHK-002-01`, and the answer should begin `Kabul is the national capital of Afghanistan`.

Older saved benchmark runs remain unchanged. The deployment keeps backups of replaced files under `backups/clean-answer-fix-<timestamp>/`.
