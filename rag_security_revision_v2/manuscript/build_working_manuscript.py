"""Build a working article from saved evidence; never modifies historical files.

Study C is included as executed only when completed responses and the full local
freeze chain pass byte checks. Human semantic review remains pending here.
"""
from __future__ import annotations

import base64
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from review_addendum import apply_review_addendum

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
WORKSPACE = WORK.parent
SOURCE = WORKSPACE / 'revision/Revised_Manuscript.md'
REPO = 'https://github.com/rizwanullahmuahed2-ui/RAG-Security-Lab/tree/6f76858df91277e4b962ee94b4286a25cfe08d4d'
COMMIT = '6f76858df91277e4b962ee94b4286a25cfe08d4d'
FIGURES = ['original_pipeline.png', 'generative_outcomes.png',
           'original_answer_accuracy.png', 'original_attack_success.png']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def replace_section(text, heading, replacement):
    start = text.index(heading)
    end = text.find('\n## ', start + len(heading))
    if end < 0:
        end = len(text)
    return text[:start] + replacement.rstrip() + '\n' + text[end:]


def replace_subsection(text, heading, replacement):
    start = text.index(heading)
    ends = [position for marker in ['\n### ', '\n## ']
            if (position := text.find(marker, start + len(heading))) >= 0]
    end = min(ends) if ends else len(text)
    return text[:start] + replacement.rstrip() + '\n' + text[end:]


def verify_c():
    run = WORK / 'study_c'
    analysis = WORK / 'analysis/study_c/analysis.json'
    if not (run / 'completion.json').exists() or not analysis.exists():
        return None
    for filename in ['design_freeze.json', 'generation_freeze.json']:
        assert sha(run / filename) == (run / (filename + '.sha256')).read_text().strip(), filename
    design = load(run / 'design_freeze.json')
    for key, base in [('data_hashes', WORK / 'data'), ('source_hashes', WORK / 'runner'), ('run_hashes', run)]:
        for name, expected in design[key].items():
            assert sha(base / name) == expected, name
    for name, expected in design.get('external_hashes', {}).items():
        path = Path(name) if Path(name).is_absolute() else WORK / 'data' / name
        assert sha(path) == expected, name
    generation = load(run / 'generation_freeze.json')
    for name, expected in generation['run_hashes'].items():
        assert sha(run / name) == expected, name
    completion = load(run / 'completion.json')
    assert sha(run / 'responses.jsonl') == completion['responses_sha256']
    requests = load(run / 'requests.json')
    assert all(hashlib.sha256(canonical(payload)).hexdigest() == key for key, payload in requests.items())
    responses = [json.loads(line) for line in (run / 'responses.jsonl').read_text().splitlines() if line.strip()]
    config = load(WORK / 'data/config.json')
    keys = {(row['round_id'], row['request_sha256']) for row in responses}
    assert len(keys) == len(responses) == len(requests) * config['rounds']
    assert all(row['response']['model'] == config['generator'] for row in responses)
    assert all(hashlib.sha256(canonical(row['response'])).hexdigest() == row['response_sha256'] for row in responses)
    result = load(analysis)
    assert result.get('summary'), 'Completed C analysis must contain result rows'
    assert load(WORK / 'analysis/study_c/analysis_manifest.json')['files']['analysis.json'] == sha(analysis)
    for key in ['design_and_generation_freezes_verified', 'request_payload_hashes_verified',
                'raw_response_hashes_and_models_verified', 'completion_response_archive_hash_verified']:
        assert result['integrity'][key] is True, key
    assert result['integrity']['analysis_script_sha256'] == sha(WORK / 'analysis/analyze_study_c.py')
    return {'analysis': result, 'completion': completion, 'config': config,
            'n': len(load(WORK / 'data/test_questions.json')), 'analysis_sha256': sha(analysis)}


def metric(c, module, condition, defense, name, copies=1):
    # Clean rows have dose zero; the other one-copy core/controlled rows have one.
    target_copies = 0 if condition == 'clean' else copies
    rows = [row for row in c['analysis']['summary']
            if row['module'] == module and row['condition'] == condition and row['defense'] == defense
            and int(row['copies_per_target']) == target_copies and row['metric'] == name]
    assert len(rows) == 1, (module, condition, defense, name, copies)
    assert int(rows[0]['n_questions']) == c['n']
    return rows[0]


def rate(row, field='mean_question_rate'):
    value = row.get(field)
    if value is None:
        return f"{100*row['rate_lower']:.1f}–{100*row['rate_upper']:.1f}*"
    return f'{100*value:.1f}'


def c_abstract(c):
    target = rate(metric(c, 'core', 'targeted', 'none', 'strict_target_choice_proxy'))
    unrelated = rate(metric(c, 'core', 'unrelated', 'none', 'strict_target_choice_proxy'))
    rerank = rate(metric(c, 'core', 'targeted', 'rerank', 'strict_target_choice_proxy'))
    controlled = rate(metric(c, 'controlled', 'targeted', 'none', 'strict_target_choice_proxy'))
    repeated = [rate(metric(c, 'dose', 'targeted', 'none', 'strict_target_choice_proxy', copies))
                for copies in [2, 5]]
    return f'''## Abstract

Retrieval relevance does not ensure that a retrieval-augmented generation system follows valid evidence. We examine question-addressed knowledge-base insertions through a source-screened follow-up, an audited generative archive and historical extractive evidence. The follow-up C uses {c['n']} calendar-year or dated-population questions, 620 shared clean passages, unit-matched donors and equal-length targeted, unrelated and reference-concordant insertions. A locally frozen protocol combines API embeddings, gpt-4.1-mini-2025-04-14, four defense arms and three fresh generation rounds per unique payload. Separate experiments impose insertion exposure while retaining both supporting passages, or repeat identical insertions at fixed target coverage. Across questions, the strict concise target-choice proxy averages {target}% under targeted insertion and {unrelated}% under unrelated insertion; reranking gives {rerank}%. When exposure and supporting evidence are retained by construction, targeted insertion gives {controlled}% and unrelated insertion gives 0.0%. With two and five copies per target, the undefended proxy rises to {repeated[0]}% and {repeated[1]}%. Reranking also reduces clean reference-choice outputs, while a supplied-label filter loses its target-output protection when identical text receives accepted labels. These results distinguish exposure, evidence retention and answer production within this pipeline. A separate scoring implementation reproduces the archived B numerical results, but its source audit finds five ambiguous references, six requiring correction and ten target claims whose falsity is not established by the available evidence. The matching principal execution archive of historical A remains unrecovered. Source screening is AI-assisted, and these automatic proxies do not establish semantic attack success. Independent human judgments remain required and pending; repeated calls and shared-corpus condition rows do not increase the independent question count.
'''


