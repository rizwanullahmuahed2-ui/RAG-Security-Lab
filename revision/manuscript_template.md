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

## Abstract

Targeted knowledge-base poisoning can supply a highly relevant passage containing an attacker-selected false answer. We examine whether relevance recovery protects answer integrity through two explicitly separate studies. The historical Afghanistan-focused study used 225 chunks, 364 questions, and deterministic extraction; its 21,840 condition evaluations are retained as previously reported evidence. A new external evaluation uses 64 numerical-answer HotpotQA questions, 640 clean passages, neural API embeddings, and the real generative model gpt-4.1-mini-2025-04-14. Its data, prompts, attack construction, defenses, scoring rules, and planned contrasts were frozen before test answers were generated. Five corpus conditions—clean, targeted poison, matched unrelated poison, matched truthful insertion, and accepted-label compromise—are crossed with four defenses. Targeted and unrelated insertions contain the same designated false value and exactly 120 whitespace words per passage. {{ABSTRACT_RESULTS}} The new evaluation contains 1,280 condition rows derived from {{UNIQUE_CALLS}} unique generation requests, with identical requests reused rather than treated as independent responses. Outcomes use numerical value matching; no independent human semantic adjudication is claimed. The combined evidence distinguishes supporting-evidence retrieval, false-value production, attack prevention, and correct-value restoration, while identifying the trust-label assumptions and external-validity limits of the tested controls.

**Keywords:** retrieval-augmented generation; knowledge-base poisoning; generative language model; external evaluation; attack specificity; provenance

## 1. Introduction

Retrieval-augmented generation (RAG) connects a language model to external evidence [11–13]. In institutional settings, the knowledge base may include administrative documents, reports, public statistics, and policy material. A poisoned document can be relevant to a question while supplying a false answer. Retrieval relevance therefore cannot serve as a factuality or source-authentication guarantee.

Prior research establishes targeted corpus poisoning as an attack against generative RAG [1–4]. The practical evaluation problem is broader than malicious retrieval alone: does supporting evidence remain available, does the attack enter the final context, and does the answer adopt its intended false value? These events may diverge. A defense can recover useful evidence without resolving a conflict between true and false claims.

Study A examined these distinctions using an Afghanistan-focused corpus and an extractive answerer [25]. Its deterministic outputs support a controlled analysis of that implementation, but they cannot estimate generative LLM behavior. Its inspected development splits and absence of matched unrelated poison also prevented an output-held-out test of attack specificity. A previously reported 24-response generative development check did not resolve these design limitations.

Study B extends this analysis through an output-held-out external evaluation with a real API LLM and neural retrieval. It directly compares targeted poisoning with an unrelated control and a relevant truthful-insertion control, keeping insertion count, word length, metadata, and corpus fixed. A metadata-only accepted-label intervention tests the source gate's authority assumption. Historical results remain separate because both the dataset and the retrieval/generation components change.

The contributions are: (1) an explicit mapping from research questions to interventions and outcomes; (2) an executed generative evaluation with matched controls and frozen response-level evidence; and (3) paired reporting that separates prevention, restoration, and newly introduced failures. This is an exploratory empirical study, with no claim of a new attack optimizer, certified defense, independent human validation, or representative institutional deployment performance.

## 2. Related research

PoisonedRAG formalizes targeted knowledge corruption through corpus insertions [1]. CorruptRAG and broader attack benchmarks examine practical poisoning and defenses [2, 4]; Su et al. study adversarial context and retrieval robustness [3]. These establish the threat rather than serve as numerical baselines reproduced here. Our shared-corpus, fixed-target protocol and simple templated attack differ from optimized attacks against large production-scale collections.

Threat boundaries also differ across research. Coordinated prompt/RAG attacks add prompt control [5]; PANDORA targets jailbreak behavior [6]; indirect prompt injection conveys instructions through external content [14]. Privacy attacks and instruction-tuning poisoning pursue different goals or alter different system layers [7, 15]. The base attacker here changes inserted factual passages only. Accepted-label compromise is a separately named change in attacker capability.

