"""Render the native Confluence manifest. Run with Python 3 and Matplotlib."""
import hashlib
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[2] / "assets/world/confluence-map.json"
PROPOSAL = {"name": "Offshore sanctuary", "xz_m": [-83, 45],
            "status": "Unbuilt candidate location for the illustration only. Outside the playable bounds. "
                      "The proposal adds no new geometry, collision or navigation. Its sightline has not been tested."}

PAPER, INK, MUTED, RULE = "#f8f5ec", "#152f30", "#415c58", "#c3c9b9"
SEA, TEAL, BRICK = "#cbe2da", "#20756a", "#a54938"
LANE = ["#95532b", "#566e35", "#4c6988"]
TEAM = {"sun": "#ae502e", "moon": "#425a87"}
BLOCK = "#58615e"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xz(point):
    return [point[0], point[2]]


def map_xy(point):
    """East (+X) points down, Sun to Moon (+Z) points right."""
    x, z = point
    return (z, -x)


def footprint(ax, center, dimensions, **style):
    cx, cy = map_xy(center)
    x, z = dimensions
    ax.add_patch(Rectangle((cx - z / 2, cy - x / 2), z, x, **style))


def lane_band(ax, points, half_width):
    # Use world metres for the clear corridor, independently of figure size.
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        dx, dy = x1-x0, y1-y0
        normal = half_width / math.hypot(dx, dy)
        a, b = -dy * normal, dx * normal
        corners = [(x0+a,y0+b),(x1+a,y1+b),(x1-a,y1-b),(x0-a,y0-b)]
        ax.add_patch(Polygon(corners, color="#e6e2d3", linewidth=0, zorder=2))
    for p in points:
        ax.add_patch(Circle(p, half_width, color="#e6e2d3", linewidth=0, zorder=2))