def audit_sections():
    audit = load(WORK / 'reference_audit/B_reference_audit_summary.json')
    rows = list(csv.DictReader((WORK / 'reference_audit/B_retrospective_source_sensitivity.csv').open(encoding='utf-8-sig')))
    lookup = {(row['subset'], row['condition'], row['defense']): row for row in rows}
    table = ['| Retrospective set | n | Clean reference only | Targeted reference only | Targeted target only | Reranked target only |',
             '|:--|--:|--:|--:|--:|--:|']
    sets = [('all_64_archived_cases', 'Complete archived set'),
            ('source_aligned_exact_relation_retrospective', 'Source-aligned exact relation, including 311'),
            ('source_aligned_quantitative_retrospective', 'Source-aligned quantitative cases')]
    for key, label in sets:
        clean = lookup[(key, 'clean', 'none')]
        target = lookup[(key, 'targeted', 'none')]
        rerank = lookup[(key, 'targeted', 'rerank')]
        table.append(f"| {label} | {clean['n']} | {clean['numeric_gold_only_count']} | {target['numeric_gold_only_count']} | {target['numeric_false_only_count']} | {rerank['numeric_false_only_count']} |")
    assert audit['gold_status_counts'] == {'accepted': 53, 'ambiguous': 5, 'needs_correction': 6}
    return '''### 5.6. Reference validity and retrospective diagnostic analysis

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

''' + '\n'.join(table) + '''

The 51-case subset requires a source-aligned reference relation and a target contradicted by that exact source-defined relation. Removing the numeric band name gives 50 quantitative cases. Both subsets retain 25 target-only outputs without defense and 14 after reranking. The original 34/64 and 17/64 remain the archived results. Selection for this analysis occurred after the original outputs were available, and its source judgments remain subject to real human review.

The revised automatic evaluator adds a deliberately restrictive concise-number proxy and flags negation, quotation, qualification, uncertainty and abstention language. Across the 376 unique archived outputs, it detects abstention language in 46, compared with 41 literal UNKNOWN responses under the old rule. These flags include potentially conflicting answers and are not 46 confirmed semantic abstentions. The strict-format proxy recognizes 194 reference choices, 47 target choices, 27 other numerical choices and 108 outputs outside its format. Rejecting a long answer from this proxy does not establish that the answer is wrong. For example, the Koufax response gives 1972 while explicitly declaring the evidence-based answer UNKNOWN; factual correctness, evidence support and abstention require separate judgments.

Two-reviewer forms cover all 376 question–context–response cases and preserve their mapping to 1,280 condition rows. Stage 1 withholds condition names, defense names, automatic judgments and the attacker target; Stage 2 is released only after initial decisions are locked. The case wording may still reveal treatment structure. Actual independent labels, agreement and adjudication are pending; neither these source classifications nor the new proxy is reported as human validation [27].
'''


def alignment_section(c):
    c_location = ('C: Section 5.7, Tables 10–12 and saved paired/case tables' if c else
                  'C: prospective protocol in Section 4.8; execution results pending')
    return '''### 3.1. Questions aligned with the experimental design

Four research questions link the interventions to their measured outcomes. Study B supplies the archived generative comparisons. The separate C follow-up adds source-screened questions, controlled exposure, fixed-target repetition and three fresh generation rounds. Study A contributes historical extractive evidence only; it is not pooled with either generative study.

**Table 1. Alignment of research questions, comparisons and evidence. B and C retain their own data, endpoints and denominators.**

| Question | Controlled comparison | Measured outcomes | Evidence and result location |
|:--|:--|:--|:--|
| RQ1. Does question targeting increase designated target output or reduce reference matching relative to unrelated and reference-concordant insertions? | B and C core: targeted versus unrelated and benign, fixed questions and dose. C also fixes exposure in a separate context intervention and varies identical-copy dose at fixed target coverage. | B: archived target-only and reference-only numerical outputs. C: strict concise target-choice proxy and designated numerical target production; reference choice is secondary. | B: Section 5.1. ''' + c_location + ''' |
| RQ2. How do supporting-evidence recovery and insertion exposure relate to generated outputs? | B and C core: clean versus attacked, no defense versus reranking. C controlled contexts retain both complete supporting passages and impose insertion exposure. | All-support Recall@5, assigned-insertion exposure and answer-proxy coexistence; controlled-context answer outcomes are separate from ordinary retrieval. | B: Section 5.2; A: historical Section 5.5. ''' + c_location + ''' |
| RQ3. How do defenses prevent target outputs or recover reference values, and how does changing supplied labels affect them? | B and C core: four defense arms and identical targeted text under rejected versus accepted labels. C repetition compares no defense and reranking at each fixed-target dose. | Paired proxy prevention, reference-choice recovery and newly introduced target choices; labels are supplied experimental assumptions. | B: Section 5.3; A: historical Section 5.5. ''' + c_location + ''' |
| RQ4. What measured utility cost accompanies the defenses and rejection of legitimate evidence? | B and C core: each defense versus the undefended clean corpus. C separately rejects a required support, with all-accepted and equally sized non-support rejection controls. | Reference matching and strict EM on generated clean answers. The C label-error stress test measures retrieval recovery only and supplies no generated-answer cost estimate. | B: Section 5.4; A: historical Section 5.5. C: Section 4.8 and saved retrieval-stress results; core answer results follow ''' + ('Section 5.7' if c else 'after execution') + '''. |

At B's original execution, the two planned RQ1 contrasts under no defense used target-only and reference-value-only numerical outputs. They were specified in the local freeze before B answers were inspected; subsequent B source screening and diagnostic analyses are retrospective. C separately fixes targeted-minus-unrelated and targeted-minus-benign contrasts under no defense, using its strict concise target-choice proxy and designated numerical target production. C reference choice, evidence recovery, controlled exposure, repetition and defense transitions are secondary analyses. Neither study was publicly preregistered, and neither automatic endpoint establishes completed human semantic validation.

C averages planned rounds within each of its 62 questions before averaging across questions. Condition rows, reused payloads and fresh calls do not increase the question count or remove dependence from the shared corpus. The three studies therefore have separate denominators and support no pooled attack-success rate.
'''