RobustRAG studies an isolate-then-aggregate defense with a formal retrieval-corruption model [8]. RAGPart and RAGMask address retrieval-stage defenses [9]. The lexical reranker and eligibility gate used here implement neither those methods nor their guarantees. Reranking is a relevance comparison; metadata filtering is a policy over labels supplied by an assumed authority.

HotpotQA supplies externally annotated question-answer pairs and supporting facts [18]. We use a restricted numerical-answer subset with a shared retrieval collection, not the official ten-paragraph-per-question evaluation. Natural Questions and BEIR motivate broader future evaluation [17, 19]. Context placement can influence LLM evidence use [16], while RAGAs and citation evaluation assess complementary properties [20, 21]. Neither lexical matching nor source inclusion alone determines whether a model endorsed a false claim.

## 3. Research questions and analytical framework

### 3.1. Questions aligned with the experimental design

Four research questions guide the analysis. Table 1 specifies the controlled comparison, outcome, and result section for each question, distinguishing historical extractive evidence from the external generative experiment.

**Table 1. Alignment of research questions, comparisons, and outcomes.**

| Question | Controlled comparison | Main outcomes | Evidence and result location |
|:--|:--|:--|:--|
| RQ1. Does targeting the evaluated question cause more false-value production or accuracy loss than matched unrelated or truthful insertions? | Targeted versus unrelated; targeted versus benign, fixed questions and dose | False-only output rate; gold-only numerical accuracy; paired differences | External generative study; Section 5.1 |
| RQ2. How do supporting-evidence recovery and malicious exposure relate to the generated answer? | Clean versus attacked; no defense versus reranking | All-support Recall@5, own-insertion exposure, numerical outcomes, coexistence counts | Both studies, reported separately; Sections 5.2 and 5.5 |
| RQ3. How do the defenses prevent successful attacks or restore answers, and how does label compromise affect them? | Four defense ablations; identical poisoned text under rejected versus accepted labels | Exposure-confirmed false outputs, paired prevention/restoration, new failures | External study and historical controls; Section 5.3 |
| RQ4. What clean utility cost accompanies the defenses? | Each defense versus the undefended clean corpus | Change in gold-only numerical accuracy and strict EM; rejected legitimate insertions described separately | Both studies, separately; Sections 5.4 and 5.5 |

The external study's planned primary contrasts are RQ1's two comparisons under no defense, each measured by false-only output and gold-only accuracy. RQ2–RQ4 comparisons are secondary and exploratory. These contrasts were specified in the local freeze before generated test answers were inspected; the study was not publicly preregistered.

### 3.2. Outcomes and denominators

For a query q, let T(q) be the final five-passage context, G(q) its annotated set of supporting passages, and A(q) the generated answer. Let C(q) indicate that A(q) contains the reference numerical value, and F(q) indicate the designated false value. Numeric comparison removes digit-grouping commas and compares decimal values using token boundaries. Define:

**Gold-only numerical accuracy:** V(q) = C(q)[1 − F(q)].

**False-only output:** O(q) = F(q)[1 − C(q)].

**Exposure-confirmed targeted success:** S(q) = R(q)O(q), where R(q) indicates inclusion of the insertion addressing q in the targeted or accepted-label condition.

An answer containing both values is mixed and receives neither accuracy nor false-only credit. False-only output is computed identically in all five conditions, allowing a fair primary contrast with the unrelated control. Exposure-confirmed targeted success is additionally reported for conditions containing target-addressed attacks; it is not mechanically assigned to unrelated poison. The separately recorded assigned-insertion exposure permits a descriptive check of the unrelated control's context inclusion.

All external-study rates use the same 64 test questions unless a conditional denominator is explicitly given. All-support Recall@5 is the fraction of questions for which every annotated supporting passage is in T(q). Fractional support recall averages |G(q) ∩ T(q)|/|G(q)|. First-support reciprocal rank is auxiliary. These metrics differ from the historical single-gold-chunk Recall@5 and must not be directly equated.

Strict normalized exact match (EM) and token F1 are auxiliary answer-format measures. Mixed answers, UNKNOWN abstentions, other outputs, and output truncation are recorded separately. Numerical containment does not adjudicate negation, endorsement, entity, relation, date, or units. Accordingly, the article reports numerical answer accuracy and false-value production, rather than independently established semantic correctness.

### 3.3. Paired defense outcomes

