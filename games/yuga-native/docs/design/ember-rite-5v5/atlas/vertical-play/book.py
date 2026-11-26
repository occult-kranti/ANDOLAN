"""Publish the complete fieldbook PDF with working citations, page labels and bookmarks.

Requires Pandoc, Chromium, Playwright and PyMuPDF. The lightweight --check option
checks the source fingerprint, bookmarks, nonempty pages and embedded map appendices.
"""

import argparse
import base64
import hashlib
import html
from pathlib import Path
import shutil
import subprocess
from urllib.parse import quote
import fitz

HERE = Path(__file__).resolve().parent
ROOT = "https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/"
REPO = HERE.parents[6]
CHAPTERS = [
    ("README.md", "Architecture and hero play"),
    ("door-register.md", "Eight courts and 27 entrances"),
    ("element-register.md", "53 registered environment elements"),
    ("hero-abilities.md", "Figures, abilities and team plays"),
    ("physics.md", "Movement, trajectories and opening clocks"),
    ("encounters.md", "Ten-player encounter scripts"),
    ("research.md", "Comparative hero and map research"),
]
PLANS = [
    ("mandala-cover-atlas.pdf", "Mandala cover plans"),
    ("companion-courts.pdf", "Six companion courts"),
]
OUT = HERE / "ember-rite-fieldbook.pdf"
CSS = """
@page{size:A4;margin:16mm 15mm 19mm}*{box-sizing:border-box}body{margin:0;font:10pt/1.42 'Noto Sans',sans-serif;color:#26372e}
h1,h2,h3{font-family:'Noto Serif',serif;line-height:1.18;color:#204234;break-after:avoid}
h1{font-size:25pt;letter-spacing:-.045em;margin:1mm 0 4mm}h2{font-size:15.2pt;margin:6mm 0 2mm;border-top:.45pt solid #bbb9a5;padding-top:2.6mm}h3{font-size:12pt;margin:4mm 0 2mm}p{margin:1.8mm 0 2.8mm;orphans:3;widows:3}
a{color:#245c4b;text-decoration:underline;text-decoration-thickness:.45pt}em{color:#465d51}
table{width:100%;border-collapse:collapse;font-size:8.1pt;line-height:1.32;margin:3mm 0;table-layout:auto}
th{text-align:left;color:#254236;background:#e7e9db}td,th{padding:1.35mm 1.5mm;border:.4pt solid #c1c7b7;overflow-wrap:anywhere;vertical-align:top}thead{display:table-header-group}tr{break-inside:avoid}th p,td p{margin:0}
code{font-size:8pt;overflow-wrap:anywhere}pre{background:#f0f0e8;padding:2mm;white-space:pre-wrap}ul,ol{padding-left:5mm}li{margin:.7mm 0}
.art{width:100%;height:53mm;object-fit:cover;object-position:50% 57%;display:block;margin:1mm 0 6mm}.head{font-size:8pt;letter-spacing:.1em;font-weight:bold;color:#8c462b;margin-bottom:3mm}
"""


def fingerprint():
    h = hashlib.sha256()
    for path in [
        Path(__file__),
        HERE / "district-banner.webp",
        *((HERE / f) for f, _ in [*CHAPTERS, *PLANS]),
        HERE / "mandala-staging.svg",
    ]:
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def make():
    from playwright.sync_api import sync_playwright

    combined = fitz.open()
    toc = []

    def insert(data, title):
        with fitz.open(stream=data, filetype="pdf") as source:
            toc.append([1, title, len(combined) + 1])
            start = len(combined)
            combined.insert_pdf(source)
            for item in source.get_toc():
                if item[0] == 1 and item[1] != title:
                    toc.append([2, item[1], start + item[2]])

    with sync_playwright() as p:
        b = p.chromium.launch(
            executable_path=shutil.which("chromium"), args=["--no-sandbox"]
        )
        page = b.new_page()
        art = base64.b64encode((HERE / "district-banner.webp").read_bytes()).decode()
        for idx, (file, title) in enumerate(CHAPTERS):
            fragment = subprocess.run(
                ["pandoc", "--from=gfm", "--to=html5", str(HERE / file)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            tab = html.escape(title)
            doc = (
                f'<!doctype html><meta charset="utf-8"><style>{CSS}</style><title>{tab}</title>'
                f'<p class="head">YUGA &nbsp; / &nbsp; EMBER RITE &nbsp; / &nbsp; {idx + 1:02d}</p>'
                + (
                    f'<img class="art" alt="Mandala Rift concept study" src="data:image/webp;base64,{art}">'
                    if idx == 0
                    else ""
                )
                + fragment
            )
            page.set_content(doc)
            # link resolution is relative to the real checked-in chapter; it remains usable offline once online again.
            base = ROOT + quote((HERE / file).relative_to(REPO).as_posix())
            page.evaluate(
                """base=>document.querySelectorAll('a[href]').forEach(a=>{
                const raw=a.getAttribute('href');if(!/^[a-z]+:/i.test(raw))a.href=new URL(raw,base).href;
            })""",
                base,
            )
            insert(page.pdf(print_background=True, prefer_css_page_size=True), title)
        page.set_content(
            '<meta charset="utf-8"><style>@page{size:A4;margin:14mm}body{font:14px Georgia;color:#354f40}svg{width:100%}</style><h1>Mandala preparation floor</h1>'
            + (HERE / "mandala-staging.svg").read_text()
        )
        insert(
            page.pdf(print_background=True, prefer_css_page_size=True),
            "Preparation floor and four lofts",
        )
        b.close()
    for file, title in PLANS:
        insert((HERE / file).read_bytes(), title)
    combined.set_toc(toc)
    combined.set_metadata(
        dict(
            title="Ember Rite | Architecture and vertical hero play",
            author="YUGA map design panel",
            keywords=fingerprint(),
        )
    )
    combined.set_page_labels(
        [{"startpage": 0, "prefix": "", "style": "D", "firstpagenum": 1}]
    )
    combined.save(OUT, garbage=4, deflate=True)
    combined.close()


def verify():
    with fitz.open(OUT) as pdf:
        assert pdf.metadata["keywords"] == fingerprint(), "Stale fieldbook PDF"
        sections = [item for item in pdf.get_toc() if item[0] == 1]
        assert len(sections) == len(CHAPTERS) + len(PLANS) + 1
        assert len(pdf) >= 22 and all(len(page.get_text().strip()) > 8 for page in pdf)
        external = sum(
            bool(link.get("uri")) for page in pdf for link in page.get_links()
        )
        assert external >= 100, external
        print(
            f"{len(pdf)} pages, {len(sections)} bookmarked sections, {external} working PDF link annotations."
        )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if not args.check:
        make()
    verify()