def c_methods(c):
    prepared = (WORK / 'data/test_questions.json').exists()
    n = len(load(WORK / 'data/test_questions.json')) if prepared else 62
    status = ('The follow-up was executed under the two-stage freeze described below.' if c else
              'This follow-up is prospective and is not counted as an executed result in this version. ' +
              ('Its selected inputs have been prepared.' if prepared else 'Its selected inputs are being prepared.'))
    return f'''### 4.7. Source audit and revised evaluation protocol

The original B scores are preserved. A versioned source audit and diagnostic evaluator are supplied separately. The audit distinguishes source-consistent reference relations, unresolved questions and targets whose falsity is not established. Its accepted label means agreement with a specified saved source, not independent truth certification. Documentation links source snapshot, passage, question, reference, insertion and output, following the purpose of dataset documentation rather than treating documentation as validation [28].

The new format proxy accepts only a restricted affirmative scalar answer, optionally with a short fixed prefix or listed unit, and rejects detected negation, quotation, bounds, uncertainty, abstention language and execution problems. It does not validate the entity, relation, unit or real-world truth. Factual correctness, support from any provided passage, support from provided clean passages, target-claim endorsement and abstention remain separate semantic axes. A false answer can be supported by a poisoned context; numerical co-occurrence is not entailment [20, 21].

### 4.8. Prospective follow-up C: source screening, exposure and repetition

{status} C uses {n} new calendar-year or dated-population questions and {n} context-title-disjoint donor questions. The target size was refined from 64 to 62 before any C output because exact unit matching was available for 57 year pairs and five population pairs; coarse counts with mismatched fine units were excluded. The 192 automatically screened candidates, 135 source-accepted cases and all exclusion reasons are retained. Of 11 eligible dated-population candidates, the last in the predefined hash order remains an unpaired reserve; ten enter the five population pairs. Source screening was AI-assisted; human confirmation remains a separate pending task. Original questions are preserved, and no C answer was used to choose cases.

All 128 B test/donor IDs and context-title sets are excluded. The new examples also have mutually disjoint complete context-title sets. These are explicit source-title checks; they do not prove disjoint entities, source families, facts under paraphrase or model pretraining. Every C query searches the same {10*n}-passage clean collection. Each positive condition adds {n} passages, one per target, giving a final added-content share of {n}/{11*n} = 9.1%. The five corpus conditions and four defense arms follow B, with the same generator snapshot, embedding model, candidate count, final context length and prompt. The donor and target share an attacker-designated value that conflicts with their respective source-defined exact values; source-based contradiction is not independent human factual validation.

The separate exposure-controlled module fixes two complete support passages and two clean non-support passages. A fifth slot contains a constructed neutral clean filler, the targeted insertion, the unrelated insertion or the reference-concordant insertion; all four slot texts have 120 whitespace words. The filler is explicitly recorded as constructed indexing text, not a source quotation. The variable slot is approximately balanced across ranks and fixed across the four arms of each question. Reranking and filtering are absent from this module, so both the inserted text and the required clean support are present by construction. It measures a controlled context intervention separately from natural retrieval competition.

The fixed-target repetition module uses one, two and five identical copies per target, with no defense or reranking. Target coverage stays fixed. Its final added-content shares are 9.1%, 16.7% and 33.3%; this is a repetition stress test, not diverse attack generation or a reproduction of A's missing repetition archive. A separate retrieval-only label-error test rejects one required clean support, with all-accepted and equally sized non-support rejection controls. That test measures support recovery under a hypothetical label error; no final-answer cost is inferred without generator measurements.

For each unique exact payload, three fresh provider calls are made in separate rounds. Identical payloads may reuse a response within one round; a response cannot be reused across rounds. The aggregate is the mean across rounds within question, then the mean across questions. Fresh calls at temperature zero do not guarantee statistically independent outputs, and {n} questions do not become {3*n} independent questions. Per-round ranges are descriptive; the shared corpus still couples retrieval outcomes. No population confidence guarantee is claimed [29].

The first local freeze covers source-screened data, code, evaluator definitions and embedding requests before embeddings are requested. The second freezes returned vectors, final contexts and exact generation requests before completions. Every dispatch, including an empty-cache start or resumed run, checks the relevant freeze and pending payload. Model mismatch, permanent API failure, changed inputs and the recorded money ceiling stop execution. Offline tamper tests require zero dispatch after a changed pending request. These are file-integrity controls, not authentication against an adversary controlling the files and hashes. Failures, truncations and unresolved outputs are reported with planned denominators and explicit bounds; they are not silently counted as unsuccessful attacks.
'''


def c_results(c):
    if c is None:
        return ''
    n = c['n']; rounds = c['config']['rounds']; done = c['completion']
    table = ['| Corpus | Defense | Strict target choice (%) | Strict reference choice (%) | All-support Recall@5 (%) |',
             '|:--|:--|--:|--:|--:|']
    labels = {'clean': 'Clean', 'targeted': 'Targeted', 'unrelated': 'Unrelated', 'benign': 'Reference-concordant', 'accepted_label': 'Accepted label'}
    defense = {'none': 'None', 'rerank': 'Rerank', 'filter': 'Filter', 'filter_rerank': 'Filter + rerank'}
    for condition in ['clean', 'targeted', 'unrelated', 'benign', 'accepted_label']:
        for arm in ['none', 'rerank', 'filter', 'filter_rerank']:
            values = [rate(metric(c, 'core', condition, arm, name)) for name in
                      ['strict_target_choice_proxy', 'strict_reference_choice_proxy', 'all_support']]
            table.append('| ' + labels[condition] + ' | ' + defense[arm] + ' | ' + ' | '.join(values) + ' |')
    targeted = metric(c, 'core', 'targeted', 'none', 'strict_target_choice_proxy')
    unrelated = metric(c, 'core', 'unrelated', 'none', 'strict_target_choice_proxy')
    reranked = metric(c, 'core', 'targeted', 'rerank', 'strict_target_choice_proxy')
    result = f'''### 5.7. Study C: source-screened prospective follow-up

The completed follow-up evaluates {n} fixed questions over {rounds} fresh generation rounds. The archive records {done['fresh_provider_successes']:,} successful provider responses for {done['unique_payloads']:,} different payloads and {done['condition_evaluations']:,} condition evaluations. The completion report records {done['normal_stop']:,} normal stops, {done['truncations']} truncations and {done['other_finish_reasons']} other finish reasons; execution details remain separate from answer outcomes. Exact duplicates within a round reuse one response. No cross-round response reuse or model fallback is permitted.

The undefended strict target-choice proxy averages {rate(targeted)}% under targeted insertion and {rate(unrelated)}% under unrelated insertion. Reranking gives {rate(reranked)}% in the targeted condition. These are syntactically restricted automatic choices, not independently adjudicated false-claim endorsement or factual accuracy. B and C differ in reference screening and selected data, so their rates are not a causal comparison of models or a replacement for B's archived denominator.

**Table 10. Study C core outcomes, averaged first across rounds within each question and then across the {n} questions. Asterisks indicate planned-denominator lower–upper bounds when valid outputs are incomplete.**

''' + '\n'.join(table) + '\n\n'
    controlled = ['| Controlled slot | Strict target choice (%) | Strict reference choice (%) |', '|:--|--:|--:|']
    for condition in ['clean', 'targeted', 'unrelated', 'benign']:
        controlled.append('| ' + labels[condition] + ' | ' + ' | '.join(
            rate(metric(c, 'controlled', condition, 'none', name)) for name in
            ['strict_target_choice_proxy', 'strict_reference_choice_proxy']) + ' |')
    result += f'''**Table 11. Controlled-exposure C outcomes. Each of the {n} questions retains the same four clean passages and one fixed replacement position across four arms; this is a constructed-context comparison, not ordinary retrieval.**

''' + '\n'.join(controlled) + '\n\n'
    dose = ['| Copies per fixed target | Defense | Strict target choice (%) | Strict reference choice (%) | Own-insertion exposure (%) |',
            '|--:|:--|--:|--:|--:|']
    for copies in [1, 2, 5]:
        for arm in ['none', 'rerank']:
            module = 'core' if copies == 1 else 'dose'
            values = [rate(metric(c, module, 'targeted', arm, name, copies)) for name in
                      ['strict_target_choice_proxy', 'strict_reference_choice_proxy', 'assigned_insert_exposed']]
            dose.append(f'| {copies} | {defense[arm]} | ' + ' | '.join(values) + ' |')
    result += f'''**Table 12. C repetition at fixed coverage of all {n} targets. Copies repeat identical text; results do not measure paraphrase diversity or an optimized attack.**

''' + '\n'.join(dose) + '\n\n'
    paired = next(row for row in c['analysis']['paired_defense_outcomes']
                  if row['condition'] == 'targeted' and row['defense'] == 'rerank'
                  and row['metric'] == 'strict_target_choice_proxy')
    per_round = paired['per_round_counts']
    counts = lambda key: '/'.join(str(row[key]) for row in per_round)
    result += f'''The paired targeted transitions make the net reranking change interpretable. In rounds 1/2/3, the undefended exposure-confirmed target-choice counts are {counts('initial_success_lower')}; reranking prevents {counts('prevented_lower')}, restores reference choices in {counts('restored_reference_lower')} and introduces {counts('new_success_lower')} new exposure-confirmed target choices. Thus prevention and restoration are different events. The 186 paired cells repeat the same {n} questions and are not 186 independent targets.

'''
    stress = load(WORK / 'study_c/retrieval_label_stress_summary.json')
    stress_lookup = {(row['condition'], row['defense']): row for row in stress['summary']}
    before = stress_lookup[('all_accepted', 'filter')]['all_support_count']
    rejected = stress_lookup[('support_rejected', 'filter')]['all_support_count']
    distractor = stress_lookup[('distractor_rejected', 'filter')]['all_support_count']
    result += f'''The retrieval-only label-error stress test retains all annotated supports for {before}/{n} questions with all clean labels accepted. Rejecting one required support per question makes this {rejected}/{n} after filtering, whereas rejecting one clean non-support passage retains {distractor}/{n}. This result concerns annotated-passage coverage: no generator calls were made in that module, and it does not measure final-answer harm, alternative evidence or real-world authentication.

'''
    if (ROOT / 'figures/study_c_outcomes.png').exists():
        result += f'''![Figure 5. Source-screened Study C automatic outcomes across three fresh provider rounds on {n} fixed questions. Plot ranges, where shown, describe variation between rounds on the same corpus; they are not population confidence intervals or human-validation results.](figures/study_c_outcomes.png){{width=16.7cm}}

'''
    cases = [json.loads(line) for line in (WORK / 'analysis/study_c/cases.jsonl').read_text().splitlines() if line.strip()]
    by_case = {row['case_id']: row for row in cases}
    representatives = {row['case_group']: by_case[row['representative_case_ids'][0]]
                       for row in c['analysis']['case_groups'] if row['representative_case_ids']}
    support_case = representatives['annotated_support_retained_with_target_choice_proxy']['observed']
    prevention_case = representatives['proxy_prevention_without_reference_choice_restoration']
    assert support_case['qid'] == '5ae26c435542994d89d5b420'
    assert support_case['answer'] == '1832' and support_case['reference'] == '1825'
    assert support_case['all_support'] and support_case['round_id'] == 2
    assert prevention_case['qid'] == '5a8f54165542992414482a52'
    assert prevention_case['observed']['answer'].endswith('is UNKNOWN.')
    assert prevention_case['counterpart']['answer'] == '12,289'
    result += '''The first hash-selected support-retention example asks for the birth year of the composer of *Cagliostro-Walzer*. In round 2 under accepted-label filtering, the saved answer is “1832,” the designated target. The final context places the insertion first, the passage identifying Johann Strauss II second, and the passage giving his birth date in 1825 third. Both annotated supports are therefore present; their availability does not force reference-choice output. In the first hash-selected prevention-without-restoration example, the Meadowbrook Parkway question changes from “12,289” without defense to a response identifying North Merrick but stating that its 2010 population “is UNKNOWN” after filtering and reranking. The defended context retains the route-to-community link but omits the annotated population passage. These are traceable output and context observations, not completed human judgments about factuality or abstention. The case index retains every qualifying case, including those not illustrated here.

'''
    review = load(WORK / 'evaluation/study_c_review/human_review_packet/REVIEW_STATUS.json')
    assert review['completed_human_judgments'] == 0
    result += f'''A separate blank human-review frame contains {review['unique_cases']:,} distinct C question–context–answer–finish-reason cases, mapped to all {done['condition_evaluations']:,} condition/round rows. Identical returned answers in identical payloads across rounds may share one human assessment; all round and provider-response mappings are retained. This does not merge C with B's 376-case frame or complete either study's semantic endpoint. The user will coordinate two other actual reviewers. Their initial independent labels, agreement and source-linked adjudication remain pending.
'''
    return result


