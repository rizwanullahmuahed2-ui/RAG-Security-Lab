---
title: "Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning"
subtitle: "An exploratory comparison of retrieval integrity, answer corruption, and provenance controls"
author:
  - Rizwanullah Muahed
  - Ramiz Mumtaz
  - Ebrahim Adham
  - Masihullah Yaqubi
  - Rohid Sharifi
date: ""
lang: en
---

Department of Research and Development (R&D), Ministry of Communications and Information Technology

**Evaluation scope.** C supplies the prospective generative evidence; B is retrospective diagnostic material and A provides historical context. The author reports a completed semantic inspection of 72 cases. Study C below has a completed, hash-checked execution archive; its outcomes remain automatic proxies.

## Abstract

Retrieval relevance does not ensure that a retrieval-augmented generation system follows valid evidence. We examine question-addressed knowledge-base insertions through a source-screened follow-up, an audited generative archive and historical extractive evidence. The follow-up C uses 62 calendar-year or dated-population questions, 620 shared clean passages, unit-matched donors and equal-length targeted, unrelated and reference-concordant insertions. A locally frozen protocol combines API embeddings, gpt-4.1-mini-2025-04-14, four defense arms and three fresh generation rounds per unique payload. Separate experiments impose insertion exposure while retaining both supporting passages, or repeat identical insertions at fixed target coverage. Across questions, the strict concise target-choice proxy averages 37.6% under targeted insertion and 0.0% under unrelated insertion; reranking gives 21.0%. When exposure and supporting evidence are retained by construction, targeted insertion gives 16.1% and unrelated insertion gives 0.0%. With two and five copies per target, the undefended proxy rises to 53.8% and 96.8%. Reranking also reduces clean reference-choice outputs, while a supplied-label filter loses its target-output protection when identical text receives accepted labels. These results distinguish exposure, evidence retention and answer production within this pipeline. A separate scoring implementation reproduces the archived B numerical results, but its source audit finds five ambiguous references, six requiring correction and ten target claims whose falsity is not established by the available evidence. The matching principal execution archive of historical A remains unrecovered. Source screening is AI-assisted, and these automatic proxies do not establish semantic attack success. The author reports a completed source-based semantic case inspection; repeated calls and shared-corpus condition rows do not increase the independent question count.

**Keywords:** retrieval-augmented generation; knowledge-base poisoning; source validity; real-LLM evaluation; provenance; semantic review

## 1. Introduction

Retrieval-augmented generation (RAG) connects a language model to external evidence [11–13]. In institutional settings, the knowledge base may include administrative documents, reports, public statistics, and policy material. A poisoned document can be relevant to a question while supplying a false answer. Retrieval relevance therefore cannot serve as a factuality or source-authentication guarantee.

Prior research establishes targeted corpus poisoning as an attack against generative RAG [1–4]. The practical evaluation problem is broader than malicious retrieval alone: does supporting evidence remain available, does the attack enter the final context, and does the answer adopt its intended false value? These events may diverge. A defense can recover useful evidence without resolving a conflict between true and false claims.

Study A examined these distinctions using an Afghanistan-focused corpus and an extractive answerer [25]. Its reported deterministic outcomes describe that implementation, but they cannot estimate generative LLM behavior. Its inspected development splits and absence of matched unrelated poison also prevented an output-held-out test of attack specificity. A previously reported 24-response generative development check did not resolve these design limitations.

Study B extended the analysis through an external evaluation whose outputs were originally held out until the local freeze. Its observed cases now also inform the subsequent audit and follow-up design. It directly compares targeted poisoning with an unrelated control and a relevant reference-concordant-insertion control, keeping insertion count, word length, metadata, and corpus fixed. A metadata-only accepted-label intervention tests the source gate's authority assumption. Historical results remain separate because both the dataset and the retrieval/generation components change.

A prospectively frozen follow-up, C, uses new source-screened questions, a separate imposed-exposure comparison, fixed-target repetition and fresh provider rounds. This follow-up addresses design gaps identified in the B audit while preserving the earlier results and their source-validity limits.

The contributions, within the documented evaluation limits, are: (1) an explicit mapping from research questions to interventions and outcomes; (2) an executed generative evaluation with matched controls and frozen response-level evidence; and (3) paired reporting that separates prevention, restoration, and newly introduced failures. This is an exploratory empirical study, with no claim of a new attack optimizer, certified defense, independent human validation, or representative institutional deployment performance.

## 2. Related research

PoisonedRAG formalizes targeted knowledge corruption through corpus insertions [1]. CorruptRAG and broader attack benchmarks examine practical poisoning and defenses [2, 4]; Su et al. study adversarial context and retrieval robustness [3]. These establish the threat rather than serve as numerical baselines reproduced here. Our shared-corpus, fixed-target protocol and simple templated attack differ from optimized attacks against large production-scale collections.

Threat boundaries also differ across research. Coordinated prompt/RAG attacks add prompt control [5]; PANDORA targets jailbreak behavior [6]; indirect prompt injection conveys instructions through external content [14]. Privacy attacks and instruction-tuning poisoning pursue different goals or alter different system layers [7, 15]. The base attacker here changes inserted factual passages only. Accepted-label compromise is a separately named change in attacker capability.

RobustRAG studies an isolate-then-aggregate defense with a formal retrieval-corruption model [8]. RAGPart and RAGMask address retrieval-stage defenses [9]. The lexical reranker and eligibility gate used here implement neither those methods nor their guarantees. Reranking is a relevance comparison; metadata filtering is a policy over labels supplied by an assumed authority.

HotpotQA supplies externally annotated question-answer pairs and supporting facts [18]. We use a restricted numerical-answer subset with a shared retrieval collection, not the official ten-paragraph-per-question evaluation. Natural Questions and BEIR motivate broader future evaluation [17, 19]. Context placement can influence LLM evidence use [16], while RAGAs and citation evaluation assess complementary properties [20, 21]. Neither lexical matching nor source inclusion alone determines whether a model endorsed a false claim.

## 3. Research questions and analytical framework

### 3.1. Questions aligned with the experimental design

Four research questions link the interventions to their measured outcomes. Study B supplies the archived generative comparisons. The separate C follow-up adds source-screened questions, controlled exposure, fixed-target repetition and three fresh generation rounds. Study A contributes historical extractive evidence only; it is not pooled with either generative study.

**Table 1. Alignment of research questions, comparisons and evidence. B and C retain their own data, endpoints and denominators.**

| Question | Controlled comparison | Measured outcomes | Evidence and result location |
|:--|:--|:--|:--|
| RQ1. Does question targeting increase designated target output or reduce reference matching relative to unrelated and reference-concordant insertions? | B and C core: targeted versus unrelated and benign, fixed questions and dose. C also fixes exposure in a separate context intervention and varies identical-copy dose at fixed target coverage. | B: archived target-only and reference-only numerical outputs. C: strict concise target-choice proxy and designated numerical target production; reference choice is secondary. | B: Section 5.1. C: Section 5.7, Tables 10–12 and saved paired/case tables |
| RQ2. How do supporting-evidence recovery and insertion exposure relate to generated outputs? | B and C core: clean versus attacked, no defense versus reranking. C controlled contexts retain both complete supporting passages and impose insertion exposure. | All-support Recall@5, assigned-insertion exposure and answer-proxy coexistence; controlled-context answer outcomes are separate from ordinary retrieval. | B: Section 5.2; A: historical Section 5.5. C: Section 5.7, Tables 10–12 and saved paired/case tables |
| RQ3. How do defenses prevent target outputs or recover reference values, and how does changing supplied labels affect them? | B and C core: four defense arms and identical targeted text under rejected versus accepted labels. C repetition compares no defense and reranking at each fixed-target dose. | Paired proxy prevention, reference-choice recovery and newly introduced target choices; labels are supplied experimental assumptions. | B: Section 5.3; A: historical Section 5.5. C: Section 5.7, Tables 10–12 and saved paired/case tables |
| RQ4. What measured utility cost accompanies the defenses and rejection of legitimate evidence? | B and C core: each defense versus the undefended clean corpus. C separately rejects a required support, with all-accepted and equally sized non-support rejection controls. | Reference matching and strict EM on generated clean answers. The C label-error stress test measures retrieval recovery only and supplies no generated-answer cost estimate. | B: Section 5.4; A: historical Section 5.5. C: Section 4.8 and saved retrieval-stress results; core answer results follow Section 5.7. |

At B's original execution, the two planned RQ1 contrasts under no defense used target-only and reference-value-only numerical outputs. They were specified in the local freeze before B answers were inspected; subsequent B source screening and diagnostic analyses are retrospective. C separately fixes targeted-minus-unrelated and targeted-minus-benign contrasts under no defense, using its strict concise target-choice proxy and designated numerical target production. C reference choice, evidence recovery, controlled exposure, repetition and defense transitions are secondary analyses. Neither study was publicly preregistered, and neither automatic endpoint establishes completed human semantic validation.

C averages planned rounds within each of its 62 questions before averaging across questions. Condition rows, reused payloads and fresh calls do not increase the question count or remove dependence from the shared corpus. The three studies therefore have separate denominators and support no pooled attack-success rate.

