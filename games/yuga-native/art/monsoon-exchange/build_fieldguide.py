"""Assemble the illustrated Monsoon Exchange design atlas and append the vector survey sheets."""

import argparse
import io
import json
import tempfile
from pathlib import Path

import fitz
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
INVENTORY = NATIVE / "docs/research/dust2-map-lab/inventory"
SOURCE = "https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/games/yuga-native/"
LIVE = "https://occult-kranti.github.io/ANDOLAN/production/monsoon-exchange/"
W, H = landscape(A4)
M = 35
PAPER, INK, TEAL, RUST, DIM, RULE = (
    "#f5f0e4",
    "#192e2c",
    "#075952",
    "#97472c",
    "#425350",
    "#bbc5ba",
)


def read(path):
    return json.loads(path.read_bytes())


class Atlas:
    def __init__(self, output):
        self.c = canvas.Canvas(str(output), pagesize=(W, H), invariant=1)
        self.c.setTitle("Monsoon Exchange | A map design atlas for YUGA")
        self.c.setAuthor("YUGA environment and level design")
        self.pages = []
        for family, file in [
            ("Body", "NotoSans-Regular.ttf"),
            ("Display", "NotoSerif-Regular.ttf"),
        ]:
            pdfmetrics.registerFont(TTFont(family, str(NATIVE / "assets/fonts" / file)))

    def text(self, x, y, value, *, size=10, font="Body", color=INK):
        self.c.setFillColor(HexColor(color))
        self.c.setFont(font, size)
        self.c.drawString(x, y, str(value))

    def paragraph(self, x, y, width, value, *, size=11, leading=16, color=INK):
        for line in simpleSplit(value, "Body", size, width):
            self.text(x, y, line, size=size, color=color)
            y -= leading
        return y

    def line(self, x1, x2, y):
        self.c.setStrokeColor(HexColor(RULE))
        self.c.setLineWidth(0.65)
        self.c.line(x1, y, x2, y)

    def page(self, section, title, description):
        self.pages.append(title)
        c = self.c
        c.setFillColor(HexColor(PAPER))
        c.rect(0, 0, W, H, fill=1, stroke=0)
        self.text(M, H - 28, "YUGA   /   ENVIRONMENT DESIGN", size=9, color=TEAL)
        self.text(W - 260, H - 28, section.upper(), size=9, color=RUST)
        self.line(M, W - M, H - 37)
        self.text(M, H - 78, title, size=31, font="Display")
        self.paragraph(
            M, H - 101, W - 2 * M, description, size=11, leading=15, color=DIM
        )

    def link(self, x, y, title, url):
        self.text(x, y, title, size=9, color=TEAL)
        length = pdfmetrics.stringWidth(title, "Body", 9)
        self.c.linkURL(url, (x, y - 3, x + length, y + 10), relative=0, thickness=0)
        return length

    def end(self, links):
        self.line(M, W - M, 35)
        x = M
        for label, url in links:
            x += self.link(x, 20, label, url) + 20
        self.text(W - M - 29, 20, f"{len(self.pages):02d}", size=9, color=DIM)
        self.c.showPage()

    def image(self, relative, x, y, w, h, *, backed=False):
        with Image.open(HERE / relative) as im:
            im = im.convert("RGB")
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=91, optimize=True)
            ratio = min(w / im.width, h / im.height)
            pw, ph = im.width * ratio, im.height * ratio
        if backed:
            self.c.setFillColor(HexColor("#192b29"))
            self.c.rect(x, y, w, h, stroke=0, fill=1)
        self.c.drawImage(ImageReader(buf), x + (w - pw) / 2, y + (h - ph) / 2, pw, ph)

    def note(self, x, y, width, heading, body):
        self.text(x, y, heading, font="Display", size=16, color=TEAL)
        return self.paragraph(x, y - 22, width, body, size=10.5, leading=15) - 12


