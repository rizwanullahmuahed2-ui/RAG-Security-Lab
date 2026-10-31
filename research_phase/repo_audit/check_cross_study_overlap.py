"""Bounded exact-match and shared-phrase audit, without semantic claims."""
from pathlib import Path
from collections import defaultdict
import csv
import hashlib
import json
import re
import unicodedata

A=Path('/workspace/research_phase/repo_snapshot')
B=Path('/workspace/revision/experiment')
OUT=Path(__file__).resolve().parent


def csv_rows(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def js(path):return json.loads(path.read_text())
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def strict(text):return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())
def relaxed(text):return ' '.join(re.sub(r'[\W_]+',' ',unicodedata.normalize('NFKC',text).casefold()).split())
def match_fields(left,right,normalizer):
    index=defaultdict(list)
    for rid,text in right:index[normalizer(text)].append(rid)
    return [{'study_a_id':lid,'study_b_ids':index[normalizer(text)],'normalized_text':normalizer(text)} for lid,text in left if normalizer(text) and normalizer(text) in index]
def hashes(folder):return {str(p.relative_to(folder)):digest(p) for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def main():
    before_a=hashes(A);before_b=hashes(B)
    docs=csv_rows(A/'data/raw/documents.csv');chunks=csv_rows(A/'data/raw/chunks.csv');questions=csv_rows(A/'data/raw/questions.csv')
    tests=js(B/'test_questions.json');donors=js(B/'control_donors.json');bdocs=js(B/'clean_documents.json')
    aq=[(q['question_id'],q['question']) for q in questions]
    bq=[('test:'+q['id'],q['question']) for q in tests]+[('donor:'+q['id'],q['question']) for q in donors]
    at=[(d['document_id'],d['title']) for d in docs]
    bt=[(role+':'+q['id']+':'+str(i),title) for role,group in [('test',tests),('donor',donors)] for q in group for i,title in enumerate(q['context_titles'])]
    ax=[('document:'+d['document_id'],d['text']) for d in docs]+[('chunk:'+c['chunk_id'],c['text']) for c in chunks]
    bx=[('paragraph:'+d['id'],d['text']) for d in bdocs]
    bbody=[]
    for d in bdocs:
        prefix=d['title']+'. '
        assert d['text'].startswith(prefix)
        bbody.append(('body:'+d['id'],d['text'][len(prefix):]))
    bsent=[(role+':'+q['id']+':support:'+str(i),sentence) for role,group in [('test',tests),('donor',donors)] for q in group for i,sentence in enumerate(q['supporting_sentences'])]
    exact={}
    for name,normalize in [('NFKC_casefold_whitespace',strict),('NFKC_casefold_alphanumeric_tokens',relaxed)]:
        exact[name]={
            'questions':match_fields(aq,bq,normalize),'document_titles_vs_all_selected_context_titles':match_fields(at,bt,normalize),
            'clean_text_vs_prefixed_paragraphs':match_fields(ax,bx,normalize),'clean_text_vs_paragraph_bodies':match_fields(ax,bbody,normalize),
            'clean_text_vs_annotated_support_sentences':match_fields(ax,bsent,normalize)}
    # Shared phrases are reported as literal string matches, never entity/fact duplicates.
    ngram_results={}
    for n in [8,12]:
        index=defaultdict(set)
        for rid,text in bbody:
            tokens=relaxed(text).split()
            for i in range(len(tokens)-n+1):index[tuple(tokens[i:i+n])].add(rid)
        shared=[];seen=set()
        for lid,text in ax:
            tokens=relaxed(text).split()
            for i in range(len(tokens)-n+1):
                phrase=tuple(tokens[i:i+n])
                if phrase in index:
                    key=(lid,phrase)
                    if key not in seen:
                        shared.append({'study_a_id':lid,'study_b_ids':sorted(index[phrase]),'tokens':' '.join(phrase)})
                        seen.add(key)
        ngram_results[str(n)]={'shared_phrase_records':len(shared),'examples':shared[:30]}
    domain_terms={}
    for term in ['Afghanistan','Kabul','Bamiyan','Kandahar','Herat','Hindu Kush','World Bank']:
        pattern=re.compile(r'(?<!\w)'+re.escape(strict(term))+r'(?!\w)')
        matches={}
        for label,fields in [('questions',bq),('selected_context_titles',bt),('paragraph_bodies',bbody)]:
            found=[rid for rid,text in fields if pattern.search(strict(text))]
            matches[label]={'count':len(found),'record_ids':found[:20]}
        domain_terms[term]=matches
    assert before_a==hashes(A) and before_b==hashes(B)
    report={'scope':'Post hoc bounded exact-string, phrase, and declared-keyword audit; no semantic entity/fact matching or pretraining-contamination test',
            'repository_commit':'6f76858df91277e4b962ee94b4286a25cfe08d4d',
            'denominators':{'study_a_questions':len(aq),'study_b_test_questions':len(tests),'study_b_donor_questions':len(donors),
                            'study_a_document_titles':len(at),'study_b_test_and_donor_context_titles':len(bt),
                            'study_a_document_and_chunk_text_fields':len(ax),'study_a_unique_clean_texts_after_strict_normalization':len({strict(t) for _,t in ax}),
                            'study_b_indexed_paragraphs':len(bdocs),'study_b_test_and_donor_support_sentence_fields':len(bsent)},
            'normalization_definitions':{'NFKC_casefold_whitespace':'Unicode NFKC, casefold, whitespace collapse',
                                        'NFKC_casefold_alphanumeric_tokens':'Unicode NFKC, casefold, nonword/underscore characters replaced by spaces, whitespace collapse'},
            'exact_matches':exact,'literal_shared_ngrams':ngram_results,'bounded_domain_keyword_scan':domain_terms,
            'original_files_unchanged':True,
            'limits':[
              'Zero exact matches would rule out only duplicate strings under the specified normalizations, not paraphrases, same entities, same facts, or shared source families.',
              'Donor full context paragraphs are not retained in the local Study B donor file; donor questions, context titles and annotated support sentences were inspected, not their full paragraph bodies.',
              'Only committed current canonical Study A inputs at this Git revision were compared; exact historical principal-run input identity is not established without its missing manifest/archive.',
              'Both studies draw on publicly available material. These checks do not establish independence from model pretraining, and no model-contamination test was performed.',
              'Shared short phrases or domain keywords, if present, are literal overlap findings, not proof of identical underlying facts.'
            ]}
    (OUT/'cross_study_overlap.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    md=['# Bounded cross-study overlap check','',
        'This post hoc read-only check compares the recovered current canonical Afghanistan inputs with the saved HotpotQA Study B material. It does not change either dataset and makes no network or model call.','',
        '## Scope','',
        f"Compared {len(aq)} Study A question strings with {len(tests)} test and {len(donors)} donor questions; {len(at)} original document titles with {len(bt)} selected context titles; and {len(ax)} document/chunk text fields with {len(bdocs)} indexed Study B paragraphs, both with and without the added title prefix. Annotated support sentences from both test and donor records were also compared.",'',
        '| Normalization | Questions | Titles | Full prefixed paragraphs | Paragraph bodies | Whole clean text vs support sentence |','|:--|--:|--:|--:|--:|--:|']
    for name,values in exact.items():
        md.append('| '+name+' | '+' | '.join(str(len(values[k])) for k in ['questions','document_titles_vs_all_selected_context_titles','clean_text_vs_prefixed_paragraphs','clean_text_vs_paragraph_bodies','clean_text_vs_annotated_support_sentences'])+' |')
    md+=['','## Literal phrase and keyword checks','',
         f"Shared eight-token phrase records: {ngram_results['8']['shared_phrase_records']}; shared twelve-token phrase records: {ngram_results['12']['shared_phrase_records']}. These are literal phrase checks, not semantic judgments.",'']
    for term,values in domain_terms.items():md.append('- '+term+': '+', '.join(f"{k}={v['count']}" for k,v in values.items()))
    md+=['','## What this supports','',
         'These checks provide a concrete exact-overlap result now that original canonical inputs are accessible. Any claim must name the compared Git revision, Study B subset and normalization rules.','',
         '## What it does not support','']+['- '+s for s in report['limits']]
    (OUT/'cross_study_overlap.md').write_text('\n'.join(md)+'\n')
    print(json.dumps({'denominators':report['denominators'],'exact_match_counts':{norm:{k:len(v) for k,v in values.items()} for norm,values in exact.items()},
                      'shared_ngram_counts':{n:r['shared_phrase_records'] for n,r in ngram_results.items()},
                      'nonzero_keyword_findings':{term:{k:v['count'] for k,v in values.items() if v['count']} for term,values in domain_terms.items() if any(v['count'] for v in values.values())},
                      'original_files_unchanged':True},indent=2))


if __name__=='__main__':main()
