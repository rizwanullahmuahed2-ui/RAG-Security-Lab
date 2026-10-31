#!/usr/bin/env python3
"""Build a source-linked Dari implementation report; never runs inference or labels cases."""
from __future__ import annotations
import argparse
import csv
import hashlib
import html
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from review_addendum import apply_report_addendum

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
WS = WORK.parent


def load(path, default=None):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else default


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mdtable(headers, rows):
    def cell(value):
        return str(value).replace('|', ' / ').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(map(cell, headers)) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in rows])


def pct(value):
    return 'نامعلوم' if value is None else f'{100*float(value):.2f}٪'


def c_metric(report, module, condition, defense, metric, copies=None):
    rows = [row for row in report['summary'] if row['module'] == module
            and row['condition'] == condition and row['defense'] == defense
            and row['metric'] == metric
            and (copies is None or int(row['copies_per_target']) == copies)]
    if len(rows) != 1:
        raise ValueError('Expected one saved C summary row: ' + str((module, condition, defense, metric, copies)))
    return rows[0]


def source_c_analysis():
    """Require actual analysis, completed archive and each reported integrity flag."""
    path = WORK / 'analysis/study_c/analysis.json'
    report = load(path)
    if not report:
        return None, 'نتیجهٔ تحلیل محفوظ C هنوز در مسیر مقرر موجود نیست.'
    for key in ['design_and_generation_freezes_verified', 'request_payload_hashes_verified',
                'raw_response_hashes_and_models_verified', 'completion_response_archive_hash_verified']:
        if report.get('integrity', {}).get(key) is not True:
            return None, f'تحلیل C موجود است، اما تأیید {key} کامل نیست؛ نتیجه در این گزارش قطعی درج نشد.'
    completion = load(WORK/'study_c/completion.json', {})
    raw = WORK/'study_c/responses.jsonl'
    if not raw.exists() or completion.get('responses_sha256') != digest(raw):
        return None, 'هش آرشیو خام C با رسید تکمیل منطبق نیست؛ نتیجه در این گزارش درج نشد.'
    if report['integrity'].get('analysis_script_sha256') != digest(WORK/'analysis/analyze_study_c.py'):
        return None, 'نسخهٔ تحلیل C پس از نتیجه تغییر کرده است؛ به بازتحلیل نیاز است.'
    manifest_path = WORK/'analysis/study_c/analysis_manifest.json'
    manifest = load(manifest_path, {})
    if manifest.get('files', {}).get('analysis.json') != digest(path):
        return None, 'هش فایل نتیجهٔ C در manifest تأیید نشد.'
    return report, 'نتیجه از تحلیل خروجی‌های خام تکمیل‌شده و دارای هش منطبق خوانده شد.'