def c_discussion(c):
    if c is None:
        return ''
    value = lambda module, condition, defense, name, copies=1: rate(metric(c, module, condition, defense, name, copies))
    return f'''### 6.4. What the follow-up adds to the explanation

C separates question targeting from two important context effects. In ordinary retrieval, the assigned targeted insertion is present for {value('core', 'targeted', 'none', 'assigned_insert_exposed')}% of questions, whereas the assigned unrelated insertion is present for {value('core', 'unrelated', 'none', 'assigned_insert_exposed')}%. The core targeted-versus-unrelated contrast therefore includes a difference in natural exposure. In the controlled module, both kinds of insertion are always present in the same assigned slot and both clean supports remain available. Targeted insertion still produces a {value('controlled', 'targeted', 'none', 'strict_target_choice_proxy')}% strict target-choice rate, compared with {value('controlled', 'unrelated', 'none', 'strict_target_choice_proxy')}% for unrelated insertion. This comparison supports a targeting effect within those constructed contexts. The lower targeted rate than in ordinary retrieval cannot be attributed solely to evidence retention: the two modules also differ in their selected surrounding passages and context construction.

Repetition changes context composition as well as the prominence of the designated answer. With one, two and five identical copies per fixed target, undefended target-choice rates are {value('core', 'targeted', 'none', 'strict_target_choice_proxy')}%, {value('dose', 'targeted', 'none', 'strict_target_choice_proxy', 2)}% and {value('dose', 'targeted', 'none', 'strict_target_choice_proxy', 5)}%. Corresponding all-support recall falls from {value('core', 'targeted', 'none', 'all_support')}% to {value('dose', 'targeted', 'none', 'all_support', 2)}% and {value('dose', 'targeted', 'none', 'all_support', 5)}%. Because duplicate passages are retained with distinct IDs, repeated insertion can crowd clean supports out of the five-passage context. These results concern identical-copy repetition at a high fixed target coverage; they establish neither diverse-attack strength nor a reproduction of the missing historical repetition archive.

The defense comparison also has a utility cost. Reranking reduces the one-copy targeted-choice proxy from {value('core', 'targeted', 'none', 'strict_target_choice_proxy')}% to {value('core', 'targeted', 'rerank', 'strict_target_choice_proxy')}%, but it also changes clean reference-choice output from {value('core', 'clean', 'none', 'strict_reference_choice_proxy')}% to {value('core', 'clean', 'rerank', 'strict_reference_choice_proxy')}% and clean all-support recall from {value('core', 'clean', 'none', 'all_support')}% to {value('core', 'clean', 'rerank', 'all_support')}%. A lower target-choice rate therefore cannot stand alone as evidence of preserved answer utility. Filtering illustrates a different boundary: it excludes all base insertions by their supplied labels and reproduces the corresponding clean context. When the same targeted text receives accepted labels, its undefended target-choice rate returns under filtering. The retrieval-only label-error result further shows why rejecting needed clean material must be examined, while leaving generated-answer effects unmeasured in that module.

The combined evidence supports a limited pipeline-level conclusion: targeting, passage competition, repeated content and assumed source labels can change automatic answer production in different ways. Source-title exclusion and assistant source screening improve the follow-up's construction without proving semantic independence or factual truth. The pending two-person semantic evaluation is needed to distinguish endorsed false claims, supported but false answers, abstention and unresolved references. Neither an absent target number nor a matching reference number resolves those questions by itself.

'''


