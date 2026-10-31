"""Create a concise Persian report to accompany the final manuscript."""
from pathlib import Path
import html
import json
import re

from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT=Path(__file__).resolve().parent


def fa(value):
    return str(value).translate(str.maketrans('0123456789,','۰۱۲۳۴۵۶۷۸۹٬'))


def main():
    a=json.loads((ROOT/'experiment/analysis.json').read_text())
    assert a['n_test_questions']==64 and a['unique_generation_calls']==376
    s={(r['condition'],r['defense']):r for r in a['summary']}
    false=int(s[('targeted','none')]['numeric_false_only_sum'])
    unrelated=int(s[('unrelated','none')]['numeric_false_only_sum'])
    rerank=int(s[('targeted','rerank')]['numeric_false_only_sum'])
    sections=[
        ('title','گزارش پاسخ به ملاحظات مقاله'),
        ('greeting','آمر محترم،'),
        ('body','با احترام، نسخهٔ نهایی بازنگری‌شدهٔ مقالهٔ «امنیت تولید تقویت‌شده با بازیابی در برابر آلودگی هدفمند پایگاه دانش» برای بررسی تقدیم می‌شود. چهار ملاحظهٔ مطرح‌شده به شرح زیر در مقاله اعمال شده است:'),
        ('item','۱. اجرای آزمایش با LLM واقعی: آزمایش از طریق API و با مدل ثابت GPT-4.1 mini روی ۶۴ سؤال اجرا شد. ۳۷۶ درخواست متفاوت، مبنای ۱٬۲۸۰ ردیف ارزیابی در پنج وضعیت داده و چهار حالت دفاع قرار گرفت.'),
        ('item','۲. همسویی با سؤال‌های تحقیق: جدول ۱، هر سؤال تحقیق را به مقایسهٔ آزمایشی، معیار و بخش نتیجهٔ مربوط وصل می‌کند. نتایج بخش‌های ۵.۱ تا ۵.۴ به همان ترتیب تنظیم شده‌اند.'),
        ('item','۳. آزمون خارجی و کنترل آلودگی نامرتبط: یک زیرمجموعهٔ تازه از HotpotQA پیش از مشاهدهٔ خروجی آزمون ثابت شد. کنترل نامرتبط با همان مقدار نادرست، تعداد درج و طول متن اضافه شد؛ کنترل متن درست و جعل برچسب اعتماد نیز ارزیابی شدند.'),
        ('item','۴. روشن‌سازی روش تحقیق: مراحل انتخاب داده، بازیابی، دفاع‌ها، تولید پاسخ، معیارها، مخرج نرخ‌ها، تحلیل جفتی و حدود نتیجه در بخش‌های ۳ و ۴ تشریح شده‌اند.'),
        ('body','فلوچارت و هر دو نمودار نسخهٔ اصلی بدون تغییر در تصویر حفظ شده‌اند. نمودار آزمایش جدید نیز در مقاله موجود است؛ مقاله در مجموع چهار شکل دارد.'),
        ('result',f'خلاصهٔ نتیجهٔ جدید: بدون دفاع، مقدار نادرست هدف در {fa(false)} پاسخ از ۶۴ پاسخ تولید شد؛ در کنترل نامرتبط این تعداد {fa(unrelated)} بود و با بازرتبه‌بندی به {fa(rerank)} پاسخ رسید.'),
        ('limit','حد تفسیر نتایج: نمره‌دهی فعلی بر تطبیق خودکار عدد استوار است. داوری معنایی مستقل انسانی انجام نشده و این موضوع همراه با محدودیت‌های تعمیم در بخش ۷ مقاله صریحاً بیان شده است.'),
        ('closing','پیوست: مقالهٔ نهایی به شکل PDF و Word، و پاسخ تفصیلی به چهار ملاحظه.'),
        ('closing','با احترام'),
    ]
    (ROOT/'Response_to_Supervisor_FA.md').write_text('\n\n'.join(('# ' if kind=='title' else '')+text for kind,text in sections)+'\n')
    d=Document()
    for section in d.sections:
        section.page_width=Cm(21);section.page_height=Cm(29.7)
        section.top_margin=Cm(1.8);section.bottom_margin=Cm(1.8)
        section.left_margin=Cm(2);section.right_margin=Cm(2)
    for kind,text in sections:
        p=d.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        node=OxmlElement('w:bidi');node.set(qn('w:val'),'1');p._p.get_or_add_pPr().append(node)
        p.paragraph_format.space_after=Pt(6)
        p.paragraph_format.line_spacing=1.15
        r=p.add_run(text);r.font.name='Noto Naskh Arabic';r.font.size=Pt(12 if kind!='title' else 18)
        r._r.get_or_add_rPr().rFonts.set(qn('w:cs'),'Noto Naskh Arabic')
        rtl=OxmlElement('w:rtl');rtl.set(qn('w:val'),'1');r._r.get_or_add_rPr().append(rtl)
        if kind in ['title','greeting']:r.bold=True
        if kind=='title':r.font.color.rgb=RGBColor.from_string('173F5F')
    d.core_properties.title='گزارش پاسخ به ملاحظات مقاله'
    d.save(ROOT/'Response_to_Supervisor_FA.docx')
    body=[]
    for kind,text in sections:
        escaped=html.escape(text)
        for term in ['GPT-4.1 mini','LLM','API','HotpotQA','PDF','Word']:
            escaped=escaped.replace(term,f'<bdi dir="ltr">{term}</bdi>')
        body.append(f'<h1>{escaped}</h1>' if kind=='title' else f'<p class="{kind}">{escaped}</p>')
    page='''<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8"><title>گزارش پاسخ به ملاحظات مقاله</title>
<style>@page{size:A4;margin:18mm 20mm}html{direction:rtl}body{font-family:"Noto Naskh Arabic",serif;font-size:12.3pt;line-height:1.62;color:#17212b}h1{font-size:20pt;color:#173f5f;margin:0 0 12px;border-bottom:1px solid #b6c6d1;padding-bottom:8px}p{margin:0 0 9px;text-align:justify;break-inside:avoid}.greeting{font-weight:bold}.result{background:#edf3f7;padding:8px 12px;border-right:3px solid #173f5f}.limit{font-size:11.5pt;color:#394956}.closing{margin-bottom:4px}bdi{font-family:"DejaVu Sans",sans-serif;font-size:.88em}</style><body>'''+''.join(body)+'</body></html>'
    (ROOT/'Response_to_Supervisor_FA.html').write_text(page)
    message='آمر محترم، با احترام، نسخهٔ نهایی بازنگری‌شدهٔ مقاله مطابق چهار ملاحظهٔ شما پیوست است. آزمایش با LLM واقعی، آزمون خارجی و کنترل آلودگی نامرتبط اضافه شده و سؤال‌های تحقیق و روش آزمایش همسو و روشن شده‌اند. فلوچارت و نمودارهای اصلی نیز حفظ شده‌اند. حدود ارزیابی در متن مقاله مشخص است. برای بررسی تقدیم می‌شود.\n'
    (ROOT/'Message_to_Supervisor_FA.txt').write_text(message)
    print('Persian supervisor report and suggested sending message created.')


if __name__=='__main__':main()