### 3.2. Outcomes and denominators

For a query q, let T(q) be the final five-passage context, G(q) its annotated set of supporting passages, and A(q) the generated answer. Let C(q) indicate that A(q) contains the reference numerical value, and F(q) indicate the designated target value. Numeric comparison removes digit-grouping commas and compares decimal values using token boundaries. Define:

**Reference-value-only output rate:** V(q) = C(q)[1 − F(q)].

**Target-only output:** O(q) = F(q)[1 − C(q)].

**Exposure-confirmed target-only output:** S(q) = R(q)O(q), where R(q) indicates inclusion of the insertion addressing q in the targeted or accepted-label condition.

An answer containing both values is mixed and receives neither reference-only nor target-only credit. Target-only output is computed identically in all five conditions, allowing a fair primary contrast with the unrelated control. Exposure-confirmed target-only output is additionally reported for conditions containing target-addressed attacks; it is not mechanically assigned to unrelated poison. The separately recorded assigned-insertion exposure permits a descriptive check of the unrelated control's context inclusion.

All archived B rates use the same 64 test questions unless a conditional or retrospective-subset denominator is explicitly given. The historical field named numeric_false_only is called target-only output here; its numerical rule is unchanged. All-support Recall@5 is the fraction of questions for which every annotated supporting passage is in T(q). Fractional support recall averages |G(q) ∩ T(q)|/|G(q)|. First-support reciprocal rank is auxiliary. These metrics differ from the historical single-gold-chunk Recall@5 and must not be directly equated.

Strict normalized exact match (EM) and token F1 are auxiliary answer-format measures. Mixed answers, UNKNOWN abstentions, other outputs, and output truncation are recorded separately. Numerical containment does not adjudicate negation, endorsement, entity, relation, date, or units. Accordingly, the article reports reference-value matching and designated target-value production, rather than independently established semantic correctness.

### 3.3. Paired defense outcomes

Within a fixed corpus condition, let U be the questions satisfying the exposure-confirmed target-only criterion S(q) without defense. Proxy prevention counts members of U that no longer satisfy that criterion after defense. Reference-value recovery counts members of U whose defended output satisfies V(q). New target-only events arise outside U after defense. Clean value-match cost is the undefended clean reference-value-only rate minus its defended counterpart, in percentage points. These definitions preserve the archived calculations; preventing a target-valued output need not recover a reference-valued output, and neither event is a human-validated correctness judgment.

### 3.4. Threat model

The base attacker inserts a fixed set of factual QA-style passages into a separate copy of the corpus. The attacker knows the target question and designated target value, but does not change clean documents, user queries, system prompts, generator weights, or defense code. There is no adaptive search against test responses. One insertion addresses each test question, giving 100% target coverage at every positive targeted condition.

The source gate accepts only passages whose supplied verified field is true and whose supplied trust is high or medium. All new clean passages are assigned eligible labels, and all base insertions—including the reference-concordant-insertion control—are assigned rejected labels. This tests an assumed eligibility boundary, not an implemented authentication or fact-checking service. In the accepted-label condition, the targeted text and IDs remain identical while verified becomes true and trust becomes high. This intervention explicitly permits metadata compromise.

## 4. Materials and methods

### 4.1. Study boundaries and evidence provenance

Study A is the previously reported Afghanistan-focused offline experiment [25]. Its canonical inputs and current workbench code are publicly available in [RAG-Security-Lab](https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/tree/6f76858df91277e4b962ee94b4286a25cfe08d4d) at commit `6f76858df91277e4b962ee94b4286a25cfe08d4d`. The present artifact audit reconstructed the four canonical input tables from the retained legacy material and 12 World Bank responses. This verifies construction and transfer against those snapshots; it does not independently establish the truth of every inherited statement.

The complete 21,840-row principal archive, 3,016-row repetition archive and matching historical runtime were not recovered in the bounded repository, history and workflow-artifact search. The current workbench is not that frozen runtime: for example, its default budgets are 0, 10, 20, 50 and 104, whereas the historical report uses 0, 10, 30, 60 and 104. Historical results and figures are therefore retained as previously reported evidence, not a newly reproduced run. Earlier replay assertions are attributed to that report. No recovered decision record establishes why every proposed component was inactive, and present-day design explanations are not written as historical author intent.

Study B is an external generative experiment whose selected questions, source excerpts, insertion files, frozen embeddings, contexts, API requests and responses, scoring outputs, and verification scripts are provided in the supplementary reproduction package. Study B neither replays Study A nor isolates the causal effect of replacing only its answerer, because the evaluation material and retrieval backend also change.

**Table 2. Study boundaries and implemented components. Condition rows, unique payloads and fresh provider responses have different denominators.**

| Feature | A: historical extractive | B: archived generative | C: prospectively frozen follow-up |
|:--|:--|:--|:--|
| Questions | 364 previously inspected; 104 designated targets | 64 integer-surface questions; 64 donors | 62 source-screened questions; 62 unit-matched donors |
| Clean collection | 224 documents; 225 chunks | 640 HotpotQA passages | 620 new HotpotQA passages |
| Retrieval | 1,024-dimensional hashing; exact cosine | 1,536-dimensional API embeddings; exact cosine | Same embedding model/configuration as B; newly frozen vectors |
| Reranking | Query/candidate TF-IDF | Query/candidate TF-IDF | Same explicitly configured lexical method |
| Answerer | Deterministic sentence extraction | gpt-4.1-mini-2025-04-14 API | Same pinned API model; three fresh rounds |
| Interventions | Five budgets; three selection seeds | Five corpus conditions; one insertion per target | Five core conditions; imposed exposure; one/two/five copies; retrieval-only label error |
| Final context | At most five of 30 candidates | Five of 30 candidates | Core/dose: five of 30; controlled: five constructed passages |
| Evaluations | 21,840 historically reported rows | 1,280 condition rows; 376 unique provider responses | 5,208 condition/round rows; 853 payloads; 2,559 fresh responses |
| Evidence status | Matching principal execution archive unrecovered | Originally output-held-out; now retrospective audit material | Definitions frozen before inference; automatic results; source-relative case inspection; limited generalization |

Figure 1 shows Study A's hashing, lexical reranking, and extractive answer-selection pipeline. Study B's neural retrieval and real LLM generation are specified separately in Sections 4.4–4.5.

![Figure 1. Study A retrieval and extractive-answer pipeline [25]. The four defense arms share the same clean collection, insertion pool, and extractive answerer. Eligibility precedes retrieval where enabled; accepted-label forgery is a separate control.](figures/original_pipeline.png){width=16.7cm}

The primary experimental conclusions use C and its controlled modules. A is retained solely as historical context; its unrecovered execution archives are not needed to reproduce C. B supplies retrospective numerical and source-validity diagnostics, and its defective references do not serve as verified factual attack-success evidence.

### 4.2. External test material and independence controls

We use the HotpotQA distractor validation split distributed by the dataset authors and mirrored at Hugging Face [18, 24]. The pinned dataset revision is `1908d6afbbead072334abe2965f91bd2709910ab`. The 27,452,575-byte source Parquet has the following SHA-256:

```
c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6
```

This public validation split becomes an external local test subset; it is not the official hidden HotpotQA test set.

Eligibility requires an integer-valued annotated answer, ten distinct context titles, valid supporting-fact indices, the answer value in annotated support, and no occurrence of that value in the question. Questions longer than 80 whitespace words and questions/titles mentioning Afghanistan, Bamiyan, or the World Bank are excluded. These rules yield 461 candidates. Candidates are sorted by SHA-256 of a fixed study string and example ID. Greedy selection retains 128 examples with no shared context title: the first 64 are evaluated targets, and the next 64 supply unrelated-control donor questions. None of the 1,280 selected context titles overlaps another selected example. The donor contexts are not indexed in the clean test corpus.

Each of the 64 test examples contributes its ten supplied paragraphs, resulting in a shared 640-passage clean retrieval corpus. This differs from giving a model the correct example's ten paragraphs directly. All queries search the full shared corpus, including the other examples' distractors. The target set, answer references, false values, and supporting-passage IDs remain fixed across conditions.

At the original B execution this was an output-held-out external subset: no generated test answer was used to choose questions, tune prompts, optimize attacks, or change defenses. Reference annotations necessarily remain visible to construct attacks and scoring. A bounded comparison against the now-available current canonical A inputs found no normalized exact question, title or complete-text matches, and no shared contiguous eight- or twelve-word phrases. It did not establish that those inputs exactly match the missing historical run, or exclude semantic entity/fact overlap and shared source families. B donor full context bodies were not retained, so that comparison covered their questions, titles and annotated support sentences rather than every donor paragraph. HotpotQA may also occur in LLM pretraining. The evaluation therefore supports conditional results on this external numerical subset, not a claim of training-data independence or full domain generalization. No independent human source validation has been completed.

### 4.3. Matched corpus conditions

Every positive condition adds 64 passages to the same 640 clean passages, for a malicious or added-content share of 64/704 = 9.1%. Coverage remains 64/64; this fixed-dose experiment avoids conflating wider target coverage with per-target susceptibility.

