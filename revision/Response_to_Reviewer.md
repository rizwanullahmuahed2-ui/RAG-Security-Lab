---
title: "Response to the four review comments"
subtitle: "Executed revisions and remaining verification boundaries"
lang: en
---

The manuscript now separates the previously reported extractive study (Study A) from a newly executed generative evaluation (Study B). The response below describes changes actually made. No result has been invented, and planned independent human review is not presented as completed work.

## Comment 1. Conduct experiments with a real LLM

**Response.** We added an executed API experiment using **gpt-4.1-mini-2025-04-14**, rather than attributing deterministic sentence-extraction results to a language model. Study B uses text-embedding-3-small at 1,536 dimensions, exact cosine retrieval of 30 candidates, optional TF-IDF reranking, and five final passages. The generator uses temperature 0 and at most 64 output tokens, with no fallback. All 376 distinct study requests returned the requested snapshot and a normal stop reason; there were no API errors or truncations. Reused identical requests produce 1,280 condition rows, not 1,280 independent responses.

Without defense, the designated false value appears alone in 34/64 targeted outputs (53.1%), compared with 0/64 under matched unrelated poison. Reranking reduces the count to 17/64. Filtering rejects all base insertions, while accepting the identical poisoned text restores 34/64 false-only outputs under filtering alone. Exact API requests, responses, usage, contexts, embeddings, and hash manifests accompany the revision.

**Locations.** Abstract; Sections 4.1, 4.4–4.6; Sections 5.1–5.4; Table 4; Figure 2; Data availability; `experiment/`.

**Boundary.** This is one real model snapshot and an exploratory numerical-answer subset. Primary outcomes are automatic numerical matches. Independent human semantic adjudication is still pending. The original extractive results remain separately attributed in Section 5.5 and are not pooled with these outcomes.

## Comment 2. Align the study with the research questions

**Response.** We rewrote the research questions and added Table 1, explicitly mapping each question to its controlled comparison, denominator, outcome, and result section. The result structure follows the same order:

1. RQ1: target specificity, tested with targeted/unrelated and targeted/truthful comparisons.
2. RQ2: supporting-evidence availability, exposure, and generated-value outcomes.
3. RQ3: defense ablations, paired prevention/restoration, and accepted-label compromise.
4. RQ4: clean utility cost, with the metric stated explicitly.

The two RQ1 comparisons under no defense are the locally prespecified primary contrasts; remaining comparisons are secondary and exploratory. Ambiguous historical hypothesis numbering is replaced by this consistent question-to-result structure. Claims about evidence recovery now reflect each study's actual outcomes: unlike Study A, reranking in Study B reduces all-support recall rather than improving it.

**Locations.** Section 3.1 and Table 1; Sections 5.1–5.5; Discussion and Conclusion.

## Comment 3. Add an independent test set and an unrelated-poisoning control

**Response.** We added a new-to-this-revision, output-held-out external subset from the pinned HotpotQA distractor validation split: 64 evaluated questions and 64 unrelated-control donors. A deterministic, output-independent selection rule produced 1,280 pairwise distinct context titles across the selected examples. The test corpus comprises 640 passages. Inputs, question IDs, supporting references, false values, prompt, defense rules, and planned contrasts were hashed before test generation; no generated test answer was used for tuning.

Five corpus conditions share the same test questions and clean corpus: clean; targeted poison; unrelated poison; truthful insertion; and accepted-label compromise. All positive conditions contain 64 insertions and exactly 120 whitespace words per inserted passage. A targeted/unrelated pair contains the **same designated false integer**, with the donor question replacing the evaluated question. The truthful control retains the evaluated question and inserts its reference value. Accepted-label compromise changes only trust and verification labels of the targeted text.

The targeted-minus-unrelated false-output difference is +53.1 percentage points, with an exploratory question-bootstrap interval of +40.6 to +65.6. Gold-only numerical accuracy differs by −25.0 points (−37.5 to −12.5). These intervals are conditional on the frozen corpus and saved responses.

**Locations.** Sections 4.2–4.3; Table 3; Section 5.1 and Tables 4–5; Section 7; input and generation freeze manifests.

**Boundary.** “External local test subset” does not mean the official hidden HotpotQA test set or independence from model pretraining. Original Study A raw inputs were unavailable, preventing exhaustive old/new overlap checking. Title disjointness does not prove semantic entity disjointness. These limitations are explicit, and no independent human source audit is claimed.

## Comment 4. Clarify the research methodology

**Response.** Section 4 now specifies a controlled, exploratory, repeated-measures factorial design. It identifies the statistical unit (64 questions), corpus construction and selection, reference and attack provenance, five interventions, four defenses, filter order, embedding dimensions, retrieval/reranking settings, prompt text, model snapshot, generation parameters, caching, failure policy, scoring equations, denominators, planned contrasts, and uncertainty procedure. The 1,280 condition rows are distinguished from 376 distinct generation requests and 64 question units.

We separate gold-only numerical accuracy, false-only outputs, exposure-confirmed targeted success, supporting-evidence recall, strict EM, abstention, paired prevention, correct-value restoration, and newly successful attacks. For example, reranking prevents 24/34 baseline targeted successes, restores 11/34 reference values, and introduces seven new successes; the net attack reduction alone would hide these transitions. Rejected-label filtering is explicitly an idealized eligibility check, and the accepted-label control identifies its authority boundary.

**Locations.** Sections 3.2–3.4 and 4.1–4.6; Tables 2–7; Section 7; Appendices A–B; reproduction README and scripts.

## Verification status for submission

The real LLM experiment, frozen external subset, matched controls, analysis tables, figure, and editable manuscript are complete. Independent human semantic review, original-archive re-execution, and exhaustive historical-data overlap verification are **not complete**. Blank blinded review sheets and a rubric are supplied. The manuscript states these boundaries and avoids claiming human-validated ASR, certified robustness, a public archive, or deployment approval.

The original pipeline diagram and both historical plots are preserved unchanged as Figures 1, 3, and 4. The new real-LLM comparison is Figure 2. Captions distinguish historical extractive evidence from new generative evidence; the original curves were not reconstructed from unavailable raw archives.
