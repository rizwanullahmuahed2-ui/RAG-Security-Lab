"""Print the local research report; all browser network requests are blocked."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,
                             args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.route('**/*',lambda route:route.abort())
    page.set_content((root/'Research_Stage_Report_FA.html').read_text(),wait_until='load')
    page.evaluate('document.fonts.ready')
    page.pdf(path=str(root/'Research_Stage_Report_FA.pdf'),format='A4',print_background=True,
             prefer_css_page_size=True,display_header_footer=True,header_template='<div></div>',
             footer_template='<div style="font-family:Arial;font-size:8px;width:100%;text-align:center;color:#555"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
    browser.close()
print('Research-stage report PDF rendered.')
