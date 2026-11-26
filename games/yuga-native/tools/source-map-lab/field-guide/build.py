"""Build the printable Dust II field guide from a finished local map lab.

python build.py --lab /path/to/dust2-map-lab --output dust2-field-guide.pdf
Requires Pillow and ReportLab. Uses the licensed fonts already shipped with YUGA.
"""

import argparse
import io
import json
from pathlib import Path

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

WIDTH, HEIGHT = A4
M = 42
CONTENT = WIDTH - 2 * M
GUTTER = 13
COL = (CONTENT - GUTTER) / 2
RIGHT = M + COL + GUTTER
INK = "#1c2c28"
GRAY = "#425550"
JADE = "#155846"
OCHRE = "#98592b"
LINE = "#aebdb1"
PALE = "#e8efe8"
SAND = "#f4eee0"
BRANCH = "game/yuga-hanuman-trial"
NATIVE = Path(__file__).resolve().parents[3]
BASE = f"https://github.com/occult-kranti/ANDOLAN/blob/{BRANCH}/games/yuga-native/"
RESEARCH = BASE + "docs/research/dust2-map-lab/"
TOOLS = BASE + "tools/source-map-lab/"
ATLAS = BASE + "docs/design/ember-rite-5v5/atlas/vertical-play/"
EDITION = "26 November 2026"
PAGES = 7


