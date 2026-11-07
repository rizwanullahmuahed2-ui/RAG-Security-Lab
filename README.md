# RAG Security Lab

This project studies what happens when false passages enter a retrieval-augmented generation system. It includes the current research manuscript and saved model responses, plus a local dashboard for inspecting an earlier offline benchmark.

## Current research

- [Article: PDF](research/current/RAG_Security_Article.pdf) · [Word](research/current/RAG_Security_Article.docx)
- [Implementation report: PDF](research/current/Implementation_Report_FA.pdf) · [Word](research/current/Implementation_Report_FA.docx)
- [Response to the expert's comments](research/current/Response_to_Expert_FA.pdf)
- [Author's review of 72 responses](rag_security_revision_v2/manual_review/Author_Semantic_Findings_FA.md)
- [Evidence guide in Dari](rag_security_revision_v2/release/GITHUB_EVIDENCE_README_FA.md) · [Link register](research/current/Link_Register_FA.md)

Study C contains 62 questions, 620 clean passages and 2559 saved generative responses across three rounds. It compares targeted, unrelated and reference-consistent passages, with exposure and repetition controls. Study B is a post-hoc diagnostic analysis; study A is historical context. The exact original run archive for A was not recovered.

The author's manual review covers 72 selected responses. Its findings describe those cases; they are not a semantic accuracy estimate for the whole benchmark. Assistant review notes retain their original attribution. The manuscripts are unpublished; see the [author and version notes](research/README.md).

### Verify saved evidence

From the repository root, with Python 3.11+:

```sh
python rag_security_revision_v2/release/verify_evidence.py
```

This checks the published hashes, saved responses, 5208 condition rows, 196 summary cells, 48 paired-transition counts and 244 historical files. It uses the standard library, makes no new model calls and leaves published evidence unchanged. Look for `"verification": "passed"`.

## Try the local dashboard

![Offline evidence dashboard](docs/dashboard.png)

The original app runs without model downloads or paid APIs. It uses lexical embeddings, exact cosine search, TF-IDF reranking and sentence extraction. These dashboard results are separate from study C's saved generative experiments.

Use Python 3.11–3.13. Create and activate a virtual environment, then run:

```sh
python -m pip install -r requirements-dev.txt
python main.py --validate-only
python -m streamlit run app.py
```

Open http://localhost:8501. Choose a question, run it with no injected passages, then change the poison budget or defense. Compare the answer with the passages actually retrieved. The corpus contains 224 documents, 225 chunks, 364 questions and 104 controlled poisoning passages.

## Development

```sh
python -m pytest -q
python main.py --offline --experiment clean
```

The [experiment guide](docs/EXPERIMENTS.md) covers seeds, attack selection, scoring and exports. The [dataset card](data/DATASET_CARD.md) records sources and splits. Current code lives in `src/`; `research_phase/repo_snapshot/` and the revision directories retain historical material needed to check the research. Earlier workbench measurements remain in [VALIDATION.md](VALIDATION.md).

Lexical answer matching can miss negation and paraphrases. Source filtering assumes trustworthy ingestion metadata. Read the retrieved context and study-specific limits before interpreting an attack-success number. HotpotQA/Wikipedia and WDI material retain their source attribution and terms.
