# Review and remediation

The review covered the supplied entry points and configuration plus the actual loaders, chunker, embedding, vector store, retrieval, defenses, generation, evaluation, dashboard, datasets, and tests in the Desktop project. Work was performed in the task workspace; the Desktop original was preserved.

| Finding | Consequence | Implemented change |
|---|---|---|
| 36 of 56 documents lacked chunks | Most of the added corpus was invisible to retrieval | Rebuilt missing chunks, retained existing gold references, added coverage regression test |
| Only 28 questions / 20 poisons | Weak coverage and limited dose comparisons | 364 questions / 104 poisons with sourced observation snapshots and family splits |
| Arbitrary substring matching | `34` could match `134` | Numeric/word boundaries, Unicode support, strict-match companion metric |
| Any poison could satisfy the attack prerequisite | Unrelated passage received credit for a targeted attack | Match injected/retrieved poison IDs to the exact target question |
| True and false values could both score positively | Conflicting answers looked successful | Separate ambiguous-answer flag and conservative verdict |
| Python truthiness of string `False` | Direct API callers could mark control questions targeted | Explicit boolean parsing in evaluator; invalid CSV booleans rejected |
| ASR denominator hid absent attacks | Low budgets could look safer just because targets were not attacked | Report all-target and actually-injected denominators separately |
| Old files were merged in fixed filename order | Old all-results files could overwrite new observations | Independent run directories; no cross-run merging |
| Backends could change after load failures | Results were not necessarily from the requested model | Explicit offline defaults, fallback disabled by default, actual backend manifest |
| Missing dataset/backend/environment provenance | Difficult to reproduce or compare results | Dataset/code hashes, config, versions, seeds, evidence and timing per run |
| Paths resolved inconsistently | Launching outside the project broke CSV loading | Resolve all configured paths from the configuration location |
| Trust/query/answer links were not checked | Corrupted tables could silently invalidate research | Cross-table provenance, query, ground-truth and attack integrity validation |
| Post-retrieval filtering | Poison could fill the candidate pool and starve legitimate evidence | Metadata predicate applied within vector retrieval plus final defensive check |
| Chroma ephemeral clients shared collection names | Sessions and tests could overwrite each other | Unique collection namespace for every in-memory store |
| Single unbounded vector insert | Larger corpora exceeded Chroma batch limits | Use the client-reported maximum batch size |
| Approximate search varied on identical clean corpora | Selection seeds could appear to affect clean results | Deterministic exact cosine backend is now default; Chroma remains configurable |
| Seedless generator used Python hash | Poison text could differ between processes | Stable SHA-256-derived seed |
| Hardcoded budget labels and chart ordering | Expanded budgets vanished from plots | Numeric dose plots and dynamic defense series |
| No filtering-only condition | Could not isolate the effect of filtering from reranking | Added filtering-only ablation |
| Dashboard cached mutable shared resources | Session interference and stale datasets | Session-local resources, input-signature invalidation, stored-run selection |
| Empty lexical vocabulary and invalid chunk parameters | Avoidable runtime failures | Deterministic empty-vocabulary handling and early validation |
| Optional model libraries were mandatory requirements | Unnecessary heavyweight installation | Separate core, development, optional-model and tested-version requirements |

The original test suite passed before changes (48 tests). Added regressions exercise the research-integrity problems, not merely file existence. See the final delivery message and `VALIDATION.md` for completed validation and measured results.

Remaining boundaries: inherited factual claims are not all reverified; the expanded benchmark is primarily numeric; attacks are deterministic templates; metadata filtering is not a general poison detector; no real neural-model/API evaluation has been completed in this session. There is no claim of production readiness or publication-ready generalization.