class Guide:
    def __init__(self, lab, output):
        self.lab = lab
        self.pdf = canvas.Canvas(
            str(output), pagesize=A4, pageCompression=1, invariant=1
        )
        self.pdf.setTitle("Dust II, rebuilt | YUGA map field guide")
        self.pdf.setAuthor("YUGA level design research, ANDOLAN")
        self.pdf.setCreator("YUGA map field guide builder")
        self.pdf.setDateFormatter(lambda *_: "D:20261126000000Z")
        self.pdf.setSubject(
            "CS:GO Source 1, an editable Nexuiz remake and a measured ground-material change"
        )
        fonts = NATIVE / "assets" / "fonts"
        for nick, file in [
            ("Serif", "NotoSerif-Regular.ttf"),
            ("Sans", "NotoSans-Regular.ttf"),
        ]:
            pdfmetrics.registerFont(TTFont(nick, str(fonts / file)))
        self.page_no = 0

    def evidence(self, filename):
        return json.loads((self.lab / "evidence" / filename).read_text())

    def text(self, x, y, value, size=11, font="Sans", color=INK, align="left"):
        c = self.pdf
        c.setFillColor(colors.HexColor(color))
        c.setFont(font, size)
        getattr(
            c,
            {
                "left": "drawString",
                "right": "drawRightString",
                "center": "drawCentredString",
            }[align],
        )(x, HEIGHT - y, str(value))

    def para(self, x, y, width, value, size=11, leading=16, color=INK):
        for line in simpleSplit(value, "Sans", size, width):
            self.text(x, y, line, size, color=color)
            y += leading
        return y

    def rule(self, x, y, x2, color=LINE, weight=0.55):
        self.pdf.setStrokeColor(colors.HexColor(color))
        self.pdf.setLineWidth(weight)
        self.pdf.line(x, HEIGHT - y, x2, HEIGHT - y)

    def fill(self, x, y, w, h, color):
        self.pdf.setFillColor(colors.HexColor(color))
        self.pdf.rect(x, HEIGHT - y - h, w, h, stroke=0, fill=1)

    def link(self, x, y, label, url, size=9.15, internal=False):
        self.text(x, y, label, size, color=JADE)
        length = pdfmetrics.stringWidth(label, "Sans", size)
        self.rule(x, y + 2.1, x + length, color=JADE, weight=0.45)
        bounds = (x - 1, HEIGHT - y - 4, x + length + 1, HEIGHT - y + size + 1)
        if internal:
            self.pdf.linkRect("", url, bounds, relative=0, thickness=0)
        else:
            self.pdf.linkURL(url, bounds, relative=0, thickness=0)
        return x + length

    def pic(self, x, y, w, h, source):
        if isinstance(source, Path):
            with Image.open(source) as im:
                rgb = im.convert("RGB")
        else:
            rgb = source.convert("RGB")
        if abs(rgb.width / rgb.height - w / h) > 0.025:
            raise ValueError(f"Image aspect ratio would distort {source}")
        rgb.thumbnail((1360, 1360), Image.Resampling.LANCZOS)
        data = io.BytesIO()
        rgb.save(data, "JPEG", quality=91, optimize=True, subsampling=0)
        data.seek(0)
        self.pdf.drawImage(ImageReader(data), x, HEIGHT - y - h, w, h, mask=None)
        self.pdf.setStrokeColor(colors.HexColor(LINE))
        self.pdf.setLineWidth(0.45)
        self.pdf.rect(x, HEIGHT - y - h, w, h, fill=0, stroke=1)

    def pair(self, y, key, is_native=False):
        if is_native:
            root = self.lab / "radiant" / "previews"
            before, after = root / f"original-{key}.jpg", root / f"jade-{key}.jpg"
        else:
            root = self.lab / "renders"
            before, after = root / f"{key}-baseline.png", root / f"{key}-jade.png"
        with Image.open(before) as im:
            h = COL * im.height / im.width
        self.pic(M, y, COL, h, before)
        self.pic(RIGHT, y, COL, h, after)
        return y + h

    def page(self, section, bookmark):
        if self.page_no:
            self.pdf.showPage()
        self.page_no += 1
        self.pdf.bookmarkPage(bookmark)
        self.pdf.addOutlineEntry(section, bookmark, level=0, closed=False)
        self.text(M, 28, "YUGA   /   LEVEL DESIGN", 8.2, "Helvetica-Bold", JADE)
        self.text(WIDTH - M, 28, section.upper(), 8, "Sans", GRAY, "right")
        self.rule(M, 40, WIDTH - M)
        self.rule(M, 804, WIDTH - M)
        self.text(M, 820, "Dust II map study   /   " + EDITION, 8.0, color=GRAY)
        self.text(
            WIDTH - M,
            820,
            f"{self.page_no} / {PAGES}",
            8.2,
            "Helvetica-Bold",
            GRAY,
            "right",
        )

    def heading(self, title, strap):
        self.text(M, 87, title, 31.5, "Serif")
        return self.para(M, 113, CONTENT, strap, 10.65, 15.4, GRAY)

    def sub(self, y, title):
        self.text(M, y, title, 17.7, "Serif")

    def tag(self, x, y, text):
        self.text(x, y, text, 8.3, "Helvetica-Bold", JADE)


