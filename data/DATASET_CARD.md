# Afghanistan RAG poisoning benchmark

This benchmark tests controlled knowledge-base passage injection. It is not a current Afghanistan factbook, and poisoned passages are deliberately false experimental material.

## Contents

| Table | Original active input | Expanded |
|---|---:|---:|
| Documents | 56 | 224 |
| Searchable chunks | 21 | 225 |
| Questions | 28 | 364 |
| Poisoned passages | 20 | 104 |

Only 20 of the original 56 documents had chunks. The expansion indexes the other 36 while preserving all original chunk IDs and question references. Original inputs are retained in `data/legacy/`.

The 168 new documents each represent a distinct indicator/year observation for Afghanistan: 12 World Development Indicators series, 2010–2023 inclusive. Each observation has two deterministic question phrasings. These are 168 observations, not 336 independent facts. The dataset is deliberately narrow: numeric historical facts dominate. It is not a broad natural-language QA benchmark.

## Sources and reconstruction

Source: World Bank, World Development Indicators, source ID 2. Country: AFG. Raw JSON responses, exact response bodies, retrieval timestamps, request URLs, and SHA-256 hashes are saved under `data/sources/worldbank/`. `dataset_manifest.json` lists source and output checksums.

API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/898581-api-basic-call-structures

Series:

| Code | Measure |
|---|---|
| SP.POP.TOTL | Total population |
| SP.URB.TOTL.IN.ZS | Urban population share |
| SP.DYN.LE00.IN | Life expectancy at birth |
| SP.DYN.TFRT.IN | Total fertility rate |
| SP.DYN.IMRT.IN | Infant mortality rate |
| NY.GDP.MKTP.CD | GDP, current US dollars |
| NY.GDP.PCAP.CD | GDP per capita, current US dollars |
| IT.NET.USER.ZS | Individuals using the Internet |
| IT.CEL.SETS.P2 | Mobile subscriptions per 100 people |
| EG.ELC.ACCS.ZS | Access to electricity |
| AG.LND.AGRI.ZS | Agricultural land share |
| AG.LND.FRST.ZS | Forest area share |

Values are rounded to two decimal places with decimal half-up rounding. Questions explicitly request that precision. Missing values are skipped, never imputed; the saved snapshot has 168 non-null observations. Values describe their stated year and snapshot, not the present. Upstream series can be revised. Exact source values remain in the JSON and document notes.

The public source data remain subject to their applicable World Bank and upstream-provider terms; this project does not relicense them or claim World Bank endorsement. Source attribution and URLs accompany each document. Terms: https://www.worldbank.org/en/about/legal/terms-of-use-for-datasets

## Verification boundaries

New `verified` labels mean checked against the stored API response, not independently measured or certified. Legacy documents retain inherited labels and claims, which were not independently re-audited. Some legacy values may differ from revised WDI estimates. The legacy slice is separated in reports and assigned only to development.

## Splits and attacks

All observations and paraphrases from an indicator belong to the same split. The 12 alphabetically sorted indicator codes are partitioned into four development, four validation, and four test families. Legacy questions are development only. Splits partition evaluation questions, not KB visibility: the full legitimate KB is available in every run, as required for retrieval QA.

Every other year of each indicator has one targeted question and one controlled poisoning passage: 84 new targets plus 20 inherited targets. New attacks substitute a numeric value (normally 83% of the original) in a plausible-looking correction. They are synthetic benchmark attacks, not sourced facts. The attack table labels them `attacker_generated`, `untrusted`, and `unverified`; they are never merged into the clean document CSV.

Paraphrases of targeted questions are **transfer probes**, not unaffected control questions. A poison can affect them even though their `targeted_for_attack` flag is false. Attack success is attributed only to a question's explicitly linked poison. Collateral effects are reflected in overall answer accuracy and per-question evidence.

Budgets select a prefix of one seeded permutation, so smaller poison sets are nested within larger sets. Selection uses the full pool even when a question split is selected; injected-target counts reveal the actual exposure of that split.

## Interpretation

- Years and paraphrases are correlated. Do not treat all rows as independent samples.
- Wilson intervals are descriptive, not a claim of independent sampling or publication-level significance.
- Source filtering is an idealized provenance policy: injected records are untrusted by construction. Zero attack success under that policy does not establish protection against compromised trusted sources or forged metadata.
- Lexical containment cannot reliably understand negation, conflicting time references, or semantic equivalents. Inspect evidence and adjudicate a sample manually.
- Offline extraction does not model a reasoning LLM. Neural retrieval and API generation need separate, explicitly configured experiments.