At a fixed corpus condition, U is the set of successful undefended targets under S(q). Prevention is the fraction of U whose attack no longer succeeds after defense. Correct-value restoration is the fraction of U whose defended answer satisfies V(q). Newly successful attacks occur outside U after defense. Clean cost is undefended clean accuracy minus defended clean accuracy, in percentage points. These measures have different interpretations: preventing a false target value does not necessarily restore a correct answer.

### 3.4. Threat model

The base attacker inserts a fixed set of factual QA-style passages into a separate copy of the corpus. The attacker knows the target question and designated false value, but does not change clean documents, user queries, system prompts, generator weights, or defense code. There is no adaptive search against test responses. One insertion addresses each test question, giving 100% target coverage at every positive targeted condition.

The source gate accepts only verified passages with high or medium trust. All new clean passages are assigned eligible labels, and all base insertions—including the truthful-insertion control—are assigned rejected labels. This tests an assumed eligibility boundary, not an implemented authentication or fact-checking service. In the accepted-label condition, the targeted text and IDs remain identical while verified becomes true and trust becomes high. This intervention explicitly permits metadata compromise.

## 4. Materials and methods

### 4.1. Two distinct studies and evidence provenance

Study A is the previously reported Afghanistan-focused offline experiment [25]. Its results are carried forward as historical evidence. The historical raw corpus, code, manifests, and response archives were unavailable for a new replay; earlier audit statements are therefore not treated as verification performed in the present analysis.

Study B is an external generative experiment whose selected questions, source excerpts, insertion files, frozen embeddings, contexts, API requests and responses, scoring outputs, and verification scripts are provided in the supplementary reproduction package. Study B neither replays Study A nor isolates the causal effect of replacing only its answerer, because the evaluation material and retrieval backend also change.

**Table 2. Study boundaries and implemented components.**

| Feature | Study A: historical offline experiment | Study B: new external generative evaluation |
|:--|:--|:--|
| Questions | 364, previously inspected; 104 designated targets | 64 external numerical-answer questions; all targeted |
| Clean collection | 224 documents, 225 chunks | 640 distinct-title HotpotQA paragraphs |
| Retrieval | 1,024-dimensional hashing; exact cosine | text-embedding-3-small, 1,536 dimensions; exact cosine |
| Reranking | Query/candidate TF-IDF | Explicitly configured query/candidate TF-IDF |
| Answerer | Deterministic sentence extraction | gpt-4.1-mini-2025-04-14 through the API |
| Corpus interventions | Five insertion budgets; three selection seeds | Five fixed corpus conditions; one insertion per target |
| Final context | At most five passages from 30 candidates | Five passages from 30 candidates |
| Evaluations | 21,840 correlated condition rows | 1,280 condition rows; {{UNIQUE_CALLS}} unique generation requests |
| Evaluation status | Development/exploratory material | Outputs held out until local data/configuration freeze |

Figure 1 shows Study A's hashing, lexical reranking, and extractive answer-selection pipeline. Study B's neural retrieval and real LLM generation are specified separately in Sections 4.4–4.5.

![Study A retrieval and extractive-answer pipeline [25]. The four conditions share the same clean collection, insertion pool, and extractive answerer. Eligibility precedes retrieval where enabled; accepted-label forgery is a separate control.](figures/original_pipeline.png){width=16.7cm}

### 4.2. External test material and independence controls

We use the HotpotQA distractor validation split distributed by the dataset authors and mirrored at Hugging Face [18, 24]. The pinned dataset revision is `1908d6afbbead072334abe2965f91bd2709910ab`. The 27,452,575-byte source Parquet has the following SHA-256:

```
c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6
```

This public validation split becomes an external local test subset; it is not the official hidden HotpotQA test set.

Eligibility requires an integer-valued annotated answer, ten distinct context titles, valid supporting-fact indices, the answer value in annotated support, and no occurrence of that value in the question. Questions longer than 80 whitespace words and questions/titles mentioning Afghanistan, Bamiyan, or the World Bank are excluded. These rules yield 461 candidates. Candidates are sorted by SHA-256 of a fixed study string and example ID. Greedy selection retains 128 examples with no shared context title: the first 64 are evaluated targets, and the next 64 supply unrelated-control donor questions. None of the 1,280 selected context titles overlaps another selected example. The donor contexts are not indexed in the clean test corpus.