def build_text(c):
    text = SOURCE.read_text()
    # Preserve the measured definitions while removing an unsupported factual interpretation.
    for old, new in [
        ('Gold-only numerical accuracy', 'Reference-value-only output rate'),
        ('gold-only numerical accuracy', 'reference-value-only output rate'),
        ('Gold-only accuracy', 'Reference-value-only output rate'),
        ('gold-only accuracy', 'reference-value-only output rate'),
        ('false-only output', 'target-only output'), ('False-only output', 'Target-only output'),
        ('truthful-insertion', 'reference-concordant-insertion'),
        ('truthful insertion', 'reference-concordant insertion'),
        ('Truthful question-addressed', 'Reference-concordant question-addressed'),
        ('truthful question-shaped', 'reference-concordant question-shaped'),
        ('newly inserted truthful passage', 'newly inserted reference-concordant passage'),
        ('The truthful control', 'The reference-concordant control'),
        ('useful legitimate additions', 'potentially useful reference-concordant additions'),
        ('annotated correct value', 'annotated reference value'),
        ('designated false value', 'designated target value'),
        ('same false integers', 'same target integers'),
        ('same false values', 'same target values'),
        ('and truthful insertion', 'and reference-concordant insertion'),
        ('The four conditions share', 'The four defense arms share'),
        ('2024.eacl- demo.16', '2024.eacl-demo.16'),
        ('https://arxiv.org/abs/2302.12173 RAG SECURITY RESEARCH', 'https://arxiv.org/abs/2302.12173'),
    ]:
        text = text.replace(old, new)
    abstract = '''## Abstract

Relevant retrieved text can supply an attacker-selected answer without protecting answer integrity. We examine this distinction through a historical extractive study and an archived real-LLM evaluation, with source and evaluation audits kept separate from the original scores. Study A used 225 chunks and 364 questions; its reported outcomes remain historical because the matching principal execution archive has not been recovered. Study B used 64 integer-surface-answer HotpotQA questions, 640 shared clean passages, neural API embeddings and gpt-4.1-mini-2025-04-14. Five corpus conditions crossed four defenses, producing 1,280 condition rows from 376 unique generation requests. The archived numerical rule records the designated target value for 34/64 questions under targeted insertion and 0/64 under unrelated insertion; reranking reduces this to 17/64. Independent recomputation reproduces those numbers. An AI-assisted source audit, however, finds five ambiguous question/reference pairs, six requiring correction and ten targets whose falsity is not established by the available evidence. A retrospective 50-case source-aligned quantitative subset gives 25 target-only outputs without defense and 14 with reranking; it does not replace the original denominator or establish semantic attack success. The gate rejects base insertions by construction and loses that protection when identical text receives accepted labels. These findings separate numerical production, source validity, evidence availability and protection under assumed labels. Human semantic review remains a required, pending step.
'''
    if c:
        abstract = c_abstract(c)
    abstract += '\n**Keywords:** retrieval-augmented generation; knowledge-base poisoning; source validity; real-LLM evaluation; provenance; semantic review\n'
    text = replace_section(text, '## Abstract', abstract)
    note = ('**Working research revision.** Archived scores, source-audit findings and later automatic results are versioned separately. Independent human semantic review has not been completed. ' +
            ('Study C below has a completed, hash-checked execution archive; its outcomes remain automatic proxies.' if c else
             'Study C is a prospective protocol and is not presented as an executed result.'))
    affiliation = 'Department of Research and Development (R&D), Ministry of Communications and Information Technology'
    text = text.replace(affiliation, affiliation + '\n\n' + note, 1)
    intro_old = 'Study B extends this analysis through an output-held-out external evaluation with a real API LLM and neural retrieval.'
    text = text.replace(intro_old, 'Study B extended the analysis through an external evaluation whose outputs were originally held out until the local freeze. Its observed cases now also inform the subsequent audit and follow-up design.')
    if c:
        text = text.replace('The contributions are: (1)', 'A prospectively frozen follow-up, C, uses new source-screened questions, a separate imposed-exposure comparison, fixed-target repetition and fresh provider rounds. This follow-up addresses design gaps identified in the B audit while preserving the earlier results and their source-validity limits.\n\nThe contributions are: (1)', 1)
    text = text.replace('The contributions are: (1)', 'The contributions, within the documented evaluation limits, are: (1)')
    # New provenance replaces a false blanket absence claim.
    old = 'Study A is the previously reported Afghanistan-focused offline experiment [25]. Its results are carried forward as historical evidence. The historical raw corpus, code, manifests, and response archives were unavailable for a new replay; earlier audit statements are therefore not treated as verification performed in the present analysis.'
    new = f'''Study A is the previously reported Afghanistan-focused offline experiment [25]. Its canonical inputs and current workbench code are publicly available in [RAG-Security-Lab]({REPO}) at commit `{COMMIT}`. The present artifact audit reconstructed the four canonical input tables from the retained legacy material and 12 World Bank responses. This verifies construction and transfer against those snapshots; it does not independently establish the truth of every inherited statement.

The complete 21,840-row principal archive, 3,016-row repetition archive and matching historical runtime were not recovered in the bounded repository, history and workflow-artifact search. The current workbench is not that frozen runtime: for example, its default budgets are 0, 10, 20, 50 and 104, whereas the historical report uses 0, 10, 30, 60 and 104. Historical results and figures are therefore retained as previously reported evidence, not a newly reproduced run. Earlier replay assertions are attributed to that report. No recovered decision record establishes why every proposed component was inactive, and present-day design explanations are not written as historical author intent.'''
    assert old in text
    text = text.replace(old, new)
    text = text.replace('### 4.1. Two distinct studies and evidence provenance', '### 4.1. Study boundaries and evidence provenance')
    if c:
        start = text.index('**Table 2. Study boundaries and implemented components.**')
        end = text.index('\nFigure 1 shows', start)
        text = text[:start] + '''**Table 2. Study boundaries and implemented components. Condition rows, unique payloads and fresh provider responses have different denominators.**

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
| Evidence status | Matching principal execution archive unrecovered | Originally output-held-out; now retrospective audit material | Definitions frozen before inference; automatic results; human review pending |
''' + text[end:]
    old = 'Complete overlap checking against Study A is impossible without its raw inputs, and title disjointness does not establish semantic entity disjointness.'
    new = 'A bounded comparison against the now-available current canonical A inputs found no normalized exact question, title or complete-text matches, and no shared contiguous eight- or twelve-word phrases. It did not establish that those inputs exactly match the missing historical run, or exclude semantic entity/fact overlap and shared source families. B donor full context bodies were not retained, so that comparison covered their questions, titles and annotated support sentences rather than every donor paragraph.'
    assert old in text; text = text.replace(old, new)
    text = text.replace('This is an output-held-out external subset:', 'At the original B execution this was an output-held-out external subset:')
    text = text.replace('so the unrelated statement is false under its own annotation.', 'so the inserted value differs from its donor annotation. This numerical difference alone is not a source-validity check; donor references were outside the later 64-question B source audit.')
    text = text.replace('| Targeted factual corruption |', '| Intended targeted factual corruption |')
    text = text.replace('**Exposure-confirmed targeted success:**', '**Exposure-confirmed target-only output:**')
    text = text.replace('These paired contrasts answer RQ1 for the implemented attack and numerical subset; they do not establish an optimized attack success probability.', 'These contrasts answer the automatic numerical endpoint of RQ1 on the original subset. Because ten designated target propositions lack source-established falsity, they do not establish semantic attack success or an optimized attacker success probability.')
    text = text.replace('All external-study rates use the same 64 test questions unless a conditional denominator is explicitly given.', 'All archived B rates use the same 64 test questions unless a conditional or retrospective-subset denominator is explicitly given. The historical field named numeric_false_only is called target-only output here; its numerical rule is unchanged.')
    text = text.replace('At a fixed corpus condition, U is the set of successful undefended targets under S(q).', 'At a fixed corpus condition, U is the set of undefended targets satisfying the archived numerical criterion S(q). Prevention and restoration below refer to that criterion, not independently adjudicated factual endorsement.')
    text = text.replace('The source gate accepts only verified passages with high or medium trust.', 'The source gate accepts only passages whose supplied verified field is true and whose supplied trust is high or medium.')
    text = text.replace('Its deterministic outputs support a controlled analysis of that implementation,', 'Its reported deterministic outcomes describe that implementation,')
    text = text.replace('Does targeting the evaluated question cause more false-value production or accuracy loss than matched unrelated or reference-concordant insertions?', 'Does question targeting increase target-value output or reduce reference-value matching relative to the unrelated and reference-concordant controls?')
    text = text.replace('How do the defenses prevent successful attacks or restore answers, and how does label compromise affect them?', 'How do defenses prevent target-value outputs or recover reference values, and how does changing supplied labels affect them?')
    text = text.replace('Exposure-confirmed false outputs, paired prevention/restoration, new failures', 'Exposure-confirmed target outputs, paired proxy prevention/recovery, new target outputs')
    text = text.replace('neither accuracy nor false-only credit', 'neither reference-only nor target-only credit')
    text = text.replace('Exposure-confirmed targeted success is additionally reported', 'Exposure-confirmed target-only output is additionally reported')
    text = text.replace('distinguished from exposure-confirmed targeted success.', 'distinguished from exposure-confirmed target-only output.')
    text = text.replace('| Study B: new external generative evaluation |', '| Study B: archived external generative evaluation |')
    text = text.replace('64 external numerical-answer questions; all targeted', '64 external integer-surface-answer questions; all targeted')
    text = text.replace('| Gold | False | EM |', '| Reference | Target | EM |')
    text = text.replace('Gold/false use automatic value matching;', 'Reference/target use the unchanged archived automatic value-matching indicators;')
    text = text.replace('its accuracy difference is', 'its reference-value-match difference is')
    text = text.replace('the accuracy difference is', 'the reference-value-match difference is')
    text = text.replace('false-output difference', 'target-output difference')
    text = text.replace('lower false-output rate', 'lower target-output rate')
    text = text.replace('Of the 41 questions with a gold-only clean output,', 'Of the 41 questions with a reference-only clean output,')
    text = text.replace('The remaining 17 targeted false outputs occur on questions already lacking a gold-only clean output, so 34 successes should not be interpreted as 34 newly lost correct answers.', 'The remaining 17 target-valued outputs occur on questions already lacking a reference-only clean output. Thus 34 target-only events are not 34 losses of previously reference-matching responses, and neither count establishes semantic correctness.')
    text = text.replace('the article reports numerical answer accuracy and false-value production, rather than independently established semantic correctness.', 'the article reports reference-value matching and designated target-value production, rather than independently established semantic correctness.')
    text = text.replace('a question-addressed false assertion produces substantially more designated target values than a matched unrelated false assertion.', 'a question-addressed assertion of an attacker-designated value produces substantially more target-valued outputs than the matched unrelated assertion. The B source audit does not establish the falsity of every target claim, and its donor references have not received that audit.')
    text = text.replace('17 (41.5%) produce the false value after undefended targeted poisoning.', '17 (41.5%) produce the designated target value after undefended targeted poisoning.')
    text = text.replace('Preserving aggregate answer accuracy can coexist with excluding potentially useful reference-concordant additions.', 'Preserving aggregate reference-value matching can coexist with excluding potentially useful reference-concordant additions.')
    text = text.replace('whether evidence recovery, false-answer prevention, and correct-value restoration coincide.', 'whether evidence recovery, target-output prevention and reference-value restoration coincide.')
    text = text.replace('Independent recomputation reproduces those numbers.', 'A separate scoring implementation reproduces those numbers.')
    text = replace_subsection(text, '### 3.1. Questions aligned with the experimental design', alignment_section(c))
    text = replace_subsection(text, '### 3.3. Paired defense outcomes', '''### 3.3. Paired defense outcomes

Within a fixed corpus condition, let U be the questions satisfying the exposure-confirmed target-only criterion S(q) without defense. Proxy prevention counts members of U that no longer satisfy that criterion after defense. Reference-value recovery counts members of U whose defended output satisfies V(q). New target-only events arise outside U after defense. Clean value-match cost is the undefended clean reference-value-only rate minus its defended counterpart, in percentage points. These definitions preserve the archived calculations; preventing a target-valued output need not recover a reference-valued output, and neither event is a human-validated correctness judgment.
''')
    text = replace_subsection(text, '### 5.3. RQ3: Defense ablations and accepted-label compromise', '''### 5.3. RQ3: Defense ablations and accepted-label compromise

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
''')
    before_results = '## 5. Results organized by research question'
    text = text.replace(before_results, c_methods(c) + '\n\n' + before_results, 1)
    text = text.replace('## 6. Discussion', audit_sections() + '\n\n' + c_results(c) + '\n\n## 6. Discussion', 1)
    text = text.replace('## 7. Validity limitations and further work', c_discussion(c) + '## 7. Validity limitations and further work', 1)
    # Restrict old one-dose/no-repeat descriptions to B.
    text = text.replace('The generative experiment covers one model snapshot, one numerical-answer subset, one templated attack, one positive dose, one context length, and simple defenses.', 'The archived B experiment covers one model snapshot, one integer-surface subset, one templated attack, one positive dose, one context length and simple defenses. C adds three identical-copy doses on a new source-screened subset, while retaining the same model, context length and simple defenses; it does not establish broader-model or production-scale performance.')
    text = text.replace('and no repeated-generation variance is measured.', 'and B measures no fresh repeated-generation variation.')
    text = text.replace('Exhaustive overlap with the historical raw data remains unverified, semantic entity overlap is possible, and the public benchmark may be present in model training.', 'The bounded A/B overlap audit uses current canonical A inputs, whose exact identity with the principal historical run remains unverified. Semantic entity/fact overlap is possible, and the public benchmark may be present in model training.')
    text = text.replace('Reference annotations and derived false claims have not received independent human adjudication.', 'Reference annotations and derived target claims have not received independent human adjudication. The source audit identifies concrete defects, not merely a hypothetical future validation need; source-consistent classifications are AI-assisted and are not final human factual judgments.')
    text = text.replace('The unrelated corpus changes accuracy only from 41/64 to 40/64 under no defense, whereas the targeted corpus reduces it to 24/64.', 'The unrelated corpus changes reference-value-only outputs from 41/64 to 40/64 under no defense, whereas the targeted corpus gives 24/64.')
    text = text.replace('For institutional pilots, source ownership, dates and versions, protected metadata changes, conflict review, and response-level records should be evaluated alongside retrieval quality.', 'The supplied labels were assigned by the dataset constructor; no recovered evidence identifies an operational authority that approved every document. For institutional pilots, source ownership, dates and versions, protected metadata changes, conflict review and response-level records must be evaluated alongside retrieval quality. In A, the two rejected low-trust mineral chunks have no directly assigned gold questions, so zero observed clean loss after rejecting them is weak evidence about the cost of rejecting needed legitimate material.')
    text = text.replace('The reference-concordant-insertion comparison is needed because a question-shaped passage can be more retrievable regardless of whether its answer is true.', 'The reference-concordant-insertion comparison is needed because a question-shaped passage can be more retrievable regardless of its factual validity. Reference concordance is all that this B condition guarantees; the source audit shows why it must not be called a fully truth-validated control.')
    conclusion = '''## 8. Conclusion

The archived real-LLM experiment shows that question-addressed insertions can change numerical answer production: the original rule records 34/64 target-only outputs without defense and 17/64 with reranking, while a supplied-label gate removes rejected insertions and loses that protection when identical text receives accepted labels. Recomputed scores agree with the archive, but source review identifies reference, relation and target-validity defects. The 50-case sensitivity analysis retains 25 and 14 target-only outputs under the same two conditions; these retrospective counts do not replace the original sample or establish human-validated attack success.

The defensible conclusion concerns the measured pipeline and declared automatic constructs. Relevant evidence, target-value prevention and reference-value recovery are different outcomes. Historical inputs and current code are available, but the exact principal A runtime and complete result archives remain unrecovered. The source-review materials, revised evaluator and two-reviewer protocol make these limitations examinable. Independent semantic judgments and broader operational evidence are still needed before claiming factual security or authenticated institutional protection.
'''
    if c:
        target = rate(metric(c, 'core', 'targeted', 'none', 'strict_target_choice_proxy'))
        controlled = rate(metric(c, 'controlled', 'targeted', 'none', 'strict_target_choice_proxy'))
        repeated = rate(metric(c, 'dose', 'targeted', 'none', 'strict_target_choice_proxy', 5))
        conclusion = f'''## 8. Conclusion

The prospectively frozen {c['n']}-question follow-up shows that question-addressed insertions change automatic answer production in this RAG pipeline. The strict target-choice proxy averages {target}% without defense and 0.0% under the unrelated control. When both insertions are forced into matched positions and both clean supports remain present, the corresponding rates are {controlled}% and 0.0%. Five identical copies per target raise the undefended proxy to {repeated}% while excluding at least one annotated support for every question. Reranking lowers targeted-choice output but also reduces clean reference-choice output, making prevention, evidence recovery and utility distinct outcomes.

The supplied-label gate removes rejected insertions by construction and loses that protection when identical text receives accepted labels. This is an assumed authority boundary, not operational document authentication. The archived B calculations remain reproducible, while its source audit identifies reference and target-validity defects; retrospective subsets do not replace its original denominator. Historical A inputs and current code are available, but the matching principal execution archive remains unrecovered.

These findings support conditional conclusions about the recorded model, contexts and automatic constructs. Source screening is AI-assisted, fresh rounds do not create new independent questions, and neither reference matching nor target production establishes factual correctness or semantic endorsement. The separate two-reviewer frames make the required human evaluation executable, but actual independent judgments and adjudication remain pending.
'''
    text = replace_section(text, '## 8. Conclusion', conclusion)
    old = "The materials are provided with the manuscript; no public repository or permanent artifact identifier has been assigned. Study A's raw archives were not available for a new replay, and independent human review and external replication have not been completed."
    new = f"Study A's canonical data and current workbench are available in the public repository at the pinned commit above. The local B and C evidence, versioned reference audit, diagnostic evaluator and separate reviewer packets accompany this working revision; their public availability is not inferred from the older repository commit. The exact principal A execution archives remain unrecovered. Independent human review and external replication have not been completed. No permanent archival identifier for the full revised evidence package is claimed."
    assert old in text; text = text.replace(old, new)
    if c:
        execution = c['analysis']['execution']
        usage = execution['reported_generation_usage_distinct_calls']
        c_availability = f'''The separate C archive is supplied under `rag_security_revision_v2/`: `data/` contains all candidate decisions, original test and full donor records, source cards and constructed insertions; `study_c/` contains both hash freezes, returned embeddings, exact contexts and payloads, raw responses and the usage ledger; `analysis/study_c/` contains condition, round, paired-transition and case tables. Its 2,559 distinct calls report {usage['prompt_tokens']:,} prompt tokens and {usage['completion_tokens']:,} completion tokens. The recorded conservative cost is USD {execution['cost_committed_usd_conservative']:.4f}, calculated from reported usage at the saved uncached rates rather than presented as an invoice. API access is needed for new inference, while the saved-output analyses are offline. The C review frame is separate under `evaluation/study_c_review/`; its blank forms do not constitute completed human evaluation.\n\n'''
        text = text.replace('## Appendix A. Reproduction and review procedure', c_availability + '## Appendix A. Reproduction and review procedure', 1)
    text = text.replace("HotpotQA/Wikipedia-derived excerpts and adaptations retain attribution and the dataset's CC BY-SA 4.0 terms [18, 24];", "Source-specific redistribution terms require separate attention. HotpotQA/Wikipedia-derived excerpts and adaptations retain attribution and the dataset's stated CC BY-SA 4.0 terms [18, 24];")
    old = '4. Give `human_review_blinded.csv` to two independent reviewers with the review rubric, withholding `human_review_key.csv` until labels are complete. Resolve disagreements and report agreement and adjudicated results separately from the current automatic scores.'
    new = '4. Give each actual reviewer only their own Stage 1 file in `evaluation/human_review_packet/` and the review rubric. Keep `coordinator_only/` separate. Lock both independent initial submissions before releasing Stage 2 target sheets. Record qualifications, construction involvement, agreement and source-linked adjudication. The coordinator is arranging two other people; no completed human labels are present. Software does not authenticate identity or independence.\n5. For C, verify the separate design and generation freezes, three round-specific response mappings and complete planned denominators before running `analysis/analyze_study_c.py`. Its source screening and outcomes must not silently replace B. Its separate initial-review forms and private coordinator key are supplied under `evaluation/study_c_review/`.'
    assert old in text; text = text.replace(old, new)
    text = text.replace("Its underlying archives were unavailable for a new replay. The integrity and completeness checks performed in the present analysis apply to Study B's included evidence only;", "Its complete principal and repetition execution archives were not recovered in the bounded search, although canonical inputs and current code are available. The present integrity checks and reconstruction of A inputs do not reproduce its historical outputs. Checks on B's included response evidence apply to that archive only;")
    # Number preserved figures explicitly, without changing their pixels.
    for number, filename in enumerate(FIGURES, 1):
        pattern = r'!\[([^\n]*)\]\(figures/' + re.escape(filename) + r'\)'
        text, count = re.subn(pattern, lambda match: '![' + f'Figure {number}. ' + match.group(1) + '](figures/' + filename + ')', text)
        assert count == 1, filename
    text += '\n\n[26] U.S. National Archives. Records of the Army Air Forces [AAF], Record Group 18. Sections 18.1 and 18.5 distinguish establishment in 1941 from reorganization in 1942. https://www.archives.gov/research/guide-fed-records/groups/018.html\n\n[27] Ron Artstein and Massimo Poesio. 2008. Inter-Coder Agreement for Computational Linguistics. Computational Linguistics 34(4), 555–596. https://aclanthology.org/J08-4004/\n\n[28] Timnit Gebru, et al. 2021. Datasheets for Datasets. Communications of the ACM 64(12), 86–92. https://doi.org/10.1145/3458723\n\n[29] Rotem Dror, Gili Baumer, Segev Shlomov and Roi Reichart. 2018. The Hitchhiker’s Guide to Testing Statistical Significance in Natural Language Processing. ACL, 1383–1392. https://aclanthology.org/P18-1128/\n'
    text = text.replace('The integrity and completeness checks performed in the present analysis apply to Study B', 'The integrity and completeness checks performed on the archived responses apply to Study B')
    return apply_review_addendum(text, WORK)


