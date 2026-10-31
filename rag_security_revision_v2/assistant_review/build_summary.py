"""Summarize actual source-based AI case notes; never relabel them as human ratings."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import csv,hashlib,json,html
ROOT=Path(__file__).resolve().parent
WORK=ROOT.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=read(ROOT/'AI_STAGE1_NOTES.json')['records'];lock=read(ROOT/'AI_PASS1_LOCK.json')
assert sha(ROOT/'AI_STAGE1_NOTES.json')==lock['ai_notes_sha256']
inputs={r['case_id']:r for i in range(1,5)for r in read(ROOT/f'pass1_input_{i}.json')['cases']}
quotes=read(ROOT/'QUOTE_CHECKS.json')
for q in quotes:
 r=inputs[q['case_id']];texts=[r['model_answer']]
 for name in ['annotated_reference_sentences_json','annotated_reference_passages_json','provided_numbered_passages_json','provided_clean_subset_json']:texts+=json.loads(r[name])
 q['verbatim_found_in_evidence_or_answer']=' '.join(q['quote'].split())in' '.join(' '.join(texts).split())
assert all(q['verbatim_found_in_evidence_or_answer']for q in quotes)
(ROOT/'QUOTE_CHECKS_REVIEWED.json').write_text(json.dumps({'explanation':'The one initial unmatched quote was a verbatim excerpt of the model answer; the initial check searched evidence only. All188quotations match evidence or exactanswer. The original first-pass lock is preserved.','checks':quotes},ensure_ascii=False,indent=2)+'\n')
groups=[]
for group,study in [('uniform_sample','B'),('uniform_sample','C'),('flagged_diagnostic_supplement','B')]:
 sub=[r for r in rows if r['selection_group']==group and r['study']==study]
 groups.append({'selection_group':group,'study':study,'n_cases':len(sub),'counts':{f:dict(Counter(r[f]for r in sub))for f in ['ai_answer_vs_source','ai_support_any_provided','ai_contradicted_by_provided','ai_support_actual_clean_subset','ai_abstention','ai_reference_annotation']}})
summary={'status':'completed_AI_case_wise_semantic_assessment','created_at_utc':datetime.now(timezone.utc).isoformat(),'total_cases':72,'uniform_sample_cases':64,'uniform_sample_by_study':{'B':32,'C':32},'diagnostic_supplement_cases':8,'assessment_origin':'AI assistant contexts reading original questions, exact answers and saved evidence; not human item-level ratings.','author_manual_inspection_reported_completed':True,'author_inspection_distinct_from_this_72_case_assessment':True,'structured_human_ratings_received_for_these_cases':0,'selection_sha256':sha(ROOT/'selection_freeze.json'),'notes_sha256':sha(ROOT/'AI_STAGE1_NOTES.json'),'verbatim_quotes_verified':188,'groups':groups,'limitations':['Retrospective analysis after main automatic results were known.','Unique displayed cases, not independent questions; case reuse and shared evidence remain.','Diagnostic supplement selected using automatic review flags, separate from the uniform64.','Source-relative assistant judgments are not external factual verification or human metric calibration.','No independent two-person human agreement, adjudication or semantic ASR is claimed.']}
(ROOT/'AI_CASE_REVIEW_SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
fields=['study','case_id','selection_group','question','dataset_reference_unadjudicated','model_answer','ai_answer_vs_source','ai_support_any_provided','ai_contradicted_by_provided','ai_support_actual_clean_subset','ai_abstention','ai_reference_annotation','ai_rationale']
with(ROOT/'Case_Review_72.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
 for r in rows:w.writerow({k:r.get(k,inputs[r['case_id']].get(k,''))for k in fields})
lines=['# بررسی ساختارمند ۷۲ مورد پاسخ و زمینه','', 'این پرونده، بررسی موردی توسط دستیار هوش مصنوعی را ثبت می‌کند. بررسی دستی قبلی نویسنده، فعالیت جداگانه‌ای است که خود او انجام‌شدن آن را اعلام کرده است؛ ۷۲ مورد حاضر به نام رأی انسانی ثبت نشده‌اند.','', 'نمونهٔ اصلی ۶۴ مورد دارد: ۳۲ مورد از قاب ۳۷۶موردی B و ۳۲ مورد از قاب ۸۹۷موردی C، با بذر تصادفی ثبت‌شده پیش از خواندن موارد منتخب. هشت مورد تشخیصی B بر پایهٔ پرچم‌های روش خودکار جدا افزوده شده است. شمارها مربوط به مورد پرسش–زمینه–پاسخ است و تعداد پرسش مستقل یا نرخ موفقیت معنایی حمله نیست.','', '| بخش | موارد | سازگار با منبع | مخالف منبع | ادعای پاسخ ندارد | نامشخص | سازگاری جزئی |','|---|---:|---:|---:|---:|---:|---:|']
for g in groups:
 c=g['counts']['ai_answer_vs_source'];label=g['study']+('؛ نمونهٔ تصادفی'if g['selection_group']=='uniform_sample'else'؛ مکمل تشخیصی')
 lines.append('| '+label+' | '+' | '.join(str(x)for x in [g['n_cases'],c.get('agrees',0),c.get('contradicts',0),c.get('no_answer_claim',0),c.get('undetermined',0),c.get('partly_agrees',0)])+' |')
lines+=['','در مکمل تشخیصی، دو پاسخ هم‌زمان عددی را اظهار و دربارهٔ همان پاسخ امتناع کرده‌اند؛ یک پاسخ امتناع جزئی و یک پاسخ امتناع کامل داشته است. این نتایج، اندازه‌گیری توافق ارزیاب انسانی نیست.','', 'نمونه‌های قابل ردیابی شامل پاسخ Koufax با عدد1972 و عبارتUNKNOWN، ابهام شخص در سؤال جایزهٔ بازیگری، حفظ قید«بیش از3000» و وجود شاهد جایگزین سال1943 در متنOperationLadbroke است. پاسخ آخر نشان می‌دهد فقدان شاهد علامت‌گذاری‌شده به‌تنهایی فقدان تمام شواهد معتبر را ثابت نمی‌کند.','', 'تمام۱۸۸ نقل‌قول با متن شواهد یا پاسخ دقیق سیستم تطبیق داده شد. متن کامل هر۷۲ تصمیم، شناسه‌ها، دلیل و شواهد درAI_STAGE1_NOTES.json وCase_Review_72.csv محفوظ است.']
(ROOT/'Case_Review_Report_FA.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'cases':72,'groups':[(g['study'],g['selection_group'],g['n_cases'])for g in groups],'quotes_verified':188,'human_ratings_created':0}))
