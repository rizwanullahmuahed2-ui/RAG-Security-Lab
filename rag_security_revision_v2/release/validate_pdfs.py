"""Check exported PDF text geometry using Poppler; no inference or review labels."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent


def main():
    out = ROOT / 'qa'
    out.mkdir(exist_ok=True)
    results = {}
    for name, relative in [('paper', 'manuscript/Working_Manuscript_v2.pdf'),
                           ('report', 'report/Implementation_Report_FA.pdf')]:
        pdf = WORK / relative
        xml = out / (name + '_bbox.html')
        text = out / (name + '_text.txt')
        subprocess.run(['pdftotext', '-bbox-layout', str(pdf), str(xml)], check=True)
        subprocess.run(['pdftotext', '-layout', str(pdf), str(text)], check=True)
        namespace = {'x': 'http://www.w3.org/1999/xhtml'}
        pages = ET.parse(xml).findall('.//x:page', namespace)
        outside = []
        count = 0
        for number, page in enumerate(pages, 1):
            width, height = float(page.attrib['width']), float(page.attrib['height'])
            for word in page.findall('.//x:word', namespace):
                count += 1
                box = {k: float(v) for k, v in word.attrib.items()}
                if (min(box['xMin'], box['yMin']) < -.5 or box['xMax'] > width + .5
                        or box['yMax'] > height + .5):
                    outside.append({'page': number, 'text': word.text, 'box': box})
        assert pages and not outside, outside[:3]
        contents = text.read_text()
        assert '\ufffd' not in contents
        if name == 'paper':
            assert all('Figure ' + str(n) in contents for n in range(1, 6))
            assert '37.6' in contents and ('20.9' in contents or '21.0' in contents)
        results[name] = {'path': relative, 'pages': len(pages), 'text_words': count,
                         'text_boxes_outside_page': len(outside),
                         'replacement_characters': contents.count('\ufffd'),
                         'sha256': hashlib.sha256(pdf.read_bytes()).hexdigest()}
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(),
              'tool': 'Poppler pdftotext geometry and extraction; separate visual samples',
              'status': 'passed', 'documents': results,
              'scope': 'Export legibility/geometry checks, not human semantic validation'}
    (ROOT / 'PDF_QUALITY_CHECKS.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
