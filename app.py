"""Streamlit research workbench. Start with: python -m streamlit run app.py"""
from __future__ import annotations
from pathlib import Path
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import json
import hashlib
from html import escape
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
from src.evaluation.question_comparison import SPREAD, REPEATED, TARGETED, answer_at_level, comparison_row
from src.attacks.targeted_pool import build_targeted_pool
from src.generation.llm_interface import get_llm
from src.vectorstore.exact_store import get_vector_store
from src.ui.dashboard import (
    DEFENSE_LABELS, answer_export, completed_runs, evidence_table, filter_rows,
    parse_selection_seeds, safe_source_url,
)

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="RAG Security Lab", page_icon="🔬", layout="wide")
st.html(f"<style>{(ROOT / 'src/ui/dashboard.css').read_text(encoding='utf-8')}</style>")
st.html('<div class="lab-kicker">RETRIEVAL · EVIDENCE · RESILIENCE</div>')
st.title("RAG Security Lab")
st.html('<div class="lab-intro">Follow a poisoned passage from the knowledge base to the answer. '
        'Test a question, inspect its sources, then measure what each defense changes.</div>')
config = load_config(ROOT / "config.yaml")
st.html(f'<span class="lab-badge">Configured answer engine: {escape(config.llm_backend)} · '
        f'Retrieval store: {escape(config.vector_db.backend)}</span>')
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
@st.cache_data(show_spinner=False)
def targeted_pool(questions, poisons, chunks):
    return build_targeted_pool(questions, poisons, chunks)
counts = st.columns(4)
for column, label, frame in zip(counts, ["Documents", "Searchable chunks", "Questions", "Poison passages"], [documents, chunks, questions, poisons]):
    column.metric(label, len(frame))
if config.llm_backend == "extractive":
    st.info("Answer engine: offline evidence extraction (not a generative LLM). "
            "Answers are selected from retrieved documents; missing evidence should produce an insufficient-evidence response. "
            "These results do not measure a reasoning LLM's robustness.")
st.sidebar.header("Experiment controls")
st.sidebar.caption("01 / Set exposure and defense")
budget = st.sidebar.slider("Injected passages", min_value=0, max_value=len(poisons), value=0, step=1,
    help="In targeted mode these copies attack the selected question. In corpus-spread mode they are selected from the original benchmark pool.", key="poison_budget")
defense = st.sidebar.selectbox("Defense", [v[0] for v in DEFENSE_VARIANTS],
                               format_func=DEFENSE_LABELS.get, key="defense")
with st.sidebar.expander("Repeatability: what is a seed?"):
    st.write("A seed is the number used to shuffle the poison list. Keep 42 to repeat the same selection. "
             "With the same seed, 20 passages contains the first 10 plus 10 more. "
             "Changing the seed selects a different group; a larger seed does not make the attack stronger.")
    seed = int(st.number_input("Selection seed (keep 42 for comparisons)", min_value=0, max_value=2**32-1,
                              value=config.poisoning.random_seed, key="selection_seed"))
st.sidebar.caption("Source filtering assumes ingestion assigns trustworthy metadata. It is not a learned poison detector.")
st.sidebar.divider()
st.sidebar.markdown(f"**Current setup**  \n{budget} injected passages  \n{DEFENSE_LABELS[defense]}  \nSelection seed {seed}")
st.sidebar.caption("The question tab uses its selected attack mode. Benchmark experiments always spread attacks across questions.")
ask_tab, run_tab, explore_tab = st.tabs(["Ask & inspect", "Experiments & results", "Dataset & provenance"])

