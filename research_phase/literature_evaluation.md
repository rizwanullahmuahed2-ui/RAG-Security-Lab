# Methodological research: evaluation and strength of evidence

Scope: nine primary methodological sources were checked through canonical publication records and relevant sections of the papers. This is a focused review, not a systematic literature review. No LLM was called, no new experimental outcome was generated, and no existing manuscript or frozen evidence file was modified. Recommendations below are our applications of the sources to this study; they are not all requirements imposed by those publications.

## 1. Main conclusions for the expert's review

1. **Numerical containment is an auxiliary observation, not an endorsement judgment.** An output can contain the reference value while negating it, quoting it, identifying it as outdated, or declining to answer. A useful next evaluation should separately record the answer the model actually endorses and its consistency with the independently checked reference. This recommendation combines the expert's concrete objection with the multidimensional evaluation in ALCE and RAGAs; neither paper validates the current numerical rule.
2. **Context faithfulness is particularly dangerous as the sole metric in a poisoning experiment.** RAGAs defines faithfulness against the provided context. Logically, copying an inserted false claim can be context-faithful while factually wrong. Therefore a high faithfulness score would not establish resistance to knowledge corruption. This is an inference from its definition, not an empirical result reported by RAGAs.
3. **Separate evidence selection, reference correctness, answer correctness, and targeted false endorsement.** ALCE and HotpotQA both support evaluation of evidence and answers as distinct dimensions. Their exact benchmark metrics should not simply be transplanted without adapting their assumptions to the task.
4. **Human agreement is evidence about annotation reliability, not a truth guarantee.** Human reference checking, a clear rubric, independent initial labels, disagreement records, and a reported agreement statistic are complementary. Artstein and Poesio explicitly distinguish reliability from validity. A second AI pass or an empty review sheet is not completed independent human assessment.
5. **Freeze and document the intended target of generalization.** The 64-question external subset is a local output-held-out evaluation on a restricted selection. Public benchmark status and disjoint titles do not prove absence from pretraining, entity independence, or compatibility with an Afghanistan institutional workload. A provenance datasheet and explicit split/exclusion records are useful, but do not themselves establish representativeness.
6. **State the experimental unit and the source of variability.** Cached identical payloads do not create independent model draws. Paired comparisons should retain question alignment. Shared corpus interference and repeated formulations of a fact limit the interpretation of simple question bootstrap intervals. New-corpus, new-attack, and fresh-generation variation are different estimands.

## 2. Verified sources and their limits

