"""Extract original PDF figures without redrawing or resampling their pixels."""
from pathlib import Path
import argparse
import hashlib
import json
import fitz

ROOT = Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('source_pdf',type=Path)
    args=parser.parse_args()
    document=fitz.open(args.source_pdf)
    figures=ROOT/'figures'
    figures.mkdir(exist_ok=True)
    mapping=[(5,38,'original_pipeline','Original Figure 1: historical extractive-pipeline flowchart'),
             (9,47,'original_answer_accuracy','Original Figure 2: historical answer-value accuracy'),
             (9,48,'original_attack_success','Original Figure 3: historical targeted attack success')]
    records=[]
    for page,xref,stem,description in mapping:
        assert any(item[0]==xref for item in document[page].get_images(full=True))
        item=document.extract_image(xref)
        destination=figures/(stem+'.'+item['ext'])
        destination.write_bytes(item['image'])
        original=fitz.Pixmap(document,xref)
        extracted=fitz.Pixmap(item['image'])
        assert original.width==extracted.width and original.height==extracted.height
        assert original.samples==extracted.samples
        records.append({'file':destination.name,'original_page':page+1,'pdf_image_xref':xref,
                        'original_description':description,'width_px':original.width,'height_px':original.height,
                        'image_sha256':hashlib.sha256(item['image']).hexdigest(),
                        'pixel_sha256':hashlib.sha256(original.samples).hexdigest(),
                        'pixel_identity_verified':True,'resampled':False,'redrawn':False})
    manifest={'source_pdf_name':args.source_pdf.name,'source_pdf_sha256':hashlib.sha256(args.source_pdf.read_bytes()).hexdigest(),
              'description':'Three historical figures preserved unchanged from supplied PDF; no new historical data reconstruction.',
              'figures':records}
    (figures/'original_figures_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
