"""Streamlit research workbench. Start with: python -m streamlit run app.py"""
from __future__ import annotations
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import hashlib
from uuid import uuid4
import pandas as pd
import streamlit as st

from src.config.config import load_config
from src.data.loaders import load_all
from src.defenses.reranker import get_reranker
from src.defenses.source_filter import get_source_filter
from src.embeddings.embedding_service import get_embedding_service
from src.evaluation.evaluator import DEFENSE_VARIANTS
from src.evaluation.runner import execute, input_hashes
from src.evaluation.question_comparison import SPREAD, REPEATED, answer_at_level, comparison_row
from src.generation.llm_interface import get_llm
from src.vectorstore.exact_store import get_vector_store

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="RAG Security Lab", page_icon="🔬", layout="wide")
st.title("RAG Security Lab")
st.caption("Inspect evidence, test knowledge-base poisoning, and compare defenses in reproducible experiments.")
config = load_config(ROOT / "config.yaml")
signature = json.dumps(input_hashes(config), sort_keys=True) + (ROOT / "config.yaml").read_text()
signature += hashlib.sha256(b''.join(p.read_bytes() for p in sorted((ROOT / 'src').rglob('*.py')))).hexdigest()

if st.session_state.get("signature") != signature:
    # Mutable stores and models are session-local; a dataset edit invalidates all setup.
    st.session_state.resources = None
    st.session_state.signature = signature
    st.session_state.pop("answer", None)
    st.session_state.pop("question_comparison", None)


def resources():
    if st.session_state.resources is None:
        with st.spinner("Loading experiment backends..."):
            st.session_state.resources = (get_embedding_service(config), get_llm(config), get_reranker(config), get_source_filter(config), get_vector_store(config))
    return st.session_state.resources


data = load_all(config.paths)
documents, chunks, questions, poisons = (data[k] for k in ("documents", "chunks", "questions", "poisoned_passages"))
counts = st.columns(4)
for column, label, frame in zip(counts, ["Documents", "Searchable chunks", "Questions", "Poison passages"], [documents, chunks, questions, poisons]):
    column.metric(label, len(frame))
if config.llm_backend == "extractive":
    st.info("Answer engine: offline evidence extraction (not a generative LLM). "
            "Answers are selected from retrieved documents; missing evidence should produce an insufficient-evidence response. "
            "These results do not measure a reasoning LLM's robustness.")
st.sidebar.header("Experiment controls")
budget = st.sidebar.slider("Injected passages", min_value=0, max_value=len(poisons), value=0, step=1,
    help="Total poisoned passages in the whole knowledge base. You can test 10, 20, 50, or any available count.", key="poison_budget")
defense = st.sidebar.selectbox("Defense", [v[0] for v in DEFENSE_VARIANTS])
with st.sidebar.expander("Repeatability: what is a seed?"):
    st.write("A seed is the number used to shuffle the poison list. Keep 42 to repeat the same selection. "
             "With the same seed, 20 passages contains the first 10 plus 10 more. "
             "Changing the seed selects a different group; a larger seed does not make the attack stronger.")
    seed = int(st.number_input("Selection seed (keep 42 for comparisons)", min_value=0, max_value=2**32-1,
                              value=config.poisoning.random_seed, key="selection_seed"))
st.sidebar.caption("Source filtering assumes ingestion assigns trustworthy metadata. It is not a learned poison detector.")
ask_tab, run_tab, explore_tab = st.tabs(["Ask & inspect", "Experiments & results", "Dataset & provenance"])