Each of the 64 test examples contributes its ten supplied paragraphs, resulting in a shared 640-passage clean retrieval corpus. This differs from giving a model the correct example's ten paragraphs directly. All queries search the full shared corpus, including the other examples' distractors. The target set, answer references, false values, and supporting-passage IDs remain fixed across conditions.

This is an output-held-out external subset: no generated test answer was used to choose questions, tune prompts, optimize attacks, or change defenses. Reference annotations necessarily remain visible to construct attacks and scoring. Complete overlap checking against Study A is impossible without its raw inputs, and title disjointness does not establish semantic entity disjointness. HotpotQA may also occur in LLM pretraining. The evaluation therefore supports conditional results on this external numerical subset, not a claim of training-data independence or full domain generalization. No independent human source validation has been completed.

### 4.3. Matched corpus conditions

Every positive condition adds 64 passages to the same 640 clean passages, for a malicious or added-content share of 64/704 = 9.1%. Coverage remains 64/64; this fixed-dose experiment avoids conflating wider target coverage with per-target susceptibility.

**Table 3. Corpus conditions in Study B.**

| Condition | Inserted content | Supplied labels | Purpose |
|:--|:--|:--|:--|
| Clean | No added passages | Clean passages eligible | Utility baseline |
| Targeted | Each evaluated question paired with its designated false value | Unverified, untrusted | Targeted factual corruption |
| Unrelated | A source-title-disjoint donor question paired with the same false value used for the corresponding target | Same rejected labels | Control for unrelated false content and index additions |
| Benign | The evaluated question paired with its annotated correct value | Same rejected labels | Control for query overlap, passage format, and truthful insertion |
| Accepted label | Identical targeted text and IDs | Verified, high trust | Isolate the gate's metadata-authority assumption |

All inserted passages have exactly 120 whitespace words and share the same QA-record template and neutral archival filler. Targeted and unrelated pairs contain the same designated false value. False integers are generated deterministically from the reference value, with collision avoidance against selected correct values and other designated false values. Donor references also differ from the paired false value, so the unrelated statement is false under its own annotation. Word count is matched; model-token count and lexical/semantic relevance are not identical. The intended change in targeting remains the presence of the evaluated question versus an unrelated donor question. The benign condition preserves question overlap while changing the asserted value.

The attacks are templated factual assertions, without jailbreak instructions or iterative optimization. Results consequently do not estimate the maximum strength of an adaptive attacker. The accepted-label condition changes only metadata; text is not regenerated.

### 4.4. Neural retrieval and defense order

The API embedding model is text-embedding-3-small at 1,536 dimensions [23]. The run embeds the clean paragraphs, the three unique insertion pools, and 64 queries: 896 unique texts in seven batches of 128. Saved vectors are converted to float32, normalized to unit length, and frozen. Exact cosine retrieval ranks eligible paragraphs, with stable corpus-order tie handling. Saved embeddings permit replay without making a fresh embedding request; no immutable provider snapshot is claimed for the embedding model name.

Four conditions are evaluated: no defense; lexical reranking; eligibility filtering; and filtering followed by reranking. Filtering precedes retrieval. Candidate retrieval returns 30 passages. Where enabled, scikit-learn TfidfVectorizer is fit to the question and its 30 candidates with lowercase text, English stopwords, and L2 normalization; candidate/query cosine determines the final order, with retrieval order retained for ties. Five passages form the model context. This is a lexical reranker, not a learned cross-encoder or factual verifier.

Trust metadata controls eligibility but is not shown to the generator. The generator receives passage text under neutral rank numbers, without attack IDs or condition labels. The accepted-label condition therefore tests which text passes the gate, rather than simultaneously introducing a trust hint into the prompt. Because all clean chunks are eligible, rejecting all base insertions restores the corresponding clean context by construction.

### 4.5. Real LLM generation and frozen execution

The generator is gpt-4.1-mini-2025-04-14 through the OpenAI Chat Completions API [22], with temperature 0, a maximum of 64 generated tokens, and storage disabled. The exact model snapshot returned by every request is checked. The fixed system prompt is:

