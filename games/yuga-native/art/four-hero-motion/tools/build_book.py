"""Build the four-hero animator PDF from its Markdown scripts and local reference art.

Run python games/yuga-native/art/four-hero-motion/tools/build_book.py from any
directory. Requires Pillow, ReportLab, local DejaVu fonts (fontconfig) and the four
Cycles turnarounds recorded in evidence/blender-stills.json. The two passes
resolve the clickable page directory. PDF metadata uses a fixed timestamp.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate, Flowable, Frame, ListFlowable, ListItem, PageBreak,
    PageTemplate, Paragraph, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[3]
GITHUB = 'https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/'
W, H = letter
MARGIN = 44
BODY = W - 2 * MARGIN
INK = '#172829'
PAPER = '#faf8f2'
MUTED = '#535f59'
TEAL = '#185c5e'
RULE = '#c3c9bc'


@dataclass(frozen=True)
class Chapter:
    key: str
    accent: str
    release: str
    ability: str
    caption: str

    @property
    def name(self):
        return self.key.capitalize()

    @property
    def script(self):
        return ROOT / 'scripts' / (self.key + '.md')


CHAPTERS = (
    Chapter('hanuman', '#914623', 'Enhanced and classic kits · 60 fps review', 'Mountain Pulse',
            'Read the coiled tail, lift and landing as a classic descent. In enhanced Confluence the caster stays planted and the impact lands on the remote mark.'),
    Chapter('rama', '#75571b', 'Enhanced and classic kits · 60 fps review', 'Dawn Volley',
            'The board shows a left-hand bow and three arrows together. The rig holds the bow in wrist.R. Use the script for handedness and for the staggered enhanced release.'),
    Chapter('shiva', '#286167', 'Proposed kit · 30 fps authoring', 'Tandava Downbeat',
            'Follow the raised left knee to the proposed contact at F24. Carry the drum beaters through the stop while the trident keeps its upright line.'),
    Chapter('krishna', '#536330', 'Proposed kit · 30 fps authoring', 'Govardhan Canopy',
            'Read the left-hand flute handoff before the raised finger. The proposed shield grant is F30. Judge the canopy width across all three panels.'),
)


def register_fonts():
    fonts = [
        ('Body', 'DejaVu Sans', 'Book'), ('BodyBold', 'DejaVu Sans', 'Bold'),
        ('BodyItalic', 'DejaVu Sans', 'Oblique'), ('BodyBoldItalic', 'DejaVu Sans', 'Bold Oblique'),
        ('Display', 'DejaVu Serif', 'Book'), ('Mono', 'DejaVu Sans Mono', 'Book'),
    ]
    for name, family, style in fonts:
        file = subprocess.check_output(
            ['fc-match', '-f', '%{file}', f'{family}:style={style}'], text=True)
        pdfmetrics.registerFont(TTFont(name, file))
    pdfmetrics.registerFontFamily('Body', normal='Body', bold='BodyBold', italic='BodyItalic',
                                  boldItalic='BodyBoldItalic')


def style(name, font, size, leading, **options):
    return ParagraphStyle(name, fontName=font, fontSize=size, leading=leading,
                          textColor=HexColor(INK), allowWidows=0, allowOrphans=0, **options)


def source_url(path):
    return GITHUB + quote(path.resolve().relative_to(REPO).as_posix(), safe='/')


TOKENS = re.compile(r'(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*|\*[^*]+\*)')


def inline(line, source):
    values = []
    for part in TOKENS.split(line):
        if part.startswith('[') and '](' in part and part.endswith(')'):
            label, href = part[1:-1].split('](', 1)
            if not href.startswith(('https://', 'http://')):
                file, _, anchor = href.partition('#')
                href = source_url(source.parent / file) + ('#' + anchor if anchor else '')
            values.append(f'<a href={quoteattr(href)} color="{TEAL}"><u>{inline(label, source)}</u></a>')
        elif part.startswith('`') and part.endswith('`'):
            values.append(f'<font name="Mono">{escape(part[1:-1])}</font>')
        elif part.startswith('**') and part.endswith('**'):
            values.append('<b>' + escape(part[2:-2]) + '</b>')
        elif part.startswith('*') and part.endswith('*'):
            values.append('<i>' + escape(part[1:-1]) + '</i>')
        else:
            values.append(escape(part))
    return ''.join(values)


def script_story(ch):
    source = ch.script
    lines = source.read_text().splitlines()
    styles = {
        'title': style('title', 'Display', 22, 28, spaceAfter=12, keepWithNext=1),
        'h2': style('h2', 'Display', 15, 19, spaceBefore=9, spaceAfter=5, keepWithNext=1),
        'body': style('text', 'Body', 9.1, 13.4, spaceAfter=7),
        'cell': style('cell', 'Body', 8.5, 12.2),
        'head': style('head', 'BodyBold', 8.3, 11.7),
    }
    story = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue
        elif line.startswith('#'):
            level, title = line.split(' ', 1)
            story.append(Paragraph(inline(title, source), styles['title' if level == '#' else 'h2']))
        elif line.startswith('|'):
            rows = [line]
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i])
                i += 1
            matrix = []
            for row in rows:
                vals = [cell.strip() for cell in row.strip('|').split('|')]
                if all(re.fullmatch(r':?-{3,}:?', val) for val in vals):
                    continue
                matrix.append([Paragraph(inline(val, source), styles['cell' if matrix else 'head'])
                               for val in vals])
            fractions = (0.31, 0.69) if len(matrix[0]) == 2 else (0.22, 0.37, 0.41)
            tab = Table(matrix, [BODY * f for f in fractions], repeatRows=1, hAlign='LEFT',
                        spaceBefore=2, spaceAfter=7)
            tab.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6), ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e6e7dc')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor(PAPER), HexColor('#f3f2e9')]),
                ('LINEBELOW', (0, 0), (-1, 0), 0.65, HexColor(ch.accent)),
                ('LINEBELOW', (0, 1), (-1, -1), 0.25, HexColor(RULE)),
            ]))
            story.append(tab)
        elif re.match(r'^(?:\d+\.|-) ', line):
            ordered = not line.startswith('- ')
            pattern = r'^\d+\. ' if ordered else r'^- '
            items = [line]
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append(lines[i])
                i += 1
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(re.sub(pattern, '', s), source), styles['body'])) for s in items],
                bulletType='1' if ordered else 'bullet', start='1' if ordered else 'bullet',
                leftIndent=17, bulletFontName='BodyBold', bulletFontSize=8.4,
                bulletColor=HexColor(ch.accent), bulletOffsetY=1.5))
        else:
            while i < len(lines) and lines[i].strip() and not re.match(r'^(?:#|\||-|\d+\.)', lines[i]):
                line += ' ' + lines[i].strip()
                i += 1
            story.append(Paragraph(inline(line, source), styles['body']))
    return story


@lru_cache(maxsize=None)
def art(path):
    with Image.open(path) as src:
        rgb = src.convert('RGB')
        rgb.thumbnail((1800, 1250), Image.Resampling.LANCZOS)
        encoded = BytesIO()
        rgb.save(encoded, format='JPEG', quality=87, optimize=True, subsampling=0)
        encoded.seek(0)
        return ImageReader(encoded), rgb.width / rgb.height


def write(c, s, x, y, font='Body', size=9, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(font, size)
    c.drawString(x, y, s)


def plate(c, filename, top, max_w, max_h):
    path = ROOT / 'media' / 'art' / filename
    img, ratio = art(path)
    width = min(max_w, max_h * ratio)
    height = width / ratio
    x = (BODY - width) / 2
    c.drawImage(img, x, top - height, width, height)
    c.linkURL(source_url(path), (x, top - height, x + width, top), relative=1, thickness=0)
    return top - height


def block(c, line, x, top, width, size=9.2, leading=13):
    p = Paragraph(escape(line), style('caption', 'Body', size, leading))
    _, h = p.wrap(width, 100)
    p.drawOn(c, x, top - h)
    return top - h


class ArtPage(Flowable):
    width, height = BODY, H - 100

    def __init__(self, chapter=None, page_map=None):
        super().__init__()
        self.width, self.height = BODY, H - 100
        self.ch = chapter
        self.page_map = page_map or {}

    def draw(self):
        c = self.canv
        if self.ch is None:
            write(c, 'YUGA  /  CONFLUENCE', 0, 675, 'BodyBold', 11, TEAL)
            write(c, 'The animator’s book', -2, 615, 'Display', 42)
            write(c, 'Character studies, action beats and production scripts', 0, 584, 'Body', 13)
            base = plate(c, 'ensemble.webp', 557, BODY, 297)
            write(c, 'River ghat ensemble  ·  generated concept art', 0, base-16, 'Body', 8.4, MUTED)
            y = base - 56
            for ch in CHAPTERS:
                write(c, ch.name, 0, y, 'Display', 18, ch.accent)
                write(c, ch.release, 115, y+1, 'Body', 9.3)
                c.setFont('BodyBold', 11)
                c.drawRightString(BODY-4, y+1, str(self.page_map.get(ch.key, '–')))
                c.linkRect('', ch.key, (0, y-9, BODY, y+19), relative=1, thickness=0)
                c.setStrokeColor(HexColor(RULE))
                c.line(0, y-11, BODY, y-11)
                y -= 36
            bottom = block(c, 'Select a hero to open the art plates. Each script follows its plates. Source links open the repository path or museum collection record.', 0, y+2, BODY)
            x = 0
            for caption, file in [('Watch the illustrated animatic', 'media/video/signature-animatic.mp4'),
                                  ('Open the 3D shot plan', 'tools/render/shots.json')]:
                width = pdfmetrics.stringWidth(caption, 'BodyBold', 8.4)
                write(c, caption, x, bottom-17, 'BodyBold', 8.4, TEAL)
                c.line(x, bottom-19, x+width, bottom-19)
                c.linkURL(source_url(ROOT / file), (x, bottom-21, x+width, bottom-6), relative=1, thickness=0)
                x += width + 18
        else:
            ch = self.ch
            write(c, ch.name, -2, 659, 'Display', 33, ch.accent)
            write(c, ch.release, 0, 635, 'Body', 10)
            file = ch.key + ('.png' if ch.key in ('rama', 'hanuman') else '.webp')
            end = plate(c, file, 620, BODY, 293 if ch.key == 'shiva' else 329)
            write(c, 'Model sheet  ·  generated reference', 0, end-15, 'Body', 8.4, MUTED)
            write(c, ch.ability, 0, end-42, 'Display', 17, ch.accent)
            end = plate(c, ch.key + '-beats.webp', end-51, BODY, 214 if ch.key == 'shiva' else 177)
            bottom = block(c, ch.caption, 0, end-10, BODY)
            if bottom < -2:
                raise ValueError(f'{ch.name} art caption crosses the page')
            c.linkRect('', ch.key + '-script', (0, bottom-3, BODY, end-7), relative=1, thickness=0)



class RigPlate(Flowable):
    def __init__(self, ch):
        super().__init__()
        self.ch = ch
        self.width, self.height = BODY, 298

    def draw(self):
        c, ch = self.canv, self.ch
        receipt_path = ROOT / 'evidence/blender-stills.json'
        receipt = json.loads(receipt_path.read_text())
        capture = receipt['heroes'][ch.key]
        board = ROOT / capture['output']
        if hashlib.sha256(board.read_bytes()).hexdigest() != capture['sha256']:
            raise ValueError(f'Outdated Blender capture for {ch.name}')
        img, ratio = art(board)
        c.setStrokeColor(HexColor(RULE))
        c.line(0, 292, BODY, 292)
        write(c, 'Skinned rig study', 0, 271, 'Display', 15, ch.accent)
        c.setFont('Body', 8.4)
        c.drawRightString(BODY, 272, f"Blender {receipt['blender']}   /   {receipt['renderer']}")
        height = BODY / ratio
        c.drawImage(img, 0, 261-height, BODY, height)
        c.linkURL(source_url(board), (0, 261-height, BODY, 261), relative=1, thickness=0)
        action = next(view['pose'] for view in capture['views'] if view['view'] == 'Action')
        caption = (f"Front, profile and rear show the idle pose. The fourth view samples {ch.ability} "
                   f"at {action['phase'] * 100:.1f}% of its exported clip. Blender evaluated "
                   f"{capture['evaluated_vertices']:,} mesh vertices for the capture.")
        if ch.key == 'rama':
            caption += ' This sheet and the film use the near model. The enhanced browser uses the far model.'
        bottom = block(c, caption, 0, 250-height, BODY, size=8.6, leading=12)
        x = 0
        for label, path in [('Download the skinned model', REPO / capture['source']),
                            ('Watch the 3D film', ROOT / 'media/video' / (ch.key + '.mp4')),
                            ('Inspect pose evidence', receipt_path)]:
            width = pdfmetrics.stringWidth(label, 'BodyBold', 8.4)
            write(c, label, x, bottom-14, 'BodyBold', 8.4, TEAL)
            c.linkURL(source_url(path), (x, bottom-17, x+width, bottom-4), relative=1, thickness=0)
            x += width + 18


class Book(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(str(filename), pagesize=letter, title='YUGA Confluence • The animator’s book',
                         author='YUGA art and animation team', subject='Four hero scripts and visual studies',
                         pageCompression=1)
        frame = Frame(MARGIN, 46, BODY, H-93, leftPadding=0, rightPadding=0,
                      topPadding=0, bottomPadding=0, id='body')
        self.addPageTemplates(PageTemplate('pages', [frame], onPage=self.blank, onPageEnd=self.folio))
        self.chapter = None
        self.page_map = {}
        self.next_title = False

    def blank(self, c, doc):
        c.setFillColor(HexColor(PAPER))
        c.rect(0, 0, W, H, fill=1, stroke=0)

    def folio(self, c, doc):
        c.setStrokeColor(HexColor(RULE))
        c.setLineWidth(0.5)
        c.line(MARGIN, 34, W - MARGIN, 34)
        write(c, 'YUGA   /   CHARACTER ANIMATION', MARGIN, 20, 'BodyBold', 7.3, MUTED)
        c.setFont('Body', 8.2)
        c.drawRightString(W - MARGIN, 20, f'{self.chapter.name}   /   {doc.page}' if self.chapter else str(doc.page))
        if self.chapter and doc.page != self.page_map.get(self.chapter.key):
            write(c, self.chapter.name.upper(), MARGIN, H-31, 'BodyBold', 8, self.chapter.accent)
            c.setFont('Body', 8)
            c.drawRightString(W-MARGIN, H-31, self.chapter.release)
            c.line(MARGIN, H-37, W-MARGIN, H-37)

    def afterFlowable(self, f):
        if isinstance(f, ArtPage) and f.ch:
            self.chapter = f.ch
            self.page_map[f.ch.key] = self.page
            self.canv.bookmarkPage(f.ch.key)
            self.canv.addOutlineEntry(f.ch.name, f.ch.key, level=0)
            self.next_title = True
        elif isinstance(f, Paragraph) and self.chapter and self.next_title:
            self.next_title = False
            key = self.chapter.key + '-script'
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry('Production script', key, level=1)


def render(dest, page_map):
    story = [ArtPage(page_map=page_map)]
    for ch in CHAPTERS:
        story.extend([PageBreak(), ArtPage(ch), PageBreak(), *script_story(ch), RigPlate(ch)])
    doc = Book(dest)
    doc.build(story, canvasmaker=lambda *a, **kw: Canvas(*a, **(kw | {'invariant': 1})))
    return doc.page_map


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--output', type=Path, default=ROOT / 'animator-book.pdf')
    dest = args.parse_args().output
    register_fonts()
    with TemporaryDirectory(dir=dest.resolve().parent) as tmp:
        page_map = render(Path(tmp) / 'proof.pdf', {})
        output = Path(tmp) / 'final.pdf'
        if page_map != render(output, page_map):
            raise RuntimeError('Page map changed between passes')
        output.replace(dest)
    print(f'Wrote {dest} • {dest.stat().st_size:,} bytes • chapter starts {page_map}')


if __name__ == '__main__':
    main()