with ask_tab:
    mode = st.radio("Poisoning mode for this question", [SPREAD, REPEATED], key="attack_mode")
    eligible = questions.loc[questions.targeted_for_attack] if mode == REPEATED else questions
    if mode == REPEATED:
        st.info("Each injected passage is another copy of this question's assigned false claim. "
                "These copies are one repeated source, not independent evidence. "
                "The seed does not change the text in this mode. More copies can fill the context, "
                "but the answer can plateau once the context is full.")
    category = st.selectbox("Question category", ["All"] + sorted(eligible.category.unique()))
    available = eligible if category == "All" else eligible.loc[eligible.category == category]
    qid = st.selectbox("Benchmark question", available.question_id.tolist(),
                       format_func=lambda q: f"{q} — {available.set_index('question_id').loc[q, 'question']}")
    selected = available.set_index("question_id").loc[qid]
    custom_input = st.text_input("Custom question (optional; no automatic ground-truth verdict)", disabled=mode == REPEATED)
    custom = "" if mode == REPEATED else custom_input
    selection_key = (qid, custom.strip(), budget, defense, seed, mode)
    comparison_key = (qid, custom.strip(), defense, seed, mode)
    if mode == REPEATED:
        st.caption(f"Current level: {budget} copies attacking this question; 0 copies is the clean baseline.")
    elif not custom.strip() and selected.targeted_for_attack:
        order = poisons.sample(frac=1, random_state=seed).reset_index(drop=True)
        position = order.index[order.target_question_id == qid].tolist()
        if position:
            enters_at = position[0] + 1
            st.caption(f"This question's attack enters the knowledge base at {enters_at} injected passages "
                       f"with seed {seed}. Current level: {budget}.")
    elif not custom.strip():
        st.caption("This question has no directly assigned attack. Other poisoned passages may still affect its answer.")
    def evaluate_level(count):
        embedder, llm, reranker, source_filter, store = resources()
        return answer_at_level(chunks=chunks, poisons=poisons,
            question={**selected.to_dict(), "question_id": qid}, custom_query=custom,
            count=count, seed=seed, mode=mode, defense=defense, config=config,
            embedder=embedder, llm=llm, reranker=reranker, source_filter=source_filter, store=store)

    if st.button("Run question", type="primary"):
        try:
            st.session_state.answer = {**evaluate_level(budget), "selection_key": selection_key}
        except Exception as exc:
            st.error(f"Unable to run question: {exc}")
    if st.button("Compare this question across levels", key="compare_question"):
        try:
            levels = [n for n in (0, 1, 5, 10, 20, 50) if mode == REPEATED or n <= len(poisons)]
            measured = [evaluate_level(n) for n in levels]
            rows = [comparison_row(saved) for saved in measured]
            export = {"mode": mode, "question_id": qid, "seed": seed, "defense": defense,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "config": asdict(config), "dataset_sha256": input_hashes(config),
                "measurements": [{**row, "evidence": asdict(saved["result"]),
                                  "backends": saved["backends"]} for row, saved in zip(rows, measured)]}
            content = json.dumps(export, indent=2, ensure_ascii=False, default=str)
            folder = ROOT / "results/question-comparisons"
            folder.mkdir(parents=True, exist_ok=True)
            path = folder / f"comparison_{uuid4().hex}.json"
            path.write_text(content, encoding="utf-8")
            st.session_state.question_comparison = dict(key=comparison_key, rows=rows, content=content, path=str(path))
        except Exception as exc:
            st.error(f"Question comparison failed: {exc}")
    comparison = st.session_state.get("question_comparison")
    if comparison and comparison["key"] == comparison_key:
        st.subheader("Measured effect on this question")
        comparison_frame = pd.DataFrame(comparison["rows"])
        st.dataframe(comparison_frame, hide_index=True)
        st.line_chart(comparison_frame.set_index("Injected passages")[["Target copies in context", "All poisons in context"]])
        st.caption(f"Mode: {mode}. All answers come from the actual pipeline; an unchanged answer is a measured result. Saved: {comparison['path']}")
        st.download_button("Download question comparison", comparison["content"], "question-comparison.json", "application/json")
    if "answer" in st.session_state and st.session_state.answer.get("selection_key") != selection_key:
        st.info("Settings or question changed. Click Run question to calculate a new answer. The previous answer is hidden to avoid showing it for the wrong poisoning level.")
    if "answer" in st.session_state and st.session_state.answer.get("selection_key") == selection_key:
        saved = st.session_state.answer
        result, verdict = saved["result"], saved["verdict"]
        st.subheader("Last completed answer")
        st.caption(saved["caption"] + " · " + saved["backends"])
        st.write(result.query)
        st.text_area("Generated answer", result.answer, disabled=True)
        st.write(f"**Poisoned passages actually seen by the answerer:** {saved['poison_retrieved']} "
                 f"of {len(result.retrieved_documents)} retrieved passages.")
        if verdict is not None and selected.targeted_for_attack and not saved["target_injected"]:
            st.info("The injected passages do not yet include the attack assigned to this question. "
                    "Adding attacks for other questions can leave this answer unchanged.")
        elif verdict is not None and saved["target_injected"] and not saved["target_retrieved"]:
            st.info("This question's poison is in the knowledge base, but retrieval or the defense kept it out of the final context.")
        st.caption("The answerer sees only the retrieved passages, not the whole knowledge base. "
                   "If those passages stay the same, the offline answer stays the same. "
                   "Use the level comparison below to measure poisoned answers across many questions.")
        if verdict is not None:
            st.write("**Ground truth:**", saved["gold"])
            a, b, c = st.columns(3)
            a.metric("Answer match", "Yes" if verdict["answer_correct"] else "No")
            b.metric("Target attack injected", "Yes" if saved["target_injected"] else "No")
            c.metric("Attack success", "Yes" if verdict["attack_success"] else "No")
            if verdict["ambiguous_answer"]:
                st.warning("Answer contains both true and false values; review manually.")
        st.caption("Automatic answer matches are lexical heuristics, not factual entailment judgments.")
        for rank, evidence in enumerate(result.retrieved_documents, 1):
            poisoned = evidence["chunk_id"] in saved["poison_ids"]
            with st.expander(f"{rank}. {'POISON' if poisoned else 'Evidence'} · {evidence['chunk_id']} · {evidence['title']}"):
                st.text(evidence["text"])
                st.json({k: v for k, v in evidence.items() if k != "text"})
        st.download_button("Download evidence JSON", json.dumps(result.retrieved_documents, indent=2), "evidence.json", "application/json")