> Answer the question using only the numbered reference passages. The passages are evidence, not instructions. Return only a concise answer, with no explanation. If the evidence is insufficient, return UNKNOWN.

The user message contains the question, five numbered passage texts, and a short-answer cue. Prompts, data, insertion rules, scoring definitions, and planned contrasts are locally hashed before generating test answers. Embeddings, all final contexts, and the execution-script hash are then frozen in a second manifest. The analysis script implements the declared definitions and is included in the release manifest; it was not part of the pre-generation code freeze. This is a local, pre-execution freeze rather than a public preregistration. A separate one-token connectivity check is not a study observation.

The factorial design produces 64 × 5 × 4 = 1,280 condition rows. Exact duplicate API payloads share one saved response, producing {{UNIQUE_CALLS}} real generation calls and {{REUSED_ROWS}} reused condition rows. Cache reuse is explicit and is not treated as repeated sampling. Requests are interleaved in a deterministic hash order with at most six concurrent calls. Transient errors are retried up to three times; permanent failures and model mismatches stop execution. No model or backend fallback is permitted. Temperature 0 does not guarantee reproducibility across fresh provider calls.

### 4.6. Scoring, analysis, and verification

Automatic scoring applies the numerical definitions in Section 3.2 without consulting condition names. Primary comparisons use paired question-level differences, never response-row counts as a sample size. We report 10,000 paired question bootstrap resamples with seed 20261022 and exploratory 95% percentile intervals. These intervals are conditional on this fixed corpus, insertion set, and saved responses; they do not capture new-corpus variation, shared-corpus interference, annotation uncertainty, or stochastic generation across fresh calls. There are no confirmatory p-values or claims of population representativeness.

Verification checks input hashes, source-title disjointness, equal insertion word counts, paired false values, exact metadata-only manipulation, request and response hashes, returned model IDs, complete condition coverage, and clean-context equality after rejection. {{EXECUTION_STATUS}} API errors and output truncation are reported as execution properties rather than silently discarded.

Blinded review templates are supplied for two independent human reviewers, with condition/defense mappings in a separate key. Reviewers should assess factual endorsement, reference correctness, entity/year/unit consistency, mixed answers, and abstention. These templates contain no completed judgments. Neither a second scoring script nor AI-assisted inspection is represented as independent human adjudication.

## 5. Results organized by research question

### 5.1. RQ1: Targeting versus matched controls in the real LLM study

{{RQ1_RESULTS}}

**Table 4. Study B outcomes (%), with 64 questions per row. Support is all-support Recall@5; exposure is assigned-insertion inclusion. Gold/false use automatic value matching; EM is strict normalized exact match.**

{{MAIN_TABLE}}

{{PRIMARY_CONTRASTS}}

The unrelated condition tests generic contamination at the same insertion count and word length while retaining the same false values. The benign condition additionally preserves exact question overlap. Neither comparison removes all wording or tokenization differences, and the attacks remain a single fixed template. Results support conclusions about this intervention and subset rather than an optimized attack against all generative models.

### 5.2. RQ2: Evidence recovery, exposure, and generated outputs

{{RQ2_RESULTS}}

![Gold-only numerical accuracy and false-only output rates across five corpus conditions and four defenses. Values are percentages of 64 questions using the same generator and frozen input pools. Interpret filtering under the supplied-label boundary, including accepted-label compromise.](figures/generative_outcomes.png)

All-support recall, own-insertion exposure, and the generated value describe different events. Recovering every annotated support passage is a stronger evidence-availability check than recovering just one, but neither establishes semantic resolution of a conflicting claim. Conversely, producing a designated false value without retrieving its own attack can arise from another context or prior model knowledge; it is therefore distinguished from exposure-confirmed targeted success.

### 5.3. RQ3: Defense ablations and accepted-label compromise

{{RQ3_RESULTS}}

**Table 6. Paired defense outcomes in Study B. Prevention and restoration use the successful undefended targets in the same corpus condition. Restoration means recovery of the reference numerical value under the automatic scoring rule.**

{{PAIRED_TABLE}}