def cover(g):
    g.page("Field guide", "cover")
    g.text(M, 74, "SOURCE 1    /    DARKPLACES", 9, "Helvetica-Bold", JADE)
    g.text(M - 2, 143, "Dust II, rebuilt", 57, "Serif")
    g.para(
        M,
        177,
        CONTENT,
        "What does one change to a familiar map actually touch? We turned its walkable structural ground jade and followed the edit from source faces to engine, editor and screen.",
        14,
        21,
    )
    paths = g.lab / "renders"
    with (
        Image.open(paths / "site-a-baseline.png") as before,
        Image.open(paths / "site-a-jade.png") as after,
    ):
        picture = before.convert("RGB")
        seam = round(picture.width * 0.51)
        picture.paste(after.crop((seam, 0, picture.width, picture.height)), (seam, 0))
    top = 242
    h = CONTENT * 9 / 16
    g.pic(M, top, CONTENT, h, picture)
    g.fill(M + CONTENT * 0.51 - 0.55, top, 1.1, h, "#f6f4e9")
    g.text(M, top + h + 16, "REFERENCE", 8.0, "Helvetica-Bold", GRAY)
    g.text(
        M + CONTENT * 0.51 + 8, top + h + 16, "JADE GROUND", 8.0, "Helvetica-Bold", JADE
    )
    g.text(
        M,
        568,
        "Site A, registered Blender camera. The paint on the courtyard floor is a separate projected marking.",
        9.25,
        color=GRAY,
    )
    g.rule(M, 586, WIDTH - M)
    g.text(M, 614, "Valve’s competitive map", 16.5, "Serif")
    g.text(RIGHT, 614, "Hanzo’s editable remake", 16.5, "Serif")
    g.para(
        M,
        640,
        COL - 4,
        "CS:GO’s October 2023 legacy map contains the compiled world, both plant sites and its baked lighting. We registered it to the matching navigation mesh and rebuilt the visible scene for Blender.",
        10.1,
        15,
    )
    g.para(
        RIGHT,
        640,
        COL - 4,
        "A 2013 RocketMinsta release includes the mapper’s brush source. We compiled it, built its lighting and drove a player across the jade result in the Nexuiz client.",
        10.1,
        15,
    )
    g.rule(M, 730, WIDTH - M)
    g.tag(M, 753, "IN THIS GUIDE")
    for x, y, name, target in [
        (M, 779, "Camera comparisons · 2", "cameras"),
        (M + 169, 779, "Native builds · 4–5", "native"),
        (M + 337, 779, "YUGA transfer · 6", "yuga"),
    ]:
        g.link(x, y, name, target, 9.4, True)


def cameras(g):
    g.page("Matched cameras", "cameras")
    g.heading(
        "Three views of one district",
        "Original CS:GO geometry reconstructed in Blender. Both states use the same camera, sun, meshes and texture images. Read each pair from left to right.",
    )
    g.tag(M, 148, "REFERENCE")
    g.tag(RIGHT, 148, "JADE GROUND")
    end = g.pair(158, "overview")
    g.text(M, end + 18, "District overview", 13.2, "Serif")
    g.text(
        WIDTH - M,
        end + 18,
        "Original radar extent, north up",
        9.1,
        color=GRAY,
        align="right",
    )
    end = g.pair(449, "site-a")
    g.text(M, end + 18, "Site A", 13.2, "Serif")
    g.text(
        WIDTH - M,
        end + 18,
        "NAV 4140 · 1.60 m eye · original orange X and crates",
        9.1,
        color=GRAY,
        align="right",
    )
    end = g.pair(635, "site-b")
    g.text(M, end + 18, "Site B", 13.2, "Serif")
    g.text(
        WIDTH - M,
        end + 18,
        "NAV 1640 · 1.60 m eye · doorways and stonework",
        9.1,
        color=GRAY,
        align="right",
    )