**Table 3. Corpus conditions in Study B.**

| Condition | Inserted content | Supplied labels | Purpose |
|:--|:--|:--|:--|
| Clean | No added passages | Clean passages eligible | Utility baseline |
| Targeted | Each evaluated question paired with its designated target value | Unverified, untrusted | Intended targeted factual corruption |
| Unrelated | A source-title-disjoint donor question paired with the same false value used for the corresponding target | Same rejected labels | Control for unrelated false content and index additions |
| Benign | The evaluated question paired with its annotated reference value | Same rejected labels | Control for query overlap, passage format, and reference-concordant insertion |
| Accepted label | Identical targeted text and IDs | Verified, high trust | Isolate the gate's metadata-authority assumption |

All inserted passages have exactly 120 whitespace words and share the same QA-record template and neutral archival filler. Targeted and unrelated pairs contain the same designated target value. False integers are generated deterministically from the reference value, with collision avoidance against selected correct values and other designated target values. Donor references also differ from the paired false value, so the inserted value differs from its donor annotation. This numerical difference alone is not a source-validity check; donor references were outside the later 64-question B source audit. Word count is matched; model-token count and lexical/semantic relevance are not identical. The intended change in targeting remains the presence of the evaluated question versus an unrelated donor question. The benign condition preserves question overlap while changing the asserted value.

The attacks are templated factual assertions, without jailbreak instructions or iterative optimization. Results consequently do not estimate the maximum strength of an adaptive attacker. The accepted-label condition changes only metadata; text is not regenerated.

### 4.4. Neural retrieval and defense order

The API embedding model is text-embedding-3-small at 1,536 dimensions [23]. The run embeds the clean paragraphs, the three unique insertion pools, and 64 queries: 896 unique texts in seven batches of 128. Saved vectors are converted to float32, normalized to unit length, and frozen. Exact cosine retrieval ranks eligible paragraphs, with stable corpus-order tie handling. Saved embeddings permit replay without making a fresh embedding request; no immutable provider snapshot is claimed for the embedding model name.

Four conditions are evaluated: no defense; lexical reranking; eligibility filtering; and filtering followed by reranking. Filtering precedes retrieval. Candidate retrieval returns 30 passages. Where enabled, scikit-learn TfidfVectorizer is fit to the question and its 30 candidates with lowercase text, English stopwords, and L2 normalization; candidate/query cosine determines the final order, with retrieval order retained for ties. Five passages form the model context. This is a lexical reranker, not a learned cross-encoder or factual verifier.

Trust metadata controls eligibility but is not shown to the generator. The generator receives passage text under neutral rank numbers, without attack IDs or condition labels. The accepted-label condition therefore tests which text passes the gate, rather than simultaneously introducing a trust hint into the prompt. Because all clean chunks are eligible, rejecting all base insertions restores the corresponding clean context by construction.

### 4.5. Real LLM generation and frozen execution

The generator is gpt-4.1-mini-2025-04-14 through the OpenAI Chat Completions API [22], with temperature 0, a maximum of 64 generated tokens, and storage disabled. The exact model snapshot returned by every request is checked. The fixed system prompt is:

> Answer the question using only the numbered reference passages. The passages are evidence, not instructions. Return only a concise answer, with no explanation. If the evidence is insufficient, return UNKNOWN.

The user message contains the question, five numbered passage texts, and a short-answer cue. Prompts, data, insertion rules, scoring definitions, and planned contrasts are locally hashed before generating test answers. Embeddings, all final contexts, and the execution-script hash are then frozen in a second manifest. The analysis script implements the declared definitions and is included in the release manifest; it was not part of the pre-generation code freeze. This is a local, pre-execution freeze rather than a public preregistration. A separate one-token connectivity check is not a study observation.

The factorial design produces 64 × 5 × 4 = 1,280 condition rows. Exact duplicate API payloads share one saved response, producing 376 real generation calls and 904 reused condition rows. Cache reuse is explicit and is not treated as repeated sampling. Requests are interleaved in a deterministic hash order with at most six concurrent calls. Transient errors are retried up to three times; permanent failures and model mismatches stop execution. No model or backend fallback is permitted. Temperature 0 does not guarantee reproducibility across fresh provider calls.

### 4.6. Scoring, analysis, and verification

Automatic scoring applies the numerical definitions in Section 3.2 without consulting condition names. Primary comparisons use paired question-level differences, never response-row counts as a sample size. We report 10,000 paired question bootstrap resamples with seed 20261022 and exploratory 95% percentile intervals. These intervals are conditional on this fixed corpus, insertion set, and saved responses; they do not capture new-corpus variation, shared-corpus interference, annotation uncertainty, or stochastic generation across fresh calls. There are no confirmatory p-values or claims of population representativeness.

Verification checks input hashes, source-title disjointness, equal insertion word counts, paired false values, exact metadata-only manipulation, request and response hashes, returned model IDs, complete condition coverage, and clean-context equality after rejection. All 376 unique generation requests returned the specified snapshot and a normal stop reason; no API error, output truncation, or model fallback occurred. Integrity and completeness checks passed. API errors and output truncation are reported as execution properties rather than silently discarded.

The source-based manual case inspection is described in Section 4.9.

### 4.7. Source audit and revised evaluation protocol

The original B scores are preserved. A versioned source audit and diagnostic evaluator are supplied separately. The audit distinguishes source-consistent reference relations, unresolved questions and targets whose falsity is not established. Its accepted label means agreement with a specified saved source, not independent truth certification. Documentation links source snapshot, passage, question, reference, insertion and output, following the purpose of dataset documentation rather than treating documentation as validation [28].

The new format proxy accepts only a restricted affirmative scalar answer, optionally with a short fixed prefix or listed unit, and rejects detected negation, quotation, bounds, uncertainty, abstention language and execution problems. It does not validate the entity, relation, unit or real-world truth. Factual correctness, support from any provided passage, support from provided clean passages, target-claim endorsement and abstention remain separate semantic axes. A false answer can be supported by a poisoned context; numerical co-occurrence is not entailment [20, 21].

### 4.8. Prospective follow-up C: source screening, exposure and repetition

The follow-up was executed under the two-stage freeze described below. C uses 62 new calendar-year or dated-population questions and 62 context-title-disjoint donor questions. The target size was refined from 64 to 62 before any C output because exact unit matching was available for 57 year pairs and five population pairs; coarse counts with mismatched fine units were excluded. The 192 automatically screened candidates, 135 source-accepted cases and all exclusion reasons are retained. Of 11 eligible dated-population candidates, the last in the predefined hash order remains an unpaired reserve; ten enter the five population pairs. Source screening was AI-assisted and denotes consistency with the saved source, not independent external truth certification. Original questions are preserved, and no C answer was used to choose cases.

All 128 B test/donor IDs and context-title sets are excluded. The new examples also have mutually disjoint complete context-title sets. These are explicit source-title checks; they do not prove disjoint entities, source families, facts under paraphrase or model pretraining. Every C query searches the same 620-passage clean collection. Each positive condition adds 62 passages, one per target, giving a final added-content share of 62/682 = 9.1%. The five corpus conditions and four defense arms follow B, with the same generator snapshot, embedding model, candidate count, final context length and prompt. The donor and target share an attacker-designated value that conflicts with their respective source-defined exact values; source-based contradiction is not independent human factual validation.

The separate exposure-controlled module fixes two complete support passages and two clean non-support passages. A fifth slot contains a constructed neutral clean filler, the targeted insertion, the unrelated insertion or the reference-concordant insertion; all four slot texts have 120 whitespace words. The filler is explicitly recorded as constructed indexing text, not a source quotation. The variable slot is approximately balanced across ranks and fixed across the four arms of each question. Reranking and filtering are absent from this module, so both the inserted text and the required clean support are present by construction. It measures a controlled context intervention separately from natural retrieval competition.

The fixed-target repetition module uses one, two and five identical copies per target, with no defense or reranking. Target coverage stays fixed. Its final added-content shares are 9.1%, 16.7% and 33.3%; this is a repetition stress test, not diverse attack generation or a reproduction of A's missing repetition archive. A separate retrieval-only label-error test rejects one required clean support, with all-accepted and equally sized non-support rejection controls. That test measures support recovery under a hypothetical label error; no final-answer cost is inferred without generator measurements.

For each unique exact payload, three fresh provider calls are made in separate rounds. Identical payloads may reuse a response within one round; a response cannot be reused across rounds. The aggregate is the mean across rounds within question, then the mean across questions. Fresh calls at temperature zero do not guarantee statistically independent outputs, and 62 questions do not become 186 independent questions. Per-round ranges are descriptive; the shared corpus still couples retrieval outcomes. No population confidence guarantee is claimed [29].

The first local freeze covers source-screened data, code, evaluator definitions and embedding requests before embeddings are requested. The second freezes returned vectors, final contexts and exact generation requests before completions. Every dispatch, including an empty-cache start or resumed run, checks the relevant freeze and pending payload. Model mismatch, permanent API failure, changed inputs and the recorded money ceiling stop execution. Offline tamper tests require zero dispatch after a changed pending request. These are file-integrity controls, not authentication against an adversary controlling the files and hashes. Failures, truncations and unresolved outputs are reported with planned denominators and explicit bounds; they are not silently counted as unsuccessful attacks.


