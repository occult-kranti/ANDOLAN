"""Build the offline art-reference gallery from the verified source catalog."""
from html import escape
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
CUES = {
    "met-37960": "A running silhouette carries the mountain in one hand. The tail wraps the composition in a continuous arc.",
    "met-37986": "Seated figures use small hand gestures and a shared eye line to establish a calm exchange.",
    "met-37988": "Groups and varied scale direct attention to the healing encounter at the center of a broad landscape.",
    "met-53684": "Two seated figures and their resting bows make a quiet silhouette against a dark hillside and sky.",
    "met-39329": "A planted leg, raised leg and outward-reaching arms balance the pose within a circular frame.",
    "met-448183": "The mountain forms a protective canopy above Krishna, villagers and cattle.",
    "met-436535": "Repeated directional strokes give the clouds, cypress and field distinct rhythms.",
    "nga-74796": "Soft bands of reflected greens and small pale blossoms make the water legible under an arched bridge.",
}


def main():
    catalog = json.loads((ROOT / "catalog.json").read_text())
    cards = []
    for work in catalog["objects"]:
        cue = CUES[work["id"]]
        title = escape(work["title"])
        author = escape(work["artist"])
        date = escape(work["date"])
        source = escape(work["object_url"], quote=True)
        asset = escape(work["image_file"], quote=True)
        museum = escape(work["institution"])
        cards.append(f"""<article class="card">
  <a class="art" href="{asset}"><img src="{asset}" alt="{title}" loading="lazy"></a>
  <div class="content"><h2>{title}</h2><p class="credit">{author} · {date}</p>
  <p>{escape(cue)}</p><a class="source" href="{source}">{museum} collection record</a></div>
</article>""")
    page = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>YUGA · Art references</title>
<style>
:root{color-scheme:light;--ink:#172d2d;--muted:#50635d;--paper:#f5f1e7;--line:#d7d1c3;--accent:#9a4c2f}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"DM Sans",Arial,sans-serif;line-height:1.5}
main{max-width:1500px;margin:auto;padding:clamp(24px,5vw,72px)}header{max-width:850px;margin:0 0 40px}
.wordmark{color:#876748;font-size:.8rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase}
h1{font-family:"Instrument Serif",Georgia,serif;font-size:clamp(2.4rem,5vw,4.8rem);font-weight:500;letter-spacing:-.025em;line-height:1.04;margin:.25em 0}
header p{color:var(--muted);font-size:1.06rem;max-width:68ch}
a{color:#785036}a:focus-visible{outline:3px solid #167a75;outline-offset:3px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:20px;align-items:stretch}
.card{background:#fffdf8;border:1px solid var(--line);display:flex;flex-direction:column}
.art{display:flex;align-items:center;justify-content:center;background:#e8e2d5;padding:12px;height:260px}
.art img{display:block;max-width:100%;max-height:100%;object-fit:contain}
.content{padding:20px;display:flex;flex:1;flex-direction:column}
h2{font:500 1.35rem/1.18 "Instrument Serif",Georgia,serif;margin:0 0 8px}
p{margin:0 0 14px}.credit{font-size:.84rem;color:var(--muted)}
.source{font-size:.86rem;margin-top:auto;align-self:flex-start}
footer{border-top:1px solid var(--line);margin-top:40px;padding-top:20px;color:var(--muted);font-size:.9rem}
</style></head>
<body><main><header><div class="wordmark">YUGA · Art research</div><h1>Form, gesture and landscape</h1>
<p>Eight public-domain works from the Metropolitan Museum of Art and the National Gallery of Art. Each image opens locally. The source records describe the works, while the notes identify visual ideas for the YUGA team.</p></header>
<section class="grid" aria-label="Art references">
""" + "\n".join(cards) + """
</section><footer>Source records and image checksums are in the accompanying README and catalog. These examples are a starting point for research into many Indian art traditions.</footer></main></body></html>
"""
    (ROOT / "gallery.html").write_text(page)


if __name__ == "__main__":
    main()