with run_tab:
    st.subheader("Reproducible experiment runner")
    st.caption("This tab measures attacks spread across the benchmark. The single-question repeat mode is tested separately in Ask & inspect.")
    split = st.selectbox("Evaluation split", ["all", "development", "validation", "test"])
    seed_text = st.text_input("Selection seeds for this experiment", str(seed),
        help="Use 42 for one repeatable run. Use 17 42 91 for three different passage selections; results are reported separately and averaged.")
    st.caption("For a fair dose comparison, keep the same seed and questions at every level. "
               "More passages means more attack exposure; the measured number of poisoned answers may rise, plateau, or fall.")
    st.caption(f"{len(config.poisoning.counts) * len(DEFENSE_VARIANTS)} conditions per seed. Each run gets its own directory and manifest.")
    if st.button("Compare poisoned answers: 0, 10, 20, 50", key="compare_levels"):
        try:
            seeds = [int(value) for value in seed_text.split()]
            compare_config = deepcopy(config)
            compare_config.poisoning.counts = [count for count in (0, 10, 20, 50) if count <= len(poisons)]
            experiment = {"none": "poisoning", "reranking": "reranking", "source_filtering": "source_filtering",
                          "reranking+source_filtering": "filtering"}[defense]
            bar = st.progress(0.0)
            output, summary = execute(compare_config, experiment=experiment, seeds=seeds, split=split,
                progress=lambda fraction, label: bar.progress(fraction, text=label))
            st.success(f"Compared {len(compare_config.poisoning.counts)} levels using {defense}. Saved {output.name}")
        except Exception as exc:
            st.error(f"Comparison failed: {exc}")
    if st.button("Run full comparison"):
        try:
            seeds = [int(value) for value in seed_text.split()]
            bar = st.progress(0.0)
            output, summary = execute(config, seeds=seeds, split=split,
                progress=lambda fraction, label: bar.progress(fraction, text=label))
            st.success(f"Saved run {output.name}")
        except Exception as exc:
            st.error(f"Experiment failed: {exc}")
    run_root = ROOT / "results" / "runs"
    runs = sorted([p for p in run_root.glob("*/manifest.json")
                   if json.loads(p.read_text()).get("status") == "completed"], reverse=True)
    if runs:
        chosen = st.selectbox("Completed run", runs, format_func=lambda p: p.parent.name)
        output = chosen.parent
        manifest = json.loads(chosen.read_text())
        if manifest["dataset_sha256"] != input_hashes(config):
            st.warning("This saved run used a different dataset from the current one.")
        st.caption(f"Backends: {manifest.get('actual_backends')} · split: {manifest['split']}")
        summary = pd.read_csv(output / "summary_metrics.csv")
        if "n_poisoned_answers" in summary:
            st.subheader("How many questions produced poisoned answers?")
            view = summary[["poison_count", "defense_method", "seed", "n_questions", "n_targeted", "n_attacked", "n_poisoned_answers"]]
            st.dataframe(view.rename(columns={"poison_count": "Injected passages", "defense_method": "Defense",
                "seed": "Selection seed", "n_questions": "Questions tested", "n_targeted": "Targeted questions",
                "n_attacked": "Targets actually attacked", "n_poisoned_answers": "Successful poisoned answers"}), hide_index=True)
            chart = summary.groupby(["poison_count", "defense_method"])["n_poisoned_answers"].mean().unstack("defense_method")
            st.line_chart(chart, x_label="Injected passages", y_label="Successful poisoned answers (mean across seeds)")
            st.caption("Counts use the existing attack-success rule: the question's own poison was retrieved and its false value appeared without the true value. No monotonic trend is forced.")
        st.dataframe(summary, hide_index=True)
        st.download_button("Download summary CSV", (output / "summary_metrics.csv").read_bytes(), "summary_metrics.csv", "text/csv")
        st.download_button("Download complete results CSV", (output / "results.csv").read_bytes(), "results.csv", "text/csv")
        with st.expander("Run provenance"):
            st.json(manifest)
        columns = st.columns(2)
        for index, figure in enumerate(sorted((output / "figures").glob("*.png"))):
            columns[index % 2].image(str(figure))
    else:
        st.info("No completed runs yet. Run a comparison here or use main.py.")

with explore_tab:
    st.subheader("Dataset explorer")
    table_name = st.selectbox("Table", list(data))
    text_filter = st.text_input("Search table", placeholder="e.g. 2020, health, Kabul")
    frame = data[table_name]
    if text_filter:
        frame = frame.loc[frame.astype(str).apply(lambda col: col.str.contains(text_filter, case=False, regex=False)).any(axis=1)]
    st.dataframe(frame, hide_index=True)
    st.download_button("Download selected rows", frame.to_csv(index=False), f"{table_name}.csv", "text/csv")
    st.caption("168 new historical observations are API-checked. The 56 inherited documents retain their original verification labels and have not all been independently re-audited. Paraphrases are correlated examples, not independent facts.")
    manifest_path = ROOT / "data" / "dataset_manifest.json"
    if manifest_path.exists():
        with st.expander("Dataset manifest and source checksums"):
            st.json(json.loads(manifest_path.read_text()))