with ask_tab:
    st.subheader("Trace one answer")
    st.caption("02 / Choose an attack model and question. Run the pipeline to reveal the answer and its exact evidence.")
    mode = st.radio("Poisoning mode for this question", [TARGETED, SPREAD, REPEATED], key="attack_mode")
    eligible = questions.loc[questions.targeted_for_attack] if mode == REPEATED else questions
    active_poisons = targeted_pool(questions, poisons, chunks) if mode == TARGETED else poisons
    if mode == TARGETED:
        st.info("Every benchmark question has a synthetic targeted attack in this mode. "
                "10 passages means 10 copies attacking this question, not 10 unrelated questions. "
                "The comparison button measures all four defense settings at each level. "
                "A factual answer can switch or stay unchanged; poison count is not an error percentage. "
                "Copies use the same text, so the selection seed does not strengthen this attack.")
    if mode == REPEATED:
        st.info("Each injected passage is another copy of this question's assigned false claim. "
                "These copies are one repeated source, not independent evidence. "
                "The seed does not change the text in this mode. More copies can fill the context, "
                "but the answer can plateau once the context is full.")
    question_filters = st.columns([1, 2])
    category = question_filters[0].selectbox("Question category", ["All"] + sorted(eligible.category.unique()))
    question_search = question_filters[1].text_input("Search benchmark questions", placeholder="Question text or ID, e.g. population or Q-001", key="question_search")
    available = eligible if category == "All" else eligible.loc[eligible.category == category]
    available = filter_rows(available[["question_id", "question"]], question_search).join(
        available.drop(columns=["question_id", "question"])
    )
    if available.empty:
        st.warning("No benchmark questions match these filters. Clear the search or choose another category.")
    st.caption(f"{len(available)} matching questions · custom questions are available in corpus-spread mode.")
    qid = st.selectbox("Benchmark question", available.question_id.tolist(),
                       format_func=lambda q: f"{q} — {available.set_index('question_id').loc[q, 'question']}",
                       disabled=available.empty)
    selected = available.set_index("question_id").loc[qid] if qid is not None else None
    custom_input = st.text_input("Custom question (optional; use corpus-spread mode)", disabled=mode != SPREAD,
                                 key="custom_question")
    custom = custom_input if mode == SPREAD else ""
    selection_key = (qid, custom.strip(), budget, defense, seed, mode)
    comparison_key = (qid, custom.strip(), defense, seed, mode)
    if selected is not None and mode in (REPEATED, TARGETED):
        st.caption(f"Current level: {budget} copies attacking this question; 0 copies is the clean baseline.")
        attack = active_poisons.loc[active_poisons.target_question_id == qid].iloc[0]
        with st.expander("Inspect this question's synthetic attack"):
            st.write("Intended false answer:", attack.attacker_false_information)
            st.text(attack.poisoned_text)
            st.caption("Untrusted, unverified research data. Repeated copies are not independent sources.")
    elif selected is not None and not custom.strip() and selected.targeted_for_attack:
        order = poisons.sample(frac=1, random_state=seed).reset_index(drop=True)
        position = order.index[order.target_question_id == qid].tolist()
        if position:
            enters_at = position[0] + 1
            st.caption(f"This question's attack enters the knowledge base at {enters_at} injected passages "
                       f"with seed {seed}. Current level: {budget}.")
    elif selected is not None and not custom.strip():
        st.caption("This question has no directly assigned attack. Other poisoned passages may still affect its answer.")
    def evaluate_level(count, defense_override=None):
        embedder, llm, reranker, source_filter, store = resources()
        return answer_at_level(chunks=chunks, poisons=active_poisons,
            question={**selected.to_dict(), "question_id": qid}, custom_query=custom,
            count=count, seed=seed, mode=mode, defense=defense_override or defense, config=config,
            embedder=embedder, llm=llm, reranker=reranker, source_filter=source_filter, store=store)

    actions = st.columns([1, 2])
    if actions[0].button("Run question", type="primary", disabled=selected is None, use_container_width=True):
        try:
            with st.spinner("Retrieving passages and checking the answer..."):
                st.session_state.answer = {**evaluate_level(budget), "selection_key": selection_key}
        except Exception as exc:
            st.error(f"Unable to run question: {exc}")
    if actions[1].button("Compare this question across levels", key="compare_question", disabled=selected is None, use_container_width=True):
        try:
            levels = [n for n in (0, 1, 5, 10, 20, 50) if mode == REPEATED or n <= len(poisons)]
            methods = [v[0] for v in DEFENSE_VARIANTS] if mode == TARGETED else [defense]
            with st.spinner(f"Measuring {len(levels) * len(methods)} question configurations..."):
                measured = [evaluate_level(n, method) for n in levels for method in methods]
            rows = [comparison_row(saved) for saved in measured]
            export = {"mode": mode, "question_id": qid, "seed": seed, "defense": defense,
                "defenses_measured": methods,
                "target_attack": active_poisons.loc[active_poisons.target_question_id == qid].to_dict('records'),
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
        baseline = comparison_frame.loc[(comparison_frame['Injected passages']==0) & (comparison_frame['Defense']=='none')]
        if len(baseline) and baseline.iloc[0]['Answer match'] == False:
            st.warning("The clean baseline already fails the answer-match check. A defense can remove poison, "
                       "but it cannot by itself repair missing or conflicting clean evidence. Review this question's sources.")
        st.line_chart(comparison_frame.pivot(index="Injected passages",columns="Defense",values="Poison share of context (%)").rename(columns=DEFENSE_LABELS),
                      x_label="Injected passages", y_label="Poison share of final context (%)")
        st.caption("This chart measures poisoned context exposure, not how wrong an answer is. "
                   "Source filtering relies on trusted metadata; relevance reranking alone may not reject a relevant false claim.")
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
        exposure, context_size, target_count = st.columns(3)
        exposure.metric("Poison in final context", saved["poison_retrieved"])
        context_size.metric("Context passages", len(result.retrieved_documents))
        target_count.metric("Target copies injected", saved["target_copies_injected"])
        if verdict is not None and saved['attack_targeted'] and not saved["target_injected"] and budget > 0:
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
        if verdict is None:
            st.info("Custom question: benchmark answer-match and attack-success scores are unavailable. Inspect the evidence to assess this answer.")
        st.subheader("Evidence reaching the answerer")
        if result.retrieved_documents:
            st.dataframe(evidence_table(saved), hide_index=True, use_container_width=True)
            st.caption("Similarity and rerank scores order relevance; they do not measure factual reliability. Poison labels come from known experimental injections.")
        else:
            st.warning("No passages reached the answerer. The answer has no retrieved evidence to support it.")
        for rank, evidence in enumerate(result.retrieved_documents, 1):
            poisoned = evidence["chunk_id"] in saved["poison_ids"]
            with st.expander(f"{rank}. {'POISON' if poisoned else 'Evidence'} · {evidence['chunk_id']} · {evidence['title']}"):
                st.text(evidence["text"])
                source_url = safe_source_url(evidence.get("source_url"))
                if source_url:
                    st.link_button("Open source record", source_url)
                st.json({k: v for k, v in evidence.items() if k != "text"})
        st.download_button("Download evidence JSON", json.dumps(result.retrieved_documents, indent=2), "evidence.json", "application/json")
        st.download_button("Download answer + provenance", answer_export(saved, asdict(config), input_hashes(config)),
                           "answer-provenance.json", "application/json")
    elif "answer" not in st.session_state:
        with st.container(border=True):
            st.markdown("**Ready for a clean baseline**")
            st.write("Start with 0 injected passages and run a question. Then increase exposure or switch a defense to inspect what changes.")
            st.caption("Answers and charts appear only after the pipeline runs. Existing benchmark observations are documented in VALIDATION.md.")

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
            seeds = parse_selection_seeds(seed_text)
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
            seeds = parse_selection_seeds(seed_text)
            bar = st.progress(0.0)
            output, summary = execute(config, seeds=seeds, split=split,
                progress=lambda fraction, label: bar.progress(fraction, text=label))
            st.success(f"Saved run {output.name}")
        except Exception as exc:
            st.error(f"Experiment failed: {exc}")
    run_root = ROOT / "results" / "runs"
    run_entries, skipped_runs = completed_runs(run_root)
    runs = [path for path, _ in run_entries]
    if skipped_runs:
        st.warning(f"Skipped {len(skipped_runs)} unreadable or incomplete saved run(s). Other dashboard features remain available.")
    if runs:
        chosen = st.selectbox("Completed run", runs, format_func=lambda p: p.parent.name)
        output = chosen.parent
        manifest = json.loads(chosen.read_text())
        if manifest.get("dataset_sha256") != input_hashes(config):
            st.warning("This saved run used a different dataset from the current one.")
        st.caption(f"Backends: {manifest.get('actual_backends', 'not recorded')} · split: {manifest.get('split', 'not recorded')}")
        try:
            summary = pd.read_csv(output / "summary_metrics.csv")
        except (OSError, ValueError, pd.errors.ParserError) as exc:
            st.error(f"Unable to read this saved summary: {exc}")
            summary = pd.DataFrame()
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
        st.info("No completed runs yet. Run a comparison here or use main.py. Historical measurements in VALIDATION.md are not preloaded as live charts.")

with explore_tab:
    st.subheader("Dataset explorer")
    table_name = st.selectbox("Table", list(data))
    text_filter = st.text_input("Search table", placeholder="e.g. 2020, health, Kabul")
    frame = data[table_name]
    frame = filter_rows(frame, text_filter)
    st.caption(f"Showing {len(frame)} of {len(data[table_name])} rows. Search treats punctuation as literal text.")
    if frame.empty:
        st.info("No rows match this search. Clear the search to browse the full table.")
    st.dataframe(frame, hide_index=True)
    st.download_button("Download selected rows", frame.to_csv(index=False), f"{table_name}.csv", "text/csv")
    st.caption("168 new historical observations are API-checked. The 56 inherited documents retain their original verification labels and have not all been independently re-audited. Paraphrases are correlated examples, not independent facts.")
    manifest_path = ROOT / "data" / "dataset_manifest.json"
    if manifest_path.exists():
        with st.expander("Dataset manifest and source checksums"):
            st.json(json.loads(manifest_path.read_text()))

st.html('<div class="lab-footer">Local research workbench · Evidence and settings travel with every export. '
        'Offline extraction, synthetic attacks, and trusted metadata limit what these experiments can establish.</div>')