def write_plan():
    manifest = json.loads(SOURCE.read_bytes())
    lanes = sorted(manifest["lanes"], key=lambda lane: lane["id"])
    spawns = {entry["team"]: xz(entry["position"]) for entry in manifest["spawns"]}
    goals = manifest["objectives"]
    cores = {entry["team"]: xz(entry["position"]) for entry in goals if entry["kind"] == "core"}
    xmin, xmax, zmin, zmax = manifest["bounds"]["actor_xz"]
    boxes = manifest["authority_collision_boxes"]
    decks = manifest["traversal"]["native_collision_boxes"]
    waters = manifest["waters"]
    assert len(lanes) == 3 and len(boxes) == len(decks) == 8
    assert all(o["visual_only"] for o in goals if o["kind"] == "tower")
    proposed_x, proposed_z = PROPOSAL["xz_m"]
    assert not (xmin <= proposed_x <= xmax and zmin <= proposed_z <= zmax)

    skyline = next(p for p in manifest["props"] if p["id"] == "skyline-1")
    assert skyline["preset"] == "lanka_shikhara" and skyline["yaw_degrees"] == 0
    skyline_xz, skyline_size = xz(skyline["position"]), xz(skyline["scale"])
    assert all(abs(p-c) <= size/2 for p,c,size in zip(PROPOSAL["xz_m"],skyline_xz,skyline_size))
    nearby_scenery = {
        "id":skyline["id"], "preset":skyline["preset"], "center_xz_m":skyline_xz,
        "size_xz_m":skyline_size, "height_m":skyline["scale"][1], "collision":skyline["collision"],
        "distance_between_centers_m":round(math.dist(PROPOSAL["xz_m"],skyline_xz),3),
        "relationship":"The proposed point lies within the existing scenic tower footprint.",
        "design_decision":"Recompose or replace the existing scenic instance when testing a sanctuary here. "
                          "Adding a second tower at this point would overlap the first."}

    measures = []
    for lane in lanes:
        route = [xz(p) for p in lane["points"]]
        length = sum(math.dist(a,b) for a,b in zip(route, route[1:]))
        assert abs(length-lane["length_metres"]) < .001
        assert route[0] == spawns["sun"] and route[-1] == spawns["moon"]
        measures.append({"name":lane["name"], "centerline_xz_m":route, "centerline_m":round(length,3),
            "clear_width_m":2*lane["clear_half_width"], "spawn_to_opposite_core_via_lane_m":{
                side: round(length + math.dist(spawns[other], cores[other]),3)
                for side,other in (("sun","moon"),("moon","sun"))}})
    assert len({m["clear_width_m"] for m in measures}) == 1
    clear_width = measures[0]["clear_width_m"]

    plt.rcParams.update({"font.family":"DejaVu Sans", "savefig.facecolor":PAPER, "hatch.linewidth":.5})
    fig = plt.figure(figsize=(14.5,8.3), facecolor=PAPER)
    def figtext(x,y,text,sz=10,color=INK,**kw):
        return fig.text(x,y,text,fontsize=sz,color=color,va="top",**kw)
    def separator(y):
        fig.add_artist(plt.Line2D([.044,.956],[y,y],transform=fig.transFigure,color=RULE,lw=.85))
    def side_line(y):
        fig.add_artist(plt.Line2D([.74,.956],[y,y],transform=fig.transFigure,color=RULE,lw=.65))

    figtext(.044,.953,"YUGA   /   WORLD DESIGN",10,TEAL,weight="bold")
    figtext(.044,.91,"The three lanes of Confluence",32,fontfamily="DejaVu Serif",weight="bold")
    figtext(.046,.831,"A ground plan of both bases, the reed courts and a possible landmark across the sea.",12,MUTED)
    separator(.785)
    ax = fig.add_axes([.043,.13,.67,.625],facecolor=PAPER)
    ax.set_aspect("equal")
    ax.set_xlim(-139,139)
    ax.set_ylim(-83,103)
    ax.axis("off")

    # All rectangles use their actual sizes, including the portions outside actor bounds.
    for water in waters:
        if water["style"]=="coast":
            footprint(ax,xz(water["position"]),water["size_xz"],facecolor=SEA,edgecolor="none",zorder=1)
    footprint(ax,[(xmin+xmax)/2,(zmin+zmax)/2],[xmax-xmin,zmax-zmin],facecolor="#efeddf",
              edgecolor="#587263",linewidth=1.1,zorder=1)
    for lane, col in zip(lanes, LANE):
        pts = [map_xy(xz(p)) for p in lane["points"]]
        lane_band(ax,pts,lane["clear_half_width"])
        ax.plot(*zip(*pts),color=col,linewidth=1.9,zorder=3,solid_capstyle="round")
    for box in boxes:
        footprint(ax,xz(box["position"]),xz(box["size"]),facecolor=BLOCK,edgecolor=INK,linewidth=.6,zorder=4)
    for box in decks:
        footprint(ax,xz(box["position"]),xz(box["size"]),facecolor="#e3e3d7",edgecolor="#81877b",
                  hatch="///",linewidth=.65,zorder=4)
    for water in waters:
        if water["style"]=="swamp":
            footprint(ax,xz(water["position"]),water["size_xz"],facecolor="#86bdae",edgecolor=TEAL,
                      hatch="---",linewidth=.75,zorder=4)
    for district in manifest["districts"]:
        if district["id"] not in {"west-swamp", "east-swamp"}:
            continue
        x0, x1, z0, z1 = district["bounds_xz"]
        ax.text((z0+z1)/2 - 33, -(x0+x1)/2, district["name"], ha="right", va="center",
                size=8, color=TEAL)
    for obj in goals:
        team = TEAM[obj["team"]]
        core = obj["kind"]=="core"
        ax.scatter(*map_xy(xz(obj["position"])),marker="D" if core else "s",s=59 if core else 35,
                   facecolor=team if core else PAPER,edgecolor=team,linewidth=1.5,zorder=5)
    for side, point in spawns.items():
        ax.scatter(*map_xy(point),marker="o",s=37,facecolor=PAPER,edgecolor=TEAM[side],lw=1.6,zorder=6)
        ax.text(point[1],-75,side.capitalize()+" base",ha="center",va="center",color=TEAM[side],weight="bold",size=10)
    for lane, color in zip(lanes, LANE):
        # Label each centreline between the right-hand tower and the middle court.
        ax.text(46,-lane["center_x"]+2.8,lane["name"],fontsize=8.8,color=color,ha="center",
                va="bottom",bbox=dict(facecolor="#efeddf",edgecolor="none",pad=.5),zorder=7)
    sea = next(w for w in waters if w["style"]=="coast")
    _,sea_y = map_xy(xz(sea["position"]))
    ax.text(-112,sea_y,"Lanka Sea",fontsize=11,color=TEAL,fontfamily="DejaVu Serif",va="center")
    footprint(ax,skyline_xz,skyline_size,facecolor="none",edgecolor="#65857b",linewidth=.8,zorder=6)
    px,py = map_xy(PROPOSAL["xz_m"])
    ax.add_patch(Circle((px,py),3.3,fill=False,edgecolor=BRICK,linestyle=(0,(2.5,2)),linewidth=1.4,zorder=7))
    ax.scatter(px,py,s=12,marker="+",color=BRICK,lw=1,zorder=8)
    ax.text(px+13,py,"Proposed sanctuary",va="center",color=BRICK,size=8.5,weight="bold",zorder=7)
    # An accurate scale bar uses the same metre coordinate system as the lanes.
    ax.plot([-17,3],[-75,-75],color=INK,lw=1.1)
    ax.vlines([-17,3],-76,-74,color=INK,lw=1.1)
    ax.text(6,-75,"20 m",va="center",color=MUTED,size=8)

    figtext(.74,.751,"Routes between bases",14,fontfamily="DejaVu Serif",weight="bold")
    for i,(lane,m,col) in enumerate(zip(lanes,measures,LANE)):
        y=.69-.039*i
        fig.add_artist(plt.Line2D([.741,.762],[y+.002,y+.002],transform=fig.transFigure,color=col,lw=2.3))
        figtext(.772,y+.012,lane["name"],10)
        figtext(.956,y+.012,f"{m['centerline_m']:,.1f} m",10,ha="right")
    figtext(.74,.57,f"Each lane has an {clear_width:g} m clear corridor.",9,MUTED)
    side_line(.525)
    figtext(.74,.502,"Reading the plan",14,fontfamily="DejaVu Serif",weight="bold")

    def symbol(y, label, marker, fill, edge):
        mark = plt.Line2D([.749],[y+.001],marker=marker,ms=6,mfc=fill,mec=edge,mew=1.3,
                          linestyle="none",transform=fig.transFigure)
        fig.add_artist(mark)
        figtext(.772,y+.012,label,9.5)
    symbol(.444,"Team base spawn","o",PAPER,INK)
    symbol(.409,"Core objective","D",INK,INK)
    symbol(.374,"Tower wayfinding marker","s",PAPER,INK)
    for y,name,fill,edge,hatch in [( .338,"Building footprint",BLOCK,INK,""),
        (.303,"Raised deck footprint","#e3e3d7","#81877b","///"),(.268,"Shallow reed water","#86bdae",TEAL,"---")]:
        fig.add_artist(Rectangle((.7405,y-.005),.017,.015,transform=fig.transFigure,facecolor=fill,
                                 edgecolor=edge,hatch=hatch,lw=.7))
        figtext(.772,y+.013,name,9.5)
    side_line(.23)
    figtext(.74,.212,"Proposed sanctuary",12,BRICK,weight="bold")
    figtext(.74,.175,"Unbuilt, offshore. The outlined area holds\nan existing skyline tower. Recompose or\nreplace that tower to test this site.",9.3,MUTED,linespacing=1.35)
    separator(.094)
    figtext(.044,.073,"Coordinates in metres   ·   +Z right, +X down   ·   Base spawns shown. Rust matches deploy heroes near the front line.",9,MUTED)
    figtext(.956,.073,f"Confluence map  /  revision {manifest['revision']}",9,MUTED,ha="right")
    output=HERE/"map-plan.png"
    fig.savefig(output,dpi=160,metadata={"Software":"Matplotlib"})
    plt.close(fig)
    def inventory(entries):
        return [{"id":e["id"],"center_xz_m":xz(e["position"]),"size_xz_m":xz(e["size"])} for e in entries]
    receipt={"source":"games/yuga-native/assets/world/confluence-map.json","source_sha256":sha256(SOURCE),
        "manifest_revision":manifest["revision"], "generator_sha256":sha256(Path(__file__)),
        "reproduce":"python games/yuga-native/docs/research/elden-ring-world-study/map-plan.py",
        "matplotlib_version":matplotlib.__version__, "figure":{"file":output.name, "sha256":sha256(output),
        "pixels":[2320,1328],"axes":"horizontal is +Z; upward is −X; equal linear scale in metres"},
        "playable_envelope_x_min_max_z_min_max_m":[xmin,xmax,zmin,zmax],"hero_radius_m":manifest["bounds"]["hero_radius"],
        "lane_routes":measures,"distance_method":"Sum of Euclidean X/Z distances along waypoints. "
        "Core distance adds the short segment from the opposing lane endpoint to its core, measured to marker centres. "
        "These are distances along a particular route, not hero deployment distances, timings or sightline measurements.",
        "team_base_spawns_xz_m":spawns, "straight_line_spawn_to_opposite_core_m":{side:math.dist(spawns[side],cores[other])
            for side,other in (("sun","moon"),("moon","sun"))}, "objectives":[{"id":o["id"],"kind":o["kind"],"xz_m":xz(o["position"]),
        "wayfinding_only":o["visual_only"]} for o in goals],
        "building_footprints":inventory(boxes),"raised_deck_footprints":inventory(decks),
        "waters":[{"id":w["id"],"type":w["style"],"center_xz_m":xz(w["position"]),"size_xz_m":w["size_xz"],
                   "traversal":w["traversal"]} for w in waters],
        "proposed_site":{**PROPOSAL, "existing_scenery":nearby_scenery},"scope":"Only the proposed site is a diagram placement. "
        "Base spawns and objective positions are authored coordinates; Rust hero deployment follows Army::frontline_spawn_for."}
    (HERE/"map-measurements.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")


if __name__ == "__main__":
    write_plan()
