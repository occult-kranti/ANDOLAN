#!/usr/bin/env python3
"""Draw the editable level sheets directly from the metre-scale layout files."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import xml.etree.ElementTree as ET

from audit import DRY, audit_geometry, hits_rect, network, shortest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'massing'))
from architecture import Architecture, PALETTE, threshold_glyph, world_xy

ORDER = ("mandala", "lanka", "ayodhya", "kurukshetra")
W, H = 1440, 1030
INK, MUTED, LINE = "#203c40", "#455f61", "#a8b8ae"
PAPER, BOARD, FLOOR = "#f8f5eb", "#dde8e2", "#fff9e7"
COVER, WATER, RISE, FOLD, FIRE = "#34494c", "#23758a", "#44735c", "#714e89", "#a54726"
SANS, SERIF, MONO = "DejaVu Sans, sans-serif", "DejaVu Serif, serif", "DejaVu Sans Mono, monospace"


def num(value):
    return format(value, ".2f").rstrip("0").rstrip(".") if isinstance(value, float) else str(value)


def add(parent, tag, **attributes):
    return ET.SubElement(parent, tag, {k.replace("_", "-"): num(v) for k, v in attributes.items()})


def words(parent, x, y, value, size=15, fill=INK, family=SANS, **attributes):
    node = add(parent, "text", x=x, y=y, fill=fill, font_family=family, font_size=size, **attributes)
    node.text = str(value)
    return node


def rect(parent, x, y, w, h, fill, **style):
    return add(parent, "rect", x=x, y=y, width=w, height=h, fill=fill, **style)


def line(parent, x1, y1, x2, y2, color, width=1, **style):
    return add(parent, "line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=color, stroke_width=width, **style)


def circle(parent, x, y, r, fill, **style):
    return add(parent, "circle", cx=x, cy=y, r=r, fill=fill, **style)


def path(parent, points, color, width, **style):
    return add(parent, "polyline", points=" ".join(f"{x:.2f},{y:.2f}" for x, y in points),
               fill="none", stroke=color, stroke_width=width, stroke_linecap="round",
               stroke_linejoin="round", **style)


def kicker(parent, x, y, value, fill=MUTED):
    return words(parent, x, y, value.upper(), 13, fill, MONO, letter_spacing=1.25)


def codes(nodes):
    special = {"a": "A", "b": "B", "atk": "AT", "def": "DF", "mid": "M"}
    ordinary = [key for key in nodes if key not in special]
    return {**special, **{key: str(i) for i, key in enumerate(ordinary, 1)}}


def edge_points(nodes, edge):
    return [nodes[edge["from"]]["xz"], *edge.get("via", []), nodes[edge["to"]]["xz"]]


class View:
    def __init__(self, bounds, frame, pad):
        x1, z1, x2, z2 = bounds
        x, y, width, height = frame
        self.scale = min((width - 2 * pad) / (x2 - x1), (height - 2 * pad) / (z2 - z1))
        self.origin = (x + width / 2 - (x1 + x2) * self.scale / 2,
                       y + height / 2 + (z1 + z2) * self.scale / 2)

    def xy(self, p):
        return self.origin[0] + self.scale * p[0], self.origin[1] - self.scale * p[1]

    def footprint(self, group, item, fill, **style):
        x, z = item["xz"]
        w, d = item["size"]
        px, py = self.xy((x - w / 2, z + d / 2))
        return rect(group, px, py, w * self.scale, d * self.scale, fill, **style)


def marker(group, x, y, code, r=9.6):
    if code in ("A", "B"):
        return words(group, x, y + r * .5, code, r * 1.55, FIRE, SANS,
                     text_anchor="middle", font_weight="bold", stroke=PAPER, stroke_width=2.5,
                     paint_order="stroke")
    if code in ("AT", "DF"):
        rect(group, x - r * 1.55, y - r, r * 3.1, 2 * r, INK, rx=2)
    else:
        circle(group, x, y, r, INK if code == "M" else FLOOR, stroke=INK, stroke_width=1)
    words(group, x, y + 3.7, code, 11, PAPER if code in ("AT", "DF", "M") else INK, MONO,
          text_anchor="middle", font_weight="bold")


def map_view(svg, defs, data, frame, bounds, key, inset=None):
    nodes = data["nodes"]
    view = View(bounds, frame, 35 if not inset else 8)
    x, y, width, height = frame
    clip = add(defs, "clipPath", id="clip-" + key)
    rect(clip, x, y, width, height, "white")
    canvas = add(svg, "g", clip_path=f"url(#clip-{key})")
    rect(canvas, x, y, width, height, BOARD)
    xlo, zlo = (x - view.origin[0]) / view.scale, (view.origin[1] - y - height) / view.scale
    xhi, zhi = xlo + width / view.scale, zlo + height / view.scale
    spacing = 5 if inset else 10
    for u in range(math.ceil(xlo / spacing) * spacing, math.floor(xhi / spacing) * spacing + 1, spacing):
        px, _ = view.xy((u, 0))
        line(canvas, px, y, px, y + height, "#b7c9bf", .8 if u % (spacing * 4) == 0 else .4)
    for u in range(math.ceil(zlo / spacing) * spacing, math.floor(zhi / spacing) * spacing + 1, spacing):
        _, py = view.xy((0, u))
        line(canvas, x, py, x + width, py, "#b7c9bf", .8 if u % (spacing * 4) == 0 else .4)

    physical = [e for e in data["links"] if e["kind"] != "fold"]
    # Outline the union in two passes so a room edge does not draw a wall across a doorway.
    for border in (True, False):
        for e in physical:
            pts = [view.xy(p) for p in edge_points(nodes, e)]
            path(canvas, pts, INK if border else FLOOR, e["width"] * view.scale + (2.2 if border else 0))
        for n in nodes.values():
            view.footprint(canvas, n, FLOOR, stroke=INK if border else FLOOR, stroke_width=2.2 if border else 0)
    for e in data["links"]:
        kind = e["kind"]
        pts = [view.xy(p) for p in edge_points(nodes, e)]
        if kind == "water":
            path(canvas, pts, "#a7dbe0", max(2, e["width"] * view.scale - 1))
            path(canvas, pts, WATER, 1.4, stroke_dasharray="2 4")
        elif kind == "ramp":
            path(canvas, pts, RISE, 1.75, stroke_dasharray="6 3")
    # The floor of each room is level. A water approach stops at the threshold
    # and must never visually flood the dry ignition disk.
    for node_id, n in nodes.items():
        incident = [e["kind"] for e in physical if node_id in (e["from"], e["to"])]
        view.footprint(canvas, n, "#a7dbe0" if set(incident) == {"water"} else FLOOR)
    for e in data["links"]:
        if e["kind"] != "fold":
            continue
        pts = [view.xy(p) for p in edge_points(nodes, e)]
        path(canvas, pts, FOLD, 2.6, stroke_dasharray="8 5")
        for dx, dy in [pts[0], pts[-1]]:
            add(canvas, "polygon", points=f"{dx},{dy-5} {dx+5},{dy} {dx},{dy+5} {dx-5},{dy}",
                fill=FLOOR, stroke=FOLD, stroke_width=1.6)
            for stroke in threshold_glyph(e["quarter_turns"]):
                path(canvas,[(dx+12+u*5,dy+10-v*5) for u,v in stroke],FOLD,1.6)
    feature = data["architecture"]
    node = nodes[feature["node"]]
    fw,fd = feature["footprint"]
    footprint = [view.xy(world_xy(fw*i/2,fd*j/2,node,feature["axis_deg"]))
                 for i,j in [(-1,-1),(1,-1),(1,1),(-1,1),(-1,-1)]]
    path(canvas,footprint,"#816142",1.5,stroke_dasharray="9 3 2 3")
    for item in data["cover"]:
        view.footprint(canvas, item, "url(#hatch)", stroke=INK, stroke_width=1)
    for ray in data["sightlines"]:
        start, end = [view.xy(ray[which]) for which in ("from", "to")]
        path(canvas, [start, end], "#355a86", 1.8, stroke_dasharray="8 3 2 3")
        for px, py in [start, end]:
            circle(canvas, px, py, 2.4, FLOOR, stroke="#355a86", stroke_width=1.25)
    markers = codes(nodes)
    for site in ("a", "b"):
        cx, cy = view.xy(nodes[site]["xz"])
        for radius, stroke, dash in [(4.5, "#996849", "2 3"), (3, FIRE, "")]:
            circle(canvas, cx, cy, radius * view.scale, "none", stroke=stroke, stroke_width=1.45,
                   **({"stroke_dasharray": dash} if dash else {}))
    if not inset:
        for node_id, n in nodes.items():
            mx, my = view.xy(n["xz"])
            marker(canvas, mx, my, markers[node_id])
        north_x, north_y = x + width - 28, y + 40
        words(canvas, north_x, north_y - 17, "N", 13, INK, MONO, text_anchor="middle")
        add(canvas, "polygon", points=f"{north_x},{north_y-10} {north_x+6},{north_y+11} "
            f"{north_x},{north_y+7} {north_x-6},{north_y+11}", fill=INK)
    else:
        for index, c in enumerate(data["cover"], 1):
            cx, cy = view.xy(c["xz"])
            if x + 19 < cx < x + width - 19 and y + 11 < cy < y + height - 26:
                words(canvas, cx, cy + 3.5, f"C{index}", 11, PAPER, MONO, text_anchor="middle",
                      stroke=INK, stroke_width=2.5, paint_order="stroke")

    bar = 5 if inset else 20
    bx, by = x + 15, y + height - 14
    box_width = bar * view.scale + 12
    rect(canvas, bx - 6, by - 18, max(box_width, 47), 24, PAPER, rx=2, opacity=.92)
    words(canvas, bx, by - 6, f"{bar} m", 11, INK, MONO)
    line(canvas, bx, by, bx + bar * view.scale, by, INK, 2.1)
    for tx in (bx, bx + bar * view.scale):
        line(canvas, tx, by - 3, tx, by + 2, INK, 1.2)
    rect(svg, x, y, width, height, "none", stroke=LINE)
    return view


def draw_section(svg, data, left, top, width, height):
    nodes, ids = data["nodes"], data["section"]["route"]
    edges = {frozenset((e["from"], e["to"])): e for e in data["links"] if e["kind"] != "fold"}
    distances = [0.]
    for a, b in zip(ids, ids[1:]):
        points = edge_points(nodes, edges[frozenset((a, b))])
        distances.append(distances[-1] + sum(math.dist(p, q) for p, q in zip(points, points[1:])))
    levels = [nodes[k]["y"] for k in ids]
    bottom = top + height
    low, high = min(levels) - .75, max(levels) + .75
    plot_left, plot_w = left + 53, width - 86
    positions = [(plot_left + d / distances[-1] * plot_w,
                  bottom - 9 - (v - low) / (high - low) * (height - 20)) for d, v in zip(distances, levels)]
    for level in sorted(set(levels)):
        py = bottom - 9 - (level - low) / (high - low) * (height - 20)
        line(svg, plot_left, py, left + width - 22, py, LINE, .8, stroke_dasharray="3 4")
        if level in (min(levels), max(levels)):
            words(svg, left + 36, py + 4, f"{level:g}", 11, MUTED, MONO, text_anchor="end")
    first, last = positions[0], positions[-1]
    add(svg, "polygon", points=" ".join(f"{px:.2f},{py:.2f}" for px,py in
        [*positions, (last[0], bottom), (first[0], bottom)]), fill="#d5e4d9", opacity=.84)
    path(svg, positions, RISE, 2.6)
    tags = codes(nodes)
    for k, (px, py) in zip(ids, positions):
        circle(svg, px, py, 3, INK)
        words(svg, px, py - 8, tags[k], 12, INK, MONO, text_anchor="middle",
              paint_order="stroke", stroke=PAPER, stroke_width=2.3)
    words(svg, plot_left, bottom + 16, "0 m", 12, MUTED, MONO)
    words(svg, last[0], bottom + 16, f"{distances[-1]:.1f} m", 12, MUTED, MONO, text_anchor="end")


def legend(svg, data):
    entries = [("floor","Dry floor"), ("cover","Solid cover"), ("ramp","Ramp"),
               ("sight","Test sightline"), ("ring","3 m kindle / 4.5 m apron"),
               ("building","Building study")]
    kinds = {e["kind"] for e in data["links"]}
    if "water" in kinds:
        entries.insert(3, ("water","Shallow water"))
    if "fold" in kinds:
        entries.insert(3, ("fold","Fold"))
    x, y = 45, 986
    for k, label in entries:
        if k in ("floor","cover","water"):
            rect(svg, x, y - 10, 20, 12, {"floor":FLOOR,"cover":"url(#hatch)","water":"#a7dbe0"}[k],
                 stroke=INK, stroke_width=.85)
            if k == "water":
                line(svg,x+1,y-4,x+19,y-4,WATER,1.3,stroke_dasharray="2 3")
        elif k == "ring":
            circle(svg,x+9,y-4,5,"none",stroke=FIRE,stroke_width=1.2)
            circle(svg,x+9,y-4,9,"none",stroke=FIRE,stroke_width=1.1,stroke_dasharray="2 2")
        elif k == "building":
            rect(svg,x,y-10,21,12,"none",stroke="#816142",stroke_width=1.5,stroke_dasharray="9 3 2 3")
        else:
            color, dash = {"fold":(FOLD,"5 3"),"ramp":(RISE,"6 3"),"sight":("#355a86","6 3 1 3")}[k]
            line(svg,x,y-4,x+23,y-4,color,2,stroke_dasharray=dash)
        words(svg,x+29,y,label,14)
        x += 55 + len(label) * 7.5


def sheet(data, page):
    svg = ET.Element("svg", {"xmlns":"http://www.w3.org/2000/svg","width":str(W),"height":str(H),
        "viewBox":f"0 0 {W} {H}", "role":"img", "aria-labelledby":"title description"})
    add(svg,"title",id="title").text = f'{data["title"]} — Ember Rite level blueprint'
    add(svg,"desc",id="description").text = data["decision"] + " North is up. Two scaled site details and a floor elevation section accompany the plan."
    defs = add(svg, "defs")
    hatch = add(defs, "pattern", id="hatch", patternUnits="userSpaceOnUse", width=5, height=5)
    rect(hatch,0,0,5,5,COVER)
    line(hatch,0,5,5,0,"#b8c2b6",.65)
    rect(svg,0,0,W,H,PAPER)
    rect(svg,0,0,W,8,INK)
    kicker(svg,44,43,"YUGA    /    Ember Rite")
    words(svg,1396,43,f"LEVEL DESIGN     /     SHEET {page:02d} OF 12",13,MUTED,MONO,text_anchor="end",
          letter_spacing=1.1)
    words(svg,42,100,data["title"],48,INK,SERIF)
    words(svg,45,139,data["subtitle"],19,MUTED)
    line(svg,44,159,1396,159,INK,1.3)
    kicker(svg,44,188,"Floor plan")
    x1,z1,x2,z2 = data["bounds"]
    words(svg,650,188,f"{x2-x1:g} × {z2-z1:g} m   /   +Z north",13,MUTED,MONO,text_anchor="end")
    map_view(svg,defs,data,(44,202,608,701),data["bounds"],"plan")
    for j, sentence in enumerate(textwrap.wrap(data["decision"], 80)):
        words(svg,45,928 + j*19,sentence,14,INK)
    for site, x in [("a",686),("b",1052)]:
        n = data["nodes"][site]
        sx, sz = n["xz"]; width, depth = n["size"]
        kicker(svg,x,189,f"Site {site.upper()}   /   Detail",FIRE)
        words(svg,x,221,n["label"],24,INK,SERIF)
        # The detail window includes the room and adjacent approaches at the same plan aspect.
        dz = max(11, depth * .70, width * .42)
        dx = dz * 344 / 196
        map_view(svg,defs,data,(x,236,344,196),(sx-dx,sz-dz,sx+dx,sz+dz),"site-"+site,site)
        words(svg,x,455,f"{width:g} × {depth:g} m floor   /   elevation {n['y']:+g} m",13,MUTED,MONO)
    line(svg,686,478,1396,478,LINE)
    kicker(svg,686,505,"Callout key")
    words(svg,1396,505,"Floor elevation (m)",13,MUTED,MONO,text_anchor="end")
    tags = codes(data["nodes"])
    ids = ["atk","def","a","b","mid"] + [k for k in data["nodes"] if k not in ("atk","def","a","b","mid")]
    per_col = (len(ids) + 1) // 2
    row_gap = min(26,199 / max(1,per_col-1))
    for i, k in enumerate(ids):
        row, col = i % per_col, i // per_col
        x, y = 687+col*366, 535 + row*row_gap
        n = data["nodes"][k]
        marker(svg,x+13,y-5,tags[k],8.8)
        words(svg,x+38,y,n["label"],15,INK)
        words(svg,x+341,y,f"{n['y']:+g}",13,MUTED,MONO,text_anchor="end")
    line(svg,686,758,1396,758,LINE)
    kicker(svg,686,786,"Longitudinal section")
    section_title = data["section"]["title"]
    words(svg,686,813,section_title,20,INK,SERIF)
    draw_section(svg,data,686,835,710,76)
    words(svg,686,950,"Profile connects room centres. Vertical scale exaggerated. Landings are flat in the 3D model.",13,MUTED)
    line(svg,44,964,1396,964,INK,1)
    legend(svg,data)
    words(svg,1396,1011,"Design blockout    /    Ember Rite · 5v5",12,MUTED,MONO,text_anchor="end")
    ET.indent(svg, space="  ")
    return ET.tostring(svg,encoding="utf-8",xml_declaration=True) + b"\n"


def field_sheet(data, page, links, covers):
    svg = ET.Element("svg", {"xmlns":"http://www.w3.org/2000/svg","width":str(W),"height":str(H),
        "viewBox":f"0 0 {W} {H}","role":"img","aria-labelledby":"title description"})
    add(svg,"title",id="title").text = f'{data["title"]} — round rehearsal and prop schedule'
    add(svg,"desc",id="description").text = "Uncontested walking budgets, landmark callouts, cover elevations and shoulder-camera test lines."
    rect(svg,0,0,W,H,PAPER)
    rect(svg,0,0,W,8,INK)
    kicker(svg,44,43,"YUGA    /    Ember Rite")
    words(svg,1396,43,f"LEVEL DESIGN     /     SHEET {page:02d} OF 12",13,MUTED,MONO,
          text_anchor="end",letter_spacing=1.1)
    words(svg,42,100,data["title"] + "  /  Encounter notes",43,INK,SERIF)
    words(svg,44,139,"Carry the vessel, draw a response, and leave a route back to the fire.",19,MUTED)
    line(svg,44,159,1396,159,INK,1.3)
    kicker(svg,44,188,"Retake from the opposite site")
    kicker(svg,770,188,"Landmarks at player height and on the skyline")
    dry = network([e for e in links if e.kind in DRY])
    options = network(links)
    nodes = data["nodes"]
    starts = {"atk","def"}
    dry_time, dry_path, _ = shortest(dry,"a","b",starts)
    best, _, _ = shortest(options,"a","b",starts)
    bx, bw, by = 45, 644, 256
    words(svg,bx,225,"How much time does a late retake leave?",22,INK,SERIF)
    scale = bw / 40
    used = 0
    remaining = 40 - dry_time - 3.5
    for duration, fill in [(dry_time,"#42796c"),(3.5,"#ad5430"),(remaining,"#e0e7d5")]:
        visible = max(0., min(duration, 40 - used))
        if visible:
            rect(svg,bx+used*scale,by,visible*scale,18,fill)
        used += visible
    for t in (0,10,20,30,40):
        tx = bx + t*scale
        line(svg,tx,by+18,tx,by+24,INK)
        words(svg,tx,by+40,f"{t} s",12,MUTED,MONO,text_anchor="middle" if t not in (0,40) else ("start" if t==0 else "end"))
    slack = f"Time to react and fight  {remaining:.1f} s" if remaining >= 0 else f"Over the clock by  {abs(remaining):.1f} s"
    for xx, color, title in [(bx,"#42796c",f"Walk  {dry_time:.1f} s"),(bx+202,"#ad5430","Quench  3.5 s"),
                             (bx+408,"#768968",slack)]:
        rect(svg,xx,by+57,10,10,color)
        words(svg,xx+17,by+67,title,14,INK)
    route = " → ".join(nodes[k]["label"] for k in dry_path)
    for i, row in enumerate(textwrap.wrap(route,75)):
        words(svg,bx,by+98+20*i,row,16,INK)
    note = (f"With the optional crossings open, the fastest rotation takes {best:.1f} s."
            if best < dry_time - .05 else "Opening optional crossings leaves the fastest rotation time unchanged.")
    if not any(e.kind not in DRY for e in links):
        note = "Every crossing here is ordinary dry movement."
    words(svg,bx,by+149,note,14,MUTED)
    line(svg,44,423,713,423,LINE)
    kicker(svg,44,450,"Opening assignments   /   dry walking time")
    words(svg,329,482,"Attack spawn",15,MUTED)
    words(svg,527,482,"Defend spawn",15,MUTED)
    for i, goal in enumerate(("a","b","mid")):
        y = 514 + i * 31
        words(svg,44,y,nodes[goal]["label"],18,INK,SERIF)
        for xx, start in [(329,"atk"),(527,"def")]:
            closed = (starts - {start}) | ({"a","b"} - {goal})
            duration, _, _ = shortest(dry,start,goal,closed)
            words(svg,xx,y,f"{duration:.1f} s",16,INK,MONO)
    words(svg,44,607,"Centreline estimates at 5 m/s, before peeks, fighting and the final step to the vessel.",14,MUTED)

    for i, item in enumerate(data["artifacts"]):
        y = 225 + i*95
        words(svg,770,y,item["label"],22,INK,SERIF)
        words(svg,1395,y,nodes[item["node"]]["label"],14,MUTED,MONO,text_anchor="end")
        for j, row in enumerate(textwrap.wrap(item["cue"],73)):
            words(svg,770,y+27+21*j,row,15,INK)
    line(svg,44,631,1396,631,INK,1.1)
    kicker(svg,44,658,"Cover schedule   /   front elevations facing north")
    words(svg,1396,658,"Dashed guide at 1.7 m",13,MUTED,MONO,text_anchor="end")
    y_base = 780
    widths = [item["size"][0] for item in data["cover"]]
    col_width = (1396-44) / len(widths)
    px_per_m = min(22, (col_width-39) / max(widths))
    for i,item in enumerate(data["cover"]):
        xx = 44 + col_width * (i+.5)
        w,d = item["size"]
        h = item["height"]
        rect(svg,xx-w*px_per_m/2,y_base-h*px_per_m,w*px_per_m,h*px_per_m,COVER,
             stroke=INK,stroke_width=.8)
    line(svg,44,y_base,1396,y_base,INK)
    line(svg,44,y_base-1.7*px_per_m,1396,y_base-1.7*px_per_m,"#a77b5b",1.3,stroke_dasharray="5 4")
    for i,item in enumerate(data["cover"]):
        xx = 44 + col_width * (i+.5)
        w,d = item["size"]
        words(svg,xx,804,f"C{i+1}   {item['height']:g} m high",13,MUTED,MONO,text_anchor="middle")
        name_lines = textwrap.wrap(item["label"],22)
        for row, name in enumerate(name_lines):
            words(svg,xx,827+row*16,name,15,INK,SANS,text_anchor="middle")
        words(svg,xx,865,f"{w:g} × {d:g} m",13,MUTED,MONO,text_anchor="middle")
    line(svg,44,883,1396,883,LINE)
    kicker(svg,44,908,"Shoulder-camera tests")
    for i, probe in enumerate(data["sightlines"]):
        xx = 44 + i*685
        a, b = probe["from"], probe["to"]
        blockers = [name for name,box in covers if hits_rect(a,b,box)]
        words(svg,xx,939,probe["label"],20,INK,SERIF)
        names = ", ".join(blockers) if blockers else "clear in plan"
        words(svg,xx,963,f"{math.dist(a,b):.1f} m in plan  /  {names}",14,MUTED)
    line(svg,44,984,1396,984,INK,1)
    words(svg,44,1009,"Test from both ends, both shoulders, and at the near and far lips of the planted vessel.",14,MUTED)
    words(svg,1396,1009,"Design rehearsal    /    Ember Rite · 5v5",12,MUTED,MONO,text_anchor="end")
    ET.indent(svg,space="  ")
    return ET.tostring(svg,encoding="utf-8",xml_declaration=True) + b"\n"


def polygon(svg, points, fill, stroke=INK, width=.7, **attributes):
    area=sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(points,points[1:]+points[:1]))
    if abs(area) > .025:
        return add(svg,"polygon",points=" ".join(f"{x:.2f},{y:.2f}" for x,y in points),
                   fill=fill,stroke=stroke,stroke_width=width,stroke_linejoin="round",**attributes)


def cut_profile(part, axis, value):
    """Intersect a convex course with a true cutting plane from the mesh edges."""
    points = set()
    for face in part.faces:
        for i,j in zip(face,face[1:]+face[:1]):
            a,b=part.vertices[i],part.vertices[j]
            da,db=a[axis]-value,b[axis]-value
            if abs(da)<1e-7:
                points.add(tuple(round(v,7) for v in a))
            if da*db < 0:
                points.add(tuple(round(v+da/(da-db)*(w-v),7) for v,w in zip(a,b)))
    if len(points)<3:
        return []
    u,v=[i for i in range(3) if i!=axis]
    cx=sum(p[u] for p in points)/len(points)
    cy=sum(p[v] for p in points)/len(points)
    return sorted(points,key=lambda p:math.atan2(p[v]-cy,p[u]-cx))


def dimension(svg, p, q, offset, label):
    dx,dy=q[0]-p[0],q[1]-p[1]
    length=math.hypot(dx,dy)
    ux,uy=dx/length,dy/length
    nx,ny=-uy,ux
    a=(p[0]+nx*offset,p[1]+ny*offset)
    b=(q[0]+nx*offset,q[1]+ny*offset)
    line(svg,*a,*b,MUTED,.9)
    for old,end in [(p,a),(q,b)]:
        line(svg,*old,end[0]+nx*3,end[1]+ny*3,MUTED,.7)
        line(svg,end[0]-3*ux-2*nx,end[1]-3*uy-2*ny,end[0]+3*ux+2*nx,end[1]+3*uy+2*ny,INK,1)
    x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
    theta=math.degrees(math.atan2(dy,dx))
    if theta>90: theta-=180
    if theta<=-90: theta+=180
    words(svg,x,y-4,label,12,INK,MONO,text_anchor="middle",transform=f"rotate({theta:g} {x:g} {y:g})",
          stroke=PAPER,stroke_width=2.7,paint_order="stroke")


def detail_plan(svg, arch, frame):
    left,top,w,h=frame
    rect(svg,left,top,w,h,BOARD,stroke=LINE)
    angle=math.radians(arch.bearing)
    c,s=math.cos(angle),math.sin(angle)
    a,b=arch.w/2,arch.d/2
    scale=min((w-138)/(2*(a*abs(c)+b*abs(s))),(h-106)/(2*(a*abs(s)+b*abs(c))))
    mx,my=left+w/2,top+h/2
    def project(p):
        x,y=p[:2]
        return mx+scale*(x*c+y*s),my-scale*(-x*s+y*c)
    # Grid ticks describe plan registration. Feature coordinates retain their survey datum.
    for direction,center,extent in [(0,mx,w),(1,my,h)]:
        for step in range(-math.ceil(extent/scale/4),math.ceil(extent/scale/4)+1):
            val=center+step*2*scale
            if direction==0 and left<val<left+w:
                line(svg,val,top,val,top+h,"#c1d2c9",.7)
            elif direction==1 and top<val<top+h:
                line(svg,left,val,left+w,val,"#c1d2c9",.7)
    outline=[project(v) for v in [(-a,-b),(a,-b),(a,b),(-a,b)]]
    polygon(svg,outline,FLOOR,LINE)
    cut_height=min(.95,arch.height*.24)
    # Top faces below the cut show the material and terrace steps. Solids pierced
    # by the horizontal cut use the darker section ink.
    surfaces=[]
    for part in arch.parts:
        for face in part.faces:
            pts=[part.vertices[i] for i in face]
            if max(p[2] for p in pts)<=cut_height:
                surfaces.append((sum(p[2] for p in pts)/len(pts),part.material,pts))
    for _,mat,pts in sorted(surfaces,key=lambda s:s[0]):
        polygon(svg,[project(v) for v in pts],PALETTE[mat],MUTED,.55)
    for part in arch.parts:
        pts=cut_profile(part,2,cut_height)
        if pts:
            polygon(svg,[project(v) for v in pts],INK,INK,.6)
    path(svg,outline+[outline[0]],MUTED,1.4,stroke_dasharray="5 3")
    p,q=project((-a,-b)),project((a,-b))
    dimension(svg,p,q,22,f"{arch.w:g} m")
    dimension(svg,project((a,-b)),project((a,b)),24,f"{arch.d:g} m")
    p,q=project((0,-b)),project((0,b))
    path(svg,[p,q],FIRE,1.7,stroke_dasharray="6 3")
    ux,uy=(q[0]-p[0])/(arch.d*scale),(q[1]-p[1])/(arch.d*scale)
    for marker_pos,letter in [(p,"I"),(q,"II")]:
        circle(svg,*marker_pos,9,PAPER,stroke=FIRE,stroke_width=1.3)
        words(svg,*[marker_pos[0],marker_pos[1]+4],letter,10,FIRE,MONO,text_anchor="middle")
    mid=(mx+ux*12,my+uy*12)
    arrow=[mid,(mid[0]-7*ux-3.5*uy,mid[1]-7*uy+3.5*ux),
           (mid[0]-7*ux+3.5*uy,mid[1]-7*uy-3.5*ux)]
    polygon(svg,arrow,FIRE,FIRE)
    # Section mark crosses the building at its central transverse station.
    sta,sb=project((-a,arch.cut_axial)),project((a,arch.cut_axial))
    line(svg,*sta,*sb,"#486989",1.2,stroke_dasharray="8 3 2 3")
    nx,ny=left+w-27,top+35
    words(svg,nx,ny-11,"N",12,INK,MONO,text_anchor="middle")
    polygon(svg,[(nx,ny-6),(nx+5,ny+10),(nx,ny+6),(nx-5,ny+10)],INK)
    line(svg,left+16,top+h-17,left+16+2*scale,top+h-17,INK,2)
    words(svg,left+16,top+h-23,"2 m",12,INK,MONO)
    words(svg,left+w-13,top+h-13,f"Plan cut  +{cut_height:.2f} m",11,MUTED,MONO,text_anchor="end")


def detail_elevation(svg, arch, frame, sliced=False):
    left,top,w,h=frame
    rect(svg,left,top,w,h,"#f0ede1",stroke=LINE)
    under=arch.water_level-.28 if arch.water_level is not None else 0
    scale=min((w-139)/arch.w,(h-80)/(arch.height-under))
    mx=left+w/2
    baseline=top+(h+(arch.height+under)*scale)/2
    def project(v):
        return mx+v[0]*scale,baseline-v[2]*scale
    if sliced:
        for part in arch.parts:
            pts=cut_profile(part,1,arch.cut_axial)
            if pts:
                fill=PALETTE[part.material] if part.material=="Water" else "#6e746b"
                polygon(svg,[project(v) for v in pts],fill,INK,.8)
    else:
        faces=[]
        for part in arch.parts:
            for face in part.faces:
                vertices=[part.vertices[i] for i in face]
                faces.append((sum(p[1] for p in vertices)/len(vertices),part.material,vertices))
        for _,mat,vertices in sorted(faces,key=lambda f:-f[0]):
            polygon(svg,[project(v) for v in vertices],PALETTE[mat],MUTED,.65)
    line(svg,left+12,baseline,left+w-12,baseline,MUTED,.8,stroke_dasharray="5 3")
    words(svg,left+12,baseline-5,f"{arch.level:+g} m",12,MUTED,MONO)
    if sliced and arch.water_level is not None:
        py=baseline-scale*arch.water_level
        line(svg,left+12,py,left+w-12,py,WATER,1,stroke_dasharray="3 3")
        words(svg,left+12,py+13,f"{arch.water_level+arch.level:+g} m",12,WATER,MONO)
    if not sliced:
        end=mx+arch.w*scale/2
        dimension(svg,(end,baseline),(end,baseline-arch.height*scale),23,f"{arch.height:g} m")
        if arch.clear_height:
            dimension(svg,(mx,baseline),(mx,baseline-arch.clear_height*scale),-16,
                      f"{arch.clear_height:.2f} m clear")
    else:
        p=(mx-arch.opening*scale/2,baseline)
        q=(mx+arch.opening*scale/2,baseline)
        dimension(svg,p,q,-19 if arch.water_level is not None else 18,f"{arch.opening:g} m clear")
    if arch.water_level is None and sliced:
        words(svg,left+w-13,top+h-13,f"Axial station  {arch.cut_axial+arch.d/2:.2f} m from I",12,MUTED,MONO,text_anchor="end")


def architecture_sheet(data,page,links):
    arch=Architecture(data)
    svg=ET.Element("svg",{"xmlns":"http://www.w3.org/2000/svg","width":str(W),"height":str(H),
                          "viewBox":f"0 0 {W} {H}","role":"img","aria-labelledby":"title description"})
    add(svg,"title",id="title").text=data["title"]+" — "+arch.name+" plan, elevation and transverse section"
    add(svg,"desc",id="description").text=arch.play+" The plan is north up, uses metres, and locates two opposed thresholds."
    rect(svg,0,0,W,H,PAPER)
    rect(svg,0,0,W,8,INK)
    kicker(svg,44,43,"YUGA    /    Ember Rite")
    words(svg,1396,43,f"LEVEL DESIGN     /     SHEET {page:02d} OF 12",13,MUTED,MONO,text_anchor="end",letter_spacing=1.1)
    words(svg,42,100,arch.name,47,INK,SERIF)
    host = data["architecture"]["node"]
    number = codes(data["nodes"])[host]
    words(svg,44,139,f'{data["title"]}  /  map station {number}, {arch.node["label"]}  /  {arch.form.replace("_"," ")}',19,MUTED)
    line(svg,44,159,1396,159,INK,1.3)
    kicker(svg,44,189,"Threshold plan   /   north up")
    kicker(svg,723,189,"Elevation   /   from entrance I")
    detail_plan(svg,arch,(44,203,647,341))
    detail_elevation(svg,arch,(723,203,673,341))
    p,q=arch.thresholds
    words(svg,44,570,f"I  ({p[0]:g}, {p[1]:g})     II  ({q[0]:g}, {q[1]:g})     map X, Z in metres",14,INK,MONO)
    words(svg,723,570,f"Bearing I → II   {arch.bearing%360:03g}°      II → I   {(arch.bearing+180)%360:03g}°",14,INK,MONO)
    line(svg,44,593,1396,593,LINE)
    kicker(svg,44,621,"Transverse section   /   marked line")
    kicker(svg,723,621,"Route register")
    detail_elevation(svg,arch,(44,637,647,274),sliced=True)
    node_id=data["architecture"]["node"]
    nodes=data["nodes"]
    dry=network([e for e in links if e.kind in DRY])
    branches={}
    ax=(math.sin(math.radians(arch.bearing)),math.cos(math.radians(arch.bearing)))
    for link in data["links"]:
        if link["kind"] not in DRY or node_id not in (link["from"],link["to"]):
            continue
        a,b=link["from"],link["to"]
        neighbor=b if a==node_id else a
        line_points=edge_points(nodes,link)
        point=line_points[1] if a==node_id else line_points[-2]
        tx,ty=point[0]-arch.node["xz"][0],point[1]-arch.node["xz"][1]
        branches[neighbor]=(tx*ax[0]+ty*ax[1])/math.hypot(tx,ty)
    sequence=[nodes[k]["label"] for k in sorted(branches,key=branches.get)]
    stages=[sequence[0],arch.node["label"],sequence[-1]] if len(sequence)>=2 else [arch.node["label"],*sequence]
    words(svg,723,658," → ".join(stages),22,INK,SERIF)
    for i,row in enumerate(textwrap.wrap(arch.play,78)):
        words(svg,723,687+i*21,row,15,MUTED)
    folds=[e for e in data["links"] if e["kind"]=="fold"]
    if folds:
        for i,e in enumerate(folds):
            y=762+i*72
            a,b=e["from"],e["to"]
            duration,_,_=shortest(dry,a,b,set(("atk","def","a","b"))-{a,b})
            turn=e["quarter_turns"]*90
            words(svg,723,y,nodes[a]["label"]+" ⇄ "+nodes[b]["label"],18,INK,SERIF)
            words(svg,723,y+22,f"Outbound {turn:+g}°   /   return {-turn:+g}°   ·   {e['seconds']:g} s fold   ·   {duration:.1f} s dry",14,FOLD,MONO)
            words(svg,723,y+43,e["cue"],13,MUTED)
    else:
        blocked={"atk","def"}
        walk,_,_=shortest(dry,"a","b",blocked)
        any_route,_,_=shortest(network(links),"a","b",blocked)
        words(svg,723,764,"A → B change of site",19,INK,SERIF)
        words(svg,723,790,f"{walk:.1f} s dry   /   {any_route:.1f} s with optional routes",15,INK,MONO)
        water_edges=[e for e in data["links"] if e["kind"]=="water"]
        if water_edges:
            e=next((e for e in water_edges if node_id in (e["from"],e["to"])),water_edges[0])
            low,high=[nodes[e[key]] for key in ("from","to")]
            words(svg,723,829,"Wading approach   /   landing floor datums",14,MUTED)
            words(svg,723,853,f"{low['label']}  {low['y']:+g} m    →    {high['label']}  {high['y']:+g} m",15,INK)
        else:
            words(svg,723,838,"Both exits join ordinary dry routes.",15,MUTED)
    if arch.water_level is None:
        note=f"Passage {arch.opening:g} m wide. Full-width headroom {arch.clear_height:.2f} m above the dry threshold."
    else:
        note=f"Dry deck {arch.level:+g} m. Side-basin water study {arch.level+arch.water_level:+g} m. The central route stays open to the sky."
    words(svg,44,938,note,14,MUTED)
    line(svg,44,963,1396,963,INK,1)
    words(svg,44,990,f"Architectural reference {arch.source_id}   ·   Route-strip reference C1   ·   All dimensions are YUGA design values.",14,MUTED)
    words(svg,1396,990,"Original district study    /    metres",12,MUTED,MONO,text_anchor="end")
    ET.indent(svg,space="  ")
    return ET.tostring(svg,encoding="utf-8",xml_declaration=True)+b"\n"


def make_pdf(directory, sheets):
    # Inkscape embeds glyphs as text, keeping the print atlas searchable and zoomable.
    from pypdf import PdfWriter
    with tempfile.TemporaryDirectory() as temp:
        writer = PdfWriter()
        for index, source in enumerate(sheets):
            pdf = Path(temp) / (source.stem + ".pdf")
            subprocess.run(["inkscape", str(source), "--export-filename=" + str(pdf)], check=True,
                           env={**os.environ, "SOURCE_DATE_EPOCH":"0"})
            writer.append(pdf, import_outline=False)
            if index % 3 == 0:
                title = json.loads((ROOT / "maps" / f"{source.stem}.json").read_text())["title"]
                outline = writer.add_outline_item(title, index)
            else:
                writer.add_outline_item("Encounter notes" if index % 3 == 1 else "Architectural detail",
                                        index, parent=outline)
        writer.add_metadata({"/Title":"YUGA | Ember Rite map atlas","/Author":"YUGA level design"})
        with (directory / "yuga-map-atlas.pdf").open("wb") as out:
            writer.write(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf",action="store_true",help="also assemble the vector PDF with Inkscape and pypdf")
    parser.add_argument("--out",type=Path,default=ROOT / "blueprints")
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    files = []
    for index, key in enumerate(ORDER):
        data = json.loads((ROOT / "maps" / f"{key}.json").read_text())
        links, covers = audit_geometry(data)
        page = 3 * index + 1
        for stem, drawing in ((key, sheet(data, page)),
                              (key + "-encounters", field_sheet(data, page + 1, links, covers)),
                              (key + "-architecture", architecture_sheet(data, page + 2, links))):
            output = args.out / f"{stem}.svg"
            output.write_bytes(drawing)
            files.append(output)
    if args.pdf:
        make_pdf(args.out,files)


if __name__ == "__main__":
    main()
