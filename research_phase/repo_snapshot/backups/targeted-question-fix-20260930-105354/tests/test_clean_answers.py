"""Regression coverage for wrong clean answers; no answer-table lookup."""
from pathlib import Path
import pytest
from src.config.config import load_config
from src.data.loaders import load_all
from src.embeddings.embedding_service import get_embedding_service
from src.generation.llm_interface import ExtractiveLLM
from src.generation.rag_pipeline import RagPipeline
from src.retrieval.retriever import Retriever
from src.vectorstore.exact_store import ExactVectorStore
from src.vectorstore.indexer import index_chunks

@pytest.fixture(scope='module')
def clean_pipeline():
    c=load_config(Path(__file__).resolve().parents[1]/'config.yaml')
    d=load_all(c.paths);e=get_embedding_service(c);s=ExactVectorStore()
    index_chunks(d['chunks'],e,s,'clean')
    return RagPipeline(Retriever(e,s,'clean'),ExtractiveLLM(),'',0,300,30,5)

@pytest.mark.parametrize('question',[
    'what is capital of afghanistan', 'What is the capital of Afghanistan?',
    "What is Afghanistan's capital?", 'What is the capital city of Afghanistan?',
    'Tell me the national capital of Afghanistan.',
])
def test_capital_paraphrases_use_the_national_document(clean_pipeline,question):
    result=clean_pipeline.answer(question)
    assert result.retrieved_documents[0]['chunk_id']=='CHK-002-01'
    assert result.answer.startswith('Kabul is the national capital of Afghanistan')

@pytest.mark.parametrize('question,answer',[
    ('What is the currency of Afghanistan?','Afghani'),
    ('How many provinces does Afghanistan have?','34 provinces'),
    ('How many districts is Afghanistan divided into?','401 districts'),
    ('Kandahar is the capital of which Afghan province?','Kandahar Province'),
    ('Mazar-i-Sharif is the capital of which Afghan province?','Balkh Province'),
])
def test_other_clean_facts(clean_pipeline,question,answer):
    assert answer in clean_pipeline.answer(question).answer

def test_missing_country_does_not_get_an_afghan_answer(clean_pipeline):
    assert 'sufficient evidence' in clean_pipeline.answer('What is the capital of France?').answer

def test_wrong_year_abstains_and_total_is_not_per_capita():
    llm=ExtractiveLLM()
    wrong="In 2022, Exampleland's GDP (current US$) was 30.00."
    assert 'sufficient evidence' in llm.generate('What was Exampleland GDP in 2023?',wrong,'')
    context="In 2023, Exampleland's GDP per capita (current US$) was 10.00.\n\nIn 2023, Exampleland's GDP (current US$) was 1,000,000.00."
    assert '1,000,000.00' in llm.generate('What was Exampleland GDP (current US$) in 2023?',context,'')

def test_answers_follow_supplied_evidence_not_a_country_answer_table():
    llm=ExtractiveLLM()
    assert llm.generate('What is the capital of Exampleland?',
        'Southport is the capital of South Province in Exampleland.\n\nNorthport is the national capital of Exampleland.','').startswith('Northport')
    # Deliberately false local evidence must remain observable in attack tests.
    assert llm.generate('What is the capital of Afghanistan?',
        'Herat is the national capital of Afghanistan.','').startswith('Herat')

def test_dashboard_custom_capital_with_zero_poison():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=30).run()
    app.text_input[0].set_value('what is capital of afghanistan').run()
    app.button[0].click().run()
    assert not app.exception and not app.error
    saved=app.session_state['answer']
    assert saved['count']==0 and saved['poison_retrieved']==0
    assert saved['result'].answer.startswith('Kabul is the national capital of Afghanistan')