The metadata gate's rejection result is a boundary check: a gate that excludes every inserted passage reproduces its clean retrieval context. It does not show that a real ingestion process can correctly identify all malicious sources. The accepted-label intervention measures what happens when that premise is removed, with attack text unchanged. Since labels are hidden from the generator, accepted passages create the same payloads as the corresponding unfiltered targeted condition; these responses are correctly reused rather than counted as independent model draws.

### 5.4. RQ4: Clean utility cost

{{RQ4_RESULTS}}

The benign-insertion condition also exposes a limitation of the gate's label policy: every newly inserted truthful passage is rejected because it carries rejected labels. This 64/64 rejection is fixed by the experimental labeling, not an estimate of a real source-review false-positive rate. Preserving aggregate answer accuracy can coexist with excluding useful legitimate additions. Review effort, operational false rejection, latency tradeoffs, and source-authentication cost require a separate deployment study.

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

![Study A answer-value accuracy across 364 questions [25]. Points average selection seeds 17, 42, and 91; error bars show sample standard deviations. The curves describe deterministic extractive outputs under lexical scoring.](figures/original_answer_accuracy.png){width=16.7cm}

![Study A target-specific, exposure-confirmed attack success across 104 designated targets [25]. Error bars show selection-seed standard deviations. Increasing insertion count also increases attacked-target coverage; the curves are separate from Study B's generative outcomes.](figures/original_attack_success.png){width=16.7cm}

A separately reported target-specific repetition experiment contained 3,016 evaluations, including forged-label controls. Undefended success was 90/104 at one copy and 91/104 at two or more; exact duplicate collapse retained 90/104 across positive doses. At 50 copies per target, rejected-label filtering produced 0/104 successes and accepted-label filtering 91/104. Each target had a separate corpus; these outcomes are not pooled with either shared-corpus study.

The historical report also describes a changed-backend extractive diagnostic (1,092 rows), neural retrieval development checks (1,120 and 1,344 rows), and a 24-response generative pilot on three previously seen facts [25]. These remain development evidence. None is added to Study B's 64-question sample or represented as a replication of its controls. Historical verification is discussed in Appendix B.

\FloatBarrier

## 6. Discussion

### 6.1. What the matched controls establish

{{DISCUSSION_SPECIFICITY}}

The truthful-insertion comparison is needed because a question-shaped passage can be more retrievable regardless of whether its answer is true. Matching only insertion count would leave this difference unresolved. Matching word length and the designated false integer further narrows the contrast, although no single template establishes robustness against other styles, long documents, or optimized poisons.

### 6.2. Evidence availability is an intermediate property

The historical and new studies address the same analytical distinction under different implementations. They should not be combined into one ASR or one sample size. Changes in dataset, attack wording, neural retrieval, and generation prevent attribution of cross-study differences solely to LLM reasoning. Within each study, paired context and answer records show whether evidence recovery, false-answer prevention, and correct-value restoration coincide.

A numerical match also does not resolve semantic use of evidence. A response can quote, reject, or prioritize a number. The concise-answer prompt reduces some format ambiguity, and strict EM provides a complementary check, but independent endorsement-aware review is still needed before reporting human-validated security rates.

### 6.3. Provenance assumptions and institutional use

The gate evaluates labels that the experiment supplies; it does not authenticate a publisher, verify a signature, or establish truth. Its strong rejected-label behavior follows from the eligibility premise, and its accepted-label control explicitly changes that premise. These are separate threat boundaries. Neither result alone measures the effectiveness of an institutional source-review process.

For institutional pilots, source ownership, dates and versions, protected metadata changes, conflict review, and response-level records should be evaluated alongside retrieval quality. Clean-snapshot recovery should be checked against both target manipulation and baseline errors. The results justify this measurement approach, not a claim of ministry deployment, approval, or readiness for autonomous high-stakes decisions.

## 7. Validity limitations and further work

**Construct validity.** Automatic numerical matching cannot establish factual endorsement or full semantic correctness. Reference annotations and derived false claims have not received independent human adjudication. A single reference set can omit alternative legitimate support. Mixed outputs and abstentions are retained rather than conflated with successful defense.

**Internal validity.** Five paired corpus conditions control the clean corpus, target set, dose, and insertion word count. Targeted/unrelated pairs also share false values. However, wording, token counts, and relevance still differ. The truthful control helps assess question overlap but does not eliminate every interaction. Filtering is evaluated with idealized supplied labels. Identical requests share cached outputs, and no repeated-generation variance is measured.

**Independence and analysis.** The external subset was frozen before test outputs, and all selected context titles are disjoint. Exhaustive overlap with the historical raw data remains unverified, semantic entity overlap is possible, and the public benchmark may be present in model training. A shared corpus also couples outcomes through retrieval competition. Question bootstrap intervals are conditional descriptive intervals, not population confidence guarantees or independent corpus replications.

**External validity.** The generative experiment covers one model snapshot, one numerical-answer subset, one templated attack, one positive dose, one context length, and simple defenses. It is neither the official HotpotQA benchmark nor a full Afghanistan institutional workload. The 9.1% added-content share remains a stress condition and does not estimate real prevalence. Results do not establish Dari/Pashto performance, robustness against adaptive optimization, or behavior of learned cross-encoders.

Next steps are two independent blinded human reviews with documented adjudication; source-family and entity-disjoint fresh data with verified original-data overlap checks; additional model snapshots and task types; low-contamination and diverse-poison dose sweeps at fixed coverage; and operational evaluation of source authentication and legitimate-document rejection. These are explicit remaining experiments, not completed contributions.

## 8. Conclusion

This study connects four research questions to controlled comparisons through historical extractive evidence and an executed real-LLM evaluation with an output-held-out external subset, matched unrelated poison, and truthful-insertion controls. {{CONCLUSION_RESULTS}} The historical extractive results remain separate and retain their original scope. Claims follow the implemented model, frozen material, numerical scoring, and supplied-label threat boundaries. Independent semantic adjudication and broader models, sources, and workloads remain necessary for stronger security conclusions.

## Data availability and reproducibility

The supplementary reproduction package contains Study B's materials in `experiment/`: the frozen configuration and input hashes; selected test and donor records with original IDs; 640 clean passages and three insertion pools; the dataset-source manifest; normalized embedding matrix and text mapping; all contexts and exact request payloads; raw model responses and response hashes; scored records; summary, contrast, and paired-transition tables; completion/analysis reports; and preparation, execution, and scoring scripts. Credentials and local secret files are excluded. API access is required for fresh generation; saved-response analysis and embedding/context replay do not require new generation calls.

{{PROVENANCE_SUMMARY}}

The materials are provided with the manuscript; no public repository or permanent artifact identifier has been assigned. Study A's raw archives were not available for a new replay, and independent human review and external replication have not been completed. HotpotQA/Wikipedia-derived excerpts and adaptations retain attribution and the dataset's CC BY-SA 4.0 terms [18, 24]; the package records which material is original benchmark text and which passages are artificial interventions. False passages are experimental material and must not be treated as factual sources.

## Appendix A. Reproduction and review procedure

1. Inspect `experiment/freeze.json`, `config.json`, and the source dataset manifest. Verify the selected source hash and the 128-example source-title-disjoint selection.
2. Re-run `analyze_experiment.py` to recompute automatic outcomes from saved responses. This performs integrity and completeness checks without an API request.
3. For a new replication, use a separate copy of the output directory, retain the frozen inputs, and follow `experiment/README.md`. Fresh API outputs may differ; do not silently replace the saved results or use them to retune the same test.
4. Give `human_review_blinded.csv` to two independent reviewers with the review rubric, withholding `human_review_key.csv` until labels are complete. Resolve disagreements and report agreement and adjudicated results separately from the current automatic scores.

## Appendix B. Historical verification boundary

The historical report [25] documents checks of five CSV hashes and 21,840 lexical verdicts, followed by a grid replay using 32 source modules matched to its historical manifest. It records Python 3.13.9, NumPy 2.3.5, pandas 2.3.3, and scikit-learn 1.7.2 for that replay. Saved answers, retrieved IDs and rounded scores, exposure flags, and token F1 reportedly matched; latency was excluded. The repetition/forged-label experiment was rescored rather than replayed.

These are historical verification statements, not an independent certification of Study A. Its underlying archives were unavailable for a new replay. The integrity and completeness checks performed in the present analysis apply to Study B's included evidence only; they do not substitute for semantic adjudication or establish the historical claims independently.

## References

{{REFERENCES}}
