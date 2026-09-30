"""Synthetic, question-specific attacks for interactive stress tests.

This is a separate attack protocol, not an expansion of the published benchmark.
Ground truth is used only to construct attacks and evaluate outputs, never fed to
the retriever or answerer. All injected records remain untrusted and unverified.
"""
import hashlib
import re
from decimal import Decimal
import pandas as pd
from src.evaluation.metrics import core_value, contains_value
from src.retrieval.lexical import sentences

def _different_value(question, questions, original):
    gold = str(question['ground_truth'])
    assigned = original.loc[original.target_question_id == question['question_id']]
    if len(assigned):
        value = str(assigned.iloc[0].attacker_false_information)
        if not contains_value(value, gold) and not contains_value(gold, value):
            return value, 'existing_attack_value'
    core = core_value(gold)
    # Numeric perturbations retain units and formatting but are synthetic claims.
    match = re.search(r'-?\d[\d,]*(?:\.\d+)?', core)
    if match:
        number = Decimal(match[0].replace(',', ''))
        changed = number + max(abs(number) * Decimal('0.17'), Decimal('1'))
        places = len(match[0].split('.')[1]) if '.' in match[0] else 0
        replacement = f'{changed:,.{places}f}'
        value = core[:match.start()] + replacement + core[match.end():]
        if not contains_value(value,gold):return value, 'synthetic_numeric_perturbation'
    # Prefer a distractor of the same category. A value true for a different
    # question is deliberately misassigned here; users can inspect it before use.
    candidates = questions.sort_values('question_id').to_dict('records')
    def compatibility(row):
        other=core_value(str(row['ground_truth']))
        return (bool(re.search(r'\d',other)),
                other.casefold().split()[-1:] != core.casefold().split()[-1:],
                row.get('category') != question.get('category'))
    candidates.sort(key=compatibility)
    for row in candidates:
        value = core_value(str(row['ground_truth']))
        if value and not contains_value(value,gold) and not contains_value(gold,value):
            return value, 'different_question_distractor'
    raise ValueError(f"No distinct attack value is available for {question['question_id']}")

def build_targeted_pool(questions, original, chunks):
    """One inspectable payload per benchmark question; no dataset files changed."""
    rows = []
    for question in questions.to_dict('records'):
        qid = question['question_id']; gold = str(question['ground_truth'])
        false, method = _different_value(question, questions, original)
        # Explicit QA assertions handle answers that are not literal substrings
        # of a source sentence. Remove internal question punctuation so the
        # assertion is evaluated as one sentence by the offline extractor.
        query = str(question['question']).strip().rstrip('?').replace('?', '')
        payload = f'For the question "{query}", the reported answer is {false}.'
        # Some questions contain their own answer token. Do not silently claim
        # that these payloads are semantically adjudicated successful attacks.
        rows.append(dict(poison_id=f'TARGET-{qid}', attack_id=f'TARGET-ATTACK-{qid}',
            target_question_id=qid, target_query=question['question'],correct_answer=gold,
            attacker_false_information=false,poisoned_text=payload,
            attack_type='synthetic_targeted_counterfactual',source_status='attacker_generated',
            trust_level='untrusted',verification_status='unverified',
            construction_method=method, payload_sha256=hashlib.sha256(payload.encode()).hexdigest()))
    return pd.DataFrame(rows)