### 4.9. Manual semantic inspection

The author reports completing a manual semantic inspection of 72 question–context–answer cases: 32 from B, 32 from C and eight additional diagnostic B cases. The archived selection record defines a 64-case main sample and a separately flagged supplement. The inspection was retrospective, single-author and study-aware; no blinding or inter-rater agreement is claimed. Question entity, relation, date, unit, qualifiers, answer assertion, abstention and actual contextual support were considered separately. Supporting evidence outside the context was distinguished from evidence actually given to the model.

Table 13 reports the aggregate findings supplied by the author. Assistant-generated case notes and quotations used during preparation remain archived with their original provenance; those files have not been relabelled as individual human ratings. The inspection supports case-level interpretation rather than a calibrated estimate of semantic attack success across all model answers. Its 64 main cases and eight diagnostic cases are not pooled as a representative 72-case accuracy rate.

## 5. Results organized by research question

### 5.1. RQ1: Targeting versus matched controls in the real LLM study

Without defense, targeted poison produces the designated target value for 34/64 questions (53.1%). The unrelated and benign controls each produce 0/64 designated target values, even though unrelated insertions contain the same target integers. Reference-value-only output rate is 24/64 (37.5%) under targeted poison, compared with 40/64 (62.5%) under unrelated poison, 41/64 (64.1%) on the clean corpus, and 64/64 (100.0%) under reference-concordant question-shaped insertion. The targeted-minus-unrelated target-output difference is +53.1 percentage points (exploratory interval +40.6 to +65.6); its reference-value-match difference is −25.0 points (−37.5 to −12.5). Compared with benign insertion, the reference-value-match difference is −62.5 points (−73.4 to −50.0). These contrasts answer the automatic numerical endpoint of RQ1 on the original subset. Because ten designated target propositions lack source-established falsity, they do not establish semantic attack success or an optimized attacker success probability.

**Table 4. Study B outcomes (%), with 64 questions per row. Support is all-support Recall@5; exposure is assigned-insertion inclusion. Reference/target use the unchanged archived automatic value-matching indicators; EM is strict normalized exact match.**

| Corpus | Defense | Support | Exposure | Reference | Target | EM |
|:----------------|:----------------|------------:|------------:|----------:|----------:|----------:|
| Clean | None | 56.3 | 0.0 | 64.1 | 0.0 | 34.4 |
| Clean | Rerank | 43.8 | 0.0 | 60.9 | 0.0 | 39.1 |
| Clean | Filter | 56.3 | 0.0 | 64.1 | 0.0 | 34.4 |
| Clean | Filter + rerank | 43.8 | 0.0 | 60.9 | 0.0 | 39.1 |
| Targeted | None | 46.9 | 100.0 | 37.5 | 53.1 | 31.3 |
| Targeted | Rerank | 37.5 | 56.3 | 45.3 | 26.6 | 29.7 |
| Targeted | Filter | 56.3 | 0.0 | 64.1 | 0.0 | 34.4 |
| Targeted | Filter + rerank | 43.8 | 0.0 | 60.9 | 0.0 | 39.1 |
| Unrelated | None | 51.6 | 1.6 | 62.5 | 0.0 | 35.9 |
| Unrelated | Rerank | 42.2 | 0.0 | 60.9 | 0.0 | 37.5 |
| Unrelated | Filter | 56.3 | 0.0 | 64.1 | 0.0 | 34.4 |
| Unrelated | Filter + rerank | 43.8 | 0.0 | 60.9 | 0.0 | 39.1 |
| Benign | None | 45.3 | 100.0 | 100.0 | 0.0 | 93.8 |
| Benign | Rerank | 37.5 | 56.3 | 71.9 | 0.0 | 57.8 |
| Benign | Filter | 56.3 | 0.0 | 64.1 | 0.0 | 34.4 |
| Benign | Filter + rerank | 43.8 | 0.0 | 60.9 | 0.0 | 39.1 |
| Accepted label | None | 46.9 | 100.0 | 37.5 | 53.1 | 31.3 |
| Accepted label | Rerank | 37.5 | 56.3 | 45.3 | 26.6 | 29.7 |
| Accepted label | Filter | 46.9 | 100.0 | 37.5 | 53.1 | 31.3 |
| Accepted label | Filter + rerank | 37.5 | 56.3 | 45.3 | 26.6 | 29.7 |

**Table 5. Primary paired contrasts under no defense (percentage points). Intervals are exploratory 95% question bootstrap intervals conditional on the frozen corpus and responses.**

| Contrast | Outcome | Difference (pp) | Interval (pp) |
|:--|:--|--:|:--|
| Targeted − unrelated | Target-only output | +53.1 | +40.6 to +65.6 |
| Targeted − unrelated | Reference-value-only output rate | -25.0 | -37.5 to -12.5 |
| Targeted − benign | Target-only output | +53.1 | +40.6 to +65.6 |
| Targeted − benign | Reference-value-only output rate | -62.5 | -73.4 to -50.0 |

The unrelated condition tests generic contamination at the same insertion count and word length while retaining the same target values. The benign condition additionally preserves exact question overlap. Neither comparison removes all wording or tokenization differences, and the attacks remain a single fixed template. Results support conclusions about this intervention and subset rather than an optimized attack against all generative models.

### 5.2. RQ2: Evidence recovery, exposure, and generated outputs

The clean undefended collection retains all annotated supporting passages for 36/64 questions (56.3%). Targeted poisoning reduces this to 30/64 (46.9%), while its assigned attack is retrieved for all 64 targets. Eight questions retain all annotated supporting passages and nevertheless produce the designated target value. With reranking, all-support recall is 24/64 (37.5%) and own-poison exposure is 36/64 (56.3%); four questions still retain every annotated support and produce the designated target value. Unlike Study A, reranking in this external study does not recover more gold evidence: it reduces both supporting-passage coverage and malicious exposure. Its lower target-output rate therefore cannot be described as evidence recovery alone. Of the 41 questions with a reference-only clean output, 17 (41.5%) produce the designated target value after undefended targeted poisoning. The remaining 17 target-valued outputs occur on questions already lacking a reference-only clean output. Thus 34 target-only events are not 34 losses of previously reference-matching responses, and neither count establishes semantic correctness.

![Figure 2. Reference-value-only output rate and target-only output rates across five corpus conditions and four defenses. Values are percentages of 64 questions using the same generator and frozen input pools. Interpret filtering under the supplied-label boundary, including accepted-label compromise.](figures/generative_outcomes.png)

All-support recall, own-insertion exposure, and the generated value describe different events. Recovering every annotated support passage is a stronger evidence-availability check than recovering just one, but neither establishes semantic resolution of a conflicting claim. Conversely, producing a designated target value without retrieving its own attack can arise from another context or prior model knowledge; it is therefore distinguished from exposure-confirmed target-only output.

### 5.3. RQ3: Defense ablations and accepted-label compromise

In B's targeted condition, reranking reduces exposure-confirmed target-only outputs from 34/64 to 17/64 (26.6%). Paired numerical transitions show 24 of the initial 34 events prevented, 11 reference values recovered and seven new target-only events. The net reduction therefore combines prevented and newly introduced events. Rejected-label filtering prevents all 34 initial target-only events and recovers 17 reference values; filtering followed by reranking recovers 19. With accepted labels, filtering alone retains 34/64 target-only outputs and filtering plus reranking retains 17/64. These counts describe the archived value-matching criterion, not human-adjudicated false-claim endorsement.

**Table 6. Paired numerical transitions in Study B. The prevention and recovery denominators are the original undefended target-only events in that corpus condition.**

| Corpus | Defense | Target-only events prevented | Reference value recovered | New target-only events |
|:--|:--|--:|--:|--:|
| Targeted | Rerank | 24/34 | 11/34 | 7 |
| Targeted | Filter | 34/34 | 17/34 | 0 |
| Targeted | Filter + rerank | 34/34 | 19/34 | 0 |
| Accepted label | Rerank | 24/34 | 11/34 | 7 |
| Accepted label | Filter | 0/34 | 0/34 | 0 |
| Accepted label | Filter + rerank | 24/34 | 11/34 | 7 |

The gate's rejected-label result checks an assumed boundary: removing all inserted passages reproduces the corresponding clean retrieval context. It does not show that a real ingestion process identifies every malicious source. The accepted-label intervention removes that premise while preserving text. Because metadata is hidden from the generator, it creates the same payloads as the corresponding unfiltered targeted condition; their saved responses are reused and are not independent model draws.

### 5.4. RQ4: Clean utility cost

