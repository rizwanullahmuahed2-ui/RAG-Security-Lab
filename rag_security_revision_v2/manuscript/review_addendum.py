"""Publish the author-supplied semantic inspection within its stated scope."""
import json
import re

def apply_review_addendum(text, work):
 author=json.loads((work/'protocol/author_manual_review_statement.json').read_text())
 assert author['completed_status']=='reported_completed_by_author'
 assert author['number_of_reviewed_responses']==72
 counts=author['main_sample_findings'];assert sum(counts.values())==64
 replacements={
 'Independent human judgments remain required and pending;':'The author reports a completed source-based semantic case inspection;',
 'Independent human semantic review has not been completed.':'The author reports a completed semantic inspection of72cases.',
 'Human semantic review remains a required, pending step.':'The completed author inspection is reported separately from automatic endpoints.',
 'Independent human review and external replication have not been completed.':'The author case inspection is documented; external replication is not claimed.',
 'human confirmation remains a separate pending task.':'source screening does not independently certify external factual truth.',
 'Source screening was AI-assisted; human confirmation remains a separate pending task.':'Source screening was AI-assisted; its acceptance denotes consistency with the saved source.',
 'The pending two-person semantic evaluation is needed to distinguish endorsed false claims, supported but false answers, abstention and unresolved references.':'The completed case inspection distinguishes claim meaning, source support, abstention and unresolved references on the selected cases.',
 'The source-review materials, revised evaluator and two-reviewer protocol make these limitations examinable.':'The source-review materials, revised evaluator and case-level evidence make these limitations examinable.',
 'The separate two-reviewer frames make the required human evaluation executable, but actual independent judgments and adjudication remain pending.':'The completed72-case author inspection provides source-linked examples; it does not turn automatic target production into a population estimate of factual attack success.',
 'Next steps are two independent blinded human reviews with documented adjudication; source-family and entity-disjoint fresh data':'Further validation can use source-family and entity-disjoint fresh data',
 'human review pending |':'source-relative case inspection; limited generalization |',
 }
 for old,new in replacements.items():text=text.replace(old,new)
 text=text.replace('**Working research revision.** Archived scores, source-audit findings and later automatic results are versioned separately.', '**Evaluation scope.** C supplies the prospective generative evidence; B is retrospective diagnostic material and A provides historical context.')
 text=re.sub(r'Two-reviewer forms cover all376.*?(?=\n\n|$)','',text,flags=re.S)
 # Match the actual typeset spacing as well as compact archived wording.
 text=re.sub(r'Two-reviewer forms cover all 376.*?(?=\n\n|$)', 'All376distinct B case records and their mapping to1,280condition rows are retained for inspection. Source-validity findings and numerical matching remain separate from a claim of externally established factual truth.',text,flags=re.S)
 text=re.sub(r'A separate blank human-review frame contains.*?(?=\n\n|$)', 'The complete C case frame contains897distinct question–context–answer–finish-reason records mapped to5,208condition/round rows. Identical answers in identical payloads can share a case record, while every round and provider-response mapping remains archived.',text,flags=re.S)
 text=re.sub(r'4\. Give each actual reviewer.*?(?=\n5\.)', '4. Inspect `manual_review/author_reported_findings.json`, the72-case selection and source-linked case notes. Keep the64main cases separate from the eight diagnostic cases; their descriptive counts are not a population attack-success estimate.',text,flags=re.S)
 text=text.replace(" Its separate initial-review forms and private coordinator key are supplied under `evaluation/study_c_review/`.", ' Its complete case mappings and recorded outputs are included in the evidence package.')
 methods='''### 4.9. Manual semantic inspection

The author reports completing a manual semantic inspection of72question–context–answer cases:32from B,32from C and eight additional diagnostic B cases. The archived selection record defines a64-case main sample and a separately flagged supplement. The inspection was retrospective, single-author and study-aware; no blinding or inter-rater agreement is claimed. Question entity, relation, date, unit, qualifiers, answer assertion, abstention and actual contextual support were considered separately. Supporting evidence outside the context was distinguished from evidence actually given to the model.

Table13 reports the aggregate findings supplied by the author. Assistant-generated case notes and quotations used during preparation remain archived with their original provenance; those files have not been relabelled as individual human ratings. The inspection supports case-level interpretation rather than a calibrated estimate of semantic attack success across all model answers. Its64main cases and eight diagnostic cases are not pooled as a representative72-case accuracy rate.

'''
 text=text.replace('## 5. Results organized by research question',methods+'## 5. Results organized by research question',1)
 results='''### 5.8. Findings from the completed semantic inspection

The main finding is that occurrence of the annotated number does not establish that the answer conveys the correct claim for the question. The author-supplied review summary records the following outcomes.

**Table13. Author-reported source-relative judgments for the64main cases. These are case counts; they do not estimate factual attack success or whole-system accuracy.**

| Outcome | Main-sample cases |
|:--|--:|
| Source-consistent answer claim |41|
| Source-contradicted answer claim |16|
| Full abstention without an answer claim |3|
| Undetermined |4|
| Total |64|

The eight diagnostic cases were assessed separately; two combine an asserted numerical answer with conflicting abstention. They were selected using diagnostic flags and do not supply an unbiased error rate.

Five findings explain why the distinctions matter. First, a Koufax answer states1972 and then declares the evidence-based answer UNKNOWN: a value match misses the conflicting commitment. Second, a generic actor/award question permits a supplied-context interpretation involving Kristen Alderson and2013, whereas its annotation intends Roger Howarth and1994; a unique reference interpretation is not established. Third, “over3,000” preserves a lower bound and cannot establish an exact count or refute3,017. Fourth, some reference-consistent answers lack sufficient support in the actual model context. Fifth, the OperationLadbroke passage supplies alternative clean evidence for the1943invasion year even when an annotated support passage is absent. Consequently, annotated all-support recall measures coverage of its specified set, not the existence of every valid proof.

The author report, case selection, exact system answers, evidence and preparation notes are available under `manual_review/` and `assistant_review/`. All188quoted snippets were matched against saved source passages or the exact answer. The semantic inspection does not rewrite archived responses, silently repair B questions, replace historical denominators or establish a general semantic attack-success percentage.

'''
 # Ensure normal spacing in published prose and table labels.
 for old,new in [('of72','of 72'),('cases:32','cases: 32'),('B,32','B, 32'),('a64','a 64'),('Its64','Its 64'),('representative72','representative 72'),('Table13','Table 13'),('the64','the 64'),('states1972','states 1972'),('and2013','and 2013'),('and1994','and 1994'),('over3,000','over 3,000'),('refute3,017','refute 3,017'),('the1943invasion','the 1943 invasion'),('OperationLadbroke','Operation Ladbroke'),('All188quoted','All 188 quoted')]:methods=methods.replace(old,new);results=results.replace(old,new)
 methods=re.sub(r'(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)', ' ', methods)
 results=re.sub(r'(?<=\d)(?=[A-Za-z])|(?<=[A-Za-z])(?=\d)', ' ', results)
 # Replace methods again with the copy containing editorial spacing fixes.
 start=text.index('### 4.9. Manual semantic inspection');end=text.index('## 5. Results organized by research question',start);text=text[:start]+methods+text[end:]
 text=text.replace('## 6. Discussion',results+'## 6. Discussion',1)
 scope='The primary experimental conclusions use C and its controlled modules. A is retained solely as historical context; its unrecovered execution archives are not needed to reproduce C. B supplies retrospective numerical and source-validity diagnostics, and its defective references do not serve as verified factual attack-success evidence.\n\n'
 text=text.replace('### 4.2.',scope+'### 4.2.',1)
 text=text.replace('independent human judgments and adjudication remain pending','population semantic attack-success calibration is not claimed')
 text=re.sub(r'Blinded review templates are supplied for two independent human reviewers.*?(?=\n\n|$)', 'The source-based manual case inspection is described in Section4.9.',text,flags=re.S)
 text=text.replace('contains897distinct','contains 897 distinct').replace('to5,208condition','to 5,208 condition').replace('All376distinct','All 376 distinct').replace('to1,280condition','to 1,280 condition').replace('Section4.9','Section 4.9')
 text=text.replace('Source screening was AI-assisted; source screening does not independently certify external factual truth.', 'Source screening was AI-assisted and denotes consistency with the saved source, not independent external truth certification.')
 text=text.replace('of72cases','of 72 cases')
 text=text.replace('versioned reference audit, diagnostic evaluator and separate reviewer packets accompany this working revision; their public availability is not inferred from the older repository commit.', 'versioned reference audit, diagnostic evaluator and author semantic findings are published under rag_security_revision_v2/ in the repository. The older pinned commit identifies the historical A inputs, while the current repository snapshot records this research revision.')
 text=text.replace('The C review frame is separate under `evaluation/study_c_review/`; its blank forms do not constitute completed human evaluation.', 'Complete condition records and raw responses are provided with the C analysis; archived review-definition files preserve the original freeze history.')
 text=text.replace('`experiment/`','`revision/experiment/`').replace('`experiment/freeze.json`','`revision/experiment/freeze.json`').replace('`experiment/README.md`','`revision/experiment/README.md`').replace('`analyze_experiment.py`','`revision/experiment/analyze_experiment.py`')
 bundle='Published evidence and current documents: https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab . From the repository root, verify the saved evidence without an API key:\n\n```bash\npython rag_security_revision_v2/release/verify_evidence.py\n```\n\nThe checker validates file hashes,2,559distinct saved responses,5,208condition rows and the archived calculations without changing published files.\n\n'
 text=text.replace('## Appendix A. Reproduction and review procedure','## Appendix A. Reproduction and review procedure\n\n'+bundle,1)
 return text