def ground(g):
    native = g.evidence("native-diff.json")
    nav = g.evidence("nav-support.json")
    tex = g.evidence("texel-diff.json")
    images = g.evidence("render-diff.json")
    g.page("Ground selection", "ground")
    g.heading(
        "Which surfaces are ground?",
        "A wall and a floor can use the same texture. We tagged individual world faces by slope, material and their height relative to the official navigation mesh.",
    )
    ct = nav["counts"]
    values = [
        ct["registered jade ground"],
        ct["raised/static prop geometry"],
        ct["no close upward render surface"],
    ]
    offset = M
    for n, col in zip(values, [JADE, "#b6915c", "#627476"]):
        w = CONTENT * n / sum(values)
        g.fill(offset, 166, w, 13, col)
        offset += w
    pieces = [
        (
            "Structural ground",
            "Every sampled structural floor fell on a recoloured face.",
        ),
        (
            "Raised props",
            "Stair models, curbs, crates and other prop surfaces keep their materials.",
        ),
        (
            "Collision-only support",
            "Invisible clip brushes support these samples within the height tolerance.",
        ),
    ]
    tile = (CONTENT - 24) / 3
    for i, ((label, body), n) in enumerate(zip(pieces, values)):
        x = M + i * (tile + 12)
        g.text(x, 218, f"{n:,}", 28, "Serif")
        g.text(x, 239, label, 9.5, "Helvetica-Bold", JADE)
        g.para(x, 259, tile - 3, body, 9.45, 13.5, GRAY)
    g.text(
        M,
        319,
        "The test samples the centre of each of the 1,118 NAV areas. Its vertical tolerance is ±18 Source units.",
        9.1,
        color=GRAY,
    )
    g.rule(M, 337, WIDTH - M)
    g.sub(368, "The visible ground at Site A")
    g.tag(M, 388, "MATERIAL-ID MASK")
    g.tag(RIGHT, 388, "MATCHED JADE RENDER")
    r = g.lab / "renders"
    g.pic(M, 398, COL, COL * 9 / 16, r / "site-a-ground-mask.png")
    g.pic(RIGHT, 398, COL, COL * 9 / 16, r / "site-a-jade.png")
    g.para(
        M,
        559,
        CONTENT,
        "White marks the ground pixels visible from the camera. Crates, walls and the paint marking interrupt the mask. Edge antialiasing creates fractional coverage.",
        9.5,
        14,
        GRAY,
    )
    g.sub(620, "What the checks measured")
    checks = [
        (
            f"{native['changed_face_count']:,} faces",
            "Their material lookup changes in both native lighting variants.",
        ),
        (
            f"{native['stable_lump_count']} of 64 sections",
            "The individual BSP sections compare byte for byte, including geometry, collision and visibility.",
        ),
        (
            f"{tex['compared_pixels']:,} texels",
            "All 21 new VTFs match the expected linear RGB multiplication. Alpha is identical through all mip levels and frames.",
        ),
        (
            f"{images['views'][1]['ground_core_percent_changed']:.2f}% at Site A",
            "Share of the mask interior above the strong-change threshold. Three strong pixels lie beyond its two-pixel boundary.",
        ),
    ]
    y = 646
    for value, meaning in checks:
        g.rule(M, y - 12, WIDTH - M)
        g.text(M, y + 4, value, 11, "Helvetica-Bold", JADE)
        end = g.para(M + 145, y + 3, CONTENT - 146, meaning, 9.15, 12.4)
        y = max(y + 31, end + 13)
    g.link(M, 789, "Independent QA methods and tolerances", TOOLS + "qa/README.md")


def native(g):
    a = json.loads((g.lab / "radiant/geometry-audit.json").read_text())
    motion = json.loads((g.lab / "radiant/previews/engine-captures.json").read_text())[
        "jade_player_movement"
    ]
    g.page("A native game client", "native")
    g.heading(
        "From brushes to a playable arena",
        "Hanzo’s RocketMinsta variant supplies a complete editable Radiant map. Its jail rooms, arena pickups, scale and match rules belong to the Nexuiz remake.",
    )
    g.tag(M, 153, "ORIGINAL BUILD  /  DARKPLACES")
    g.tag(RIGHT, 153, "JADE BUILD  /  DARKPLACES")
    e = g.pair(165, "west-courtyard", True)
    g.text(M, e + 17, "West courtyard", 13.4, "Serif")
    g.text(
        WIDTH - M,
        e + 17,
        "Native client, matched spectator cameras",
        9.05,
        color=GRAY,
        align="right",
    )
    e = g.pair(346, "arches", True)
    g.text(M, e + 17, "Arches", 13.4, "Serif")
    g.text(
        WIDTH - M,
        e + 17,
        "Original stone pattern and sunlight survive the edit",
        9.05,
        color=GRAY,
        align="right",
    )
    g.rule(M, 527, WIDTH - M)
    g.sub(558, "Five passes from the editable map")
    g.para(
        M,
        582,
        CONTENT,
        "Q3Map2 compiled the brushes and curves, calculated visibility, baked lighting, drew the minimap and applied the mapper’s scale of 1.16. Both packages use the same new light bake.",
        10.9,
        16,
    )
    y = 659
    for i, (n, label) in enumerate(
        [
            (a["draw_surfaces"], "draw surfaces"),
            (a["curved_patch_surfaces"], "curved patches"),
            (a["changed_surfaces"], "jade surfaces"),
        ]
    ):
        x = M + i * CONTENT / 3
        g.text(x, y, f"{n:,}", 24, "Serif")
        g.text(x, y + 18, label, 9.8, color=GRAY)
    g.para(
        M,
        715,
        CONTENT,
        f"A stock player walked {motion['planar_walk_units']:.2f} Quake units on the modified court, rose {motion['sampled_jump_rise_units']:.2f} units at the sampled moment of a jump, then landed with {motion['samples']['landed']['health']:.0f} health. The capture records horizontal displacement and grounded state.",
        10.3,
        15,
    )
    g.link(
        M,
        783,
        "Rebuild notes, source package and compiler commands",
        RESEARCH + "remakes-and-alternatives.md",
    )
    g.link(
        RIGHT + 35,
        783,
        "Client camera and movement fixture",
        TOOLS + "radiant/capture.py",
    )


