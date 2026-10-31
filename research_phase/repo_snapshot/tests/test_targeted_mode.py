from pathlib import Path
import pandas as pd
import pytest
from src.config.config import load_config
from src.data.loaders import load_all
from src.attacks.targeted_pool import build_targeted_pool
from src.evaluation.metrics import contains_value
from src.evaluation.question_comparison import TARGETED,answer_at_level
from src.vectorstore.exact_store import ExactVectorStore

def test_targeted_pool_covers_all_questions_without_changing_benchmark():
    config=load_config(Path(__file__).resolve().parents[1]/'config.yaml');d=load_all(config.paths)
    original=d['questions'].copy(deep=True);original_pool=d['poisoned_passages'].copy(deep=True)
    pool=build_targeted_pool(d['questions'],d['poisoned_passages'],d['chunks'])
    assert len(pool)==len(d['questions'])==364
    assert pool.target_question_id.is_unique
    assert set(pool.trust_level)=={'untrusted'} and set(pool.verification_status)=={'unverified'}
    assert pool.set_index('target_question_id').loc['Q004','attacker_false_information'].endswith('Province')
    for r in pool.itertuples():assert not contains_value(r.attacker_false_information,r.correct_answer)
    pd.testing.assert_frame_equal(d['questions'],original)
    pd.testing.assert_frame_equal(d['poisoned_passages'],original_pool)
    pd.testing.assert_frame_equal(pool,build_targeted_pool(d['questions'],d['poisoned_passages'],d['chunks']))

def test_targeted_mode_rejects_unrelated_custom_query(tiny_chunks,tiny_questions,tiny_poison_pool,offline_config,embedder,llm,reranker,source_filter):
    with pytest.raises(ValueError,match='selected benchmark'):
        answer_at_level(chunks=tiny_chunks,poisons=tiny_poison_pool,question=tiny_questions.iloc[0].to_dict(),
            custom_query='unrelated question',count=10,seed=42,mode=TARGETED,defense='none',config=offline_config,
            embedder=embedder,llm=llm,reranker=reranker,source_filter=source_filter,store=ExactVectorStore())

def test_dashboard_previously_untargeted_question_and_defense():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=45).run()
    assert app.radio(key='attack_mode').value==TARGETED
    next(s for s in app.selectbox if s.label=='Benchmark question').set_value('Q004').run()
    app.button[0].click().run()
    assert app.session_state['answer']['verdict']['answer_correct']
    app.slider(key='poison_budget').set_value(10).run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    assert app.session_state['answer']['verdict']['attack_success']
    assert app.session_state['answer']['target_copies_injected']==10
    next(s for s in app.selectbox if s.label=='Defense').set_value('source_filtering').run()
    app.button[0].click().run()
    assert app.session_state['answer']['verdict']['answer_correct']
    assert app.session_state['answer']['poison_retrieved']==0
    app.button(key='compare_question').click().run(timeout=45)
    assert not app.exception and not app.error
    rows=app.session_state['question_comparison']['rows']
    assert len(rows)==24
    assert {row['Defense'] for row in rows}=={'none','reranking','source_filtering','reranking+source_filtering'}
