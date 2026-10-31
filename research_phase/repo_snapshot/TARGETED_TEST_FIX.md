# Targeted poisoning tests for every benchmark question

Updated 30 September 2026. The default Ask & inspect mode is now **Targeted test: attack the selected question**. It supports all 364 benchmark questions, including Q004 (Kabul is the capital of which Afghan province?), which was an untargeted control in the original benchmark.

In this mode the slider counts copies of the selected question's own synthetic false assertion. Inspect the false answer and payload before running. The generator reuses an existing false value when available; otherwise it makes a numeric perturbation or chooses a type-compatible distractor from another question. These synthetic values are not independently adjudicated counterfactual facts. The attack template explicitly includes the question and a claimed answer; it is a stress test of relevance matching, not a natural poisoned-document benchmark.

The original documents, questions, ground truth and 104-record poison pool remain unchanged. Corpus-spread mode still uses that original pool; the original repeated mode still reproduces its assigned attacks. Custom free-text questions remain available in corpus-spread mode. An arbitrary custom question cannot be assumed to match a benchmark attack or ground truth.

## Comparing conditions

Select a benchmark question and click **Compare this question across levels**. In targeted mode it evaluates doses 0, 1, 5, 10, 20 and 50 under all four existing defense settings. The table contains the actual answer, lexical answer match, targeted success, retrieved poison count and poison share of the five-passage context. The JSON export includes the payload and all measured defenses. If the undefended clean baseline already fails, the UI warns that this is a separate clean-evidence problem.

For Q004, the measured clean answer contains Kabul Province. Ten targeted copies induce the synthetic Kandahar Province assertion in the offline extractor; source filtering and combined filtering/reranking restore the clean answer. Relevance reranking alone does not reject the false assertion. At doses 10, 20 and 50 the context can already be saturated, so the false answer remains the same.

An answer such as a province name is categorical: there is no valid automatic rule that 10 passages must make it slightly wrong and 50 much more wrong. More copies increase available attack exposure; they do not guarantee monotonic answer degradation. Likewise, a defense is evaluated rather than guaranteed to fix every answer. Source filtering succeeds here because the synthetic insertions are marked untrusted and unverified; it is not a semantic misinformation detector.

## Validation

108 tests passed, including pool coverage, unchanged benchmark data, deterministic construction, rejecting unrelated custom questions in targeted mode, and the Streamlit clean/poisoned/defended comparison for Q004.

An exhaustive 1,092-response audit covered every one of the 364 questions in three conditions:

| Condition | Answer matches | Targeted attack successes |
| --- | --- | --- |
| Clean, no defense | 355/364 | 0 |
| 10 targeted copies, no defense | 337/364 | 27 |
| 10 targeted copies, source filtering | 355/364 | 0 |

Every source-filtered answer exactly matched the same question's undefended clean answer, and zero poison passages reached the filtered context. The 27 successes include questions already incorrect at baseline; do not equate this count with the 18 net lost answer matches. Nine clean answer-match failures remain. The scoring is lexical, the answerer is an offline extractor, and these are diagnostic results, not new real-LLM paper results.

Records, source/data hashes, and the generated attack pool are saved in `results/targeted-mode-validation/`. Restart Streamlit after installation using `python -m streamlit run app.py` from this project directory. Old files are backed up under `backups/targeted-question-fix-<timestamp>/`.
