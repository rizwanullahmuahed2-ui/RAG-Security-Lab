"""Exhaustive smoke/evidence audit for the interactive attack protocol."""
from pathlib import Path
import logging
import json
import hashlib
from datetime import datetime,timezone
from dataclasses import asdict
from src.config.config import load_config
from src.data.loaders import load_all
from src.attacks.targeted_pool import build_targeted_pool
from src.embeddings.embedding_service import get_embedding_service
from src.generation.llm_interface import get_llm
from src.defenses.reranker import get_reranker
from src.defenses.source_filter import get_source_filter
from src.vectorstore.exact_store import ExactVectorStore
from src.evaluation.question_comparison import answer_at_level,TARGETED,comparison_row
from src.evaluation.runner import input_hashes
c=load_config(Path(__file__).parent/'config.yaml');d=load_all(c.paths)
pool=build_targeted_pool(d['questions'],d['poisoned_passages'],d['chunks'])
args=dict(chunks=d['chunks'],poisons=pool,custom_query='',seed=42,mode=TARGETED,config=c,
    embedder=get_embedding_service(c),llm=get_llm(c),reranker=get_reranker(c),source_filter=get_source_filter(c),store=ExactVectorStore())
for name in logging.root.manager.loggerDict:logging.getLogger(name).setLevel(logging.ERROR)
rows=[]
for i,q in enumerate(d['questions'].to_dict('records')):
    clean=None
    for count,defense in [(0,'none'),(10,'none'),(10,'source_filtering')]:
        saved=answer_at_level(question=q,count=count,defense=defense,**args)
        if count==0:clean=saved['result'].answer
        if defense=='source_filtering':
            assert saved['result'].answer==clean
            assert saved['poison_retrieved']==0
        assert saved['target_copies_injected']==count
        rows.append(dict(question_id=q['question_id'],**comparison_row(saved),evidence=asdict(saved['result']),false_value=saved['false_info']))
    if (i+1)%52==0:print(f'Checked {i+1}/364 questions',flush=True)
summary=[]
for count,defense in [(0,'none'),(10,'none'),(10,'source_filtering')]:
    group=[r for r in rows if r['Injected passages']==count and r['Defense']==defense]
    summary.append(dict(count=count,defense=defense,n=len(group),correct=sum(r['Answer match'] for r in group),attacks=sum(r['Attack success'] for r in group)))
out=Path('results/targeted-mode-validation');out.mkdir(parents=True,exist_ok=True)
(out/'records.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
pool.to_csv(out/'synthetic_attack_pool.csv',index=False)
(out/'summary.json').write_text(json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),summary=summary,
    dataset_sha256=input_hashes(c),backends=dict(embedding=args['embedder'].backend_name,generation=args['llm'].backend_name),
    source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('src').rglob('*.py')},
    note='Synthetic QA assertions; same backend and clean dataset; lexical scoring; not a real-LLM experiment.'),indent=2))
print(json.dumps(summary))
