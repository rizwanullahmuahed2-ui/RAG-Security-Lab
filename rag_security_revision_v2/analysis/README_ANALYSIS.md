# Study C saved-output analysis

`analyze_study_c.py` analyzes archived requests, contexts and responses. It never
constructs an API transport and cannot create human judgments. Run it only after
the corresponding generation freeze and saved provider outputs exist:

```sh
python analysis/analyze_study_c.py \
  --data-root data --run-root study_c --output analysis/study_c
```

The script verifies the runner's design and generation seals, exact payload
hashes, raw response hashes, returned model IDs and, when present, the completion
archive hash. Duplicate provider response IDs across distinct supposed fresh
calls are rejected. The script supports arbitrary frozen question counts and
round counts; the study protocol determines those quantities.

The main automatic endpoint is `strict_target_choice_proxy`: a tightly restricted
concise numeric answer matching the designated target. The previous numeric
containment rule is separately reported as `old_numeric_false_only`. Neither is
independently validated semantic endorsement or factual correctness. Reference
choice, EM, F1, literal and nonliteral abstention diagnostics, and retrieval and
exposure metrics remain separate. Every actual semantic judgment is unassessed
until real review takes place.

Rates first average the planned rounds within a question and then average across
questions. Condition-row reuse and repeated provider calls do not create new
independent questions. Minimum/maximum rates across the fresh rounds describe
observed variation; they are not confidence intervals. No significance test or
population interval is produced.

Missing, malformed, empty, truncated and non-normal generations are unknown for
the main answer endpoints. A partial archive is refused by default. To obtain
explicit bounded diagnostics, add `--allow-incomplete`. Lower and upper rates use
the planned denominator. Difference bounds allow either member of a pair to be
unknown, and complete-question/paired-complete-question estimates carry their
reduced denominators as sensitivity analyses. Retrieval metrics remain observed
when only generation is missing.

Outputs include:

- `scored_rows.csv`: every frozen condition context joined to every planned round;
- `summary.csv` and `summary_by_round.csv`: question-weighted rates and round data;
- `contrasts.csv`, `paired_defense_outcomes.csv`: paired comparisons and separate
  prevention, reference restoration and newly introduced proxy successes;
- `strata_summary.csv` and `exposure_conditioned_summary.csv`: explicit strata and
  exposure-conditioned denominators;
- `cases.jsonl` and `case_index.csv`: all qualifying automatic-proxy cases and
  deterministic selection of illustrative distinct questions;
- `study_c_outcomes.png` and `.pdf`: plots of actual complete saved output only;
- `analysis.json` and `analysis_manifest.json`: definitions, integrity status,
  machine-readable results and output hashes.

For a partial core grid the main figure is withheld. Figures never substitute
zero for missing outputs. Cost is labelled conservative committed cost, rather
than an invoice amount. Token use counts saved logical calls rather than every
condition row sharing one reply.

`test_analyze_study_c.py` uses expressly synthetic data in temporary directories;
its provider has no sockets, credentials or network functions. The tests cover
missingness bounds, paired missingness, the within-question round estimand,
distinct prevention/restoration/new failures, the full saved-run join, all three
experiment modules, and tampered raw output. Those fixtures are not Study C data
and are deleted after testing.