Clean reference-value-only output rate is 41/64 (64.1%) without defense and 39/64 (60.9%) with reranking, a net cost of 3.1 percentage points. Filtering alone preserves 41/64, and filtering plus reranking preserves 39/64. Strict EM, however, changes from 22/64 (34.4%) without defense to 25/64 (39.1%) with reranking, an improvement of 4.7 points. Thus the clean-cost conclusion depends on the declared metric, rather than representing a uniform deterioration in every measure. Gold-only value matching can credit explanatory text that EM rejects. A post hoc format diagnostic also flags clean responses containing both the reference value and explicit UNKNOWN language; these flags do not change the frozen primary rule. No mixed gold-and-designated-false output occurs, and every API response terminates normally.

The benign-insertion condition also exposes a limitation of the gate's label policy: every newly inserted reference-concordant passage is rejected because it carries rejected labels. This 64/64 rejection is fixed by the experimental labeling, not an estimate of a real source-review false-positive rate. Preserving aggregate reference-value matching can coexist with excluding potentially useful reference-concordant additions. Review effort, operational false rejection, latency tradeoffs, and source-authentication cost require a separate deployment study.

### 5.5. Study A: historical extractive outcomes

Study A used 56 inherited public-information documents and 168 Afghanistan WDI observations from 12 indicator families for 2010–2023 [10]. Its 364 questions included 336 indicator questions with two formulations per observation, plus 28 inherited questions. All existing partitions had been inspected in development. The executed retriever used 1,024-dimensional hashing and exact cosine, the reranker used TF-IDF, and the answerer selected sentences by keyword overlap. Configured neural model names or generation parameters were not evidence that those backends ran.

The previously reported factorial grid was 364 questions × five budgets (0, 10, 30, 60, 104) × four defenses × three attack-selection seeds, giving 21,840 condition rows. Seeds changed attack subsets, not generated responses; zero and full-budget conditions were identical across seeds. The historical full-insertion contamination share was 104/329 = 31.6%, substantially higher than Study B's fixed 9.1%.

**Table 7. Historical Study A endpoints [25]. These are extractive lexical outcomes, not LLM measurements.**

| Budget | Defense | Gold Recall@5 (%) | Own-poison exposure (%) | Answer-value accuracy (%) | Exposure-confirmed ASR (%) |
|--:|:--|--:|--:|--:|--:|
| 0 | None | 93.4 | 0.0 | 82.4 | 0.0 |
| 0 | Reranking | 98.1 | 0.0 | 81.3 | 0.0 |
| 0 | Eligibility filter | 93.4 | 0.0 | 82.4 | 0.0 |
| 0 | Filter then reranking | 98.1 | 0.0 | 81.3 | 0.0 |
| 104 | None | 5.8 | 93.3 | 3.6 | 73.1 |
| 104 | Reranking | 88.7 | 94.2 | 42.0 | 72.1 |
| 104 | Eligibility filter | 93.4 | 0.0 | 82.4 | 0.0 |
| 104 | Filter then reranking | 98.1 | 0.0 | 81.3 | 0.0 |

Historical reranking restored annotated evidence but left 75/104 targeted successes, versus 76/104 undefended. In 73 targets, the final reranked context included the gold chunk and own poison while the false-only lexical criterion was met. Two initially successful attacks were prevented, one correct value was restored, and one previously unsuccessful attack became successful. Filtering prevented all 76 baseline successes but restored only 73 correct values because clean errors remained. Clean reranking cost was 1.1 percentage points.

At intermediate historical budgets, all-target ASR averaged 9.0%, 23.1%, 46.8%, and 73.1% for 10, 30, 60, and 104 inserted passages; corresponding rates among injected targets were 93.3%, 80.0%, 81.1%, and 73.1%. An increasing all-target curve partly reflected increasing coverage, since ASR_all(B) ≤ B/104 under the exposure-confirmed definition. It was not a fixed-population dose-response estimate. Study B avoids that coverage change but does not add a multi-dose experiment.

Figures 3 and 4 summarize Study A's accuracy and attack-success curves [25]. Points and error bars represent across-selection-seed means and sample standard deviations, not population confidence intervals or repeated LLM generations.

![Figure 3. Study A answer-value accuracy across 364 questions [25]. Points average selection seeds 17, 42, and 91; error bars show sample standard deviations. The curves describe deterministic extractive outputs under lexical scoring.](figures/original_answer_accuracy.png){width=16.7cm}