def launch(g):
    smoke = g.evidence("server-smoke.json")
    version = smoke["server"]["patch_version"]
    counts = [run["live_entities"] for run in smoke["runs"]]
    if counts[0] != counts[1] or any(run["process_exit_code"] for run in smoke["runs"]):
        raise ValueError(
            "The two Valve server probes did not produce a matching clean result"
        )
    g.page("Local launch", "launch")
    g.heading(
        "Open the local builds",
        "Choose the host engine for the edition you want to run. The same map name exists in several generations of Counter-Strike and in multiple fan ports.",
    )
    g.sub(181, "Valve Source 1")
    g.para(
        M,
        207,
        CONTENT,
        "Use Counter-Strike: Global Offensive’s legacy content. The build provides two separate csgo/maps mounts, each with its BSP and matching NAV. To keep both in a test installation, give the copied jade BSP and NAV the same distinct basename.",
        11,
        16,
    )
    g.fill(M, 273, CONTENT, 53, PALE)
    g.text(M + 12, 294, "Original console", 9.15, "Helvetica-Bold", JADE)
    g.text(
        RIGHT, 294, "Jade alias used by the server test", 9.15, "Helvetica-Bold", JADE
    )
    g.text(M + 12, 314, "map de_dust2", 12, "Courier")
    g.text(RIGHT, 314, "map de_dust2_jade", 12, "Courier")
    g.para(
        M,
        348,
        CONTENT,
        f"Two localhost Valve SRCDS {version} processes loaded these levels. Each found {counts[0]['func_bomb_target']} site triggers and {counts[0]['info_player_terrorist']} spawns per team, had zero humans and bots, and exited cleanly. The server reported missing global particle libraries. The images on page 2 use Blender.",
        10.45,
        14.8,
        GRAY,
    )
    g.link(
        M, 407, "Acquire the BSP, assets, radar and NAV", RESEARCH + "sources-dust.md"
    )
    g.link(
        RIGHT,
        407,
        "Native server commands and measured results",
        RESEARCH + "server-smoke.json",
    )
    g.rule(M, 430, WIDTH - M)
    g.sub(463, "Nexuiz 2.5.2 / DarkPlaces")
    g.para(
        M,
        490,
        CONTENT,
        "Install either rebuilt PK3 in the game’s data directory. Activate one variant at a time because both contain the mapper’s original map name. Open the Nexuiz console and enter the command below.",
        10.8,
        16,
    )
    g.fill(M, 539, CONTENT, 39, SAND)
    g.text(M + 12, 564, "map q3dust2-jb-beta6", 12, "Courier")
    g.para(
        M,
        604,
        CONTENT,
        "The graphical client loaded both packages. Its movement and collision run inside DarkPlaces. RocketMinsta-specific modes need their game code, and full audio uses the stock Nexuiz sound package.",
        10.5,
        15,
        GRAY,
    )
    g.rule(M, 659, WIDTH - M)
    g.sub(690, "Inspect geometry without either engine")
    g.para(
        M,
        716,
        CONTENT,
        "Open blender/dust2-ground-study.blend. Switch scenes for the reference and jade version. Timeline frames 1, 2 and 3 select the overview, Site A and Site B. For Hammer editing, source/de_dust2_reconstructed.vmf contains BSPSource’s reconstruction of the compiled Valve map.",
        10.3,
        15,
    )
    g.link(M, 785, "Rebuild the pictured Blender scene", TOOLS + "blender/README.md")
    g.link(
        RIGHT,
        785,
        "BSPSource decompiler",
        "https://github.com/ata4/bspsrc/tree/85943055376b9e330263a5e4e88f574d98a7f01c",
    )