def format_docx(path):
    from docx import Document
    from docx.shared import Cm, Pt, RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    document = Document(path)
    for section in document.sections:
        section.page_width = Cm(21); section.page_height = Cm(29.7)
        section.top_margin = Cm(1.8); section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(1.9); section.right_margin = Cm(1.9)
        footer = section.footer.paragraphs[0]
        footer.alignment = 1
        field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    for name in ['Normal', 'Body Text', 'First Paragraph']:
        if name in document.styles:
            style = document.styles[name]
            style.font.name = 'Times New Roman'; style.font.size = Pt(10.5)
            style.paragraph_format.line_spacing = 1.08
            style.paragraph_format.space_after = Pt(6)
    for name, size in [('Title', 18), ('Subtitle', 12), ('Heading 1', 14), ('Heading 2', 12), ('Heading 3', 11)]:
        if name in document.styles:
            style = document.styles[name]
            style.font.name = 'Times New Roman'; style.font.size = Pt(size)
            style.font.color.rgb = RGBColor(0, 0, 0)
            style.paragraph_format.keep_with_next = True
    for table in document.tables:
        for index, row in enumerate(table.rows):
            if index == 0: row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(2)
                    paragraph.paragraph_format.line_spacing = 1.0
                    for run in paragraph.runs:
                        run.font.name = 'Times New Roman'; run.font.size = Pt(8)
    document.core_properties.title = 'Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning'
    document.core_properties.subject = 'Recorded experiments and source-based manual semantic inspection'
    document.save(path)