def make_pages(book):
    survey, metrics = [
        read(HERE / "plan" / name) for name in ("survey.json", "metrics.json")
    ]
    native = read(INVENTORY / "source.json")
    fan = read(INVENTORY / "hanzo.json")
    nav = read(INVENTORY / "nav.json")
    loc = {r["id"]: r for r in survey["rooms"]}
    a, b = loc["a"], loc["b"]
    art = SOURCE + "art/monsoon-exchange/"
    dust = SOURCE + "docs/research/dust2-map-lab/"
    book.page(
        "Illustrated field guide",
        "Monsoon Exchange",
        "A western Indian trading district designed for Ember Rite. The river dyes one court indigo. The other measures the sun.",
    )
    book.image("concepts/district-keyart.webp", M, 79, 531, 363, backed=True)
    book.text(
        M,
        62,
        "Generated environment art direction, looking north from the caravan approach.",
        size=9,
        color=DIM,
    )
    x, y, width = 588, 423, W - M - 588
    y = book.note(
        x,
        y,
        width,
        "Sun Court",
        f"A raised terrace at {a['z']:+.1f} m. A copper instrument is visible from the arcade and the ledger balcony.",
    )
    y = book.note(
        x,
        y,
        width,
        "Indigo Cistern",
        f"A recessed court at {b['z']:+.1f} m. Indigo plaster and water steps distinguish the western side.",
    )
    book.note(
        x,
        y,
        width,
        "Weavers’ Gate",
        "A screen breaks the straight middle view. Two teams can read the same landmark from different approaches.",
    )
    book.end(
        [
            ("Explore the map in 2D and 3D", LIVE),
            ("Read the map handoff", art + "README.md"),
        ]
    )

    book.page(
        "Source analysis",
        "What the two Dust builds contain",
        "The native Source level and the editable arena remake have different entity graphs and different rules. Their measured inventories answer different design questions.",
    )
    cols = [
        (
            M,
            "Legacy CS:GO",
            [
                (
                    "Authored level",
                    f"{native['format']}. Its {native['entities']['count']} entities span {native['entities']['class_count']} classes. Two site volumes and fifteen spawns per team belong to this edition.",
                ),
                (
                    "Visible world",
                    f"{native['static_props']['placements']:,} static placements use {native['static_props']['normalized_used_models']:,} model paths after normalization. The file contains {native['records']['faces']:,} BSP face records and {native['records']['overlays']} overlays.",
                ),
                (
                    "Reading a gate",
                    "There are 37 func_areaportal and 19 func_occluder entities. Several locations are named doors. The native level defines zero func_door entities.",
                ),
                (
                    "Navigation",
                    f"{nav['areas']:,} bot areas yield {nav['directed_links']:,} directed links. {nav['cross_label_links']} links cross a place label. A directed link describes bot connectivity. A sightline needs its own geometric test.",
                ),
            ],
        ),
        (
            W / 2 + 12,
            "Hanzo’s Nexuiz remake",
            [
                (
                    "Editable input",
                    f"{fan['source_entities']['count']} source entities span {fan['source_entities']['class_count']} classes. The Radiant map has {fan['source_shapes']['plane_brushes']:,} plane brushes and {fan['source_shapes']['patches']} curved patches.",
                ),
                (
                    "Compiled world",
                    f"The map compiler produces {fan['compiled']['collision_brushes']:,} collision brushes, {fan['compiled']['draw_surfaces']:,} draw surfaces and {fan['compiled']['visibility_clusters']:,} visibility clusters.",
                ),
                (
                    "Doors and objectives",
                    "Twelve actual door definitions, twenty free-for-all start points, two flags and five domination points serve this edition’s game modes. These functions have separate source evidence.",
                ),
                (
                    "The reusable method",
                    "Compile the editable form, measure the collision, then compare a real client view. YUGA keeps that workflow and instantiates its own trading quarter, floor survey and ritual markers.",
                ),
            ],
        ),
    ]
    for x, title, rows in cols:
        width = W / 2 - M - 20
        book.text(x, 439, title, size=21, font="Display", color=RUST)
        y = 408
        for heading, body in rows:
            book.text(x, y, heading, size=12, color=TEAL)
            y = book.paragraph(x, y - 17, width, body, size=10, leading=14) - 13
        if y < 36:
            raise ValueError(f"Source column exceeds page: {title}")
    book.end(
        [
            ("Full entity and structural inventory", dust + "inventory/README.md"),
            ("Source-specific reuse terms", dust + "remakes-and-alternatives.md"),
            ("Rebuild evidence", dust + "README.md"),
        ]
    )

    book.page(
        "Spatial adaptation",
        "From callout to courtyard",
        "Keep the decision at a junction. Change its dimensions, construction, sight screen, surface and relationship to the ritual.",
    )
    book.image("concepts/painted-plan.webp", M, 61, 337, 384)
    x, y, width = 395, 435, W - M - 395
    rows = [
        (
            "Long approach and inner short",
            "Copper Arcade offers the longer journey to Sun Court. Ledger Balcony trades distance for an exposed change of grade. The fourth entrance, Witness Gate, links Rain Register to the sun side.",
        ),
        (
            "Upper and lower western passages",
            "Dyers’ Passage carries the covered western approach. Sluice Walk separates a shallow dye runnel from a dry stone shoulder. Both support a route to Indigo Cistern.",
        ),
        (
            "Middle crosslink",
            "Weavers’ Gate offsets the opening and leads to either quarter. Sun and Moon enter from a caravan yard and an archive court. Their ritual duties can swap while the streets stay put.",
        ),
        (
            "Reusable construction",
            "The mesh uses project-owned architecture alongside a new metric floor and room-specific cover. The generated painting proposes color and roof character. The vector sheets and Blender coordinates govern the build.",
        ),
    ]
    for heading, body in rows:
        y = book.note(x, y, width, heading, body)
    if y < 33:
        raise ValueError("Route transformations exceed page")
    book.end(
        [
            (
                "26 named Dust places and the unassigned group",
                art + "design/dust-callouts.csv",
            ),
            (
                "Reuse decisions and acceptance cases",
                art + "design/transfer-register.md",
            ),
        ]
    )

    book.page(
        "Blender survey",
        "The district as built",
        "The camera looks north. Follow the western court to the left, the raised eastern quarter to the right and the archive return across the back.",
    )
    book.image("renders/overview.webp", M, 96, W - 2 * M, 344, backed=True)
    box = metrics["floor_bounds_xy"]
    xspan, yspan = box[2] - box[0], box[3] - box[1]
    book.text(
        M,
        72,
        f"{len(survey['rooms'])} rooms     /     {len(survey['links'])} connections     /     {len(survey['entries'])} site entrances     /     {xspan:.1f} × {yspan:.1f} m floor envelope",
        size=12,
        color=TEAL,
    )
    book.text(
        M,
        51,
        f"{metrics['horizontal_floor_m2']:,.2f} m² in horizontal floor projection. Architectural roofs and surrounding facades may extend beyond this envelope.",
        size=9,
        color=DIM,
    )
    book.end(
        [
            ("Download the Blender scene", LIVE + "scene/monsoon-exchange.blend"),
            ("Download the portable glTF", LIVE + "scene/monsoon-exchange.glb"),
            ("Metric source survey", art + "plan/survey.json"),
        ]
    )

    book.page(
        "Two site studies",
        "Courts at eye level",
        "The two districts share a three-metre kindle radius. Stonework, shade and circulation give them different identities without changing the objective.",
    )
    cw = (W - 2 * M - 20) / 2
    details = [
        (
            "sun-court",
            "A  /  Sun Court",
            "Four entrances lead to the raised court. Upper ledges sit outside the ritual disk. The copper sun instrument lets a player recognize the district before reading the HUD.",
        ),
        (
            "indigo-cistern",
            "B  /  Indigo Cistern",
            "Three entrances arrive at the lower court. A dyers’ gallery and a drainage walk use different threshold silhouettes. The model preserves space around the ritual marker.",
        ),
    ]
    for i, (name, heading, body) in enumerate(details):
        x = M + i * (cw + 20)
        book.image(f"renders/{name}.webp", x, 215, cw, 226, backed=True)
        book.text(x, 180, heading, font="Display", size=21, color=TEAL)
        book.paragraph(x, 154, cw - 6, body, size=11, leading=16)
    book.end(
        [
            ("Open both courts on the floorplan", LIVE),
            ("Architectural source notes", art + "design/architecture.md"),
        ]
    )

    book.page(
        "Movement and counterplay",
        "The choice at mid",
        "Travel figures follow body-clear routes between room centres. Ground walking uses the survey’s 5 m/s nominal speed. Combat, acceleration and player decisions change the result.",
    )
    book.image("renders/weavers-gate.webp", M, 184, 400, 250, backed=True)
    book.text(M, 159, "Weavers’ Gate", font="Display", size=16, color=TEAL)
    book.paragraph(
        M,
        139,
        390,
        "The centre screen interrupts the opening view. At the Sluice, two parallel 12 m strips model a wet crossing and a dry return. All seven site entrances have two separately identified shelter positions.",
        size=10.5,
        leading=15,
    )
    routes = {r["id"]: r for r in metrics["routes"]}
    x = 465
    width = W - M - x
    book.text(x, 424, "Approach", size=10, color=TEAL)
    book.text(x + 204, 424, "Length", size=10, color=TEAL)
    book.text(x + 285, 424, "Time", size=10, color=TEAL)
    keys = [
        "a-long",
        "a-short",
        "b-vault",
        "b-sluice",
        "a-keep",
        "b-keep",
        "rotation",
        "rotation-mid",
    ]
    y = 401
    for key in keys:
        r = routes[key]
        book.line(x, W - M, y + 13)
        book.text(x, y, r["name"], size=10)
        book.text(x + 204, y, f"{r['length_3d_m']:.2f} m", size=10)
        book.text(x + 285, y, f"{r['walk_s']:.2f} s", size=10)
        y -= 23
    book.paragraph(
        x,
        186,
        width,
        "Next playtest: compare the long and short approaches after swapping sides. Record the first sightline at each gate, site entry, whether a shelter was usable and time remaining at quench.",
        size=10.5,
        leading=15,
    )
    book.end(
        [
            ("Coordinates and measured routes", art + "plan/metrics.json"),
            (
                "Round rules and clock",
                SOURCE + "docs/design/ember-rite-5v5/ROUND_AND_TECH.md",
            ),
        ]
    )

    book.page(
        "Handoff",
        "Working with the map",
        "Use the authoring files to change the map. The following measured sheets retain their original page sizes and scale bars.",
    )
    x = M
    y = 421
    for heading, body in [
        (
            "Level design",
            "Edit plan/survey.json for floor elevations, rooms, links, spawns, entries, water and cover. Regenerate the derived floor/wall data and route witnesses together. Recheck that each gate connects on foot.",
        ),
        (
            "Environment art",
            "Use scene/monsoon-exchange.blend for the full district and its named cameras. The GLB is the portable handoff. Original cloth design, paintings and their generation references sit in concepts/.",
        ),
        (
            "Engine integration",
            "Carry over objective and spawn identifiers separately from visible materials. The model and atlas are ready for inspection. A server-owned 5v5 round still needs player collision, cast and audience integration, followed by human retakes.",
        ),
    ]:
        y = book.note(x, y, 432, heading, body)
    book.image("concepts/indigo-cloth.png", 510, 173, 257, 252)
    book.text(510, 151, "Indigo resist-print material study", size=11, color=TEAL)
    book.paragraph(
        510,
        131,
        252,
        "An original ImageGen textile for the trading quarter. The native scene register records its use on the model.",
        size=10,
        leading=14,
    )
    book.end(
        [
            ("Build instructions and QA", art + "README.md"),
            ("Numerical cover and movement studies", art + "plan/"),
            ("Browse the public atlas", LIVE),
        ]
    )
    book.c.save()