def yuga(g):
    g.page("YUGA transfer", "yuga")
    g.heading(
        "Carry the method to Mandala Rift",
        "Use the North Pyramid entrance to Bazaar Sanctuary as the first transfer. Its Cart chest and Stamp screen already have measured cover heights, approach bearings and hero sightline samples.",
    )
    g.sub(187, "One entrance, two different shelters")
    g.text(M, 211, "Elevation study in metres", 9.45, color=GRAY)
    low = 401
    x0, x1 = M + 47, WIDTH - M - 12
    scale = 54
    for level, label in [(0, "0.0"), (1, "1.0"), (2, "2.0"), (2.5, "2.5")]:
        y = low - level * scale
        g.rule(x0, y, x1, "#bcc8be", 0.45)
        g.text(x0 - 8, y + 3, label, 8.8, color=GRAY, align="right")
    for x, h, label, fill in [
        (x0 + 27, 1.62, "Cart chest", "#b88d55"),
        (x0 + 157, 2.40, "Stamp screen", JADE),
        (x0 + 291, 1.80, "Standing body", "#617578"),
    ]:
        g.fill(x, low - h * scale, 64, h * scale, fill)
        g.text(
            x + 32,
            low - h * scale - 8,
            f"{h:.2f} m",
            10.3,
            "Helvetica-Bold",
            INK,
            "center",
        )
        g.text(x + 32, low + 19, label, 9.55, color=INK, align="center")
    g.para(
        M,
        454,
        CONTENT,
        "From the recorded bearing, raising the observer by 4 m exposes six of nine sampled body points behind the chest. The screen still hides all nine. The chart compares object heights. Visibility also depends on the two positions and viewing angle.",
        10.5,
        16,
        GRAY,
    )
    g.rule(M, 516, WIDTH - M)
    g.sub(550, "Build the first court comparison")
    steps = [
        (
            "Register the architecture",
            "Keep each module’s mesh, material and instance transform independent. Tag structural floor, stairs, cover, climbable props and invisible collision. Preserve the source IDs through Blender and the Rust importer.",
        ),
        (
            "Exercise the hero routes",
            "Record a grounded entry, Hanuman’s elevated route and Rama’s aiming line from each shelter. Freeze the observer transform and light. Replay the same inputs against the baseline and material experiment.",
        ),
        (
            "Record the decision",
            "Compare floor visibility, enemy silhouette and objective markings at each height. Verify that the material experiment produces identical collision traces. Archive the images, transforms and actual hit results before editing the next court.",
        ),
    ]
    y = 581
    for title, desc in steps:
        g.text(M, y, title, 11.2, "Helvetica-Bold", JADE)
        end = g.para(M + 152, y, CONTENT - 152, desc, 9.85, 14.4)
        y = end + 20
    g.link(M, 783, "Measured architecture and hero routes", ATLAS + "README.md")
    g.link(RIGHT, 783, "Entrance and shelter survey", ATLAS + "door-register.md")


