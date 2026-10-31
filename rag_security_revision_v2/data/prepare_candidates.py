"""Build prospective, outcome-unseen candidate cards; never freeze or call an API.

Automatic eligibility is only a screening stage. Every selected candidate retains
the original complete context and needs a relation/identity/source review before
it can receive a test/donor role. Historical B inputs are read only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parents[1]
OLD = WORKSPACE / "revision/experiment"
A_ROOT = WORKSPACE / "research_phase/repo_snapshot/data/raw"
EXPECTED_SHA = "c20b638ca82b21d04fe12e14ff417ad05153d4d215a65de54497fca4e972f7c6"
ORDER_PREFIX = "rag-security-followup-v1:"
NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?!\w|\.\d)")
EXACT_INTEGER = re.compile(r"(?:\d+|\d{1,3}(?:,\d{3})+)")
BOUND_PREFIX = re.compile(
    r"(?:more\s+than|less\s+than|fewer\s+than|greater\s+than|at\s+least|at\s+most|"
    r"up\s+to|over|under|about|around|approximately|roughly|nearly|almost|some|"
    r"estimated(?:\s+(?:at|to\s+be))?|exceed(?:ing|s|ed)?|maximum(?:\s+of)?|minimum(?:\s+of)?)\s*$",
    re.I,
)
BOUND_SUFFIX = re.compile(r"^\s*(?:or\s+more|or\s+less|plus|approximately)\b", re.I)
QUESTION_BOUND = re.compile(
    r"\b(?:about\s+how\s+many|approximately|roughly|more\s+than\s+how\s+many|"
    r"over\s+how\s+many|at\s+least\s+how\s+many|around\s+how\s+many|"
    r"less\s+than\s+how\s+many|under\s+how\s+many)\b", re.I,
)
NAME_PREFIX = re.compile(
    r"\b(?:band|group|route|highway|motorway|channel|station|model|flight|"
    r"battalion|regiment|division|company|engine|road|album|song|film)\s*[\"']?\s*$", re.I,
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    return " ".join("".join(c if c.isalnum() else " " for c in text).split())


def numbers(text: str) -> set[str]:
    return {str(int(m.group().replace(",", ""))) for m in NUMBER.finditer(text)}


def write_json(output: Path, name: str, value) -> None:
    (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def read_a_inventory():
    questions, titles = set(), set()
    files = []
    for filename, dest, fields in [
        ("questions.csv", questions, ["question", "question_text"]),
        ("documents.csv", titles, ["title"]),
    ]:
        path = A_ROOT / filename
        if not path.exists():
            continue
        files.append({"path": str(path), "sha256": sha(path.read_bytes())})
        with path.open(encoding="utf-8-sig", newline="") as handle:
            for record in csv.DictReader(handle):
                for field in fields:
                    if record.get(field):
                        dest.add(norm(record[field]))
    return questions, titles, files


def review_flags(question, support, gold_sentences, answer):
    """Warnings, not semantic labels: root must inspect the retained source."""
    flags = ["identity_relation_bridge_requires_source_review"]
    if re.search(r"\b(?:created|established|formed|founded|organized|reorganized|opened|launched)\b", question, re.I):
        flags.append("event_definition_establishment_vs_opening_or_reorganization")
    if re.search(r"\b(?:career|total|worldwide|ever|most|more\s+recent|older|newer|youngest|oldest)\b", question, re.I):
        flags.append("comparison_scope_or_reference_time_requires_review")
    if re.search(r"\b(?:author|writer|novelist|book|song|tour|convicted|born|from|died)\b", question, re.I):
        flags.append("person_work_place_or_event_identity_requires_review")
    if re.search(r"\b(?:his|her|their|that|which|whose|it)\b", question, re.I):
        flags.append("bridge_or_pronoun_resolution_requires_review")
    if re.search(r"\b(?:between|from)\s+\d[\d,]*\s+(?:and|to|through|until)\s+\d", " ".join(gold_sentences), re.I):
        flags.append("support_date_or_quantity_range_requires_relation_review")
    if re.search(r"\b(?:population|seasons|employees|workers|wins|tournaments|members)\b", question, re.I):
        flags.append("quantity_reference_time_or_count_definition_requires_review")
    if len(numbers(" ".join(gold_sentences))) > 1:
        flags.append("multiple_values_in_gold_sentences_disambiguate_relation")
    return flags


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "source_validation.parquet")
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    parser.add_argument("--target", type=int, default=128)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_hash = sha(args.source.read_bytes())
    if source_hash != EXPECTED_SHA:
        raise SystemExit("Pinned source SHA-256 mismatch; refusing candidate preparation")

    prior_tests = json.loads((OLD / "test_questions.json").read_text())
    prior_donors = json.loads((OLD / "control_donors.json").read_text())
    prior = prior_tests + prior_donors
    old_ids = {record["id"] for record in prior}
    old_titles = {norm(title) for record in prior for title in record["context_titles"]}
    a_questions, a_titles, a_files = read_a_inventory()
    rows = pq.read_table(args.source).to_pylist()
    counts = Counter()
    rejection_counts = Counter()
    rejected, screened = [], []
    for source_index, row in enumerate(rows):
        answer = row["answer"].strip()
        if not EXACT_INTEGER.fullmatch(answer):
            counts["not_exact_integer_surface"] += 1
            continue
        counts["integer_surface_rows"] += 1
        gold = str(int(answer.replace(",", "")))
        question = row["question"]
        titles = row["context"]["title"]
        texts = dict(zip(titles, row["context"]["sentences"]))
        support_titles = sorted(set(row["supporting_facts"]["title"]))
        reasons = []
        if row["id"] in old_ids:
            reasons.append("prior_B_question_or_donor_id")
        if set(map(norm, titles)) & old_titles:
            reasons.append("context_title_overlaps_prior_B_test_or_donor")
        if norm(question) in a_questions:
            reasons.append("exact_normalized_question_overlap_current_A")
        if set(map(norm, titles)) & a_titles:
            reasons.append("exact_normalized_context_title_overlap_current_A")
        if len(titles) != 10 or len(set(map(norm, titles))) != 10:
            reasons.append("context_does_not_have_ten_unique_titles")
        if len(support_titles) != 2:
            reasons.append("support_not_exactly_two_passages")
        if not set(support_titles) <= set(titles):
            reasons.append("missing_support_title")
        evidence, support_records = [], []
        try:
            for title, sent_id in zip(row["supporting_facts"]["title"], row["supporting_facts"]["sent_id"]):
                sentence = texts[title][sent_id]
                evidence.append(sentence)
                support_records.append({"title": title, "sentence_id": sent_id, "text": sentence})
        except (KeyError, IndexError):
            reasons.append("invalid_support_annotation")
        gold_sentences = [sentence for sentence in evidence if gold in numbers(sentence)]
        if not gold_sentences:
            reasons.append("reference_value_absent_from_annotated_support")
        if gold in numbers(question):
            reasons.append("reference_value_present_in_question")
        if len(question.split()) > 80:
            reasons.append("question_longer_than_eighty_words")
        if QUESTION_BOUND.search(question):
            reasons.append("question_requests_approximation_or_bound")
        for sentence in gold_sentences:
            for match in NUMBER.finditer(sentence):
                if str(int(match.group().replace(",", ""))) != gold:
                    continue
                prefix, suffix = sentence[:match.start()][-55:], sentence[match.end():][:30]
                if BOUND_PREFIX.search(prefix) or BOUND_SUFFIX.search(suffix):
                    reasons.append("reference_occurrence_qualified_by_bound_or_approximation")
                if NAME_PREFIX.search(prefix) and not re.search(r"\b(?:year|when)\b", question, re.I):
                    reasons.append("reference_may_be_numeric_proper_name_or_designator")
        if re.search(r"\bhow many seasons\b", question, re.I) and not re.search(r"\b(?:in|as of|by|during)\s+(?:the\s+)?\d{4}\b", question, re.I):
            reasons.append("time_varying_season_count_without_reference_date")
        unit = "year" if re.search(r"\b(?:year|when)\b", question, re.I) and 1000 <= int(gold) <= 2099 else "count"
        if unit == "count":
            if re.search(r"\bpopulation\b", question, re.I):
                unit = "population"
            elif re.search(r"\b(?:acres|hectares|miles|kilometers|kilometres)\b", question, re.I):
                unit = "area_or_distance_count"
            elif re.search(r"\b(?:months|years|days|hours)\b", question, re.I):
                unit = "duration_count"
        flags = review_flags(question, evidence, gold_sentences, gold)
        card = {
            "id": row["id"], "source_row_index": source_index,
            "selection_hash": sha((ORDER_PREFIX + row["id"]).encode()),
            "question": question, "answer": answer, "answer_numeric": gold,
            "type": row["type"], "level": row["level"], "answer_unit_class": unit,
            "context_titles": titles, "support_titles": support_titles,
            "supporting_facts": row["supporting_facts"], "supporting_sentences": evidence,
            "support_records": support_records, "gold_value_supporting_sentences": gold_sentences,
            "context": row["context"],
            "complete_support_passages": [
                {"title": title, "text": title + ". " + "".join(texts.get(title, []))}
                for title in support_titles
            ],
            "automatic_review_flags": flags,
            "source_relation_review_status": "pending_assistant_source_review_and_actual_human_review",
            "human_judgments_completed": 0,
        }
        reasons = sorted(set(reasons))
        if reasons:
            card["rejection_reasons"] = reasons
            rejected.append(card)
            rejection_counts.update(reasons)
        else:
            card["automatic_screen_status"] = "pass_not_semantic_validation"
            screened.append(card)

    screened.sort(key=lambda card: card["selection_hash"])
    selected, overlap_rejected = [], []
    used_titles = set()
    for rank, card in enumerate(screened, start=1):
        card["automatic_pass_hash_rank"] = rank
        normalized = set(map(norm, card["context_titles"]))
        overlap = normalized & used_titles
        if overlap:
            card["rejection_reasons"] = ["context_title_overlaps_earlier_selected_fresh_candidate"]
            card["overlap_titles_normalized"] = sorted(overlap)
            overlap_rejected.append(card)
            continue
        if len(selected) >= args.target:
            card["pool_status"] = "reserve_after_target_reached_not_selected"
            continue
        card["potential_fresh_rank"] = len(selected) + 1
        card["role"] = "unassigned_candidate_not_test_or_donor"
        selected.append(card)
        used_titles |= normalized

    write_json(args.output_dir, "candidates.json", selected)
    write_json(args.output_dir, "candidate_rejected_pool.json", rejected + overlap_rejected)
    write_json(args.output_dir, "candidate_automatic_pass_pool.json", screened)
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Prospective automatic candidate screening only; no test/donor assignment, insertions, final freeze, model outputs or human validation",
        "source_sha256": source_hash, "source_rows": len(rows),
        "source_file": str(args.source), "selection_order": "SHA256('rag-security-followup-v1:' + id), ascending",
        "prior_B_test_and_donor_ids": len(old_ids), "prior_B_distinct_normalized_context_titles": len(old_titles),
        "A_exact_overlap_inventory": a_files,
        "exact_integer_surface_rows": counts["integer_surface_rows"],
        "noninteger_surface_rows": counts["not_exact_integer_surface"],
        "automatic_screen_passes_before_fresh_title_greedy_selection": len(screened),
        "automatic_screen_rejected_rows": len(rejected),
        "automatic_rejection_reason_counts": dict(sorted(rejection_counts.items())),
        "fresh_global_title_overlap_rejections": len(overlap_rejected),
        "requested_candidate_count": args.target,
        "selected_potential_candidate_count": len(selected),
        "selected_unique_context_titles": len(used_titles),
        "selected_answer_unit_counts": dict(Counter(card["answer_unit_class"] for card in selected)),
        "target_128_automatic_feasibility": len(selected) >= args.target,
        "semantic_and_human_feasibility": "Not established: each original question and full support bridge must be reviewed before role assignment or inference",
        "selected_ids_overlap_B": bool({card["id"] for card in selected} & old_ids),
        "selected_titles_overlap_B": bool(used_titles & old_titles),
        "all_selected_context_title_sets_pairwise_disjoint": len(used_titles) == 10 * len(selected),
        "new_API_calls": 0, "new_model_outputs": 0, "new_human_judgments": 0,
        "limitations": [
            "Automatic number and qualifier checks do not validate entity-relation identity, temporal scope or external truth.",
            "Title disjointness does not prove semantic/source-family independence or absence from model pretraining.",
            "No candidate is made acceptable merely to fill the design target.",
        ],
    }
    write_json(args.output_dir, "candidate_selection_summary.json", summary)
    print(json.dumps({key: summary[key] for key in ["source_rows", "exact_integer_surface_rows", "automatic_screen_passes_before_fresh_title_greedy_selection", "selected_potential_candidate_count", "selected_answer_unit_counts", "target_128_automatic_feasibility"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