def main():
    ROOT.mkdir(exist_ok=True); (ROOT / 'figures').mkdir(exist_ok=True)
    watched = [SOURCE] + [WORKSPACE / 'revision/figures' / name for name in FIGURES]
    before = {str(path): sha(path) for path in watched}
    for name in FIGURES:
        shutil.copyfile(WORKSPACE / 'revision/figures' / name, ROOT / 'figures' / name)
    c = verify_c()
    if c:
        from render_current_outcomes import render_current_outcomes
        render_current_outcomes(WORK, ROOT / 'figures')
    text = build_text(c)
    markdown = ROOT / 'Working_Manuscript_v2.md'
    markdown.write_text(text)
    docx = ROOT / 'Working_Manuscript_v2.docx'
    subprocess.run(['pandoc', str(markdown), '--resource-path', str(ROOT), '-o', str(docx)], check=True)
    format_docx(docx)
    body = subprocess.check_output(['pandoc', str(markdown), '--resource-path', str(ROOT), '-s', '-t', 'html5'], text=True)
    css = '''@page{size:A4;margin:18mm 19mm}body{max-width:100%;font-family:"Times New Roman","Liberation Serif",serif;font-size:10.5pt;line-height:1.34;color:#111}h1.title{text-align:center;font-size:20pt;margin-bottom:8px}p.subtitle,p.author,p.date{text-align:center;margin:2px 0}h2{font-size:14pt;margin:18px 0 7px;break-after:avoid}h3{font-size:11.5pt;margin:14px 0 5px;break-after:avoid}p{margin:0 0 8px;text-align:justify;orphans:3;widows:3}table{border-collapse:collapse;width:100%;font-size:8.1pt;line-height:1.17;margin:10px 0 14px;table-layout:fixed}th,td{padding:4px 5px;border:1px solid #aaa;vertical-align:top;overflow-wrap:anywhere}th{background:#f1f1f1}thead{display:table-header-group}tr{break-inside:avoid}figure{margin:14px 0;break-inside:avoid}img{max-width:100%;height:auto}figcaption{font-size:9pt;line-height:1.2;margin-top:6px;text-align:justify}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:8.5pt}code{font-family:"DejaVu Sans Mono",monospace;font-size:.85em;overflow-wrap:anywhere}blockquote{margin:8px 16px;font-size:9.8pt}a{color:#111;overflow-wrap:anywhere}li{margin-bottom:5px}'''
    body = body.replace('</head>', '<style>' + css + '</style></head>')
    # Keep short scientific tables together; long tables may still paginate.
    body = re.sub(r'<table\b[^>]*>.*?</table>',
                  lambda match: match.group(0).replace('<table', '<table data-keep-short="true"', 1)
                  if len(re.findall(r'<tr\b', match.group(0))) <= 8 else match.group(0),
                  body, flags=re.S)
    body = body.replace('</head>', '<style>table[data-keep-short="true"]{break-inside:avoid}</style></head>')
    def embedded(match):
        image = ROOT / match.group(1)
        assert image.is_file()
        return 'src="data:image/png;base64,' + base64.b64encode(image.read_bytes()).decode() + '"'
    body = re.sub(r'src="(figures/[^\"]+\.png)"', embedded, body)
    (ROOT / 'Working_Manuscript_v2.html').write_text(body)
    expected = {sha(ROOT / 'figures' / name) for name in FIGURES}
    with zipfile.ZipFile(docx) as archive:
        embedded_hashes = {hashlib.sha256(archive.read(name)).hexdigest() for name in archive.namelist() if name.startswith('word/media/')}
    assert expected <= embedded_hashes, 'An original figure was omitted or altered in Word'
    if c:
        assert sha(ROOT / 'figures/study_c_outcomes.png') in embedded_hashes, 'The actual C figure is missing from Word'
    after = {str(path): sha(path) for path in watched}
    assert before == after, 'Historical source or figures changed'
    tables = [int(number) for number in re.findall(r'\*\*Table (\d+)\.', text)]
    assert tables == list(range(1, len(tables)+1)), tables
    assert '2024.eacl- demo.16' not in text and '2302.12173 RAG SECURITY RESEARCH' not in text
    report = {'built_at_utc': datetime.now(timezone.utc).isoformat(),
              'paper_status': 'research_revision_single_author_semantic_inspection',
              'study_c_completed_archive_included': c is not None,
              'study_c_analysis_sha256': c['analysis_sha256'] if c else None,
              'tables': tables, 'preserved_figure_count': 4,
              'total_figure_count': 5 if c else 4,
              'study_c_figure_embedded_unmodified_in_docx': c is not None,
              'abstract_word_count': len(text.split('## Abstract\n\n', 1)[1].split('**Keywords:**', 1)[0].split()),
              'preserved_figure_hashes': {name: sha(ROOT / 'figures' / name) for name in FIGURES},
              'historical_source_and_figures_unchanged': before == after,
              'all_original_figures_embedded_unmodified_in_docx': True,
              'structured_item_level_human_ratings_claimed': 0,
              'author_manual_inspection_reported_completed': True,
              'documented_AI_case_assessments': 72,
              'source_manuscript_sha256': sha(SOURCE),
              'generated_files_sha256': {path.name: sha(path) for path in [markdown, docx, ROOT / 'Working_Manuscript_v2.html']}}
    (ROOT / 'MANUSCRIPT_BUILD_CHECKS.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