def resources(g):
    g.page("Sources and companion code", "sources")
    g.heading(
        "Sources and companion code",
        "The three research chapters preserve exact revisions, downloads, commands and evidence. The implementation links below identify which sources ran locally and which supplied design references.",
    )
    chapters = [
        (
            "1. Finding the full CS:GO Dust II",
            "Valve depot, false Workshop match, mounted dependencies and author attribution.",
            "sources-dust.md",
        ),
        (
            "2. Rebuilding an editable Dust II fan map",
            "Hanzo’s source, Q3Map2 flags, DarkPlaces captures and alternative map licenses.",
            "remakes-and-alternatives.md",
        ),
        (
            "3. Rust map research and Call of Duty",
            "Two Rust readers on the actual BSP, CS game remakes, MW2 collision and fixture results.",
            "rust-and-cod.md",
        ),
    ]
    y = 165
    for title, desc, path in chapters:
        g.link(M, y, title, RESEARCH + path, 12.2)
        g.text(M, y + 22, desc, 9.6, color=GRAY)
        y += 56
    g.rule(M, 329, WIDTH - M)
    g.sub(364, "Projects behind the experiments")
    items = [
        (
            "vformats",
            "Read the actual v21 map with v11 static props in the Rust probe.",
            "https://github.com/charles-mills/vformats/tree/a073bddf5af1714660c1313167ae3536f8a3262c",
        ),
        (
            "SourceIO",
            "Decoded the original studio model meshes, skins and level-of-detail data.",
            "https://github.com/REDxEYE/SourceIO/tree/34be43e4d4b4da7a819de50075cb95ab7f28899d",
        ),
        (
            "NetRadiant / Q3Map2",
            "Compiled Hanzo’s editable map and generated light, visibility and radar.",
            "https://github.com/Garux/netradiant-custom/releases/tag/20260114",
        ),
        (
            "IW4L and MW2WEB",
            "Inspected the desktop Rust world loader and exercised the web fork’s collision crate on an authored test floor.",
            "https://github.com/vladtrc/iw4L/tree/8fd4fb7adf84ae8170cc70628256d735815556ea",
        ),
        (
            "Chimera",
            "Inspected the Rust Counter-Strike: Source renderer and its Dust II fixture.",
            "https://github.com/r0pi0x/Chimera/blob/383d5913f2e1f58ce79401635164e175dc7eabea/games/cs_source/tests/it/heavy/map_de_dust2.rs",
        ),
        (
            "Parpax / Unvanquished",
            "An original Radiant map with per-file rights. The author lists maps under CC BY-SA 4.0 or later.",
            "https://github.com/UnvanquishedAssets/map-parpax_src.dpkdir/blob/bcfecd7aab39abde0a90973785e66b3c2974e6a3/about/map-parpax.txt",
        ),
    ]
    y = 394
    for title, desc, url in items:
        g.rule(M, y - 13, WIDTH - M)
        g.link(M, y + 3, title, url, 10.3)
        end = g.para(M + 143, y + 3, CONTENT - 143, desc, 9.4, 13.5)
        y = max(y + 39, end + 14)
    g.link(
        M,
        660,
        "MW2WEB Rust collision implementation",
        "https://github.com/bettertech-97/mw2web/tree/379c68231ebf54d01821ad096f4ac733ccca6d1b/crates/clipmap_iw4",
    )
    g.link(
        RIGHT,
        660,
        "Executed two-triangle Rust fixture",
        RESEARCH + "probe/iw4-floor.rs",
    )
    g.rule(M, 687, WIDTH - M)
    g.para(
        M,
        713,
        CONTENT,
        "For a distributable YUGA court, use its own hero, landmark and material art or assets with applicable reuse terms. Valve’s shipped game data and the artwork credited in Hanzo’s PK3 have their own provenance. The repository carries the conversion code and the measurements.",
        9.85,
        14.6,
        GRAY,
    )
    g.link(
        M,
        784,
        "Original mapper’s design account",
        "https://www.johnsto.co.uk/design/making-dust2/",
    )
    g.link(
        RIGHT,
        784,
        "Valve’s official Dust II revision study",
        "https://www.counter-strike.net/dust2",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    book = Guide(args.lab, args.output)
    for make_page in [cover, cameras, ground, native, launch, yuga, resources]:
        make_page(book)
    book.pdf.save()


if __name__ == "__main__":
    main()