### E01. ALCE: answer correctness and citation support are distinct

Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. 2023. **Enabling Large Language Models to Generate Text with Citations.** EMNLP, 6465–6488. DOI: 10.18653/v1/2023.emnlp-main.398. [Canonical record and paper](https://aclanthology.org/2023.emnlp-main.398/).

The paper evaluates fluency, dataset-specific correctness, and citation quality separately. Its citation metrics use an NLI model to test support for generated statements, and it compares automatic scores with human judgments. Sections 3, 5.3, 6, Appendix F, and the limitations show why evidence availability and answer use cannot be conflated. The authors also identify limitations of their NLI evaluator, including partial support.

**Application:** retain retrieval diagnostics, but add reference-aware judgment of the asserted answer and claim support. **Limit:** ALCE is not a targeted-poisoning benchmark and does not validate a particular ASR rule or our numerical subset.

### E02. RAGAs: useful proxies, with a critical poisoning-specific boundary

Shahul Es, Jithin James, Luis Espinosa Anke, and Steven Schockaert. 2024. **RAGAs: Automated Evaluation of Retrieval Augmented Generation.** EACL System Demonstrations, 150–158. DOI: 10.18653/v1/2024.eacl-demo.16. [Canonical record and paper](https://aclanthology.org/2024.eacl-demo.16/).

Section 3 defines faithfulness as support of answer claims by the supplied context; answer relevance explicitly excludes factuality. The implementation prompts an LLM. WikiEval uses 50 Wikipedia pages and two human annotators; initial judgments and resolved disagreements are described in Section 4. Thus the work offers automated proxies, not an oracle for arbitrary tasks.

**Application:** optional claim-support/relevance diagnostics could complement reviewed reference labels. **Limit/inference:** a false poisoned context can support a false answer, so faithfulness alone cannot measure factual security. The published validation is not validation of our attack setting or a substitute for our own human review.

### E03. Annotation agreement is not factual validity

Ron Artstein and Massimo Poesio. 2008. **Survey Article: Inter-Coder Agreement for Computational Linguistics.** Computational Linguistics, 34(4), 555–596. DOI: 10.1162/coli.07-034-R2. [Canonical record and paper](https://aclanthology.org/J08-4004/).

Section 2.1 distinguishes agreement, reliability, and validity: consistent annotators can share an error. The survey examines assumptions of kappa, alpha, and related coefficients, and cautions against treating thresholds as universally interpretable.

**Application:** define exclusive label meanings and the unit being labeled, preserve independent initial labels, report category counts and observed agreement, and select an agreement statistic appropriate to the labels and missingness. Resolve disagreements in a separately recorded stage. **Limit:** the source does not mandate exactly two raters, a fixed sample size, or a universal passing kappa. Source-reference verification remains necessary even after high agreement.

### E04. HotpotQA's original task is not our modified numerical subset

Zhilin Yang, Peng Qi, Saizheng Zhang, Yoshua Bengio, William Cohen, Ruslan Salakhutdinov, and Christopher D. Manning. 2018. **HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering.** EMNLP, 2369–2380. DOI: 10.18653/v1/D18-1259. [Canonical record and paper](https://aclanthology.org/D18-1259/).

The original distractor setting mixes two gold paragraphs with eight retrieved distractors; the full-wiki setting is separate. Section 5.2 reports answer, supporting-fact, and joint metrics. The public development split is distinct from the official hidden test sets. Section 5.3 describes additional human answers and support labels to assess ambiguity.

**Application:** call Study B a derived, shared-corpus, numerical-answer evaluation subset. Preserve original IDs, support annotations, filtering rules, and denominators, and verify support for the particular asked relation. **Limit:** no official HotpotQA performance or pretraining-independence claim follows from our 64-example selection.

### E05. Dataset documentation should expose transformations and intended use

Timnit Gebru, Jamie Morgenstern, Briana Vecchione, Jennifer Wortman Vaughan, Hanna Wallach, Hal Daumé III, and Kate Crawford. 2021. **Datasheets for Datasets.** Communications of the ACM, 64(12), 86–92. DOI: 10.1145/3458723. [Author-institution publication record](https://www.microsoft.com/en-us/research/publication/datasheets-for-datasets/) and [author preprint](https://arxiv.org/abs/1803.09010).

The proposed documentation covers motivation, composition, collection, preprocessing/labeling, uses, distribution, and maintenance. The questions explicitly address samples versus populations, recommended splits, relationships among instances, error/noise, external dependencies, verification of derived data, and preservation of raw data/software.

**Application:** one traceable record should link source snapshot → fact → document/chunk → query/reference → target/poison → condition/result, with missing historical material explicitly identified. **Limit:** a completed datasheet is documentation, not automatic truth certification or an authentication mechanism. The publisher DOI fetch was blocked; metadata was checked on the coauthors' institutional publication record and relevant full preprint sections were consulted.

### E06. Leakage and scientific target distribution must be explicit

Sayash Kapoor and Arvind Narayanan. 2023. **Leakage and the reproducibility crisis in machine-learning-based science.** Patterns, 4(9), 100804. DOI: 10.1016/j.patter.2023.100804. [Article full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC10499856/) and [publisher DOI](https://doi.org/10.1016/j.patter.2023.100804).

The paper proposes a taxonomy of leakage, including absent separation, preprocessing/selection using test information, duplicates, and mismatches between test data and scientific claims. It distinguishes computational rerunning from the validity of analysis and recommends explicit model-information documentation.

**Application:** keep development decisions separate from fresh output evaluation, retain a selection ledger, and restrict claims to the assessed domain. **Limit:** this work does not demonstrate leakage in our corpus or reveal the API model's training data. Knowledge of target references for attack construction is not, by itself, evidence of training leakage. Publisher access was blocked; relevant full-text taxonomy sections were consulted through the primary PMC article's indexed content.

### E07. NLP statistical tests require assumptions, not just a named procedure

Rotem Dror, Gili Baumer, Segev Shlomov, and Roi Reichart. 2018. **The Hitchhiker's Guide to Testing Statistical Significance in Natural Language Processing.** ACL Long Papers, 1383–1392. DOI: 10.18653/v1/P18-1128. [Canonical record and paper](https://aclanthology.org/P18-1128/).

The paper relates test selection to the setup and metric. Its discussion of open issues explicitly notes that standard independence assumptions are often violated by NLP examples sharing documents, sources, or authors. It does not claim a universal solution for all dependent-data settings.

**Application/inference:** retain within-question pairing and declare the unit resampled. For our shared corpus, distinguish conditional query-level summaries from uncertainty across new corpus/attack realizations. Multiple formulations of one fact should not be counted as unrelated observations. **Limit:** this paper does not certify the current 64-question bootstrap, choose a power target, or establish that cluster resampling alone solves shared-index interference.

### E08. Repeated seeds only measure the randomness actually varied

Nils Reimers and Iryna Gurevych. 2017. **Reporting Score Distributions Makes a Difference: Performance Study of LSTM-networks for Sequence Tagging.** EMNLP, 338–348. DOI: 10.18653/v1/D17-1035. [Canonical record and paper](https://aclanthology.org/D17-1035/).

This empirical study shows that single-run comparisons can conceal variability in nondeterministic neural training, and advocates reporting distributions over executions.

**Application/inference:** separately log attack selection seeds, data selection, and fresh generation repeats. A repeated deterministic endpoint or reuse of a cached response supplies no new generator draw. **Limit:** the paper studies trained LSTMs, not API LLM inference; it prescribes neither a number of repetitions for this study nor an LLM sampling-variance estimate from historical selection seeds.

### E09. Report the search and selection process, not only final scores

Jesse Dodge, Suchin Gururangan, Dallas Card, Roy Schwartz, and Noah A. Smith. 2019. **Show Your Work: Improved Reporting of Experimental Results.** EMNLP-IJCNLP, 2185–2194. DOI: 10.18653/v1/D19-1224. [Canonical record and paper](https://aclanthology.org/D19-1224/).

The paper relates conclusions to tuning/search budgets and proposes a reporting checklist covering search ranges, trial counts, selection criteria, results, and runtime context. It distinguishes more complete reporting from a demand to run more experiments.

**Application:** preserve development versus frozen-test decisions, discarded conditions/failures, actual active backends, and the criterion selecting the reported model/configuration. **Limit:** the proposed expected-validation-performance method is for hyperparameter search; it is not an ASR estimator or a requirement to run arbitrary new trials.

## 3. Consequences for our next-stage decisions

These are design implications to examine in the later plan, not implemented corrections:

- Keep the existing frozen numerical results as an auditable historical score set. Introduce any semantic/adjudicated result as a new, explicitly versioned analysis; do not silently relabel the old primary metric.
- Define separate fields for correct-reference endorsement, intended-false endorsement, mixed/contradictory output, abstention, other error, reference defect, and execution failure. Explicitly check entity/relation/date/units, negation, and quotation. Decide in advance how an unsupported-but-correct answer is reported.
- If human review is possible, preserve independent initial labels and reviewer qualifications/instructions, then adjudicate disagreements. The number and sampling strategy should follow the intended claim and available resources; “two reviewers” is a practical proposed design, not a universal mandate of the cited survey.
- A number mentioned in an annotated support sentence can be unrelated to the requested fact. Eligibility by numerical occurrence alone needs relation-level source checking before a stronger factual interpretation.
- State three uncertainty targets separately: (a) variation over this frozen query set, (b) variation over new corpora/attack realizations, and (c) fresh-generation variability. Current cached observations address none of these as independent generator replications.
- Do not call a locally frozen public-validation subset an official hidden benchmark test, an external replication, or proof of no pretraining contamination.
- Publish or supply an evidence index and a small error-case table with IDs and source/response excerpts. A hash proves byte consistency; semantic correctness and source authorization require additional evidence.

## 4. Current bibliography checks within this task

- Current manuscript [21] **does include** the word “Large” and matches ALCE's verified title, authors, year, venue, and pages. A provisional concern about a missing word was rejected after checking the actual file.
- Current manuscript [20] has the correct RAGAs title/authors/year/pages, but its URL contains a literal extraction space: `2024.eacl- demo.16`. The canonical URL is `https://aclanthology.org/2024.eacl-demo.16/`. This is a presentation/link defect, not an error in the underlying experiment.
- [18] is consistent with the canonical HotpotQA record; the paper PDF spells William W. Cohen while the Anthology citation renders William Cohen. This difference is not treated as a substantive citation defect.

The cited papers supply methodological rationale. Whether an expert's item is actually closed depends on the existing/new study evidence, not on adding more citations.
