# Reproduction package: external generative RAG poisoning study

This package contains an **executed** extension, not simulated LLM outcomes.
The model was `gpt-4.1-mini-2025-04-14`. No local model was used in this study.

There are 64 evaluated questions, 64 unrelated-control donor questions, 640 clean
passages, five corpus conditions, and four defenses. The resulting 1,280 condition
rows share 376 distinct API payloads/responses; the remaining 904 rows reuse
identical requests. These are not 1,280 independent draws. No human judgments have
been completed. Read the manuscript's scope and independence limitations.

## Recompute outcomes without an API key

Use Python 3.12 with NumPy (recorded version 2.3.5):

```bash
python analyze_experiment.py
```

This verifies frozen input hashes, request and response hashes, returned model IDs,
complete condition coverage, equal insertion word counts, title disjointness, and
specified payload equivalences. It writes numerical scores and descriptive tables.
It does not validate factual endorsement or independently authenticate sources.

## Files

- `config.json`: frozen model, retrieval, prompt, matching, scoring, and analysis rules.
- `freeze.json`: initial input hash manifest, created before generated test outputs.
- `generation_freeze.json`: pre-generation context/request hashes and execution-code hash.
- `test_questions.json`: 64 questions, annotated values, designated false values, supporting facts, source IDs/titles.
- `control_donors.json`: 64 source-title-disjoint donor questions and their references.
- `clean_documents.json`: 640 original benchmark context paragraphs with titles.
- `insertions.json`: artificial targeted, unrelated, and truthful pools; each passage has 120 whitespace words.
- `source_dataset_metadata.json`: pinned upstream dataset URL, revision, and full-file SHA-256.
- `embeddings.npz`, `embedding_texts.json`, `embeddings_manifest.json`: saved normalized API embeddings and provenance.
- `contexts.jsonl`, `requests.json`: final contexts and exact unique API payloads, without credentials or HTTP authorization headers.
- `responses.jsonl`, `completion.json`: real API responses, request IDs, response hashes, usage, timing, and completion status.
- `scored_results.csv`: all 1,280 response-linked condition records.
- `summary.csv`, `contrasts.csv`, `paired_defense_outcomes.csv`, `analysis.json`: automatic results and audit checks.
- `posthoc_output_diagnostics.json`: explicitly post hoc flags for reference-value matches accompanied by UNKNOWN language; primary scores unchanged.
- `human_review_blinded.csv`, `human_review_key.csv`: blank independent-review templates and separate condition key.
- `prepare_experiment.py`, `run_experiment.py`, `analyze_experiment.py`: data selection, execution, and saved-response analysis.

## Fresh replication

Retain this release unchanged. Work in a separate copy and record it as a fresh
replication. Use the exact frozen inputs and existing embeddings/contexts if the
goal is generation replication; remove only that copy's `responses.jsonl` and
`completion.json` before requesting fresh outputs. Keep all previous responses in
this release. Run:

```bash
python run_experiment.py --stage generation --workers 6
python analyze_experiment.py
```

The execution script reads `OPENAI_API_KEY` from the process environment, or from
the `.env` file in the parent of the revision folder. Credentials are not included
in this package and must never be written into result or request files. Existing
cache entries are verified and reused. The script refuses changed frozen inputs,
model mismatch, and silent model/backend fallback. Fresh API inference is billable
and need not reproduce the saved outputs exactly, even at temperature zero.

To regenerate selected data from the pinned upstream file in a new folder, install
PyArrow (recorded version 26.0.0), obtain the source URL from the metadata manifest,
verify its SHA-256, and run `prepare_experiment.py <source.parquet>`. The selection
script refuses to replace an existing freeze. It excludes only declared patterns;
it does not prove semantic/entity disjointness or historical raw-data non-overlap.

Retrieval execution requires NumPy 2.3.5 and scikit-learn 1.8.0. Preparation used
Python 3.12.14. No OpenAI SDK is required; execution uses Python's standard HTTPS
client with the environment's configured proxy and CA trust. The embedding endpoint
uses `text-embedding-3-small`; saved vectors are the reproducible retrieval artifact
because no immutable embedding snapshot identifier is supplied by the provider.

## Dataset attribution and artificial material

HotpotQA: Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William W. Cohen,
Ruslan Salakhutdinov, and Christopher D. Manning. 2018. *HotpotQA: A Dataset for
Diverse, Explainable Multi-hop Question Answering*. EMNLP, 2369–2380.
https://aclanthology.org/D18-1259/ and https://hotpotqa.github.io/.

Source distribution: https://huggingface.co/datasets/hotpotqa/hotpot_qa, revision
`1908d6afbbead072334abe2965f91bd2709910ab`. Dataset/Wikipedia-derived text and the
adapted insertion material are shared under CC BY-SA 4.0:
https://creativecommons.org/licenses/by-sa/4.0/.
Titles and example IDs preserve attribution links to source benchmark material.
Inserted records are deliberately artificial. Targeted and unrelated statements
contain false values and must not be ingested as factual reference documents.
No new licensing declaration is made for the authors' manuscript.

Historical raw artifacts described in the original PDF were not supplied and are
not included here. Their historical audit claims were not rerun in this revision.
