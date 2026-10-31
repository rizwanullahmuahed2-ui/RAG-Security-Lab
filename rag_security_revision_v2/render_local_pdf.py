"""Render self-contained local HTML to PDF with browser network blocked."""
from pathlib import Path
import argparse
from playwright.sync_api import sync_playwright


def render(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path='/usr/bin/chromium', headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage'])
        page = browser.new_page()
        page.route('**/*', lambda route: route.abort())
        page.set_content(source.read_text(), wait_until='load')
        page.add_style_tag(content='h1,h2,h3,h4,h5,h6,.title,.subtitle{color:#000 !important;-webkit-text-fill-color:#000 !important}')
        heading_colors = page.locator('h1,h2,h3,h4,h5,h6').evaluate_all(
            '(nodes) => nodes.map(node => getComputedStyle(node).color)')
        assert heading_colors and set(heading_colors) == {'rgb(0, 0, 0)'}, heading_colors
        page.evaluate('document.fonts.ready')
        page.pdf(
            path=str(output), format='A4', print_background=True,
            prefer_css_page_size=True, display_header_footer=True,
            header_template='<div></div>',
            footer_template='<div style="font-family:Arial;font-size:8px;width:100%;text-align:center;color:#555"><span class="pageNumber"></span> / <span class="totalPages"></span></div>')
        browser.close()
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('html', type=Path)
    parser.add_argument('pdf', type=Path)
    args = parser.parse_args()
    render(args.html, args.pdf)