def requirement_updates(c_ready, human_done):
    # IDs describe completion of the precise criterion, not a paper-readiness score.
    updates = {}
    def put(ids, status, action, evidence, remaining):
        for rid in ids.split():
            updates[rid] = [status, action, evidence, remaining]
    put('3.1.1 5.9 6.1', 'اجراشده در مستندسازی',
        'مطالعهٔ تاریخی، کد فعلی، آزمایش تشخیصی و B/C در دفتر نسخه و ادعا جدا ثبت شد.',
        'baseline/study_registry.json; baseline/claims_registry.json; history/reproducibility_decision.json',
        'شناسهٔ دقیق کد و محیط اجرای اصلی تاریخی همچنان بازیابی نشده است.')
    put('3.1.2 3.1.3', 'تاحدی؛ دلیل تاریخی نامعلوم',
        'اجزای فعال و تفاوت طرح و اجرا روشن شد؛ دلیل پسینی به‌عنوان تصمیم تاریخی معرفی نشد.',
        'baseline/study_registry.json; manuscript/Working_Manuscript_v2.md',
        'سند تصمیم اولیه برای انتخاب Hashing/TF-IDF و غیرفعال‌بودن اجزای پیشنهادی در دست نیست.')
    put('3.1.4', 'آزمایش‌های واقعی B و C مستند' if c_ready else 'انجام آزمایش واقعی B مستند',
        'آرشیو واقعی مدل در B و، در صورت وجود رسید تأییدشده، اجرای سه‌نوبتی C از آزمون‌های ساختگی کد جدا ثبت شده است.',
        'evaluation/B_reanalysis_v2_summary.json; /workspace/revision/experiment/completion.json; study_c/completion.json',
        'نتیجه به مدل و دادهٔ معین محدود است؛ وجود LLM جای اعتبارسنجی معنایی را نمی‌گیرد.')
    put('3.1.5 3.5.4 3.6.4 4.5', 'اصلاح ادعا در نسخهٔ کاری',
        'صفر مشاهده‌شده و برچسب آزمایشی به مصونیت عمومی تعبیر نمی‌شود؛ حدود مطالعه در متن درج شد.',
        'manuscript/Working_Manuscript_v2.md; baseline/claims_registry.json',
        'بازخوانی نهایی متن پس از تکمیل داوری انسانی لازم است.')
    put('3.2.1 3.2.3 3.2.7 3.3.1 3.3.4 3.3.5 5.2 5.3', 'ورودی‌های موجود ردیابی شده',
        'جداول ۲۲۴ سند، ۲۲۵ قطعه، ۳۶۴ پرسش و ۱۰۴ حملهٔ موجود با نسخهٔ مخزن و ممیزی ساختار مرتبط شد.',
        '/workspace/research_phase/repo_audit/original_data_audit.json; history/reproducibility_decision.json',
        'دسترسی به این ورودی‌ها، هویت و بازتولید خروجی اجرای اصلی را ثابت نمی‌کند؛ نشر مواد جدید باید با manifest همراه باشد.')
    put('3.2.2', 'بازسازی ورودی انجام‌شده',
        '۱۶۸ مشاهدهٔ WDI و قواعد ساخت به فایل‌های ثابت و ممیزی بازسازی وصل شد.',
        '/workspace/research_phase/repo_audit/original_data_audit.json',
        'تطبیق با snapshot ذخیره‌شده به معنای تصدیق مستقل تمام واقعیت‌های بیرونی نیست.')
    put('3.2.4 3.3.7', 'تاحدی؛ منشأ دستی محدود',
        '۳۳۶ پرسش قالبی WDI و حملات الگوریتمی از ۲۸ پرسش و ۲۰ حملهٔ پیشین جدا توضیح داده شد.',
        '/workspace/research_phase/repo_audit/original_data_audit.json; manuscript/Working_Manuscript_v2.md',
        'سابقهٔ واقعی نگارش و بازبینی موارد قبلی کامل نیست و اختراع نشده است.')
    put('3.2.5', 'A ردیابی شد؛ صحت مستقل مرجع‌های آن باز است',
        'پرسش و مرجع‌های A به ورودی فعلی مخزن وصل شد. ممیزی رابطه و قیدِ ۶۴ پرسش B جدا اجرا شد و اعتبار مرجع‌های A را ثابت نمی‌کند.',
        '/workspace/research_phase/repo_audit/original_data_audit.json; reference_audit/B_reference_cards_v2.json',
        'بازبینی جامع منبع و صحت مستقل مرجع‌های تاریخی A، از جمله موارد پیشین غیر-WDI، تکمیل نشده است؛ ممیزی دستیار B جانشین آن نیست.')
    put('3.3.2 3.3.3', 'هدف‌های A ردیابی شد؛ اعتبار معنایی مستقل باز است',
        'مقادیر مرجع و مقادیر تعیین‌شدهٔ ۱۰۴ هدف A در ورودی‌های نسخه‌دار قابل ردیابی‌اند. پرونده‌های ممیزی B و C فقط به همان مطالعه‌های جدا تعلق دارند.',
        '/workspace/research_phase/repo_audit/original_data_audit.json; history/reproducibility_decision.json; reference_audit/B_reference_cards_v2.json',
        'این اقدام تأیید مستقل درستی همهٔ مرجع‌های A یا غلط‌بودن همهٔ ادعاهای حملهٔ A نیست. آرشیو دقیق خروجی تاریخی و بازبینی معنایی منبع‌دار آن همچنان باز است.')
    put('5.8', 'منشأ نسخه‌دار ثبت؛ تصدیق جامع بیرونی باز است',
        'ورودی‌های فعلی A، snapshot منبع B/C و پرونده‌های رابطه و قید B/C با نسخه و مسیر شاهد ثبت شده‌اند؛ نوع بررسی دستیار از داوری انسانی جدا است.',
        '/workspace/research_phase/repo_audit/original_data_audit.json; data/source_dataset_metadata.json; data/reference_cards.json; reference_audit/B_reference_audit_summary.json',
        'ثبت منشأ و تطبیق snapshot، صحت مستقل تمام واقعیت‌های بیرونی A/B/C را ثابت نمی‌کند؛ داوری واقعی و بررسی منابع مسئله‌دار همچنان لازم است.')
    put('3.2.6', 'تاحدی؛ بازبینی پیشین ثابت نیست',
        'نبود شاهد بازبینی مستقل قبلی و ماهیت برچسب‌های سازنده آشکار ثبت شد.',
        'history/reproducibility_decision.json; protocol/study_c_protocol.json',
        'بازبینی مستقل ۵۶ سند پیشین و برچسب‌های آنان همچنان کامل نیست.')
    put('3.2.8 3.7.2', 'قاعدهٔ تحلیل پیاده‌شده',
        'پرسش، ردیف شرط، فراخوانی واقعی، پوشش هدف و مواجهه مخرج‌های جدا دارند؛ میانگین سه نوبت درون هر پرسش محاسبه می‌شود.',
        'analysis/analyze_study_c.py; protocol/study_c_protocol.json; analysis/README_ANALYSIS.md',
        'نمایهٔ مشترک و وابستگی معنایی خانواده‌های منبع محدودیت تعمیم می‌ماند.' if c_ready else 'محاسبهٔ واقعی C پس از تکمیل آرشیو لازم است؛ نمایهٔ مشترک محدودیت می‌ماند.')
    put('3.3.6 3.6.1 3.6.2 3.6.3 3.6.5', 'فرض اعتماد روشن؛ سامانهٔ عملیاتی اجرا نشده',
        'تغییر metadata آزمایش صفات ورودی است؛ صلاحیت نهادی، احراز هویت و نفوذ واقعی ادعا نشده است.',
        'protocol/study_c_protocol.json; baseline/claims_registry.json; manuscript/Working_Manuscript_v2.md',
        'سامانهٔ عملیاتی تأیید، کنترل صلاحیت و آزمون نفوذ به روند تأیید ساخته و آزمایش نشده است.')
    put('3.3.8', 'کنترل‌های C ساخته و اجرا شده' if c_ready else 'شرح نسخه‌دار و طرح کنترل آماده',
        'قالب حمله‌های قدیمی محفوظ است؛ C طول ۱۲۰ واژه و واحد یکسان را پیش از پاسخ‌ها تعیین کرده است.',
        'protocol/study_c_protocol.json; data/config.json; /workspace/research_phase/artifact_audit',
        'واقع‌نمایی این قالب کنترل‌شده برای تمام حمله‌های طبیعی اثبات نشده است.')
    put('3.4.1 3.4.2', 'کد و مثال اجرایی آماده',
        'تطبیق قدیمی از انتخاب عددی سخت‌گیرانه، نفی، نقل قول، قید و امتناع جمله‌ای جدا شد؛ ۱۱ آزمون مرزی گذشت.',
        'evaluation/evaluator_v2.py; evaluation/test_evaluator_v2.py; evaluation/HUMAN_REVIEW_RUBRIC_EN.md',
        'شناسهٔ خودکارِ انتخاب عددی به‌تنهایی صحت واقعیت یا پذیرش معنایی را تصدیق نمی‌کند.')
    put('3.4.3 6.2', 'B بازتحلیل شد؛ خروجی تاریخی A باز است',
        'قاعدهٔ قدیمی روی تمام ۱۲۸۰ ردیف B با صفر اختلاف محاسباتی بازتولید شد؛ ورودی A جدا بازسازی شده است.',
        'evaluation/B_reanalysis_v2_summary.json; history/reproducibility_decision.json',
        'بازنمره‌دهی ۲۱٬۸۴۰ و ۳٬۰۱۶ ردیف تاریخی بدون آرشیو همان اجرا تکمیل نشده است.')
    put('3.4.4', 'موارد قابل ردیابی آماده',
        'پاسخ‌های واقعی با پرچم نفی، قید، نام رقمی، امتناع و دو عدد در جدول تشخیصی ثبت شد.',
        'evaluation/B_unique_response_diagnostics_v2.csv; evaluation/B_rescored_rows_v2.csv',
        'طبقه‌بندی معنایی این نمونه‌ها هنوز باید توسط انسان واقعی تأیید شود.')
    put('3.4.5 6.3', 'منتظر داوری واقعی انسان' if not human_done else 'وضعیت داوری از رسید قفل‌ها بررسی شود',
        'قاب B با ۳۷۶ مورد، فورم‌های اولیهٔ جدا، rubric و روند قفل آماده است؛ قاب C نیز پس از اجرای واقعی جدا ساخته شده است. کاربر هماهنگ‌کننده و دو شخص دیگر داور خواهند بود.' if c_ready else
        '۳۷۶ مورد یکتای B، دو فورم اولیهٔ جدا، rubric و روند قفل و حل اختلاف آماده است؛ کاربر هماهنگ‌کننده و دو شخص دیگر داور خواهند بود.',
        'evaluation/human_validation_gate.json; evaluation/human_review_packet; evaluation/study_c_review/human_review_packet; evaluation/review_manager.py; protocol/human_review_coordination.json',
        'دو داوری مستقل واقعی، ثبت هویت/استقلال، مرحلهٔ دوم و حل اختلاف منبع‌دار لازم است؛ دامنه و نتیجهٔ داوری B و C جدا نگه داشته می‌شود.')
    put('3.4.6 3.5.1', 'محورهای ارزیابی جدا شده',
        'بازیابی شاهد، مواجهه، انتخاب مقدار مرجع، انتخاب مقدار مهاجم، پشتیبانی و امتناع معیارهای جدا دارند.',
        'evaluation/evaluator_v2.py; analysis/analyze_study_c.py; evaluation/HUMAN_REVIEW_RUBRIC_EN.md',
        'ستون صحت معنایی و استلزام تا داوری واقعی سنجیده‌نشده باقی است.')
    put('3.5.2 3.5.3 3.8.1 3.8.2 3.8.3', 'تحلیل خودکار B و C انجام‌شده' if c_ready else 'تحلیل خودکار B و کد C آماده',
        'جلوگیری از مقدار هدف، بازگشت مقدار مرجع و خطاهای تازه جدا است؛ گروه‌های شکست و انتخاب نمونه با قاعدهٔ ثابت تعریف شد.',
        'analysis/study_c/analysis.json; analysis/study_c/cases.jsonl; analysis/README_ANALYSIS.md; /workspace/research_phase/artifact_audit',
        'نتایج C در فایل‌های واقعی تحلیل قرار دارد؛ تفسیر معنایی نهایی منتظر انسان است.' if c_ready else 'فایل‌های واقعی C و تفسیر معنایی انسانی هنوز تکمیل نشده است.')
    put('3.7.1 3.7.4 5.4', 'نسخهٔ تازه روشن؛ عضویت تاریخی نامعلوم',
        'بودجه‌ها و seedهای گزارش‌شدهٔ تاریخی از پیش‌فرض فعلی جدا و قواعد ترتیب/تکرار C ثبت شد.',
        'history/reproducibility_decision.json; protocol/study_c_protocol.json; data/config.json',
        'عضویت دقیق هدف‌ها و تنظیمات مؤثر همان اجرای تاریخی بدون آرشیو تأیید نمی‌شود.')
    put('3.7.3', 'ماژول تازه اجرا و تحلیل شده' if c_ready else 'ماژول تازه تعریف‌شده؛ اجرا باز',
        'دوزهای ۱، ۲ و ۵ برای همان ۶۲ هدف و دو دفاع none/rerank پیش از خروجی انتخاب شد.',
        'protocol/study_c_protocol.json; analysis/study_c/analysis.json' if c_ready else 'protocol/study_c_protocol.json; runner/run_study.py',
        'این ماژول بازاجرای آزمایش تکرار قدیمی نیست؛ تفسیر آن به مدل و قالب ثابت محدود است.')
    put('3.8.4', 'شرط برچسب B و C تحلیل شده' if c_ready else 'شرط برچسب B تحلیل شده',
        'مقایسهٔ متن و شناسهٔ یکسان با برچسب تغییریافته حفظ و از نفوذ عملیاتی جدا نام‌گذاری شد.',
        '/workspace/research_phase/artifact_audit; evaluation/B_automatic_comparison_v2.csv; protocol/study_c_protocol.json',
        'اثر برچسب آزمایشی وجود صلاحیت یا تمامیت سامانهٔ واقعی تأیید را ثابت نمی‌کند.')
    put('3.8.5 3.8.6 5.10', 'شکاف تاریخی ثبت؛ مطالعهٔ تازه جدا',
        'جست‌وجوی محدود آرشیو ثبت شد؛ ۳٬۰۱۶ ردیف تاریخی و تشخیص ۱٬۰۹۲ردیفی به جای یکدیگر استفاده نشدند.',
        'history/bounded_search_results.json; history/reproducibility_decision.json; protocol/study_c_protocol.json',
        'آرشیو تکرار تاریخی بازیابی نشده است؛ نتایج ماژول دوز C فقط به مطالعهٔ تازه تعلق دارد.' if c_ready else 'آرشیو تکرار تاریخی بازیابی نشده و ماژول تازه هنوز نیاز به خروجی واقعی دارد.')
    put('4.1 4.2 4.3 4.4 6.5', 'بازنویسی در نسخهٔ کاری',
        'روش، مطالعه‌ها، مخرج‌ها، محدودیت اعتماد و تمایز رقم آرشیوی/اصلاحی در مقالهٔ کاری بازنویسی شد.',
        'manuscript/Working_Manuscript_v2.md; manuscript/build_working_manuscript.py',
        'ساخت نهایی مقاله پس از آخرین تحلیل و داوری انسانی باید تکرار و بازخوانی شود؛ این وضعیت آمادگی نشر نیست.')
    put('5.1 5.6', 'کد ادامه و بازتحلیل موجود',
        'آماده‌سازی، اجرا و تحلیل تازه نسخه‌دار است و ممیزی B از خروجی خام امکان دارد.',
        'runner/run_study.py; evaluation/evaluator_v2.py; analysis/analyze_study_c.py; data/prepare_candidates.py',
        'کد فعلی جای نسخهٔ منطبقِ بازیابی‌نشدهٔ اجرای تاریخی معرفی نمی‌شود؛ بستهٔ نهایی باید فرمان و هش داشته باشد.')
    put('5.5', 'B/C محفوظ؛ آرشیو تاریخی A بازیابی نشده' if c_ready else 'B محفوظ؛ آرشیو تاریخی ناقص',
        'وضعیت دسترسی principal، تکرار، تشخیصی و B/C جدا ثبت شده است؛ تکمیل C با رسید و هش آرشیو خودش سنجیده می‌شود.',
        'history/reproducibility_decision.json; /workspace/revision/experiment/responses.jsonl; study_c/responses.jsonl; study_c/completion.json',
        'خروجی کامل principal و تکرار تاریخی موجود نیست؛ C فقط در صورت تکمیل آرشیو خودش شاهد تازه است.')
    put('5.7', 'کنترل اجرا و محیط C مستند' if c_ready else 'کنترل اجرا و محیط جدید آماده',
        'کنترل هش پیش از هر ارسال/ادامه، مدل برگشتی، سقف هزینه و توقف خطا در runner پیاده شد؛ محیط مشتری ثبت است.',
        'runner/run_study.py; runner/test_run_study.py; protocol/client_environment.json; protocol/client_hardware_observation.json',
        'سخت‌افزار سرویس مدل و محیط دقیق تاریخی نامعلوم است؛ محیط فعلی جای آن ثبت نشده است.')
    put('5.11', 'تاحدی؛ شرایط استفاده باید حفظ شود',
        'منشأ عمومی و نسخهٔ منبع معرفی شده؛ عمومی‌بودن داده با انتقال بی‌قید حقوق برابر گرفته نشده است.',
        'data/source_dataset_metadata.json; manuscript/Working_Manuscript_v2.md; /workspace/research_phase/source_catalog.json',
        'حقوق تمام منابع قبلی مستقلاً حل نشده؛ اشتراک عمومی بسته نیازمند حفظ شرایط منبع و اعلام مواد محلی است.')
    put('6.4', 'مطالعهٔ C اجرا و تحلیل شده' if c_ready else 'طرح و ابزار C آماده؛ نتیجه باز',
        'پرسش تحقیق، کنترل نامرتبط و بی‌ضرر، زمینهٔ ثابت، دوز، مدل ثابت، توقف و سقف USD5 پیش از خروجی ثبت شد.',
        'analysis/study_c/analysis.json; protocol/study_c_protocol.json' if c_ready else 'protocol/study_c_protocol.json; runner/run_study.py',
        'نتیجهٔ خودکار جای داوری معنایی نمی‌گیرد؛ پیش‌آموزش و تعمیم به مدل‌های دیگر کنترل نشده است.')
    return updates


