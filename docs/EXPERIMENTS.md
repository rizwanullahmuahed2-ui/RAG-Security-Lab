# Experiment and evidence guide

Detailed controls, reconstruction steps, output artifacts, and interpretation for RAG Security Lab. Commands run from the repository root with its Python environment active. For installation and a first walkthrough, see the [project README](../README.md).

## Experiments

```bash
python main.py --offline --experiment clean
python main.py --offline --experiment all --seeds 17 42 91
python main.py --offline --experiment all --split test --seeds 17 42 91
python -m pytest -q
```

`--experiment` also accepts `poisoning`, `reranking`, `source_filtering`, and `filtering` (reranking plus filtering). The default grid is five budgets (0, 10, 20, 50, 104 passages) × four defenses = 20 configurations per seed. All questions are evaluated by default. A three-seed full run produces 21,840 per-question observations.

Use `--config path/to/config.yaml` for an alternative configuration. `--offline` forces hashing, lexical reranking, and extractive generation. Selection seeds must be unique integers in `[0, 2**32)`.

### Comparing poisoning levels and understanding seeds

In the sidebar, select any available poison count (including 10, 20, and 50). Changing a setting hides the previous answer until you click **Run question**, so an old answer cannot be mistaken for a fresh result. The UI shows the count at which the selected question's poison enters the KB and how many poisoned passages reached the final context.

For an aggregate comparison, click **Compare poisoned answers: 0, 10, 20, 50** in the experiments tab. It tests the same question split, seed(s), and selected defense at all four levels and saves the results with the usual provenance. The count table and chart show successful poisoned answers, targets actually attacked, and the number of questions tested. `n_poisoned_answers` is also included in exported summaries.

A **seed** is a number controlling the shuffle used to select passages. Seed 42 gives the same selection on repeated runs with the same dataset. At that seed, 20 passages contains the first 10 plus 10 more. Seed 17 gives a different shuffle, not a stronger attack. Start with 42; enter `17 42 91` to test sensitivity to three selections. It is an attack-selection seed, not an LLM randomness/temperature setting.

In **Ask & inspect**, choose between **Benchmark: attacks across different questions** and **Stress test: repeat attack on this question**. The stress test inserts exactly the selected number of copies of one assigned false passage, all marked untrusted. These are deliberately duplicate evidence, not independent sources; the seed does not change their text. Only questions with an assigned attack are available in this mode.

Click **Compare this question across levels** to test 0, 1, 5, 10, 20, and 50 passages against the same question and defense. The table shows actual answers and target copies reaching context; JSON downloads include evidence, settings, backends and dataset hashes. Results are also saved in `results/question-comparisons/`. This stress test stays separate from benchmark-wide summaries. Once the finite retrieved context is saturated, adding more copies may leave the answer unchanged.

More poisoned passages do not guarantee a different answer to every individual question. New passages may attack other questions, fail retrieval, be filtered, or leave the answerer's best sentence unchanged. The default offline generator sees only the final context (usually five passages) and deterministically selects a sentence; it is not a reasoning LLM. The benchmark measures whether poisoned-answer counts rise, plateau, or fall; it never forces a rising curve.

Configuration paths resolve from the location of `config.yaml`, so launching `main.py` with an absolute path works from other directories. `reranking.final_k` controls reranked context length; `retrieval.top_k` controls the other conditions. Keep them equal for comparable context budgets.

`vector_db.backend: exact` scores every eligible vector and breaks ties by chunk ID, avoiding approximate-search variability. This is appropriate for the included corpus. Set it to `chroma` for larger experiments; Chroma uses approximate cosine search and may produce small ranking differences across rebuilt indexes. The experiment runner always uses fresh in-memory indexes; `persist_directory` remains available to direct Chroma library callers but is not used by the runner.

## Dataset and provenance

The original project contained 56 documents but indexed only 20 of them. All 56 are now searchable. The additional 168 documents are World Bank WDI observations covering 12 indicators for 2010–2023. Each has two question phrasings, yielding 336 new questions. Original inputs remain under `data/legacy/`.