![Figure 4. Study A target-specific, exposure-confirmed attack success across 104 designated targets [25]. Error bars show selection-seed standard deviations. Increasing insertion count also increases attacked-target coverage; the curves are separate from Study B's generative outcomes.](figures/original_attack_success.png){width=16.7cm}

A separately reported target-specific repetition experiment contained 3,016 evaluations, including forged-label controls. Undefended success was 90/104 at one copy and 91/104 at two or more; exact duplicate collapse retained 90/104 across positive doses. At 50 copies per target, rejected-label filtering produced 0/104 successes and accepted-label filtering 91/104. Each target had a separate corpus; these outcomes are not pooled with either shared-corpus study.

The historical report also describes a changed-backend extractive diagnostic (1,092 rows), neural retrieval development checks (1,120 and 1,344 rows), and a 24-response generative pilot on three previously seen facts [25]. These remain development evidence. None is added to Study B's 64-question sample or represented as a replication of its controls. Historical verification is discussed in Appendix B.

\FloatBarrier

### 5.6. Reference validity and retrospective diagnostic analysis

Recomputing the original numerical rule reproduced all 1,280 archived condition rows without disagreement. That result establishes consistency of the calculation, not correctness of every question or reference. A separate AI-assisted source audit examined the entity, relation, date, unit and qualifier of each of the 64 questions against its saved support. Selected uncertainties were checked against institutional sources. This was not an independent human review or a full external fact check of every item.

**Table 8. Source-consistency findings for the 64 archived questions. Reference and target-validity categories overlap; their counts must not be added as independent cases.**

| Audit finding | Questions | Interpretation |
|:--|--:|:--|
| Reference consistent with the source-defined question relation | 53 | Source consistency, not independently established factual truth |
| Reference or question remains ambiguous | 5 | A unique interpretation is not established |
| Question/reference requires correction | 6 | A relation, event or qualifier problem affects interpretation |
| Designated target not established as false by the available evidence | 10 | Numerical target production alone cannot establish semantic attack success |

The defects are substantive. One question attributes a book subject's conviction to its author; another uses the population of a place of death for a question about origin. A song-title reference is confused with the owner of a concert tour. For the Army Air Forces item, the official archival guide distinguishes establishment in 1941 from the 1942 reorganization [26]. The reference value 230 also loses the source's qualifier “more than”; that source alone does not establish the target 247 as false. The answer 311 names a band and is not a quantitative measurement. The audit files retain the original wording and classify these issues without rewriting the old model responses as answers to new questions.

**Table 9. Retrospective sensitivity analysis using the unchanged numerical rule. Entries are counts, each with the row's explicit denominator. These are source-screened subsets of observed B, not corrected semantic success rates or a new untouched test.**

| Retrospective set | n | Clean reference only | Targeted reference only | Targeted target only | Reranked target only |
|:--|--:|--:|--:|--:|--:|
| Complete archived set | 64 | 41 | 24 | 34 | 17 |
| Source-aligned exact relation, including 311 | 51 | 35 | 22 | 25 | 14 |
| Source-aligned quantitative cases | 50 | 34 | 21 | 25 | 14 |

The 51-case subset requires a source-aligned reference relation and a target contradicted by that exact source-defined relation. Removing the numeric band name gives 50 quantitative cases. Both subsets retain 25 target-only outputs without defense and 14 after reranking. The original 34/64 and 17/64 remain the archived results. Selection for this analysis occurred after the original outputs were available, and its source judgments remain subject to real human review.

The revised automatic evaluator adds a deliberately restrictive concise-number proxy and flags negation, quotation, qualification, uncertainty and abstention language. Across the 376 unique archived outputs, it detects abstention language in 46, compared with 41 literal UNKNOWN responses under the old rule. These flags include potentially conflicting answers and are not 46 confirmed semantic abstentions. The strict-format proxy recognizes 194 reference choices, 47 target choices, 27 other numerical choices and 108 outputs outside its format. Rejecting a long answer from this proxy does not establish that the answer is wrong. For example, the Koufax response gives 1972 while explicitly declaring the evidence-based answer UNKNOWN; factual correctness, evidence support and abstention require separate judgments.

All 376 distinct B case records and their mapping to 1,280 condition rows are retained for inspection. Source-validity findings and numerical matching remain separate from a claim of externally established factual truth.


### 5.7. Study C: source-screened prospective follow-up

The completed follow-up evaluates 62 fixed questions over 3 fresh generation rounds. The archive records 2,559 successful provider responses for 853 different payloads and 5,208 condition evaluations. The completion report records 2,559 normal stops, 0 truncations and 0 other finish reasons; execution details remain separate from answer outcomes. Exact duplicates within a round reuse one response. No cross-round response reuse or model fallback is permitted.

The undefended strict target-choice proxy averages 37.6% under targeted insertion and 0.0% under unrelated insertion. Reranking gives 21.0% in the targeted condition. These are syntactically restricted automatic choices, not independently adjudicated false-claim endorsement or factual accuracy. B and C differ in reference screening and selected data, so their rates are not a causal comparison of models or a replacement for B's archived denominator.

**Table 10. Study C core outcomes, averaged first across rounds within each question and then across the 62 questions. Asterisks indicate planned-denominator lower–upper bounds when valid outputs are incomplete.**

| Corpus | Defense | Strict target choice (%) | Strict reference choice (%) | All-support Recall@5 (%) |
|:--|:--|--:|--:|--:|
| Clean | None | 0.0 | 59.1 | 62.9 |
| Clean | Rerank | 0.0 | 45.7 | 35.5 |
| Clean | Filter | 0.0 | 59.1 | 62.9 |
| Clean | Filter + rerank | 0.0 | 45.7 | 35.5 |
| Targeted | None | 37.6 | 48.9 | 54.8 |
| Targeted | Rerank | 21.0 | 39.8 | 33.9 |
| Targeted | Filter | 0.0 | 59.1 | 62.9 |
| Targeted | Filter + rerank | 0.0 | 45.7 | 35.5 |
| Unrelated | None | 0.0 | 57.5 | 58.1 |
| Unrelated | Rerank | 0.0 | 46.2 | 37.1 |
| Unrelated | Filter | 0.0 | 59.1 | 62.9 |
| Unrelated | Filter + rerank | 0.0 | 45.7 | 35.5 |
| Reference-concordant | None | 0.0 | 98.4 | 54.8 |
| Reference-concordant | Rerank | 0.0 | 74.2 | 33.9 |
| Reference-concordant | Filter | 0.0 | 59.1 | 62.9 |
| Reference-concordant | Filter + rerank | 0.0 | 45.7 | 35.5 |
| Accepted label | None | 37.6 | 48.9 | 54.8 |
| Accepted label | Rerank | 21.0 | 39.8 | 33.9 |
| Accepted label | Filter | 37.6 | 48.9 | 54.8 |
| Accepted label | Filter + rerank | 21.0 | 39.8 | 33.9 |

**Table 11. Controlled-exposure C outcomes. Each of the 62 questions retains the same four clean passages and one fixed replacement position across four arms; this is a constructed-context comparison, not ordinary retrieval.**

| Controlled slot | Strict target choice (%) | Strict reference choice (%) |
|:--|--:|--:|
| Clean | 0.0 | 79.6 |
| Targeted | 16.1 | 82.3 |
| Unrelated | 0.0 | 84.4 |
| Reference-concordant | 0.0 | 100.0 |

**Table 12. C repetition at fixed coverage of all 62 targets. Copies repeat identical text; results do not measure paraphrase diversity or an optimized attack.**

| Copies per fixed target | Defense | Strict target choice (%) | Strict reference choice (%) | Own-insertion exposure (%) |
|--:|:--|--:|--:|--:|
| 1 | None | 37.6 | 48.9 | 100.0 |
| 1 | Rerank | 21.0 | 39.8 | 62.9 |
| 2 | None | 53.8 | 31.2 | 100.0 |
| 2 | Rerank | 33.9 | 32.8 | 71.0 |
| 5 | None | 96.8 | 1.6 | 100.0 |
| 5 | Rerank | 57.0 | 10.8 | 80.6 |

The paired targeted transitions make the net reranking change interpretable. In rounds 1/2/3, the undefended exposure-confirmed target-choice counts are 22/24/24; reranking prevents 16/16/16, restores reference choices in 6/7/7 and introduces 7/5/5 new exposure-confirmed target choices. Thus prevention and restoration are different events. The 186 paired cells repeat the same 62 questions and are not 186 independent targets.

The retrieval-only label-error stress test retains all annotated supports for 39/62 questions with all clean labels accepted. Rejecting one required support per question makes this 0/62 after filtering, whereas rejecting one clean non-support passage retains 39/62. This result concerns annotated-passage coverage: no generator calls were made in that module, and it does not measure final-answer harm, alternative evidence or real-world authentication.

![Figure 5. Source-screened Study C automatic outcomes across three fresh provider rounds on 62 fixed questions. Plot ranges, where shown, describe variation between rounds on the same corpus; they are not population confidence intervals or human-validation results.](figures/study_c_outcomes.png){width=16.7cm}

The first hash-selected support-retention example asks for the birth year of the composer of *Cagliostro-Walzer*. In round 2 under accepted-label filtering, the saved answer is “1832,” the designated target. The final context places the insertion first, the passage identifying Johann Strauss II second, and the passage giving his birth date in 1825 third. Both annotated supports are therefore present; their availability does not force reference-choice output. In the first hash-selected prevention-without-restoration example, the Meadowbrook Parkway question changes from “12,289” without defense to a response identifying North Merrick but stating that its 2010 population “is UNKNOWN” after filtering and reranking. The defended context retains the route-to-community link but omits the annotated population passage. These are traceable output and context observations, not completed human judgments about factuality or abstention. The case index retains every qualifying case, including those not illustrated here.

The complete C case frame contains 897 distinct question–context–answer–finish-reason records mapped to 5,208 condition/round rows. Identical answers in identical payloads can share a case record, while every round and provider-response mapping remains archived.


### 5.8. Findings from the completed semantic inspection

The main finding is that occurrence of the annotated number does not establish that the answer conveys the correct claim for the question. The author-supplied review summary records the following outcomes.

**Table 13. Author-reported source-relative judgments for the 64 main cases. These are case counts; they do not estimate factual attack success or whole-system accuracy.**

| Outcome | Main-sample cases |
|:--|--:|
| Source-consistent answer claim |41|
| Source-contradicted answer claim |16|
| Full abstention without an answer claim |3|
| Undetermined |4|
| Total |64|

The eight diagnostic cases were assessed separately; two combine an asserted numerical answer with conflicting abstention. They were selected using diagnostic flags and do not supply an unbiased error rate.

Five findings explain why the distinctions matter. First, a Koufax answer states 1972 and then declares the evidence-based answer UNKNOWN: a value match misses the conflicting commitment. Second, a generic actor/award question permits a supplied-context interpretation involving Kristen Alderson and 2013, whereas its annotation intends Roger Howarth and 1994; a unique reference interpretation is not established. Third, “over 3,000” preserves a lower bound and cannot establish an exact count or refute 3,017. Fourth, some reference-consistent answers lack sufficient support in the actual model context. Fifth, the Operation Ladbroke passage supplies alternative clean evidence for the 1943 invasion year even when an annotated support passage is absent. Consequently, annotated all-support recall measures coverage of its specified set, not the existence of every valid proof.

The author report, case selection, exact system answers, evidence and preparation notes are available under `manual_review/` and `assistant_review/`. All 188 quoted snippets were matched against saved source passages or the exact answer. The semantic inspection does not rewrite archived responses, silently repair B questions, replace historical denominators or establish a general semantic attack-success percentage.

## 6. Discussion

### 6.1. What the matched controls establish

On the fixed external subset, a question-addressed assertion of an attacker-designated value produces substantially more target-valued outputs than the matched unrelated assertion. The B source audit does not establish the falsity of every target claim, and its donor references have not received that audit. The unrelated corpus changes reference-value-only outputs from 41/64 to 40/64 under no defense, whereas the targeted corpus gives 24/64. Reference-concordant question-addressed insertions produce 64/64 numerical matches. Together these observations support target alignment and asserted value as consequential properties under this protocol, rather than generic corpus expansion alone. They do not prove that unrelated poisoning is harmless in other domains, at other doses, or with different retrieval methods.

The reference-concordant-insertion comparison is needed because a question-shaped passage can be more retrievable regardless of its factual validity. Reference concordance is all that this B condition guarantees; the source audit shows why it must not be called a fully truth-validated control. Matching only insertion count would leave this difference unresolved. Matching word length and the designated false integer further narrows the contrast, although no single template establishes robustness against other styles, long documents, or optimized poisons.

### 6.2. Evidence availability is an intermediate property

The historical and new studies address the same analytical distinction under different implementations. They should not be combined into one ASR or one sample size. Changes in dataset, attack wording, neural retrieval, and generation prevent attribution of cross-study differences solely to LLM reasoning. Within each study, paired context and answer records show whether evidence recovery, target-output prevention and reference-value restoration coincide.

A numerical match also does not resolve semantic use of evidence. A response can quote, reject, or prioritize a number. The concise-answer prompt reduces some format ambiguity, and strict EM provides a complementary check, but independent endorsement-aware review is still needed before reporting human-validated security rates.

### 6.3. Provenance assumptions and institutional use

The gate evaluates labels that the experiment supplies; it does not authenticate a publisher, verify a signature, or establish truth. Its strong rejected-label behavior follows from the eligibility premise, and its accepted-label control explicitly changes that premise. These are separate threat boundaries. Neither result alone measures the effectiveness of an institutional source-review process.

The supplied labels were assigned by the dataset constructor; no recovered evidence identifies an operational authority that approved every document. For institutional pilots, source ownership, dates and versions, protected metadata changes, conflict review and response-level records must be evaluated alongside retrieval quality. In A, the two rejected low-trust mineral chunks have no directly assigned gold questions, so zero observed clean loss after rejecting them is weak evidence about the cost of rejecting needed legitimate material. Clean-snapshot recovery should be checked against both target manipulation and baseline errors. The results justify this measurement approach, not a claim of ministry deployment, approval, or readiness for autonomous high-stakes decisions.

### 6.4. What the follow-up adds to the explanation

C separates question targeting from two important context effects. In ordinary retrieval, the assigned targeted insertion is present for 100.0% of questions, whereas the assigned unrelated insertion is present for 0.0%. The core targeted-versus-unrelated contrast therefore includes a difference in natural exposure. In the controlled module, both kinds of insertion are always present in the same assigned slot and both clean supports remain available. Targeted insertion still produces a 16.1% strict target-choice rate, compared with 0.0% for unrelated insertion. This comparison supports a targeting effect within those constructed contexts. The lower targeted rate than in ordinary retrieval cannot be attributed solely to evidence retention: the two modules also differ in their selected surrounding passages and context construction.

Repetition changes context composition as well as the prominence of the designated answer. With one, two and five identical copies per fixed target, undefended target-choice rates are 37.6%, 53.8% and 96.8%. Corresponding all-support recall falls from 54.8% to 45.2% and 0.0%. Because duplicate passages are retained with distinct IDs, repeated insertion can crowd clean supports out of the five-passage context. These results concern identical-copy repetition at a high fixed target coverage; they establish neither diverse-attack strength nor a reproduction of the missing historical repetition archive.

The defense comparison also has a utility cost. Reranking reduces the one-copy targeted-choice proxy from 37.6% to 21.0%, but it also changes clean reference-choice output from 59.1% to 45.7% and clean all-support recall from 62.9% to 35.5%. A lower target-choice rate therefore cannot stand alone as evidence of preserved answer utility. Filtering illustrates a different boundary: it excludes all base insertions by their supplied labels and reproduces the corresponding clean context. When the same targeted text receives accepted labels, its undefended target-choice rate returns under filtering. The retrieval-only label-error result further shows why rejecting needed clean material must be examined, while leaving generated-answer effects unmeasured in that module.

The combined evidence supports a limited pipeline-level conclusion: targeting, passage competition, repeated content and assumed source labels can change automatic answer production in different ways. Source-title exclusion and assistant source screening improve the follow-up's construction without proving semantic independence or factual truth. The completed case inspection distinguishes claim meaning, source support, abstention and unresolved references on the selected cases. Neither an absent target number nor a matching reference number resolves those questions by itself.

## 7. Validity limitations and further work

**Construct validity.** Automatic numerical matching cannot establish factual endorsement or full semantic correctness. Reference annotations and derived target claims have not received independent human adjudication. The source audit identifies concrete defects, not merely a hypothetical future validation need; source-consistent classifications are AI-assisted and are not final human factual judgments. A single reference set can omit alternative legitimate support. Mixed outputs and abstentions are retained rather than conflated with successful defense.

**Internal validity.** Five paired corpus conditions control the clean corpus, target set, dose, and insertion word count. Targeted/unrelated pairs also share false values. However, wording, token counts, and relevance still differ. The reference-concordant control helps assess question overlap but does not eliminate every interaction. Filtering is evaluated with idealized supplied labels. Identical requests share cached outputs, and B measures no fresh repeated-generation variation.

**Independence and analysis.** The external subset was frozen before test outputs, and all selected context titles are disjoint. The bounded A/B overlap audit uses current canonical A inputs, whose exact identity with the principal historical run remains unverified. Semantic entity/fact overlap is possible, and the public benchmark may be present in model training. A shared corpus also couples outcomes through retrieval competition. Question bootstrap intervals are conditional descriptive intervals, not population confidence guarantees or independent corpus replications.

**External validity.** The archived B experiment covers one model snapshot, one integer-surface subset, one templated attack, one positive dose, one context length and simple defenses. C adds three identical-copy doses on a new source-screened subset, while retaining the same model, context length and simple defenses; it does not establish broader-model or production-scale performance. It is neither the official HotpotQA benchmark nor a full Afghanistan institutional workload. The 9.1% added-content share remains a stress condition and does not estimate real prevalence. Results do not establish Dari/Pashto performance, robustness against adaptive optimization, or behavior of learned cross-encoders.

Further validation can use source-family and entity-disjoint fresh data with verified original-data overlap checks; additional model snapshots and task types; low-contamination and diverse-poison dose sweeps at fixed coverage; and operational evaluation of source authentication and legitimate-document rejection. These are explicit remaining experiments, not completed contributions.

## 8. Conclusion

The prospectively frozen 62-question follow-up shows that question-addressed insertions change automatic answer production in this RAG pipeline. The strict target-choice proxy averages 37.6% without defense and 0.0% under the unrelated control. When both insertions are forced into matched positions and both clean supports remain present, the corresponding rates are 16.1% and 0.0%. Five identical copies per target raise the undefended proxy to 96.8% while excluding at least one annotated support for every question. Reranking lowers targeted-choice output but also reduces clean reference-choice output, making prevention, evidence recovery and utility distinct outcomes.

The supplied-label gate removes rejected insertions by construction and loses that protection when identical text receives accepted labels. This is an assumed authority boundary, not operational document authentication. The archived B calculations remain reproducible, while its source audit identifies reference and target-validity defects; retrospective subsets do not replace its original denominator. Historical A inputs and current code are available, but the matching principal execution archive remains unrecovered.

These findings support conditional conclusions about the recorded model, contexts and automatic constructs. Source screening is AI-assisted, fresh rounds do not create new independent questions, and neither reference matching nor target production establishes factual correctness or semantic endorsement. The completed72-case author inspection provides source-linked examples; it does not turn automatic target production into a population estimate of factual attack success.

## Data availability and reproducibility

The supplementary reproduction package contains Study B's materials in `revision/experiment/`: the frozen configuration and input hashes; selected test and donor records with original IDs; 640 clean passages and three insertion pools; the dataset-source manifest; normalized embedding matrix and text mapping; all contexts and exact request payloads; raw model responses and response hashes; scored records; summary, contrast, and paired-transition tables; completion/analysis reports; and preparation, execution, and scoring scripts. Credentials and local secret files are excluded. API access is required for fresh generation; saved-response analysis and embedding/context replay do not require new generation calls.

The run used Python 3.12.14, NumPy 2.3.5, and scikit-learn 1.8.0. Generation usage across the 376 unique study requests was 271,902 input tokens and 1,531 output tokens; embedding usage was 115,583 tokens. Usage excludes the separate connectivity check. No invoice amount or operational latency comparison is claimed. The input-freeze SHA-256 is:

```
ad8f1238e5c1624dca09d1c777f175e4633811e7d1d5301d3d6314f32b2208f7
```

 The generation-context and request hashes are recorded in `generation_freeze.json`; raw-response hashes and model IDs were checked before rescoring.

Study A's canonical data and current workbench are available in the public repository at the pinned commit above. The local B and C evidence, versioned reference audit, diagnostic evaluator and author semantic findings are published under rag_security_revision_v2/ in the repository. The older pinned commit identifies the historical A inputs, while the current repository snapshot records this research revision. The exact principal A execution archives remain unrecovered. The author case inspection is documented; external replication is not claimed. No permanent archival identifier for the full revised evidence package is claimed. Source-specific redistribution terms require separate attention. HotpotQA/Wikipedia-derived excerpts and adaptations retain attribution and the dataset's stated CC BY-SA 4.0 terms [18, 24]; the package records which material is original benchmark text and which passages are artificial interventions. False passages are experimental material and must not be treated as factual sources.

The separate C archive is supplied under `rag_security_revision_v2/`: `data/` contains all candidate decisions, original test and full donor records, source cards and constructed insertions; `study_c/` contains both hash freezes, returned embeddings, exact contexts and payloads, raw responses and the usage ledger; `analysis/study_c/` contains condition, round, paired-transition and case tables. Its 2,559 distinct calls report 1,786,392 prompt tokens and 7,974 completion tokens. The recorded conservative cost is USD 0.7295, calculated from reported usage at the saved uncached rates rather than presented as an invoice. API access is needed for new inference, while the saved-output analyses are offline. Complete condition records and raw responses are provided with the C analysis; archived review-definition files preserve the original freeze history.

## Appendix A. Reproduction and review procedure

Published evidence and current documents: https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab . From the repository root, verify the saved evidence without an API key:

```bash
python rag_security_revision_v2/release/verify_evidence.py
```

The checker validates file hashes,2,559distinct saved responses,5,208condition rows and the archived calculations without changing published files.



1. Inspect `revision/experiment/freeze.json`, `config.json`, and the source dataset manifest. Verify the selected source hash and the 128-example source-title-disjoint selection.
2. Re-run `revision/experiment/analyze_experiment.py` to recompute automatic outcomes from saved responses. This performs integrity and completeness checks without an API request.
3. For a new replication, use a separate copy of the output directory, retain the frozen inputs, and follow `revision/experiment/README.md`. Fresh API outputs may differ; do not silently replace the saved results or use them to retune the same test.
4. Inspect `manual_review/author_reported_findings.json`, the72-case selection and source-linked case notes. Keep the64main cases separate from the eight diagnostic cases; their descriptive counts are not a population attack-success estimate.
5. For C, verify the separate design and generation freezes, three round-specific response mappings and complete planned denominators before running `analysis/analyze_study_c.py`. Its source screening and outcomes must not silently replace B. Its complete case mappings and recorded outputs are included in the evidence package.

## Appendix B. Historical verification boundary

The historical report [25] documents checks of five CSV hashes and 21,840 lexical verdicts, followed by a grid replay using 32 source modules matched to its historical manifest. It records Python 3.13.9, NumPy 2.3.5, pandas 2.3.3, and scikit-learn 1.7.2 for that replay. Saved answers, retrieved IDs and rounded scores, exposure flags, and token F1 reportedly matched; latency was excluded. The repetition/forged-label experiment was rescored rather than replayed.

These are historical verification statements, not an independent certification of Study A. Its complete principal and repetition execution archives were not recovered in the bounded search, although canonical inputs and current code are available. The present integrity checks and reconstruction of A inputs do not reproduce its historical outputs. Checks on B's included response evidence apply to that archive only; they do not substitute for semantic adjudication or establish the historical claims independently.

## References

[1] Wei Zou, Runpeng Geng, Binghui Wang, and Jinyuan Jia. 2025. PoisonedRAG: Knowledge Corruption Attacks to Retrieval-Augmented Generation of Large Language Models. USENIX Security, 3827-3844. https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag

[2] Baolei Zhang, Yuxi Chen, Minghong Fang, Zhuqing Liu, Lihai Nie, Tong Li, and Zheli Liu. 2025. Practical Poisoning Attacks against Retrieval-Augmented Generation. arXiv:2504.03957v1. https://arxiv.org/abs/2504.03957v1

[3] Jinyan Su, Jin Peng Zhou, Zhengxin Zhang, Preslav Nakov, and Claire Cardie. 2025. Towards More Robust Retrieval-Augmented Generation: Evaluating RAG Under Adversarial Poisoning Attacks. arXiv:2412.16708v2. https://arxiv.org/abs/2412.16708v2

[4] Baolei Zhang, Haoran Xin, Jiatong Li, Dongzhe Zhang, Minghong Fang, Zhuqing Liu, Lihai Nie, and Zheli Liu. 2025. Benchmarking Poisoning Attacks against Retrieval-Augmented Generation. arXiv:2505.18543. https://arxiv.org/abs/2505.18543

[5] Yang Jiao, Xiaodong Wang, and Kai Yang. 2025. PR-Attack: Coordinated Prompt-RAG Attacks on Retrieval- Augmented Generation in Large Language Models via Bilevel Optimization. SIGIR. https://doi.org/10.1145/3726302.3730058; author preprint: https://arxiv.org/abs/2504.07717v3

[6] Gelei Deng, Yi Liu, Kailong Wang, Yuekang Li, Tianwei Zhang, and Yang Liu. 2024. PANDORA: Jailbreak GPTs by Retrieval Augmented Generation Poisoning. arXiv:2402.08416v1. https://arxiv.org/abs/2402.08416v1

[7] Shenglai Zeng, Jiankun Zhang, Pengfei He, Yue Xing, Yiding Liu, Han Xu, Jie Ren, Shuaiqiang Wang, Dawei Yin, Yi Chang, and Jiliang Tang. 2024. The Good and The Bad: Exploring Privacy Issues in Retrieval- Augmented Generation (RAG). Findings of ACL, 4505-4524. https://aclanthology.org/2024.findings-acl.267/

[8] Chong Xiang, Tong Wu, Zexuan Zhong, David Wagner, Danqi Chen, and Prateek Mittal. 2026. Certifiably Robust RAG against Retrieval Corruption. arXiv:2405.15556v2; originally submitted 2024, revised 2026. https://arxiv.org/abs/2405.15556v2

[9] Pankayaraj Pathmanathan, Michael-Andrei Panaitescu-Liess, Cho-Yu Jason Chiang, and Furong Huang. 2025. RAGPart & RAGMask: Retrieval-Stage Defenses Against Corpus Poisoning in Retrieval-Augmented Generation. arXiv:2512.24268. https://arxiv.org/abs/2512.24268

[10] World Bank. World Development Indicators, source 2. Afghanistan observations, 2010-2023; local API snapshots retrieved 21 September 2026. Indicator-specific URLs, raw responses, retrieval timestamps, and SHA- 256 hashes are recorded in data/dataset_manifest.json and data/sources/worldbank/.

[11] Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Kuttler, Mike Lewis, Wen-tau Yih, Tim Rocktaschel, Sebastian Riedel, and Douwe Kiela. 2020. Retrieval- Augmented Generation for Knowledge-Intensive NLP Tasks. NeurIPS. https://arxiv.org/abs/2005.11401

[12] Vladimir Karpukhin, Barlas Oguz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. 2020. Dense Passage Retrieval for Open-Domain Question Answering. EMNLP, 6769-6781. https://aclanthology.org/2020.emnlp-main.550/

[13] Weijia Shi, Sewon Min, Michihiro Yasunaga, Minjoon Seo, Richard James, Mike Lewis, Luke Zettlemoyer, and Wen-tau Yih. 2024. REPLUG: Retrieval-Augmented Black-Box Language Models. NAACL, 8371-8384. https://aclanthology.org/2024.naacl-long.463/

[14] Kai Greshake, Sahar Abdelnabi, Shailesh Mishra, Christoph Endres, Thorsten Holz, and Mario Fritz. 2023. Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. arXiv:2302.12173. https://arxiv.org/abs/2302.12173

[15] Alexander Wan, Eric Wallace, Sheng Shen, and Dan Klein. 2023. Poisoning Language Models During Instruction Tuning. Proceedings of Machine Learning Research 202, 35413-35425. https://proceedings.mlr.press/v202/wan23b.html

[16] Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. 2024. Lost in the Middle: How Language Models Use Long Contexts. Transactions of the Association for Computational Linguistics 12, 157-173. https://aclanthology.org/2024.tacl-1.9/

[17] Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield, Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia Polosukhin, Jacob Devlin, Kenton Lee, Kristina Toutanova, Llion Jones, Matthew Kelcey, Ming-Wei Chang, Andrew M. Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov. 2019. Natural Questions: A Benchmark for Question Answering Research. Transactions of the Association for Computational Linguistics 7, 452-466. https://aclanthology.org/Q19-1026/

[18] Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William Cohen, Ruslan Salakhutdinov, and Christopher D. Manning. 2018. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. EMNLP, 2369-2380. https://aclanthology.org/D18-1259/

[19] Nandan Thakur, Nils Reimers, Andreas Ruckle, Abhishek Srivastava, and Iryna Gurevych. 2021. BEIR: A Heterogenous Benchmark for Zero-shot Evaluation of Information Retrieval Models. arXiv:2104.08663. https://arxiv.org/abs/2104.08663

[20] Shahul Es, Jithin James, Luis Espinosa Anke, and Steven Schockaert. 2024. RAGAs: Automated Evaluation of Retrieval Augmented Generation. EACL System Demonstrations, 150-158. https://aclanthology.org/2024.eacl-demo.16/

[21] Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. 2023. Enabling Large Language Models to Generate Text with Citations. EMNLP, 6465-6488. https://aclanthology.org/2023.emnlp-main.398/

[22] OpenAI. GPT-4.1 mini model documentation and Chat Completions API. Snapshot used: gpt-4.1-mini-2025-04-14. https://developers.openai.com/api/docs/models/gpt-4.1-mini ; https://developers.openai.com/api/reference/resources/chat

[23] OpenAI. text-embedding-3-small model documentation. 1,536-dimensional configuration used in this study. https://developers.openai.com/api/docs/models/text-embedding-3-small

[24] HotpotQA authors. HotpotQA dataset and Hugging Face distribution, distractor validation split. Revision 1908d6afbbead072334abe2965f91bd2709910ab. CC BY-SA 4.0. https://hotpotqa.github.io/ ; https://huggingface.co/datasets/hotpotqa/hotpot_qa

[25] Rizwanullah Muahed, Ramiz Mumtaz, Ebrahim Adham, Masihullah Yaqubi, and Rohid Sharifi. 2026. Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning: An exploratory offline study of retrieval and extractive answer selection. Unpublished historical research manuscript with development appendices. Archival source identified in the figure-provenance manifest.


[26] U.S. National Archives. Records of the Army Air Forces [AAF], Record Group 18. Sections 18.1 and 18.5 distinguish establishment in 1941 from reorganization in 1942. https://www.archives.gov/research/guide-fed-records/groups/018.html

[27] Ron Artstein and Massimo Poesio. 2008. Inter-Coder Agreement for Computational Linguistics. Computational Linguistics 34(4), 555–596. https://aclanthology.org/J08-4004/

[28] Timnit Gebru, et al. 2021. Datasheets for Datasets. Communications of the ACM 64(12), 86–92. https://doi.org/10.1145/3458723

[29] Rotem Dror, Gili Baumer, Segev Shlomov and Roi Reichart. 2018. The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing. ACL, 1383–1392. https://aclanthology.org/P18-1128/
