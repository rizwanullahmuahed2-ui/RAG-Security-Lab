from pathlib import Path
import re
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parent


def page_field(paragraph):
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE')
    paragraph._p.append(field)


def format_english(path,short):
    doc=Document(path)
    for section in doc.sections:
        section.page_width=Cm(21);section.page_height=Cm(29.7)
        section.top_margin=Cm(2.1);section.bottom_margin=Cm(2.0)
        section.left_margin=Cm(2.0);section.right_margin=Cm(2.0)
        section.header_distance=Cm(.8);section.footer_distance=Cm(.8)
        header=section.header.paragraphs[0]
        header.text='RAG SECURITY RESEARCH  |  '+short
        for run in header.runs:
            run.font.name='Arial';run.font.size=Pt(8);run.font.color.rgb=RGBColor.from_string('556275')
        footer=section.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
        page_field(footer)
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(11)
    normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.08
    for name in ['Body Text','First Paragraph']:
        if name in doc.styles:
            doc.styles[name].font.name='Times New Roman';doc.styles[name].font.size=Pt(11)
            doc.styles[name].paragraph_format.space_after=Pt(6)
            doc.styles[name].paragraph_format.line_spacing=1.08
    for name,size in [('Title',20),('Subtitle',12),('Heading 1',15),('Heading 2',13),('Heading 3',11.5)]:
        if name in doc.styles:
            s=doc.styles[name];s.font.name='Arial';s.font.size=Pt(size)
            s.font.color.rgb=RGBColor.from_string('173F5F')
            s.paragraph_format.keep_with_next=True
            if name.startswith('Heading'):s.font.bold=True
    for table in doc.tables:
        table.autofit=True
        if 'Research Table' not in doc.styles:
            doc.styles.add_style('Research Table',WD_STYLE_TYPE.TABLE)
        table.style='Research Table'
        borders=OxmlElement('w:tblBorders')
        for edge in ['top','left','bottom','right','insideH','insideV']:
            node=OxmlElement('w:'+edge);node.set(qn('w:val'),'single');node.set(qn('w:sz'),'4');node.set(qn('w:color'),'B6C1CA');borders.append(node)
        table._tbl.tblPr.append(borders)
        for i,row in enumerate(table.rows):
            trpr=row._tr.get_or_add_trPr();cannot=OxmlElement('w:cantSplit');trpr.append(cannot)
            if i==0:
                repeat=OxmlElement('w:tblHeader');repeat.set(qn('w:val'),'true');trpr.append(repeat)
            for cell in row.cells:
                if i==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EFF5');cell._tc.get_or_add_tcPr().append(shade)
                for p in cell.paragraphs:
                    p.paragraph_format.space_after=Pt(3);p.paragraph_format.space_before=Pt(2)
                    p.paragraph_format.line_spacing=1.0
                    for r in p.runs:
                        r.font.name='Times New Roman';r.font.size=Pt(9)
                        if i==0:r.bold=True
    figure_number=0
    for paragraph in doc.paragraphs:
        if paragraph.style.name=='Image Caption':
            figure_number+=1
            if not re.match(r'^Figure \d+\.',paragraph.text):
                paragraph.runs[0].text=f'Figure {figure_number}. '+paragraph.runs[0].text
    doc.core_properties.title='Security of Retrieval-Augmented Generation Against Targeted Knowledge-Base Poisoning' if path.name=='Revised_Manuscript.docx' else 'Response to the four review comments'
    doc.core_properties.subject='Executed real-LLM external evaluation and research revision'
    doc.save(path)


def rtl(paragraph):
    paragraph.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    prop=paragraph._p.get_or_add_pPr();node=OxmlElement('w:bidi');node.set(qn('w:val'),'1');prop.append(node)


def persian_document():
    doc=Document()
    for section in doc.sections:
        section.page_width=Cm(21);section.page_height=Cm(29.7)
        section.top_margin=Cm(2);section.bottom_margin=Cm(2)
        section.left_margin=Cm(2);section.right_margin=Cm(2)
        f=section.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER;page_field(f)
    for name in ['Normal','Title','Heading 1','Heading 2']:
        s=doc.styles[name];s.font.name='Noto Naskh Arabic';s.font.size=Pt(13 if name=='Normal' else 17)
        s.element.get_or_add_rPr().append(OxmlElement('w:rtl'))
        s.paragraph_format.space_after=Pt(8)
    for line in (ROOT/'Revision_Summary_FA.md').read_text().splitlines():
        if not line.strip():continue
        if line.startswith('# '):p=doc.add_paragraph(style='Title');line=line[2:]
        elif line.startswith('## '):p=doc.add_paragraph(style='Heading 2');line=line[3:]
        else:p=doc.add_paragraph();line=line.removeprefix('- ')
        rtl(p)
        for i,part in enumerate(re.split(r'`([^`]+)`',line)):
            r=p.add_run(part)
            if i%2:
                r.font.name='DejaVu Sans Mono';r.font.size=Pt(9)
                flag=OxmlElement('w:rtl');flag.set(qn('w:val'),'0');r._r.get_or_add_rPr().append(flag)
            else:
                r.font.name='Noto Naskh Arabic';r.font.size=Pt(13)
                flag=OxmlElement('w:rtl');flag.set(qn('w:val'),'1');r._r.get_or_add_rPr().append(flag)
                fonts=r._r.get_or_add_rPr().rFonts
                fonts.set(qn('w:cs'),'Noto Naskh Arabic')
    doc.core_properties.title='گزارش بازنگری مقاله'
    doc.save(ROOT/'Revision_Summary_FA.docx')


if __name__=='__main__':
    format_english(ROOT/'Revised_Manuscript.docx','Research article')
    format_english(ROOT/'Response_to_Reviewer.docx','Response to reviewer')
    persian_document()
    print('Formatted manuscript, reviewer response, and Persian summary.')
