"""Format the implementation plan; does not change research or experiment files."""
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

ROOT=Path(__file__).resolve().parent


def set_direction(paragraph,is_rtl):
    prop=paragraph._p.get_or_add_pPr()
    existing=prop.find(qn('w:bidi'))
    if existing is not None:prop.remove(existing)
    node=OxmlElement('w:bidi');node.set(qn('w:val'),'1' if is_rtl else '0');prop.append(node)
    paragraph.alignment=WD_ALIGN_PARAGRAPH.RIGHT if is_rtl else WD_ALIGN_PARAGRAPH.LEFT


def format_docx():
    path=ROOT/'Implementation_Plan_FA.docx';d=Document(path)
    for sec in d.sections:
        sec.page_width=Cm(21);sec.page_height=Cm(29.7)
        sec.top_margin=Cm(1.9);sec.bottom_margin=Cm(1.9)
        sec.left_margin=Cm(2);sec.right_margin=Cm(2)
        sec.header_distance=Cm(.7);sec.footer_distance=Cm(.7)
        h=sec.header.paragraphs[0];h.text='پلان اجرایی — امنیت RAG';set_direction(h,True)
        for run in h.runs:run.font.name='Noto Naskh Arabic';run.font.size=Pt(9)
        f=sec.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER
        field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');f._p.append(field)
    for name in ['Normal','Body Text','First Paragraph']:
        if name in d.styles:
            s=d.styles[name];s.font.name='Noto Naskh Arabic';s.font.size=Pt(13)
            s.paragraph_format.space_after=Pt(7);s.paragraph_format.line_spacing=1.2
    for name,size in [('Heading 1',19),('Heading 2',16),('Heading 3',14),('Heading 4',13)]:
        if name in d.styles:
            s=d.styles[name];s.font.name='Noto Naskh Arabic';s.font.size=Pt(size);s.font.bold=True
            s.font.color.rgb=RGBColor(0,0,0);s.paragraph_format.keep_with_next=True
            s.paragraph_format.space_before=Pt(12);s.paragraph_format.space_after=Pt(6)
    for p in d.paragraphs:
        text=p.text.strip()
        is_ltr=bool(re.match(r'^\[R\d+\]',text)) or bool(re.fullmatch(r'[a-f0-9]{40,64}',text))
        set_direction(p,not is_ltr)
        for run in p.runs:
            is_fa=bool(re.search(r'[\u0600-\u06ff]',run.text))
            rp=run._r.get_or_add_rPr()
            flag=OxmlElement('w:rtl');flag.set(qn('w:val'),'1' if is_fa else '0');rp.append(flag)
            if is_fa:
                run.font.name='Noto Naskh Arabic';rp.rFonts.set(qn('w:cs'),'Noto Naskh Arabic')
            elif run.text.strip():
                run.font.name='DejaVu Sans';run.font.size=Pt(10)
        if is_ltr:
            p.paragraph_format.line_spacing=1.05;p.paragraph_format.space_after=Pt(6)
            for run in p.runs:run.font.size=Pt(10)
    if 'Research Table' not in d.styles:d.styles.add_style('Research Table',WD_STYLE_TYPE.TABLE)
    for table in d.tables:
        table.style='Research Table';table.autofit=True
        bidi=OxmlElement('w:bidiVisual');table._tbl.tblPr.append(bidi)
        borders=OxmlElement('w:tblBorders')
        for edge in ['top','bottom','left','right','insideH','insideV']:
            b=OxmlElement('w:'+edge);b.set(qn('w:val'),'single');b.set(qn('w:sz'),'4');b.set(qn('w:color'),'B9B9B9');borders.append(b)
        table._tbl.tblPr.append(borders)
        for i,row in enumerate(table.rows):
            props=row._tr.get_or_add_trPr();props.append(OxmlElement('w:cantSplit'))
            if i==0:props.append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                if i==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'EEEEEE');cell._tc.get_or_add_tcPr().append(shade)
                for p in cell.paragraphs:
                    numeric=bool(re.fullmatch(r'[۰-۹0-9,./٪%+−–\-]+',p.text.strip()))
                    set_direction(p,not numeric)
                    if numeric:p.alignment=WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_after=Pt(4)
                    for run in p.runs:
                        run.font.name='Noto Naskh Arabic';run.font.size=Pt(11)
                        run._r.get_or_add_rPr().rFonts.set(qn('w:cs'),'Noto Naskh Arabic')
                        if i==0:run.bold=True
    d.core_properties.title='پلان اجرایی اصلاح و تکمیل مقالهٔ امنیت RAG'
    d.core_properties.author='RAG Security Research'
    d.core_properties.subject='Implementation plan; proposed follow-up protocol and acceptance criteria'
    d.save(path)


def build_html():
    content=(ROOT/'plan_body.html').read_text()
    css='''@page{size:A4;margin:18mm 20mm 20mm}html{direction:rtl}body{font-family:"Noto Naskh Arabic",serif;font-size:13.2pt;line-height:1.8;color:#111}h1{font-size:21pt;text-align:center;margin:0 0 20px;line-height:1.6}h2{font-size:16pt;margin:20px 0 8px;break-after:avoid;line-height:1.65}h3{font-size:14.2pt;margin:16px 0 6px;break-after:avoid}p{margin:0 0 9px;text-align:justify;orphans:3;widows:3}a{color:#111;text-decoration:underline;overflow-wrap:anywhere}code{font-family:"DejaVu Sans Mono",monospace;font-size:.72em;direction:ltr;unicode-bidi:isolate;overflow-wrap:anywhere}pre{direction:ltr;text-align:left;margin:9px 0 14px;white-space:pre-wrap;overflow-wrap:anywhere}pre code{font-size:9.3pt}strong{font-weight:700}table{border-collapse:collapse;width:100%;table-layout:fixed;margin:12px 0 16px;font-size:11.2pt;line-height:1.65}th,td{border:1px solid #aaa;padding:5px 7px;vertical-align:top;overflow-wrap:anywhere;text-align:right}th{background:#f1f1f1;font-weight:bold}thead{display:table-header-group}tr{break-inside:avoid}table:nth-of-type(2) th,table:nth-of-type(2) td{font-size:10.8pt}table:nth-of-type(2) td:nth-child(n+3){text-align:center}ul{padding-right:22px;padding-left:0}li{margin:0 0 6px;break-inside:avoid}.references{direction:ltr;text-align:left;font-family:"DejaVu Serif",serif;font-size:9.7pt;line-height:1.55}.references p{direction:ltr;text-align:left;margin-bottom:10px;break-inside:avoid}.references a{color:#222}.references code{font-size:9pt}'''
    html='<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>پلان اجرایی اصلاح مقاله</title><style>'+css+'</style></head><body>'+content+'</body></html>'
    (ROOT/'Implementation_Plan_FA.html').write_text(html)


if __name__=='__main__':
    format_docx();build_html();print('Implementation plan Word and HTML formatted.')