def build(output):
    with tempfile.TemporaryDirectory() as tmp:
        lead = Path(tmp) / "editorial.pdf"
        book = Atlas(lead)
        make_pages(book)
        with (
            fitz.open(lead) as combined,
            fitz.open(HERE / "plan/floorplans.pdf") as drawings,
        ):
            count = len(combined)
            sheets = [
                "District floorplan",
                "Sun Court entrances and cover",
                "Indigo Cistern entrances and cover",
                "Grade and water sections",
            ]
            if len(drawings) != len(sheets):
                raise ValueError(
                    "Expected the district, two site sheets and a section sheet"
                )
            combined.insert_pdf(drawings)
            toc = [[1, name, number] for number, name in enumerate(book.pages, 1)]
            toc.append([1, "Measured plans and sections", count + 1])
            toc.extend([2, title, count + page] for page, title in enumerate(sheets, 1))
            combined.set_toc(toc)
            combined.set_metadata(
                {
                    "title": "Monsoon Exchange | Map design atlas",
                    "author": "YUGA environment and level design",
                    "subject": "Dust source inventory, architectural adaptation and measured Blender district",
                }
            )
            combined.save(output, garbage=4, deflate=True, no_new_id=True)
    with fitz.open(output) as check:
        if len(check) != len(book.pages) + len(sheets) or not all(
            page.get_text().strip() for page in check
        ):
            raise ValueError("Missing pages or unreadable editorial text")
        print(
            f"{output.name}: {len(book.pages)} illustrated chapters, {len(check) - len(book.pages)} survey sheets, {sum(len(p.get_links()) for p in check)} links"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=HERE / "monsoon-exchange-atlas.pdf"
    )
    build(parser.parse_args().output)
