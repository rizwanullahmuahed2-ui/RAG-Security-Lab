# October 2026 refresh

The dashboard now separates initial, empty, custom-question and saved-run states. It adds literal-text search, evidence trust/source columns, safe source links and a combined answer/configuration/data-hash export. Unreadable saved runs are skipped with an explanation instead of preventing the app from opening.

Backend fixes preserve source URLs through reranking, check question/attack pairs rather than attack IDs alone, validate poison budgets against the selected experiment, and make generated CSV line endings deterministic. Manifest hashes now match the committed LF files on Linux as well as regenerated files on Windows. `pytest.ini` restricts discovery to the maintained tests; historical backup directories are not runnable test suites.

Verified locally on 21 October 2026:

- `python -m pytest -q`: **148 passed**.
- `python main.py --validate-only`: 224 documents, 225 chunks, 364 questions and 104 poison passages validated.
- `python main.py --offline --experiment clean --split test`: 112 questions evaluated, seed 42, no injected passages. [Saved summary](docs/validation/clean-test-summary.csv).
- Browser walkthrough: initial state, question execution and evidence view; screenshots show local execution.

These checks do not repeat the entire historical multi-seed benchmark in `VALIDATION.md` or establish live LLM performance. Default embeddings and generation are offline lexical/extractive components. The research manuscript is still pending delivery; see `research/README.md`.
