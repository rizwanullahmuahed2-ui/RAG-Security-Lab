# Original-data and provenance audit

Repository: `rizwanullahmuahed2-ui/RAG-Security-Lab` at commit `6f76858df91277e4b962ee94b4286a25cfe08d4d`. Scope: the verified selected text snapshot; no repository code was executed and no network/model call was made.

## Verified dataset

| Material | Legacy | Canonical |
|:--|--:|--:|
| documents | 56 | 224 |
| chunks | 21 | 225 |
| questions | 28 | 364 |
| poisoned_passages | 20 | 104 |

All identifier, document/chunk/question relationships and one-to-one target/poison links pass. The original 56 document records, 21 chunks, 28 questions, and 20 attacks retain their legacy field values. Only 20 legacy documents originally had chunks; 36 additional legacy documents are indexed in the canonical corpus. Each of 224 documents has at least one of the 225 chunks.

## World Bank values and paired questions

Every saved API response body matches its stored SHA-256 and parsed payload. The 12 series each contain 14 nonmissing observations for Afghanistan, 2010–2023. Independent Decimal half-up formatting reconstructs all 168 WDI documents, 336 question phrasings and 84 attack rows field-for-field, as part of a full independent reconstruction of all four canonical tables. No repository function was called.

| Indicator | Observations | Split |
|:--|--:|:--|
| AG.LND.AGRI.ZS | 14 | development |
| AG.LND.FRST.ZS | 14 | development |
| EG.ELC.ACCS.ZS | 14 | development |
| IT.CEL.SETS.P2 | 14 | development |
| IT.NET.USER.ZS | 14 | validation |
| NY.GDP.MKTP.CD | 14 | validation |
| NY.GDP.PCAP.CD | 14 | validation |
| SP.DYN.IMRT.IN | 14 | validation |
| SP.DYN.LE00.IN | 14 | test |
| SP.DYN.TFRT.IN | 14 | test |
| SP.POP.TOTL | 14 | test |
| SP.URB.TOTL.IN.ZS | 14 | test |

The two phrasings of an observation share their reference, source chunk and split. They are 168 fact groups, not 336 independent facts. Canonical question counts are development 140, validation 112 and test 112; their target counts are 48, 28 and 28. The paper reports prior inspection, so split names alone do not make these fresh final test data.

## Question coverage and record length

Only 188 of 224 documents and 188 of 225 chunks are directly gold-linked by the 364 questions. All 36 newly indexed legacy documents have no such question. The two low-trust mineral chunks rejected by the gate have zero gold-linked questions. This does not invalidate relationship checks, but limits a clean-cost interpretation: the benchmark does not directly test losing those legitimate facts. One question is typed multi_document while the schema provides a single gold document/chunk link.
The 56 inherited document records contain 36–177 whitespace words (median 79), and 168 WDI records 37–42 words (median 41). The 104 poisons are also short (legacy median 31 words, WDI median 30). These are bounded benchmark records, not evidence of 224 independent long-form source documents.

## Label boundary

Canonical document labels: `{"high/verified": 187, "medium/verified": 35, "low/verified": 2}`.
Canonical chunk labels: `{"high/verified": 188, "medium/verified": 35, "low/verified": 2}`.
The declared gate accepts 223/225 clean chunks. Two low-trust but verified inherited mineral documents/chunks are rejected. All 104 original attacks are untrusted and unverified, so exclusion is fixed by the supplied labels. Saved WDI numbers can be checked against their payloads; inherited factual claims and the authority/authentication process for labels remain a separate unresolved issue.

## Paper identity and implementation version

The repository research manifest declares the same original 18-page PDF SHA-256 as the local original-figure manifest: `87059e66898a6aaecede4d4d8224e2de97ed045f79b822eb2d903fbd3cc7533f`. The text snapshot does not contain the binary PDF itself. Repository metadata assign no manuscript publication date, venue or DOI.
The current workbench is not the historical principal source snapshot. Its default budgets are 0/10/20/50/104 versus the principal study’s 0/10/30/60/104. Current active names are hashing-lexical-v2:1024d and extractive-evidence-v2. Current offline retrieval ranks sentence coverage/proximity with vector similarity as a tie-breaker, while the principal report describes pure exact cosine candidates with its older extraction behavior. Configured neural-model names do not show that neural components or an LLM ran.

