"""Validate and lock AI-only case notes before opening attacker-target sheets."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 if(ROOT/'AI_PASS1_LOCK.json').exists():raise SystemExit('Existing AI first-pass lock must not be overwritten')
 manifest=read(ROOT/'selection_freeze.json')
 assert sha(ROOT/'selection_freeze.json')==(ROOT/'selection_freeze.json.sha256').read_text().strip()
 assert all(sha(WORK/n)==h for n,h in manifest['source_hashes'].items())
 allowed=read(ROOT/'RUBRIC_AI_STAGE1.json')['allowed'];allrecords=[];hashes={};selection={(r['study'],r['case_id']):r for r in manifest['selection']};quotes=[]
 for i in range(1,5):
  inp=read(ROOT/f'pass1_input_{i}.json');path=ROOT/f'pass1_results_{i}.json';data=read(path);records=data['records'] if isinstance(data,dict)else data
  expected={(r['study'],r['case_id'])for r in inp['cases']};actual=[(r['study'],r['case_id'])for r in records]
  assert len(actual)==len(set(actual))and set(actual)==expected,(i,'coverage')
  source={r['case_id']:r for r in inp['cases']}
  for row in records:
   assert row['human_judgments_completed']==0
   for name,values in allowed.items():assert row[name]in values,(i,row['case_id'],name,row[name])
   assert row['ai_rationale'].strip()and isinstance(row['ai_numbers_asserted'],list)and isinstance(row['ai_source_evidence'],list)
   assert all(isinstance(x,str)for x in row['ai_source_evidence'])
   text=' '.join(' '.join(json.loads(source[row['case_id']][n]))for n in ['annotated_reference_sentences_json','annotated_reference_passages_json','provided_numbered_passages_json','provided_clean_subset_json'])
   norm=lambda s:' '.join(s.split())
   for quote in row['ai_source_evidence']:
    quotes.append({'case_id':row['case_id'],'quote':quote,'verbatim_substring_found':norm(quote)in norm(text)})
   allrecords.append({**row,**{k:v for k,v in selection[(row['study'],row['case_id'])].items()if k.startswith('selection_')},'assistant_partition':i})
  hashes[path.name]=sha(path);hashes[f'pass1_input_{i}.json']=sha(ROOT/f'pass1_input_{i}.json')
 assert len(allrecords)==manifest['total_cases']==72
 output=ROOT/'AI_STAGE1_NOTES.json';output.write_text(json.dumps({'review_type':'AI case-wise source-relative semantic notes; not human validation','human_judgments_completed':0,'records':sorted(allrecords,key=lambda r:(r['study'],r['case_id']))},ensure_ascii=False,indent=2)+'\n')
 q=ROOT/'QUOTE_CHECKS.json';q.write_text(json.dumps(quotes,ensure_ascii=False,indent=2)+'\n')
 lock={'locked_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'AI initial case reading before target-sheet release','records':len(allrecords),'human_judgments_completed':0,'selection_sha256':sha(ROOT/'selection_freeze.json'),'ai_notes_sha256':sha(output),'inputs_and_partitions_sha256':hashes,'quote_checks':{'total':len(quotes),'verbatim_found':sum(r['verbatim_substring_found']for r in quotes),'unmatched':sum(not r['verbatim_substring_found']for r in quotes)},'independence_limit':'Assistant contexts had study background and prior automatic results in their conversation. Input fields hid targets/condition labels but this is not an independent or fully blinded human pass.'}
 (ROOT/'AI_PASS1_LOCK.json').write_text(json.dumps(lock,indent=2)+'\n');print(json.dumps(lock,indent=2))
if __name__=='__main__':main()