```bash
# Deterministic rebuild from saved responses; no network required:
python scripts/build_dataset.py
# Fetch only missing source snapshots:
python scripts/fetch_worldbank.py
# Intentionally update source snapshots, then rebuild:
python scripts/fetch_worldbank.py --refresh
python scripts/build_dataset.py
```

Canonical inputs are `data/raw/*.csv`; root `documents.csv` is a synchronized compatibility copy. Edit the canonical inputs for ordinary experiments. The builder intentionally reconstructs from `data/legacy/` and the saved API snapshots, so preserve custom edits separately before invoking it.

Read [the dataset card](../data/DATASET_CARD.md) for provenance, rounding, correlated paraphrases, family-level splits, source terms, and verification boundaries. New observations are checked against saved API responses. The original 56 documents retain inherited verification labels and have not all been independently re-audited.

## What a run saves

Every run receives a unique `results/runs/<timestamp>_<id>/` directory:

- `manifest.json`: completion status, actual backends, dataset/code hashes, package versions, seeds, scope and limitations.
- `config.json`: effective configuration.
- `results.csv`: per-question answers, scores, exact target exposure, retrieved text and metadata, latency, split and seed.
- `summary_metrics.csv`: per-condition, per-seed metrics and descriptive Wilson intervals.
- `seed_summary.csv`: mean and standard deviation across attack-selection seeds.
- `by_category.csv`, `by_split.csv`: subgroup summaries.
- `figures/`: dose-response and defense comparisons from actual measured results.

`results/latest.json` points to the latest completed run. Old runs are never merged into new summaries. Failed runs retain a failure manifest and never replace that pointer. Run evidence can be large and is excluded from Git by default.

A fresh clone starts without completed benchmark runs in the dashboard. [VALIDATION.md](../VALIDATION.md) records historical local measurements; their full run directories are not committed. The separately committed `results/targeted-mode-validation/` contains targeted-mode validation artifacts. Generate a new run to inspect current results and provenance.

## Scoring and threat model

An attacker can add passages, but cannot alter legitimate documents or assign trusted ingestion metadata. Compare no defense, reranking, source filtering, and both defenses. Source filtering runs inside vector retrieval so untrusted documents cannot exhaust the candidate pool. This is an idealized provenance policy, not a learned poison detector.

The results distinguish:

- Any poison retrieved vs the specific target's poison retrieved.
- Target selected for attack vs its poison actually injected at this budget.
- Answer containment accuracy vs strict normalized exact match and token F1.
- All-target attack success rate vs attack success among actually attacked questions.
- Ambiguous answers containing both true and false values, which require manual review.

Attack success requires the target's own poison in the final context, a match to its false claim, and no simultaneous match to the true value. Numeric boundaries prevent `34` matching `134`. Scoring remains lexical: negation, semantic equivalence, and temporal inconsistencies still require human assessment. Exported evidence makes this review possible.

WDI years and paraphrases are correlated, and seed variation only changes poison selection. Wilson intervals are descriptive; seed standard deviation is not a significance test. A filtering defense with zero ASR under trusted metadata is not proof of safety against compromised trusted sources.

## Optional neural and API backends

```bash
python -m pip install -r requirements-models.txt
```

Set `embedding_backend: sentence_transformers` and `reranking.backend: cross_encoder` in `config.yaml`. Initial use downloads model weights. Leave `allow_fallback: false` for fail-fast experiments; explicitly enable fallback only when that is part of the experiment design. The manifest records what actually loaded.

For generative experiments, the existing Anthropic integration remains available: set `llm_backend: anthropic`, supply a provider-supported `llm_model`, and set `ANTHROPIC_API_KEY` in your environment. Do not put credentials in project files. API generation incurs provider usage; it was not used for the supplied validation run. A full grid generates one request per question per condition per seed.

The offline pipeline is tested here; the neural and paid API paths require separate integration validation in your chosen environment.