## Separate committed targeted validation

The committed summary reports 364 clean questions (355 matches), 364 attacked questions with ten own-assertion copies (337 matches, 27 attacks), and 364 filtered questions (355 matches, zero attacks): 1,092 condition rows under a different per-target protocol. The 364-entry synthetic pool is present and its payload hashes and question/reference links pass. Full response records were excluded from this snapshot, so the reported outcome counts are not freshly rescored here.
All four summary input checksums match CRLF conversions of the current LF canonical CSVs. This precisely explains those input-hash differences. Of 35 recorded source files, 29 match current bytes and six differ: src/config/config.py, src/data/loaders.py, src/defenses/reranker.py, src/evaluation/runner.py, src/generation/rag_pipeline.py, src/retrieval/retriever.py. Current source is not a byte-identical historical diagnostic snapshot.

## Checks passed

- All 117 inspected text files match the supplied Git-blob/SHA-256 snapshot manifest.
- Counts 224/225/364/104, unique identifiers, all reference relationships, and attack/query/value linkage verified.
- All canonical CSV hashes match dataset_manifest; synchronized root documents.csv is byte-identical.
- All 12 World Bank saved response hashes match bodies and payloads; 168 nonmissing AFG indicator-year observations produce exactly 336 deterministic phrasings and 84 targeted attacks.
- All four canonical tables reconstructed field-for-field using independent audit logic from legacy CSVs and saved WDI records; no repo builder was executed.
- Inherited records preserve legacy field values; legacy unindexed documents are now covered.
- 223 clean chunks pass the declared gate, two low-trust verified chunks do not; all 104 attacks are rejected-label by construction.
- The repository paper manifest and the figure-source manifest refer to the same original 18-page PDF fingerprint.
- All four separate diagnostic input hashes reconcile with current raw CSVs by LF-to-CRLF conversion; this is an encoding/line-ending difference, not evidence of changed table values.

## Still unresolved

- The principal 21,840 response archive, original effective config, exact historical source snapshot and run manifest remain absent from this current text snapshot; its ASR/accuracy curves cannot be freshly rescored here.
- Stored World Bank payload agreement verifies the recorded snapshot values, not external authentication of the original HTTP session or current revised World Bank estimates.
- 56 inherited document claims and verification labels have not been independently fact-checked; a verified label is not evidence of fresh review.
- No reviewer identity/authority, document signature validation, protected label-change workflow or operational trust-source authentication is established by the CSV metadata.
- Only 188/224 documents and 188/225 chunks have a gold-linked question. All 36 newly indexed legacy documents have no direct gold question; neither of the two rejected low-trust mineral chunks has one. Zero observed clean cost is weak evidence about rejecting task-relevant legitimate documents.
- Short templated WDI observations (median 41 words) dominate added data; legacy document records have median 79 words. Record counts do not establish the diversity of full original source documents.
- The three named question splits are not new output-held-out data when prior development has inspected them; WDI paired formulations and years are correlated.
- The 6.8MB diagnostic records file was excluded from the local snapshot. Summary counts 355/337/27 are reported, not response-level recomputed by this audit.
- Six current source files differ from the separate diagnostic source hashes; current code is not a byte-identical historical run snapshot.
- The repository snapshot does not supply the local HotpotQA/GPT-4.1-mini experiment archive; the local 64-question Study B remains a separate artifact bundle.
- No code execution, model inference, new attack experiment, live data refresh, or human semantic adjudication was performed in this audit.

## Meaning for the expert’s comments

The public repository materially closes the earlier data-access gap: full canonical corpus, legacy inputs, original attack pool, source snapshots, deterministic construction logic and configs are now inspectable. It does not retroactively publish or validate the missing principal run. The next plan can use these verified inputs to reconstruct or run a separately versioned experiment, while preserving reported historical numbers as historical until the exact archive is obtained or an explicitly new replication is executed.