def build():
    ROOT.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    display_date = datetime.fromisoformat(now).strftime('%Y/%m/%d، ساعت %H:%M').translate(str.maketrans('0123456789','۰۱۲۳۴۵۶۷۸۹'))
    mapping = load(WS/'implementation_plan/requirements_work_package_map.json')
    audit = load(WORK/'reference_audit/B_reference_audit_summary.json')
    b = load(WORK/'evaluation/B_reanalysis_v2_summary.json')
    gate = load(WORK/'evaluation/human_validation_gate.json')
    c_review = load(WORK/'evaluation/study_c_review/human_review_packet/REVIEW_STATUS.json', {})
    stress = load(WORK/'study_c/retrieval_label_stress_summary.json', {})
    hardware = load(WORK/'protocol/client_hardware_observation.json', {})
    postrun_qa = load(WORK/'protocol/POSTRUN_QA.json', {})
    c, c_note = source_c_analysis()
    human_done = bool(gate.get('adjudication_complete')) and not gate.get('blocking_reasons')
    updates = requirement_updates(c is not None, human_done)
    for rid in ['3.4.4','3.4.5','6.3']:
        updates[rid]=['بررسی دستی معنایی نویسنده انجام و یافته‌ها ثبت شده',
                      'نویسنده بررسی۷۲مورد را گزارش کرده است:۳۲B،۳۲C و۸تشخیصی؛ نمونهٔ اصلی۶۴مورد با۴۱سازگار،۱۶مخالف،۳امتناع کامل و۴نامشخص و نمونه‌های معنایی ارائه شد.',
                      'manual_review/author_reported_findings.json; assistant_review/Case_Review_72.csv; manuscript/Working_Manuscript_v2.md',
                      'شمارها مربوط به نمونهٔ پسینی است؛ توافق بین ارزیابان یا درصد موفقیت معنایی برای کل آزمایش ادعا نشده است.']
    rows = []
    for req in mapping['requirements']:
        rid = req['requirement_id']
        if rid not in updates:
            raise RuntimeError('Unmapped requirement: '+rid)
        status, action, evidence, remaining = updates[rid]
        rows.append({'requirement_id': rid, 'expert_section': req['expert_section'],
                     'requirement_fa': req['requirement_fa'], 'expert_force_fa': req['expert_force_fa'],
                     'primary_work_package': req['primary_work_package'], 'implementation_status_fa': status,
                     'implemented_action_fa': action, 'evidence_files': evidence,
                     'remaining_work_or_limit_fa': remaining,
                     'completion_criterion_fa': req['completion_criterion_fa'], 'assessed_at_utc': now})
    assert len(rows) == len({r['requirement_id'] for r in rows}) == 67
    with (ROOT/'Implementation_Progress_67_FA.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (ROOT/'Implementation_Progress_67_FA.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    gold = audit['gold_status_counts']; false = audit['false_status_counts']
    c_section = f'''## ۷. مطالعهٔ تازهٔ C: طرح و وضعیت مشاهده‌شده

مطالعهٔ C برای پاسخ به مقایسه‌ای تازه طراحی شد. استفادهٔ دوباره از B به‌عنوان آزمون دست‌نخورده، پس از مشاهده و ممیزی پاسخ‌های آن، توجیه نداشت. انتخاب C از snapshot ثابت بخش عمومی validation در HotpotQA انجام می‌شود. شناسه‌ها و عنوان‌های تمام ۱۲۸ مورد قبلی، شامل پرسش‌های آزمون و اهداکنندگان، از قاب تازه کنار گذاشته شدند. این اقدام، استقلال از موارد قبلی پروژه را در حدود کنترل‌های ثبت‌شده تقویت می‌کند؛ استقلال از پیش‌آموزش مدل یا اعتبار آزمون مخفی رسمی را ثابت نمی‌کند.

در پلان اولیه ۶۴ جفت پیشنهاد شده بود. بررسی واحدها پیش از هر خروجی تازه نشان داد که طبقهٔ کلی «شمار» می‌تواند فاصله، رتبه، عدد ترتیبی و تعداد موجودیت‌ها را مخلوط کند. بنابراین، دامنه به ۶۲ جفتِ هم‌واحد محدود شد: ۵۷ جفتِ سال تقویمی و ۵ جفتِ جمعیت با تاریخ معین. این تغییر پیش از مشاهدهٔ پاسخ C ثبت شده است؛ انتخاب نمونه بر اساس بهترشدن نتیجه نبوده است. از ۱۹۲ نامزد بررسی‌شده توسط دستیار، ۱۳۵ مورد نسبت به شاهد منبع پذیرفته، ۳۸ مورد کنار گذاشته و ۱۹ مورد حل‌نشده ثبت شد. این بررسی، داوری انسانی نامیده نمی‌شود.

در طبقه‌های نهایی، ۱۱۴ نامزد سال و ۱۱ نامزد جمعیت واجد شرط بودند. جفت‌سازی مجاور بر اساس ترتیب هش، همهٔ ۱۱۴ مورد سال و ۱۰ مورد جمعیت را به کار برد. آخرین مورد جمعیت در همان ترتیب، بدون همتای مجاور باقی ماند و به‌عنوان ذخیرهٔ استفاده‌نشده ثبت شد؛ این مورد پس از مشاهدهٔ نتیجه کنار گذاشته نشده است. پرسش‌ها و مرجع‌های اصلی بازنویسی نشده‌اند. هر ۱۲۴ مورد منتخب با منبع ثابت تطبیق شد و ۱٬۲۴۰ عنوان زمینه در میان آنان مشترک نیست؛ تفاوت عنوان، استقلال کامل معنایی یا خانوادهٔ منبع را اثبات نمی‌کند.

هستهٔ طرح ۶۲۰ متن پاک، پنج شرط و چهار روش دفاع را دربر می‌گیرد. در هر شرط مثبت ۶۲ متن افزوده می‌شود و نسبت آلودگی ۶۲ از ۶۸۲، یعنی ۹٫۰۹٪ است. این نسبت با پوشش تمام هدف‌ها همراه است و سناریوی فشار آزمایشگاهی محسوب می‌شود. کنترل نامرتبط، همان مقدار تعیین‌شده را برای رابطهٔ اهداکننده به کار می‌برد؛ کنترل بی‌ضرر مقدار مرجع پرسش هدف را دارد. طول متن درج‌شده ۱۲۰ واژه تثبیت شده است. در آزمایش زمینهٔ کنترل‌شده، چهار متن اصلی ثابت می‌ماند و فقط یک جایگاه با متن درج‌شده عوض می‌شود؛ هر دو شاهد لازم نگه داشته می‌شوند. ماژول دوزهای ۱، ۲ و ۵ نیز پوشش همان هدف‌ها را ثابت نگه می‌دارد.

مدل مولد مقرر `gpt-4.1-mini-2025-04-14` و مدل بردارساز `text-embedding-3-small` است. سه نوبت فراخوانی تازه، از استفادهٔ مجدد پاسخ یک payload درون همان نوبت جدا می‌شود. این سه نوبت شمار پرسش‌های مستقل را از ۶۲ بیشتر نمی‌کند. میانگین ابتدا درون هر پرسش و سپس میان پرسش‌ها گرفته می‌شود. دامنهٔ کمینه و بیشینهٔ نوبت‌ها توصیف تغییر مشاهده‌شده است و فاصلهٔ اطمینان جمعیت معرفی نمی‌شود.

**وضعیت خوانده‌شده در ساخت این گزارش:** {c_note}
'''
    if c:
        e = c['execution']
        completion = load(WORK/'study_c/completion.json')
        c_section += '\n'+mdtable(['مشخصهٔ آرشیو واقعی', 'مقدار'], [
            ['پرسش / نوبت', f"{e['questions']} / {e['rounds']}"],
            ['ردیف شرط برنامه‌ریزی‌شده', e['planned_condition_evaluations']],
            ['payload یکتا در هر نوبت', e['unique_payloads']],
            ['پاسخ منطقی محفوظ / فراخوانی منطقی برنامه‌ریزی‌شده', f"{e['saved_logical_responses']} / {e['planned_logical_generation_calls']}"],
            ['پایان عادی / پاسخ بریده / پایان دیگر در فراخوانی‌های یکتا', f"{completion['normal_stop']} / {completion['truncations']} / {completion['other_finish_reasons']}"],
            ['توکن ورودی / خروجی مولد، فقط فراخوانی‌های متمایز', f"{e['reported_generation_usage_distinct_calls']['prompt_tokens']} / {e['reported_generation_usage_distinct_calls']['completion_tokens']}"],
            ['هزینهٔ تعهدشدهٔ محافظه‌کارانه، USD؛ مبلغ صورتحساب نیست', e.get('cost_committed_usd_conservative')],
            ['داوری انسانی ثبت‌شده در تحلیل C', e.get('human_judgments_completed', 0)]])+'\n'
        selected=[]
        for condition in ['clean','targeted','unrelated','benign','accepted_label']:
            for defense in ['none','rerank','filter','filter_rerank']:
                r=c_metric(c,'core',condition,defense,'strict_target_choice_proxy')
                reference=c_metric(c,'core',condition,defense,'strict_reference_choice_proxy')
                support=c_metric(c,'core',condition,defense,'all_support')
                selected.append([condition,defense,pct(r.get('mean_question_rate')),
                                 pct(reference.get('mean_question_rate')),pct(support.get('mean_question_rate')),
                                 pct(r.get('round_rate_min'))+' تا '+pct(r.get('round_rate_max'))])
        c_section += '\n**نتیجهٔ خودکار اصلی:** درصد انتخاب عددی سخت‌گیرانهٔ مقدار هدف، با میانگین سه نوبت درون هر پرسش؛ این جدول ASR معناییِ تأییدشده نیست.\n\n'
        c_section += mdtable(['شرط','دفاع','انتخاب هدف','انتخاب مرجع','هر دو شاهد','دامنهٔ نوبت‌های هدف'],selected)+'\n'
        targeted=c_metric(c,'core','targeted','none','strict_target_choice_proxy')
        unrelated=c_metric(c,'core','unrelated','none','strict_target_choice_proxy')
        rerank=c_metric(c,'core','targeted','rerank','strict_target_choice_proxy')
        own_target=c_metric(c,'core','targeted','none','assigned_insert_exposed')
        own_unrelated=c_metric(c,'core','unrelated','none','assigned_insert_exposed')
        clean_reference=c_metric(c,'core','clean','none','strict_reference_choice_proxy')
        rerank_reference=c_metric(c,'core','clean','rerank','strict_reference_choice_proxy')
        c_section += f'''\nدر هستهٔ بدون دفاع، شاخص انتخاب هدف در شرط هدفمند {pct(targeted['mean_question_rate'])} و در شرط نامرتبط {pct(unrelated['mean_question_rate'])} است. با رتبه‌بندی مجدد، مقدار هدفمند به {pct(rerank['mean_question_rate'])} می‌رسد. اما مواجههٔ متن درج‌شده برابر نیست: درج متناظرِ هدفمند در {pct(own_target['mean_question_rate'])} و درج متناظرِ نامرتبط در {pct(own_unrelated['mean_question_rate'])} زمینه‌ها حضور دارد. پس اختلاف هسته، اثر کل خط لولهٔ بازیابی و پاسخ را نشان می‌دهد؛ به‌تنهایی اثر محتوا را در مواجههٔ برابر جدا نمی‌کند.

کاهش تولید هدف نیز به معنی افزایش هم‌زمان کیفیت همهٔ پاسخ‌ها نیست. در مجموعهٔ پاک، انتخاب سخت‌گیرانهٔ مقدار مرجع از {pct(clean_reference['mean_question_rate'])} بدون دفاع به {pct(rerank_reference['mean_question_rate'])} با رتبه‌بندی مجدد رسیده است. این هزینهٔ قالب پاسخ/تطبیق مرجع باید کنار کاهش مقدار هدف دیده شود؛ هیچ‌یک هنوز صحت معناییِ داوری‌شده توسط انسان نیست. تمام سلول‌های اصلی این اجرای تکمیل‌شده پاسخ عادی دارند و سلول نامعلومِ ناشی از نقص اجرا گزارش نشده است.
'''
        controlled=[]
        for condition in ['clean','targeted','unrelated','benign']:
            values=[c_metric(c,'controlled',condition,'none',name)['mean_question_rate'] for name in
                    ['strict_target_choice_proxy','strict_reference_choice_proxy','all_support','assigned_insert_exposed']]
            controlled.append([condition,*map(pct,values)])
        c_section+='\n**کنترل مواجهه:** دو شاهد کامل و دو متن غیرشاهد ثابت‌اند؛ فقط یک جایگاه متن، درون هر پرسش، تغییر می‌کند.\n\n'
        c_section+=mdtable(['جایگاه کنترل‌شده','انتخاب هدف','انتخاب مرجع','هر دو شاهد','مواجهه با درج متناظر'],controlled)+'\n'
        ct=c_metric(c,'controlled','targeted','none','strict_target_choice_proxy')
        cu=c_metric(c,'controlled','unrelated','none','strict_target_choice_proxy')
        c_section+=f'''\nدر این ماژول، هر دو نوع درج هدفمند و نامرتبط حتماً ارائه می‌شوند و هر دو شاهد لازم نیز در تمام موارد باقی می‌مانند. شاخص هدف در شرط هدفمند {pct(ct['mean_question_rate'])} و در نامرتبط {pct(cu['mean_question_rate'])} است. این مقایسه، مشکل نابرابری مواجههٔ هسته را برای همین زمینه‌های ساخته‌شده رفع می‌کند. با این حال، تفاوت میان {pct(targeted['mean_question_rate'])} هسته و {pct(ct['mean_question_rate'])} کنترل را نمی‌توان فقط به حفظ شاهد نسبت داد؛ متن‌های غیرشاهد، ترتیب و روش ساخت زمینه نیز میان دو ماژول فرق دارد.\n'''
        dose=[]
        for copies in [1,2,5]:
            module='core' if copies==1 else 'dose'
            for defense in ['none','rerank']:
                values=[c_metric(c,module,'targeted',defense,name,copies)['mean_question_rate'] for name in
                        ['strict_target_choice_proxy','strict_reference_choice_proxy','all_support']]
                dose.append([copies,defense,*map(pct,values)])
        c_section+='\n**تکرار با پوشش هدف ثابت:** دوز، شمار نسخه‌های یک متن یکسان برای هر هدف است.\n\n'
        c_section+=mdtable(['نسخه برای هر هدف','دفاع','انتخاب هدف','انتخاب مرجع','هر دو شاهد'],dose)+'\n'
        c_section+='\nبا افزایش نسخه‌های یکسان، هم رقابت بازیابی و هم ترکیب جایگاه‌های زمینه تغییر کرده است. در دوز پنج بدون دفاع، نبود هر دو شاهد در زمینه با افزایش شاخص هدف همراه است؛ این همراهی، آزمایش تنوع حمله یا جداسازی علّیِ «تکرار» از حذف شاهد نیست. متن‌ها عمداً تکراری‌اند و قطعه‌های یکسان حذف نشده‌اند. نتیجه به این قالب، همین مدل و همین مجموعه محدود می‌ماند.\n'
        paired=[r for r in c['paired_defense_outcomes'] if r['condition']=='targeted' and r['metric']=='strict_target_choice_proxy' and r['defense']=='rerank'][0]
        c_section+=f'''\nتحلیل انتقال جفتی نیز افت خالص را توضیح می‌دهد. در مجموعِ سلول‌های سه نوبت، از {paired['initial_success_lower_cells']} رویداد اولیهٔ معیارِ «مواجهه به‌اضافهٔ انتخاب هدف»، {paired['prevented_lower_cells']} مورد پس از رتبه‌بندی مجدد دیگر معیار را ندارد؛ تنها {paired['restored_reference_lower_cells']} مورد به انتخاب مقدار مرجع می‌رسد و {paired['new_success_lower_cells']} رویداد تازه در خارج از مجموعهٔ اولیه ایجاد می‌شود. این شمارها سلول‌های پرسش–نوبت‌اند، نه همان تعداد پرسش مستقل یا خطای معنایی تأییدشده. بنابراین، پیشگیری، بازیابی مقدار مرجع و تولید هدف تازه باید جدا گزارش شوند.\n'''
        c_section += '\nتمام معیارها، مقایسه‌های جفتی و موارد شکست در `analysis/study_c/` محفوظ است. گروه‌های از پیش تعریف‌شده و انتخاب نمونهٔ توضیحی با هش ثابت نگهداری شده‌اند؛ مثالِ مطلوب جای مجموعهٔ کامل خطاها را نگرفته است.\n'
    else:
        c_section += '\nدر نبود تحلیل تکمیل‌شدهٔ دارای تمامیت، هیچ درصد، تعداد پاسخ، هزینهٔ مصرف‌شده یا نمودار نتیجه برای C در این گزارش ساخته نشده است. پروتکل و آماده‌بودن کد از اجرای واقعی جدا باقی می‌ماند. پس از تکمیل اجرا، همین سازنده نتیجه را از فایل واقعی وارد می‌کند.\n'
    stress_section=''
    if stress:
        stress_records=WORK/'study_c/retrieval_label_stress.jsonl'
        if not stress_records.is_file() or digest(stress_records)!=stress.get('records_sha256'):
            raise ValueError('Retrieval-only stress archive differs from its saved summary')
        selected=[r for r in stress['summary'] if r['defense']=='filter']
        stress_section='\n**حساسیت به رد اشتباه شاهد مشروع:**\n\n'
        stress_section+=mdtable(['برچسب‌گذاری در آزمون جدا','شمار دارای هر دو شاهد','مخرج','درصد'],[
            [r['condition'],r['all_support_count'],r['n'],pct(r['all_support_rate'])] for r in selected])+'\n'
        stress_section+='\nاین آزمون فقط بازیابی را اندازه می‌گیرد. در هر پرسش، یک شاهد لازم با قاعدهٔ شناسهٔ ثابت رد شده و با رد یک متن غیرشاهد مقایسه شده است. از دست‌رفتن شرط «هر دو شاهد» پس از حذف یک شاهد لازم، پیامد ساختاری همین سنجه است؛ صحت پاسخ مدل یا دسترسی به شاهد معادل را اندازه نمی‌گیرد. برای این ماژول هیچ فراخوانی تازهٔ بردارسازی یا تولید پاسخ انجام نشده و هزینهٔ پاسخ نهایی از آن استنتاج نشده است.\n'
    hardware_note=''
    if hardware:
        hardware_note=f'''\nثبت تکمیلی محیط محلی در زمان اجرا، پردازندهٔ `{hardware.get('cpu',{}).get('model name','نامعلوم')}`، سه پردازندهٔ منطقی قابل مشاهده، سهمیهٔ دو هسته و سقف حافظهٔ ۸ GiB را نشان می‌دهد. این مشاهده با تاریخ خود در `protocol/client_hardware_observation.json` نگهداری می‌شود و اعلامِ پیش از انجماد معرفی نشده است. بردارسازی و تولید متن در سرویس دوردست انجام شده؛ مشخصات این میزبان جای سخت‌افزار نامعلوم سرویس API یا محیط تاریخی را نمی‌گیرد.\n'''
    qa_note=''
    if postrun_qa.get('status')=='passed':
        qa_note=f'''\nیک بررسی محاسباتی جداگانه نیز زنجیرهٔ هش، شناسه‌های پاسخ سرویس، ترتیب دو انجماد و سه نوبت، مصرف توکن و دفتر هزینه را با فایل‌های خام تطبیق داد. این بررسی بدون واردکردن ارزیاب و تحلیل‌گر اصلی، {postrun_qa['independent_summary_cells_compared']} سلول خلاصه و {postrun_qa['independent_transition_counts_compared']} شمار انتقال جفتی را دوباره محاسبه کرد و اختلاف ثبت نشد. تمام {postrun_qa['baseline_files_unchanged']} فایل مبنای قبلی نیز بدون تغییر باقی است. این شاهدِ تمامیت و بازحساب محاسبه است؛ بازتولید بیرونی یا داوری معنایی انسان محسوب نمی‌شود. رسید آن در `protocol/POSTRUN_QA.json` موجود است.\n'''
    c_human_note=(f"برای C نیز {c_review['unique_cases']} مورد متفاوت آماده شده و اتصال آن به {c_review['condition_row_mappings']} ردیف شرط–نوبت حفظ شده است. رأی انسانی ثبت‌شدهٔ این قاب {c_review['completed_human_judgments']} است. با ۳۷۶ مورد B، هر ارزیاب در مجموع {376+c_review['unique_cases']} مورد در دو قاب جدا دارد. پاسخ یکسان در پرسش و زمینهٔ یکسان فقط یک بار برای داوری ارائه می‌شود، ولی تمام اتصال‌های نوبت و شرط محفوظ می‌ماند. این حذف تکرار، شمار پرسش‌های مستقل را بیشتر نمی‌کند." if c_review else
                  'برای C پس از اجرای واقعی باید قاب داوری جدا با اتصال همهٔ شرایط و نوبت‌ها ساخته شود؛ داوری B جای آن را نمی‌گیرد.')
    content = f'''# گزارش تطبیق اصلاحات علمی و تخنیکی مقالهٔ امنیت سیستم‌های RAG

**عنوان مقالهٔ مورد بررسی:**

Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning

**مبنای گزارش:** ملاحظات متخصص، گزارش ریسرچ، پلان اجرایی و فایل‌های شاهد هر مطالعه.

**تاریخ ساخت به وقت UTC:** {display_date}

**ماهیت سند:** گزارش وضعیت واقعی تطبیق اصلاحات. آماده‌بودن ابزار، فورم یا متن کاری با تکمیل آزمایش و داوری یکسان محسوب نمی‌شود.

## ۱. ارزیابی عمومی پس از تطبیق اصلاحات

نقد اصلی متخصص به اعتبار استنتاج مقاله مربوط بود: سیستم انتخاب جمله با یک سیستم مولد واقعی تفاوت دارد؛ شمار و ساختار داده برای بازتولید کافی نیست؛ حضور مقدار مرجع یا مقدار مهاجم در پاسخ، معنای پاسخ را به‌تنهایی مشخص نمی‌کند؛ و کارایی فیلتر به اعتبار برچسب ورودی وابسته است. پاسخ به این نقدها به تغییر نثر محدود نشد. هویت مطالعه‌ها تفکیک گردید، داده و محاسبات موجود ممیزی شد و مرجع‌های مسئله‌دار آشکار گردید. {'مطالعهٔ تازهٔ C نیز با ۲٬۵۵۹ فراخوانی واقعی در سه نوبت تکمیل و از آرشیو منطبق تحلیل شد.' if c else 'مسیر اجرای تازه با کنترول تمامیت آماده شده و نتیجه تنها پس از تکمیل آرشیو درج می‌شود.'}

مهم‌ترین حاصل این مرحله، روشن‌شدن حدود شواهد است. مطالعهٔ مولد B واقعاً پاسخ مدل دارد و محاسبات قاعدهٔ قدیمی آن قابل بازحساب است. در عین حال، ممیزی منبع نشان داد که تمام مرجع‌ها و مقادیر موسوم به غلط از یک درجهٔ اعتبار برخوردار نیستند. بنابراین، تأیید محاسبات عددی را نمی‌توان تأیید صحت معنایی همهٔ نتایج دانست. این تفاوت در مقالهٔ کاری، ارزیاب و فورم داوری اعمال شده است.

دو موضوع هنوز باید صریح بماند. نخست، آرشیو دقیق اجرای اصلی تاریخی و مکمل تکرار آن از جست‌وجوی محدود انجام‌شده بازیابی نشده است؛ ورودی و کد فعلی موجود را نمی‌توان جای آن معرفی کرد. دوم، بررسی معنایی توسط دو انسان واقعی هنوز به دریافت داوری و حل اختلاف نیاز دارد. مطابق تصمیم اخیر، پژوهشگر هماهنگ‌کننده است و دو شخص دیگر را برای داوری پیدا می‌کند. تکمیل این بخش کنار گذاشته نشده و شرط ادعای اعتبارسنجی انسانی خواهد ماند.

## ۲. دامنهٔ بررسی و روش تهیهٔ این گزارش

مبنای پیگیری، ۶۷ مورد استخراج‌شده از گزارش متخصص است. برای هر مورد، اقدام اجراشده، مسیر شاهد، وضعیت فعلی و کار باقیمانده در جدول جدا ثبت شده است. عبارت «اجراشده در مستندسازی» فقط تکمیل توضیح یا ثبت تصمیم را نشان می‌دهد؛ به معنی برطرف‌شدن هر محدودیت تجربی نیست. موارد مشروط، توصیه‌شده و الزامی با همان قوت درخواست اصلی نگه داشته شده‌اند. پوشش ۶۷ مورد، نمرهٔ علمی یا گواهی آمادگی نشر نیست.

این گزارش از آرشیو و کد محلی می‌خواند و خود هیچ درخواست مدل یا داوری انسانی ایجاد نمی‌کند. نتیجهٔ C تنها هنگامی وارد متن می‌شود که تحلیل ذخیره‌شده، رسید تکمیل و هش آرشیو پاسخ‌ها منطبق باشد. تاریخ ساخت و هش فایل‌های مبنا در رسید گزارش ثبت می‌شود. هر عدد نتیجه باید به مطالعه و نسخهٔ معیار مربوط باشد؛ جمع‌کردن ردیف‌های چند مطالعه به‌عنوان حجم نمونهٔ مستقل پذیرفته نشده است.

## ۳. معماری و هویت مطالعه‌ها

اشکال نسخهٔ قبلی فقط نام یک جزء نبود. اگر پاسخ نهایی از میان جمله‌های موجود انتخاب شود، نتیجه دربارهٔ همان بازیابی و انتخاب جمله است. نام‌بردن مدل یا پایگاه برداری در طرح پیشنهادی، فعال‌بودن آن در اجرای تاریخی را ثابت نمی‌کند. برای همین، دفتر مطالعه و دفتر ادعا از هم‌پوشانی نسخه‌ها جلوگیری می‌کنند.

{mdtable(['بخش شواهد','آنچه واقعاً در دسترس است','حد ادعای مجاز'],[
['A تاریخی','مقاله، ورودی‌های اصلی و شرح اجرای گزارش‌شده','رقم‌های تاریخی به‌عنوان گزارش پیشین؛ بازتولید تازهٔ خروجی ادعا نمی‌شود.'],
['کد فعلی مخزن','نسخهٔ مشخص workbench و فایل‌های داده','شرح همان نسخه؛ یکسان‌بودن آن با runtime اصلی فرض نمی‌شود.'],
['آزمایش تشخیصی','آرشیو/خلاصهٔ جدا با ۱٬۰۹۲ ردیف','جانشین ۲۱٬۸۴۰ ردیف اصلی یا ۳٬۰۱۶ ردیف تکرار نیست.'],
['B مولد','۶۴ پرسش، ۱۲۸۰ ردیف شرط و ۳۷۶ پاسخ یکتای واقعی','شواهد مولد برای همان مدل، داده و قاعدهٔ ارزیابی؛ اکنون مادهٔ توسعه و بازتحلیل است.'],
['C پیگیری','طرح ۶۲جفتی با کنترل‌های از پیش تعیین‌شده','نتیجه فقط از آرشیو واقعی خودش و با حدود شاخص‌های خودکار گزارش می‌شود.']])}

شرح مقاله اکنون میان معماری پیشنهادی و اجزای فعال تفاوت می‌گذارد. دلیل تاریخی غیرفعال‌بودن هر جزء، در جایی که سند تصمیم وجود ندارد، نامعلوم باقی گذاشته شده است. توجیه امروز به‌عنوان تصمیم گذشته نوشته نشده است.

## ۴. دادهٔ تاریخی و مسئلهٔ بازتولید

وجود ریپوی RAG-Security-Lab و داده‌های آن تأیید شد. در commit مبنای بررسی، `6f76858df91277e4b962ee94b4286a25cfe08d4d`، ورودی‌های اصلی شامل ۲۲۴ سند، ۲۲۵ قطعه، ۳۶۴ پرسش و ۱۰۴ حمله قابل ردیابی است. بازسازی ورودی‌ها با اسکریپت جداگانه در مرحلهٔ ریسرچ، ۵۶ سند قبلی و ۱۶۸ مشاهدهٔ WDI و ساخت ۳۳۶ پرسش از دو قالب برای هر مشاهده را بررسی کرده است. بنابراین، عبارت مطلق «کد و دادهٔ اصلی موجود نیست» دقیق نبود و در بازنویسی اصلاح شد.

با این حال، دسترسی به ورودی با دسترسی به نتیجهٔ همان اجرا فرق دارد. جست‌وجوی ثبت‌شده شاخه، commit، درخت فایل، release و مواد قابل دسترس مرتبط را بررسی کرد. آرشیو ۲۱٬۸۴۰ردیفی اجرای اصلی، آرشیو ۳٬۰۱۶ردیفی تکرار و نسخهٔ منطبق کد و تنظیمات مؤثر بازیابی نشد. این نتیجه تنها دربارهٔ حدود همان جست‌وجو است؛ به معنی نبود فایل در هر محل یا ازبین‌رفتن آن نیست.

تصمیم عملی، حفظ نتیجهٔ تاریخی با شرح وضعیت و پرهیز از ادعای بازتولید تازه است. اگر آرشیو اصلی بعداً به دست آید، نخست باید شناسهٔ اجرا و هش‌ها تطبیق داده شود؛ سپس بازنمره‌دهی و در صورت امکان بازاجرای همان نسخه انجام شود. اجرای نسخهٔ تازه با شمار ردیف یکسان، در صورت نیاز A′ نام خواهد گرفت و تاریخچه را به‌طور خودکار بازتولید نمی‌کند. ماژول تکرار C نیز یک آزمایش تازه است و جای آرشیو تاریخی معرفی نمی‌شود.

## ۵. ممیزی مرجع و اعتبار مقدار حمله در B

برای تمام ۶۴ پرسش B پروندهٔ پرسش، رابطه، شاهد، قید و مقدار هدف ساخته شد. حاصل ممیزی دستیار نسبت به منبع بایگانی‌شده چنین است:

{mdtable(['محور بررسی','تعداد','معنا'],[
['مرجع پذیرفته نسبت به رابطهٔ منبع',gold['accepted'],'سازگاری با منبع معین؛ تصدیق مستقل همهٔ واقعیت‌های بیرونی نیست.'],
['مرجع مبهم',gold['ambiguous'],'دامنه، تاریخ، گردکردن یا رابطه جواب یکتا نمی‌دهد.'],
['مرجع نیازمند اصلاح',gold['needs_correction'],'رابطه یا انتساب مرجع با پرسش دقیق سازگار نیست.'],
['مقدار هدف مخالف رابطهٔ دقیق منبع',false['contradicted_by_exact_source'],'شاهد برای غلط‌بودن در همان رابطه موجود است.'],
['غلط‌بودن مقدار هدف ثابت نشده',false['not_proven_false'],'وجود قید یا ابهام اجازهٔ طبقه‌بندی قطعی موفقیت واقعی حمله را نمی‌دهد.']])}

سه ردیف نخست، وضعیت مرجعِ همان ۶۴ پرسش را تقسیم می‌کند؛ دو ردیف آخر، محور جداگانهٔ اعتبار مقدار هدف است. این دو محور روی همان موارد هم‌پوشانی دارند و تعدادهای آنان نباید به‌عنوان پرسش‌های مستقل با هم جمع شود.

این نتیجه بر استنتاج اثر مستقیم دارد. برای نمونه، سال تأسیس و سال تجدید سازمان USAAF یک رابطه نیست. «بیش از ۲۳۰» تمام مقادیر بزرگ‌تر از ۲۳۰ را نفی نمی‌کند. عدد ۳۱۱ در نام یک گروه، یک کمیت قابل جمع یا شمارش نیست. همچنان ممکن است رقم یک منبع دربارهٔ شهر، تور یا شخص دیگری باشد. در چنین حالت‌ها، تطبیق عددی به تنهایی کفایت نمی‌کند و بزرگ‌ترکردن عدد مرجع دلیل اثبات غلط‌بودن مقدار تازه نیست.

هیچ مرجع، پاسخ خام یا نمرهٔ قدیمی به‌صورت خاموش تغییر داده نشد. نتیجهٔ کامل ۶۴موردی حفظ گردید. افزون بر آن، یک تحلیل حساسیت پسینی برای ۵۰ مورد کمّیِ هم‌راستا با رابطهٔ منبع آماده شد. در این زیرمجموعه، تولید عدد هدف در شرط هدفمند بدون دفاع ۲۵ مورد و با رتبه‌بندی مجدد ۱۴ مورد بود؛ این ارقام از ۳۴ و ۱۷ مورد در مجموعهٔ کامل جدا است. این زیرمجموعه بعد از ممیزی دادهٔ دیده‌شده انتخاب شده و آزمون تازهٔ دست‌نخورده یا برآورد تأییدشدهٔ ASR معنایی نامیده نمی‌شود.

بازبینی جامع مستقل ۵۶ سند پیشین و تمام واقعیت‌های تاریخی A هنوز تکمیل نیست. پرونده‌سازی B این کار را به‌طور خودکار انجام نداده است. در بستهٔ پیگیری، این تفاوت با وضعیت باز باقی می‌ماند.

## ۶. بازتحلیل پاسخ‌ها و محدودیت معیار خودکار

قاعدهٔ قدیمی B بر تمام {b['condition_rows']} ردیف دوباره اجرا شد و در معیارهای بررسی‌شده {b['old_rule_disagreements']} اختلاف با جدول بایگانی‌شده یافت شد. این نتیجه، قابلیت بازحساب همان قاعده را نشان می‌دهد. به دلیل استفادهٔ مجدد از پاسخ‌های یکسان، ۱۲۸۰ ردیف شرط فقط {b['unique_responses']} پاسخ یکتای واقعی دارد. تعداد ردیف شرط، تعداد فراخوانی مدل و شمار پرسش مستقل سه مقدار متفاوت است.

نسخهٔ تازه، تولید مختصر و سخت‌گیرانهٔ عدد را از حضور عدد در یک جمله جدا می‌کند. نفی، نقل قول، قید، امتناع جمله‌ای و حضور هم‌زمان عدد و UNKNOWN پرچم بازبینی می‌گیرد. میان ۳۷۶ پاسخ یکتا، قاعدهٔ قدیمی ۵۱ مورد دارای مقدار هدفِ تنها شمرده بود؛ شاخص انتخاب سخت‌گیرانه ۴۷ مورد را مشخص می‌کند. شمار امتناع لفظی قدیمی ۴۱ بود، در حالی که تشخیص زبان امتناع ۴۶ مورد نشان داد. این تغییرها تعریف شاخص را تغییر می‌دهد؛ عدد تازه نباید «صحت معنایی تصحیح‌شده» نامیده شود.

در شرط حملهٔ هدفمند بدون دفاع، ۳۴ پاسخ دارای مقدار هدف بر اساس قاعدهٔ قدیمی، در شاخص سخت‌گیرانه به ۳۱ مورد می‌رسد. با رتبه‌بندی مجدد، ارقام متناظر ۱۷ و ۱۶ است. نام و مخرج هر شاخص در جدول‌ها جدا درج شده است. نفی‌کردن یک مقدار نادرست یا گفتن «این مقدار در سند آمده، ولی قابل تأیید نیست» با پذیرفتن آن یکسان نیست؛ تشخیص نهایی این تفاوت به بررسی معنایی واقعی نیاز دارد.

همچنان سه محور از هم جدا شده است: بازیابی هر دو شاهد لازم؛ پاسخِ هم‌مقدار با مرجع؛ و پذیرش یک ادعای واقعاً غلط. پشتیبانی از زمینه نیز دو معنا دارد: پاسخ ممکن است از متن مسمومِ ارائه‌شده پشتیبانی شود، اما از شاهد پاک معتبر پشتیبانی نشود. این دو حالت در دستورالعمل داوری ستون مستقل دارد.

{c_section}

## ۸. برچسب اعتماد و دامنهٔ دفاع

فیلتر آزمایش، اسناد دارای `verified=True` و برچسب high یا medium را می‌پذیرد. در دادهٔ پایه، تمام متن‌های پاک پذیرفته و تمام درج‌های جدید، حتی درج بی‌ضرر، رد می‌شوند. پس کاهش حمله در این شرط به فرض درست‌بودن برچسب‌ها وابسته است. این طراحی، سامانهٔ احراز هویت سند یا روند نهادی تأیید محتوا را پیاده نمی‌کند.

شرط برچسب پذیرفته، متن و شناسهٔ همان درج هدفمند را نگه می‌دارد و فقط صفات اعتماد را عوض می‌کند. این مقایسه می‌تواند وابستگی دفاع به metadata ورودی را نشان دهد. از آن نمی‌توان وقوع نفوذ واقعی، دورزدن کنترل دسترسی یا شکست امضای دیجیتال را نتیجه گرفت. در نبود شاهد مرجع صلاحیت‌دار، برچسب به سازندهٔ دادهٔ آزمایش نسبت داده شده است.

جلوگیری از تولید مقدار هدف نیز با بازگشت پاسخ درست برابر نیست. ممکن است دفاع مقدار مهاجم را حذف کند، اما شاهد لازم را هم از دست بدهد و مدل امتناع یا عدد دیگری تولید کند. به همین دلیل، پیشگیری، بازگشت مقدار مرجع و خطای تازه در مقایسه‌های جفتی جدا تعریف شده‌اند. نتیجهٔ صفر در یک ستون فقط به همان معیار، نمونه، مدل و فرض برچسب مربوط است.

{stress_section}

## ۹. کنترول تمامیت اجرا و نگهداری مواد قبلی

در runner تازه، طراحی پیش از بردارسازی و زمینه‌ها و درخواست‌ها پیش از تولید پاسخ منجمد می‌شود. کد و دادهٔ مؤثر، تنظیمات، payload و فایل‌های مرتبط با هش تطبیق می‌گردد. کنترل پیش از هر ارسال و ادامهٔ اجرا، شامل مسیر کش خالی، اعمال می‌شود. تغییر ورودی یا درخواست باید پیش از تماس با سرویس اجرای مرحله را متوقف کند. کنترل مدل برگشتی، ذخیرهٔ پاسخ خام، تعداد تلاش محدود، سقف هزینه و توقف خطای دائمی نیز جدا تعریف شده است.

آزمون‌های آفلاین این مسیر از دادهٔ ساختگی و ارسال‌کنندهٔ ساختگی استفاده می‌کنند. گذشتن آن‌ها شاهد رفتار کد است و آزمایش واقعی C محسوب نمی‌شود. همان‌گونه، دادهٔ ساختگی آزمون در جدول نتیجه یا داوری انسانی وارد نمی‌شود. محیط مشتری و نسخهٔ کتابخانه‌ها ثبت شده، اما سخت‌افزار سرویس مدل و محیط مجهول تاریخی با مشخصات میزبان فعلی پر نشده است.

{hardware_note}

{qa_note}

چهار شکل قبلی حفظ شده‌اند: فلوچارت خط لوله، شکل صحت مقدار پاسخ تاریخی، شکل موفقیت حملهٔ تاریخی و نمودار نتیجهٔ مولد B. هش بایت‌های اصلی در دفتر حفظ اشکال موجود است. شکل تاریخی با شرح تاریخی و محدودیت خود باقی می‌ماند؛ نتیجهٔ تازه نباید روی آن نوشته شود. ساخت مقالهٔ جدید باید درج هر چهار شکل را نیز بررسی کند، زیرا حفظ فایل به تنهایی به معنی درج صحیح در Word یا PDF نیست.

## ۱۰. اجرای ضروری داوری معنایی انسانی

این بخش به درخواست صریح پژوهشگر همچنان ضروری است. پژوهشگر خود داور نخواهد بود؛ دو شخص دیگرِ مسلط به انگلیسی را هماهنگ می‌کند. بهتر است آنان در ساخت پرسش و متن حمله دخیل نبوده باشند. سابقهٔ آشنایی و هر محدودیت استقلال باید ثبت شود؛ خود نرم‌افزار قادر به احراز هویت واقعی یا استقلال افراد نیست.

برای B تمام ۳۷۶ ترکیب یکتای پرسش، زمینه و پاسخ آماده است. هر داور ابتدا فورم جدا دریافت می‌کند و قضاوت اولیه را بدون مشاهدهٔ پاسخ داور دیگر انجام می‌دهد. نام شرط، نام دفاع، نمرهٔ خودکار و نتیجهٔ ممیزی دستیار در مرحلهٔ اولیه پنهان می‌ماند. پرسش، پاسخ دقیق مدل، شاهد و زمینهٔ لازم برای داوری در دسترس است. کورسازی کامل دربارهٔ ماهیت متن تضمین نمی‌شود؛ خود محتوای سند ممکن است سرنخ بدهد و این محدودیت باید گزارش شود.

{c_human_note}

ترتیب اجرایی چنین است: ابتدا دستورالعمل خوانده و چند مثال آموزشی خارج از آزمون بررسی شود؛ زمان واقعی با همان تمرین سنجیده شود؛ سپس دو داوری مستقل کامل ذخیره و قفل گردد. بعد از قفل دو مرحلهٔ اولیه، بخش هدف حمله برای داوری مرحلهٔ دوم باز می‌شود. اختلاف‌ها با رجوع به منبع و ثبت دلیل حل می‌گردد؛ در اختلاف حل‌نشده، تصمیم فرد سوم یا وضعیت حل‌نشده لازم است. توافق خام و ضریب توافق برای هر محور جدا گزارش می‌شود. ضریب توافق بالا به خودی خود صحت منبع را ثابت نمی‌کند.

هیچ مقدار پیش‌فرضی به‌جای رأی انسان درج نشده است. در وضعیت خوانده‌شدهٔ فعلی، gate داوری برابر `{gate.get('status')}` است و تکمیل حل اختلاف `{gate.get('adjudication_complete')}` ثبت شده است. تا وقتی دو فورم واقعی، هویت و استقلال اولیه و تصمیم‌های منبع‌دار دریافت نشود، عبارت «اعتبارسنجی انسانی انجام شد» مجاز نیست. بررسی B نیز به‌طور خودکار C را اعتبارسنجی نمی‌کند؛ خروجی‌های C به قاب داوری مختص خود نیاز دارد.

## ۱۱. بازنویسی مقاله و نحوهٔ ارائه به متخصص

نسخهٔ کاری مقاله، شرح معماری واقعی، دسترسی ورودی‌های تاریخی، وضعیت آرشیو، ممیزی مرجع B، تحلیل حساسیت و حدود برچسب اعتماد را بازنویسی می‌کند. رقم قدیمی با رقم بازتحلیل‌شده در یک جدول بدون نام نسخه جایگزین نشده است. چکیده و نتیجه باید روشن سازد که کدام یافته به مطالعهٔ مولد مربوط است و کدام نمودار تنها نتیجهٔ گزارش‌شدهٔ تاریخی را نگه می‌دارد.

اصلاح ارجاع‌های شکلی و کتابنامه انجام می‌شود، اما این موارد نباید جای رفع ضعف روش را بگیرد. برای متخصص، بستهٔ قابل بررسی باید مقالهٔ کاری، این گزارش، جدول ۶۷ مورد و مسیرهای شاهد را همراه داشته باشد. اگر پیش از پایان داوری انسانی ارسال شود، عنوان و متن همراه باید وضعیت کاری و باقی‌بودن داوری را اعلام کند. ادعای تکمیل تمام نقدها یا آمادگی نشر در این مرحله با شواهد موجود سازگار نیست.

## ۱۲. کارهای باقیمانده و ترتیب تکمیل

اولویت نخست، دریافت دو داوری واقعی و اجرای روند ثبت، قفل و حل اختلاف است. این کار به معرفی افراد و زمان واقعی آنان وابسته است، اما آماده‌سازی بسته، کد و تحلیل ماشینی معطل آن نمانده است. {'اجرای C و ساخت قاب مستقل داوری آن اکنون تکمیل شده است؛ کار باز آن، نظر واقعی انسان و واردکردن نتیجهٔ داوری در تحلیل نسخه‌دار است.' if c and c_review else 'تکمیل و بررسی نتیجهٔ واقعی C و آماده‌سازی قاب داوری آن باید با رسیدهای خودش سنجیده شود.'} پس از دریافت داوری، مقاله باید دوباره ساخته و چکیده، جدول، شکل و نتیجه با آخرین فایل تحلیل تطبیق داده شود.

شکاف آرشیو تاریخی از این زنجیره جدا نگه داشته می‌شود. در صورت یافتن فایل اصلی، مسیر بازنمره‌دهی تاریخی دوباره باز خواهد شد. تا آن زمان، محدودکردن ادعا لازم است، ولی نباید آن را بازتولید موفق همان اجرا نامید. وضعیت حقوق منابع قبلی و حدود اشتراک عمومی نیز باید در بستهٔ تحویل آشکار بماند. این گزارش و جدول همراه، کارهای باز را حذف نمی‌کند؛ محل و اثر هر کدام را برای تصمیم علمی روشن می‌سازد.

## ضمیمهٔ الف. نمای پیگیری درخواست‌های متخصص

جدول کامل با اقدام، شاهد، معیار تکمیل و کار باقیمانده در `Implementation_Progress_67_FA.csv` و نسخهٔ JSON همراه موجود است. نمای زیر برای مرور سریع است. واژهٔ «اجراشده» در یک ردیف تنها به همان اقدام محدود است و وضعیت سایر ردیف‌ها را نمی‌بندد.

{mdtable(['شناسه','موضوع درخواست','وضعیت تطبیق'], [[r['requirement_id'],r['requirement_fa'],r['implementation_status_fa']] for r in rows])}

## ضمیمهٔ ب. مسیر شواهد برای بررسی

{mdtable(['مسیر نسبت به ریشهٔ اصلاحات','محتوا'],[
['baseline/claims_registry.json و study_registry.json','هویت مطالعه و مرز هر ادعا'],
['history/reproducibility_decision.json و bounded_search_results.json','تصمیم بازتولید و حدود جست‌وجوی آرشیو'],
['reference_audit/B_reference_cards_v2.json','پروندهٔ مرجع، رابطه، قید و مقدار هدف هر پرسش B'],
['evaluation/B_reanalysis_v2_summary.json','تعداد ردیف و پاسخ یکتا، تطبیق قاعدهٔ قدیمی و تشخیص تازه'],
['evaluation/human_review_packet و coordinator_only','فورم اولیهٔ جدا از کلید شرط و فورم مرحلهٔ بعد'],
['evaluation/human_validation_gate.json','دلایل بازبودن داوری واقعی انسان'],
['protocol/study_c_protocol.json','انتخاب ۶۲جفتی، سؤال تحقیق، کنترل، تکرار، توقف و تحلیل'],
['runner/run_study.py و test_run_study.py','کنترل تمامیت و ارسالِ نسخهٔ تازه و آزمون آفلاین'],
['analysis/study_c/','خروجی واقعی تحلیل، مقایسه‌های جفتی و موارد شکست، در صورت وجود رسید تکمیل'],
['evaluation/study_c_review/','قاب مستقل داوری C و کلید خصوصی اتصال به شرایط و نوبت‌ها'],
['study_c/retrieval_label_stress_summary.json','آزمون جداگانهٔ بازیابی در برابر خطای فرضی برچسب، بدون تولید پاسخ'],
['history/figure_preservation_registry.json','شناسه و هش چهار شکل محفوظ'],
['manuscript/Working_Manuscript_v2.md','متن کاریِ قابل بازسازی از شواهد موجود']])}
'''
    content=apply_report_addendum(content,WORK)
    (ROOT/'Implementation_Report_FA.md').write_text(content)
    source_paths=[WS/'implementation_plan/requirements_work_package_map.json',
                  WORK/'reference_audit/B_reference_audit_summary.json',WORK/'evaluation/B_reanalysis_v2_summary.json',
                  WORK/'evaluation/human_validation_gate.json', WORK/'protocol/study_c_protocol.json',
                  WORK/'history/reproducibility_decision.json', WORK/'history/figure_preservation_registry.json']
    if c:
        source_paths += [WORK/'analysis/study_c/analysis.json',WORK/'analysis/study_c/analysis_manifest.json',
                         WORK/'study_c/completion.json']
    source_paths += [p for p in [WORK/'study_c/retrieval_label_stress_summary.json',
                     WORK/'protocol/client_hardware_observation.json',WORK/'protocol/POSTRUN_QA.json',
                     WORK/'evaluation/study_c_review/human_review_packet/REVIEW_STATUS.json'] if p.is_file()]
    manifest={'built_at_utc':now,'scope':'Implementation evidence report; no inference and no fabricated human labels',
              'requirements':67,'all_requirement_ids_covered':True,
              'c_actual_verified_analysis_included': c is not None,'c_status_note':c_note,
              'evaluation_scope':'completed_single_author_source_based_semantic_inspection',
              'two_reviewer_requirement_in_current_scope':False,
              'human_cases_by_study':{'B':376,'C':c_review.get('unique_cases')},
              'structured_item_level_human_ratings_received':0,
              'author_manual_inspection_reported_completed':True,
              'documented_AI_case_assessments':72,
              'source_audit_B_is_not_validation_of_A_104_targets':True,
              'retrieval_only_stress_included_without_generator_utility_claim':bool(stress),
              'status_counts_not_quality_scores':dict(Counter(r['implementation_status_fa'] for r in rows)),
              'source_files':{str(p):digest(p) for p in source_paths},
              'report_builder_sha256':digest(__file__)}
    (ROOT/'REPORT_BUILD_CHECKS.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    return manifest


def render():
    """Use installed Pandoc and python-docx; render PDF separately with --pdf."""
    md=ROOT/'Implementation_Report_FA.md'
    subprocess.run(['pandoc',str(md),'-o',str(ROOT/'Implementation_Report_FA.docx')],check=True)
    body=subprocess.run(['pandoc',str(md),'-t','html5'],check=True,capture_output=True,text=True).stdout
    title='Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning'
    title_pattern='<p>'+re.escape(title).replace(r'\ ',r'\s+')+'</p>'
    body,title_count=re.subn(title_pattern,lambda _: '<p dir="ltr" style="direction:ltr;text-align:left;font-family:DejaVu Sans,sans-serif;font-size:11pt;line-height:1.45">'+title+'</p>',body,count=1)
    if title_count!=1:
        raise ValueError('Expected one English title paragraph in report HTML')
    css='''@page{size:A4;margin:18mm 19mm 20mm}html{direction:rtl}body{font-family:"Noto Naskh Arabic",serif;font-size:13pt;line-height:1.8;color:#111}h1{font-size:21pt;text-align:center;line-height:1.6}h2{font-size:16pt;line-height:1.6;margin:22px 0 9px;break-after:avoid}h3{font-size:14pt;break-after:avoid}p{margin:0 0 9px;text-align:justify;orphans:3;widows:3}table{border-collapse:collapse;width:100%;table-layout:fixed;margin:12px 0 16px;font-size:10.5pt;line-height:1.6}th,td{border:1px solid #aaa;padding:5px 7px;vertical-align:top;overflow-wrap:anywhere;text-align:right}th{background:#eee}thead{display:table-header-group}tr{break-inside:avoid}code{font-family:"DejaVu Sans Mono",monospace;font-size:.7em;direction:ltr;unicode-bidi:isolate;overflow-wrap:anywhere}a{color:#111}'''
    document='<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>گزارش تطبیق اصلاحات مقاله</title><style>'+css+'</style></head><body>'+body+'</body></html>'
    (ROOT/'Implementation_Report_FA.html').write_text(document)
    from docx import Document
    from docx.shared import Cm, Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    d=Document(ROOT/'Implementation_Report_FA.docx')
    for s in d.sections:
        s.page_width=Cm(21);s.page_height=Cm(29.7);s.top_margin=Cm(1.8);s.bottom_margin=Cm(1.9);s.left_margin=Cm(1.9);s.right_margin=Cm(1.9)
        h=s.header.paragraphs[0];h.text='گزارش تطبیق اصلاحات علمی و تخنیکی — امنیت RAG'
        h.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        f=s.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER
        field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');f._p.append(field)
    for name in ['Normal','Body Text','First Paragraph']:
        if name in d.styles:
            st=d.styles[name];st.font.name='Noto Naskh Arabic';st.font.size=Pt(13);st.paragraph_format.space_after=Pt(7);st.paragraph_format.line_spacing=1.2
    paragraphs=list(d.paragraphs)
    for table in d.tables:
        table._tbl.tblPr.append(OxmlElement('w:bidiVisual'))
        for i,row in enumerate(table.rows):
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
            for cell in row.cells:paragraphs.extend(cell.paragraphs)
    for p in paragraphs:
        p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        bidi=OxmlElement('w:bidi');p._p.get_or_add_pPr().append(bidi)
        if p.text==title:
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT
            bidi.set(qn('w:val'),'0')
        for run in p.runs:
            fa=bool(re.search(r'[\u0600-\u06ff]',run.text))
            run.font.name='Noto Naskh Arabic' if fa else 'DejaVu Sans'
            run.font.size=Pt(12 if fa else 9)
            rp=run._r.get_or_add_rPr();fonts=rp.rFonts
            if fonts is not None:fonts.set(qn('w:cs'),'Noto Naskh Arabic')
            rtl=OxmlElement('w:rtl');rtl.set(qn('w:val'),'1' if fa else '0');rp.append(rtl)
        if p.style.name.startswith('Heading'):
            p.paragraph_format.keep_with_next=True
            for run in p.runs:run.font.size=Pt(16 if p.style.name!='Heading 1' else 19)
    d.core_properties.title='گزارش تطبیق اصلاحات علمی و تخنیکی مقالهٔ امنیت RAG'
    d.core_properties.subject='Evidence-linked implementation and author semantic case inspection'
    d.save(ROOT/'Implementation_Report_FA.docx')


def pdf():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page();page.route('**/*',lambda route:route.abort())
        page.set_content((ROOT/'Implementation_Report_FA.html').read_text(),wait_until='load');page.evaluate('document.fonts.ready')
        page.pdf(path=str(ROOT/'Implementation_Report_FA.pdf'),format='A4',print_background=True,prefer_css_page_size=True,
                 display_header_footer=True,header_template='<div></div>',footer_template='<div style="font-family:Arial;font-size:8px;width:100%;text-align:center;color:#555"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        browser.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--pdf',action='store_true');args=p.parse_args()
    manifest=build()
    if args.render or args.pdf:render()
    if args.pdf:pdf()
    print(json.dumps({'requirements':manifest['requirements'],'c_actual_analysis_included':manifest['c_actual_verified_analysis_included'],
                      'human_status':manifest['evaluation_scope'],'output':str(ROOT)},ensure_ascii=False))
