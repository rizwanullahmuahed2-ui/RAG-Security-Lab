"""Render the evidence-linked expert response locally; no provider calls."""
from pathlib import Path
import subprocess,re,json,hashlib
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parent
md=ROOT/'Response_to_Expert_FA.md';docx=ROOT/'Response_to_Expert_FA.docx'
subprocess.run(['pandoc',str(md),'-o',str(docx)],check=True)
d=Document(docx)
for sec in d.sections:
 sec.page_width=Cm(21);sec.page_height=Cm(29.7);sec.top_margin=Cm(1.8);sec.bottom_margin=Cm(1.8);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
for style in d.styles:
 if style.type==1:
  style.font.name='Noto Naskh Arabic';style.font.size=Pt(11.5);style.font.color.rgb=RGBColor(0,0,0)
  style.paragraph_format.line_spacing=1.3;style.paragraph_format.space_after=Pt(6)
  if style.name.startswith('Heading'):
   style.font.size=Pt(16 if style.name=='Heading 1' else 13);style.paragraph_format.keep_with_next=True
paras=list(d.paragraphs)+[p for table in d.tables for row in table.rows for cell in row.cells for p in cell.paragraphs]
for p in paras:
 fa=bool(re.search('[\u0600-\u06ff]',p.text));p.alignment=2 if fa else 0
 if fa:
  bidi=OxmlElement('w:bidi');bidi.set(qn('w:val'),'1');p._p.get_or_add_pPr().append(bidi)
 for run in p.runs:
  run.font.name='Noto Naskh Arabic';run.font.color.rgb=RGBColor(0,0,0)
  fonts=run._element.get_or_add_rPr().rFonts
  if fonts is not None:fonts.set(qn('w:cs'),'Noto Naskh Arabic')
  rtl=OxmlElement('w:rtl');rtl.set(qn('w:val'),'1'if fa else'0');run._element.get_or_add_rPr().append(rtl)
for table in d.tables:
 for i,row in enumerate(table.rows):
  if i==0:row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
  for cell in row.cells:
   for p in cell.paragraphs:
    for run in p.runs:run.font.size=Pt(10)
d.core_properties.title='پاسخ به گزارش بررسی تخنیکی مقالهٔ امنیت در سیستم‌های RAG'
d.save(docx)
body=subprocess.check_output(['pandoc',str(md),'-s','-t','html5'],text=True)
body=body.replace('<html','<html dir="rtl" lang="fa"',1)
css='''@page{size:A4;margin:18mm 20mm}body{font-family:"Noto Naskh Arabic",serif;font-size:12pt;line-height:1.62;color:#000}h1,h2,h3{color:#000;break-after:avoid}h1{font-size:20pt;line-height:1.5}h2{font-size:15pt;margin-top:18px}p{text-align:justify;margin:0 0 10px;orphans:3;widows:3}table{width:100%;border-collapse:collapse;margin:12px 0;font-size:11pt;break-inside:avoid}th,td{border:1px solid #aaa;padding:6px 8px;text-align:right}th{background:#f1f1f1}thead{display:table-header-group}tr{break-inside:avoid}a{color:#000;text-decoration:underline;overflow-wrap:anywhere}code{font-family:"DejaVu Sans Mono",monospace;font-size:.78em;direction:ltr;unicode-bidi:isolate}li{margin-bottom:8px}'''
body=body.replace('</head>','<style>'+css+'</style></head>')
(ROOT/'Response_to_Expert_FA.html').write_text(body)
print(json.dumps({'word':str(docx),'html':str(ROOT/'Response_to_Expert_FA.html'),'headings':'black'}))
