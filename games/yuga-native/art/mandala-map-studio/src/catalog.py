#!/usr/bin/env python3
"""Export the Mandala studio catalog and original orthographic plates from its registered atlas."""
import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from hashlib import sha256
import json
from math import atan2, ceil, cos, degrees, dist, floor, hypot, pi, sin
from pathlib import Path
import re
import sys
import struct
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

STUDIO = Path(__file__).resolve().parents[1]
NATIVE = STUDIO.parents[1]
ATLAS = NATIVE / "docs/design/ember-rite-5v5/atlas"
sys.path.insert(0, str(ATLAS))
sys.path.insert(0, str(ATLAS / "massing"))
from audit import audit_geometry
from architecture import Architecture

SOURCE = ATLAS / "maps/mandala.json"
DOC = "../../docs/design/ember-rite-5v5/atlas/"
REF = {
    "layout": ("Registered map dimensions", DOC + "maps/mandala.json"),
    "mandala": ("District and gameplay study", DOC + "maps/mandala.md"),
    "pavilion": ("Pavilion plan, elevation and section", DOC + "blueprints/mandala-architecture.svg"),
    "parts": ("Measured building and approach clearances", DOC + "massing/architecture-checks.md"),
    "model": ("Editable pavilion part definitions", DOC + "massing/architecture.py"),
    "rite": ("Ritual interaction rules", DOC + "../ROUND_AND_TECH.md"),
    "objective": ("Original YUGA vessel concept", "../ember-rite-5v5/README.md"),
    "M1": ("M1 · Chola temple profiles", "https://whc.unesco.org/en/list/250/"),
    "M2": ("M2 · Hampi, markets and waterworks", "https://whc.unesco.org/en/list/241/"),
    "pampa": ("Pampā banks in Griffith’s Kiṣkindhā Kāṇḍa", "https://github.com/GITenberg/The-R-m-yan-of-V-lm-ki-translated-into-English-verse_24869/blob/b48a7a226e8a20bed61131382aa5b8bf2206e039/24869-0.txt#L37383"),
    "read": ("Historical and literary source applications", DOC + "RESEARCH_ROUNDS.md"),
    "floor": ("Exported continuous floor", DOC + "massing/mandala.glb"),
    "propmesh": ("Studio prop construction", "src/props.py"),
    "path": ("Measured routes and assumptions", DOC + "measurements.md#mandala-rift"),
}
# Study, material/lighting instruction and player cue for each distinct architectural silhouette.
ROOMS = {
 "atk": ("spice", "A broad trade gate carries two spice awnings of unequal drop. Sack seals and ochre wash sit below the arch spring.", "Use burnt madder against pale lime. Keep the three exits open under a quiet cream fascia.", "Choose reed steps to the west, the temple ahead, or the cloth court to the east."),
 "def": ("watergate", "A twin stone intake frames a suspended copper bucket. Water marks climb the piers in horizontal bands.", "Cut pale scour lines into dark wet basalt. Rim the idle bucket with dull copper.", "Read the Jar Steps, North Temple and Scale Yard exits before choosing a setup."),
 "a": ("bellcourt", "Three unequal bell ribs rise behind the western screen. The floor carries a deeply cut round ring visible around a placed vessel.", "Pick out a chalk lip in limestone. Reserve warm motion for the actual ember.", "Identify the placed vessel independently of the bell and the centre of A."),
 "b": ("bazaar", "The market hall frames a square weighbeam, a high shuttered dye cabinet and a low counter around an open round disk.", "Lay indigo shutters under an ivory fascia. Counter edges must stay legible in grayscale.", "Clear both sides of the cabinet and look for the actual vessel near B’s lip."),
 "mid": ("sluice", "A notched copper lifting wheel and gearbox sit inside the northwest edge of a raised landing.", "Patinate the iron bolts and pale the crest stone. The stopped lift only turns in the story shot.", "Leave the crest to check the ghat or market lip beyond the bent ramps."),
 "steps_s": ("reeds", "Short ghat flights cut the bank in oblique treads. Bent reed plumes split the waterline from the dry climb.", "Dry honed amber risers meet a cool silt line. Keep reeds low beside the route.", "West follows the wet loop. The inland rise brings an escort onto Dry Bank."),
 "steps_n": ("jarsteps", "Terracotta water jars rest behind three landings. Circular rims separate this stairhead from the southern reeds.", "Keep the jars matte, darken their damp bases and limewash the last tread.", "A defender can choose the low ford or the return above the bank."),
 "bank": ("bank", "A low broken parapet follows the raised outer bank. Water lilies sit well below the coping silhouette.", "Use dry straw stone against green-gray water and a quiet plaster return.", "The parapet marks the high approach into A and the escape from Reed Ford."),
 "ford": ("ford", "Flat pale stepping stones show through the shallow bed. Small wake lines collect against low gravel ridges.", "Glaze only the wet faces. Celadon ripples remain readable with sparks and sound off.", "The negative datum marks the wet loop. Turn inland for the middle exit."),
 "temple_s": ("southtemple", "Two broad threshold posts crown a dark opaque mouth with one cut V on the Southern jamb.", "Inlay the V in rubbed brass and leave the walking-arcade opening evenly lit.", "Read South Pyramid and the right-turn cue before holding. The longer arcade remains open."),
 "pyramid_s": ("tower", "Four battered courses recede above the southern passage. A V-shaped incision sits low enough to see on a return.", "Use layered buff stone, deep shade between courses, and a short intact copper ridge.", "Trace the clear opening between the wings toward Bazaar, Cloth Yard or South Temple."),
 "temple_n": ("northtemple", "A double-barred lintel and a plain north-facing porch flank the opaque northern threshold.", "Cut two broad parallel light bands into dark stone. Preserve space for destination text.", "Read North Pyramid and the left-turn cue, or take the outer dry arcade."),
 "pyramid_n": ("northpyramid", "A short terraced roof splits into two square crowns above the northern receiving porch.", "Light the two lintel bars strongly against ash stone while leaving the doorway opaque.", "Returning to North Temple turns right. The path along Scale Yard stays ordinary."),
 "yard_s": ("cloth", "Loose lengths of folded cloth hang in overlapping trapezoids at the perimeter. One low dye bath sits below the roof eave.", "Use red madder and bare warp lines above a neutral shoulder-height wall.", "The cloth border signals the sheltered southern market approach through South Pyramid."),
 "yard_n": ("scale", "A rectangular beam, hanging pan and stacks of nesting stone weights distinguish the northern trading yard.", "Keep the beam dark against cream plaster. Compose the weights below the sightline.", "The scales mark the north approach to B through North Pyramid."),
}
# Each row names the actual intermediate feature a player or environment artist must preserve.
ROUTES = {
 ("atk","steps_s","walk"): ("Bales give way to a turned bank stair at the third bend.", "Use a sack seal near departure and a slanted reed head at the stairward end."),
 ("atk","temple_s","walk"): ("A shallow western dogleg straightens before the last turn into the southern porch.", "Across the bend, let a single bright V disappear and reappear as the approach aligns."),
 ("atk","yard_s","walk"): ("Two open trade turns tighten into the north-running approach beside cloth poles.", "Set cloth widths in receding groups along the outer wall. Give the turn a blank head-height band."),
 ("def","steps_n","walk"): ("The road fans west to a north–south stair beside the jar landing.", "Use three clay rims in the far reveal and a square intake stone at the departure."),
 ("def","temple_n","walk"): ("A long straight reach beyond the intake feeds a small angled porch.", "Frame the double lintel bar from the straight while shielding the far landing."),
 ("def","yard_n","walk"): ("Three sloping street turns take the gate runner to a rectangular weighing court.", "A short shadow from the beam should appear at the final bend."),
 ("steps_s","bank","ramp"): ("The ramp cuts inland from the southern ghat, then doubles back onto high ground.", "Repeat pale coping at the two bends. Expose the runner only on the final rise."),
 ("steps_n","bank","ramp"): ("The northern jar route descends in plan before climbing to the dry shelf.", "Guide the ascent with worn outer nosings. Keep jar silhouettes at its origin."),
 ("steps_s","ford","water"): ("The outside channel turns west below the reeds and settles into the ford.", "Draw a submerged line of stones, a reed tuft and a short near-bank wake."),
 ("steps_n","ford","water"): ("The northern channel bends from the clay-jar stair into the low riverbed.", "Start the damp tide stripe below the jars and carry it through the left bend."),
 ("ford","bank","water"): ("A short dogleg leaves the central shallows and climbs out beside the parapet.", "Separate the wet toe from the dry cap with two distinct edge treatments."),
 ("bank","a","ramp"): ("A three-part descent folds around a quiet return before it opens into A.", "Reveal the three bell ribs after the raised bank lip. The objective floor stays flat."),
 ("temple_s","a","walk"): ("The southern colonnade turns behind the low western return before reaching the ghat.", "Put the strong V behind the traveller and leave the western bell ribs as the destination."),
 ("temple_n","a","walk"): ("The north colonnade bends left and rejoins the ghat directly beside its northern lip.", "Use the twin north bars at entry and a low stone lectern as the last interior cue."),
 ("pyramid_s","b","walk"): ("The northern mouth of the pavilion opens onto a curved descent to the southern market lip.", "Align the first bend to the actual masonry gap. Let the cabinet appear beyond the final turn."),
 ("pyramid_n","b","walk"): ("The northern market approach turns south behind the dye cabinet before the ring appears.", "Stage the low counter and high shutter at different reveal angles."),
 ("yard_s","pyramid_s","walk"): ("Cloth Yard crosses a diagonal rise in plan and enters the pavilion on its open southern axis.", "Follow the registered bend around the wing, with one V cut visible along the final straight."),
 ("yard_n","pyramid_n","walk"): ("The scale-yard approach peels inwards toward the short north pyramid.", "Contrast the rectangular weigh frame at departure with a double bar at arrival."),
 ("temple_s","pyramid_s","walk"): ("The ordinary south arcade bows south through two corners and returns to the pavilion.", "Keep the portal chord empty and mark the southern arcade’s continuous paving."),
 ("temple_n","pyramid_n","walk"): ("The ordinary north arcade loops north before returning to the signed receiving door.", "Keep the two corner reveals visible and use double bars to reunite the ends."),
 ("temple_s","pyramid_s","fold"): ("A one-notch threshold carries the traveller across the break with a clockwise quarter-turn.", "Separate the opaque mouths, emboss one V, and illustrate the inverse left turn on return."),
 ("temple_n","pyramid_n","fold"): ("A two-bar threshold carries the traveller across the break with an anticlockwise quarter-turn.", "Separate the opaque mouths, cut two bars, and illustrate the inverse right turn on return."),
 ("temple_s","mid","ramp"): ("The route climbs through three elbows from the southern porch to the sluice crest.", "Read the gearbox above the last stone lip and leave the lower bend screened."),
 ("temple_n","mid","ramp"): ("The northern incline gathers into a narrow straight before joining the crest.", "Set the pale crest and dark side gearbox in contrast to the double-bar porch."),
 ("mid","a","ramp"): ("The ghat descent hooks away from the crest into a sequence of short angled returns.", "Draw the intermediate changes of bearing and the low destination ring beyond them."),
 ("mid","b","ramp"): ("The market ramp curls north before it drops to the broad B floor.", "Show the backward hook, then the low weigh counter, keeping the actual plant lip uncovered."),
}
PROPS = {
 "Bell screen": ("bellscreen","Three deep bell niches sit under a broad stone cap on a solid lower wall. Each niche holds a cast bronze rosette.", "Set dark niche backs between fluted jambs. The screen must stay closed across its full body-height silhouette.", "Break the western body-height sightline across A."),
 "Stone lectern": ("lectern","A low chamfered lectern supports a sloping desk with thick returned edges.", "Use a charcoal cut under the lip and a deliberately unpolished top plane.", "Hide the lower body while keeping the standing shoulder legible at A."),
 "Dye cabinet": ("cabinet","Tall shutters with recessed panels conceal the pigment bins against the market wall.", "Wash the shutters in faded indigo, keep their rails stout and leave the back solid.", "Break a retake sightline on B’s eastern edge."),
 "Weigh counter": ("counter","A low measuring counter has three carved recesses beneath a single heavy worktop.", "Give the top one bright worn edge and keep the narrow plinth dark.", "Screen the runner’s legs while leaving a standing head visible."),
 "Bank parapet": ("parapet","A squat coping and two coursed stones cap the west-bank return.", "Use a pale dry cap with dark marks beneath the projecting drip edge.", "Break the raised runner’s silhouette on the outside approach."),
 "Sluice gearbox": ("gearbox","A riveted casing exposes one circular bearing boss and a ring of service bolts.", "Show the repaired crack and keep the housing solid inside its footprint.", "Identify the northwest pocket on the raised crossing."),
 "Bell comb": ("bellcomb","Three unequal ribs each carry a suspended brass bell. The high middle rib indexes the nearby A ring.", "Separate the ribs by real stone thickness. The three bells hang still during the approach.", "Recognize the ghat before seeing the vessel."),
 "Fold lintels": ("lintels","A matched pair of opaque stone frames carries either a deep V or two parallel bars.", "Raise the cuts above the jamb shadow and leave a sober destination sign field.", "Identify the pair and read the exit at each of the four mouths."),
 "Weighbeam": ("weighbeam","A pair of timber uprights holds a square lintel. A pivot, longer western steelyard arm and two suspended dishes leave a broad open centre.", "Give the hanger cords a clear path against plain plaster, with a dark axle at the fulcrum.", "Read B’s square silhouette and the arm pointing toward the Sluice exit."),
 "Ember vessel": ("vessel","A raised swing bail straddles a ribbed brass belly. The rolled mouth shelters one ember and the broad foot settles on the sanctuary stones.", "Show the wrapped carrying grip, two handle lugs and the recessed coal bed from a carrier’s shoulder.", "Track the carried or dropped ember, then mark its exact kindle position."),
 "Water ewer": ("ewer","A narrow-necked ewer with a hollow rising spout and an open carrying loop tips from the opposite hand.", "Use a cool glazed belly, pale water line, and a rim that remains visible against ember light.", "Locate the kindled vessel within reach and follow the independent pour channel."),
}

def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def compact(number):
    return str(round(number, 2)).rstrip("0").rstrip(".") if not float(number).is_integer() else str(int(number))

def rounded(values):
    return [round(v, 4) or 0.0 for v in values]

def point_at(points, fraction):
    lengths = [dist(a,b) for a,b in zip(points,points[1:])]
    left = fraction*sum(lengths)
    for a,b,length in zip(points,points[1:],lengths):
        if left <= length:
            return [x+(y-x)*left/length for x,y in zip(a,b)]
        left -= length
    return points[-1]

def record(id_, kind, title, anchor, study, direction, cue, views, refs, **extra):
    return {"id": id_, "kind": kind, "title": title, "center_xyz": rounded(anchor),
            "art_brief": study, "prompt": f"{study} {direction} Render {', then '.join(views).lower()}.",
            "cue": cue, "views": views, "source_refs": [{"title": REF[r][0], "href": REF[r][1]} for r in refs],
            "plate": f"plates/{id_}.svg", "render": f"renders/{id_}.webp", "clip": f"clips/{id_}.mp4", **extra}

class GroundSurface:
    """Read the registered GLB triangles so route elevations include the flat landings."""
    def __init__(self, filename):
        data=filename.read_bytes()
        if data[:4]!=b"glTF" or data[16:20]!=b"JSON":raise ValueError("Expected a glTF 2 binary")
        end=20+struct.unpack_from("<I",data,12)[0]
        doc=json.loads(data[20:end])
        binary=memoryview(data)[end+8:]
        def accessor(index):
            spec=doc["accessors"][index]
            view=doc["bufferViews"][spec["bufferView"]]
            components={"SCALAR":1,"VEC3":3}[spec["type"]]
            item=struct.Struct("<"+str(components)+{5121:"B",5123:"H",5125:"I",5126:"f"}[spec["componentType"]])
            offset=view.get("byteOffset",0)+spec.get("byteOffset",0)
            return [item.unpack_from(binary,offset+i*view.get("byteStride",item.size)) for i in range(spec["count"])]
        node=next(n for n in doc["nodes"] if "continuous floor" in n["name"])
        if any(k in node for k in ("translation","rotation","scale","matrix")):
            raise ValueError("Floor registration changed. Update the studio coordinate transform")
        self.grid=defaultdict(list)
        for primitive in doc["meshes"][node["mesh"]]["primitives"]:
            if doc["materials"][primitive["material"]]["name"]=="Skirt":continue
            vertices=[(x,-z,y) for x,y,z in accessor(primitive["attributes"]["POSITION"])]
            indices=accessor(primitive["indices"])
            for start in range(0,len(indices),3):
                a,b,c=[vertices[i[0]] for i in indices[start:start+3]]
                denom=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(denom)<1e-9:continue
                xs,zs,_=zip(a,b,c)
                item=(a,b,c,denom)
                for ix in range(floor(min(xs)/8),floor(max(xs)/8)+1):
                    for iz in range(floor(min(zs)/8),floor(max(zs)/8)+1):
                        self.grid[ix,iz].append(item)
    @lru_cache(maxsize=None)
    def height(self,x,z):
        for a,b,c,den in self.grid[floor(x/8),floor(z/8)]:
            u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(z-c[1]))/den
            v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(z-c[1]))/den
            if min(u,v,1-u-v)>=-1e-6:return u*a[2]+v*b[2]+(1-u-v)*c[2]
        raise ValueError(f"Route leaves registered floor at {(x,z)}")

def sampled_profile(ground,points):
    samples=[[0.,ground.height(*points[0])]]
    distance=0.
    for a,b in zip(points,points[1:]):
        length=dist(a,b);steps=ceil(length)
        for i in range(1,steps+1):
            x,z=[v+(w-v)*i/steps for v,w in zip(a,b)]
            samples.append([distance+length*i/steps,ground.height(x,z)])
        distance+=length
    # Simplify the graph to a maximum one-centimetre vertical discrepancy.
    def simplify(seq):
        if len(seq)<3:return seq
        (x,y),(X,Y)=seq[0],seq[-1]
        errors=[abs(h-y-(Y-y)*(p-x)/(X-x)) for p,h in seq]
        split=max(range(len(seq)),key=errors.__getitem__)
        if errors[split]<=.01:return [seq[0],seq[-1]]
        return simplify(seq[:split+1])[:-1]+simplify(seq[split:])
    return [rounded(p) for p in simplify(samples)]

def make_catalog(plan):
    floor_file=ATLAS/"massing/mandala.glb"
    ground=GroundSurface(floor_file)
    nodes = plan["nodes"]
    def xyz(n):
        x,z = nodes[n]["xz"];return [x,z,nodes[n]["y"]]
    out = []
    for key, node in nodes.items():
        motif, study, direction, cue = ROOMS[key]
        links = [f"route-{l['from']}-{l['to']}-{l['kind']}" for l in plan["links"] if key in (l["from"],l["to"])]
        refs = ["layout","mandala","M1" if "pyramid" in key or "temple" in key else "M2","read"]
        if key in ("ford","bank","steps_s"): refs.append("pampa")
        out.append(record("room-"+key, "room", node["label"], xyz(key), study, direction, cue,
            ["Approach elevation","North-up room and entries"], refs, source_key=key, motif=motif,
            size_m=node["size"], floor_m=node["y"], route_ids=links, origin="Centre of registered room at its sill."))
    edges,_ = audit_geometry(plan)
    for link, edge in zip(plan["links"],edges):
        a,b,kind,width=link["from"],link["to"],link["kind"],link["width"]
        id_=f"route-{a}-{b}-{kind}"
        points=edge.points
        lengths=[dist(p,q) for p,q in zip(points,points[1:])]
        length=sum(lengths)
        positions=[rounded((x,z,ground.height(x,z))) for x,z in points]
        study,direction=ROUTES[(a,b,kind)]
        measure=round(hypot(length,nodes[b]["y"]-nodes[a]["y"]),3)
        extra={"from":a,"to":b,"travel_kind":kind,"width_m":width,"via":link.get("via",[]),
               "points_xyz":positions, "time_s":round(edge.time,3),"motif":kind}
        normal_arcade = a.startswith("temple") and b.startswith("pyramid")
        if kind=="fold":
            title=f"{nodes[a]['label']} to {nodes[b]['label']} · fold"
            anchor=xyz(a)
            turns=link["quarter_turns"]
            extra.update(quarter_turns=turns, reverse_quarter_turns=-turns,
                         dry_bypass=f"route-{a}-{b}-walk", mouths_xyz=[xyz(a),xyz(b)],
                         waymark="One V notch" if turns>0 else "Two bars", separation_m=round(length,3))
            cue=link["cue"] + f". Hold {compact(link['seconds'])} s. Return at the inverse turn."
            views=["Paired thresholds and bearing change","Dry bypass in plan"]
            origin="Origin on the entrance floor. Paired mouths give both camera targets."
        else:
            title=f"{nodes[a]['label']} to {nodes[b]['label']}" + (" · walking arcade" if normal_arcade else "")
            x,z=point_at(points,.5);anchor=[x,z,ground.height(x,z)]
            extra.update(length_m=measure, plan_length_m=round(length,3), profile_m=sampled_profile(ground,points))
            if normal_arcade:extra.update(fold_alternative=f"route-{a}-{b}-fold")
            cue=f"{compact(width)} m {kind} · {edge.time:.1f} s unopposed from centre to centre."
            views=["North-up corridor and approach","Distance and datum profile"]
            origin="Halfway along the authored centreline by path length."
        out.append(record(id_,"route",title,anchor,study,direction,cue,views,["layout","mandala","path","floor"],origin=origin,**extra))
    for solid in plan["cover"]:
        label=solid["label"];key=slug(label)
        rooms=[(k,n) for k,n in nodes.items() if all(abs(p-c)<=w/2 for p,c,w in zip(solid["xz"],n["xz"],n["size"]))]
        host = min(rooms,key=lambda item:dist(solid["xz"],item[1]["xz"]))[0]
        motif,study,direction,cue=PROPS[label]
        out.append(record("cover-"+key,"cover",label,[*solid["xz"],nodes[host]["y"]],study,direction,cue,
             ["Front elevation","Collision footprint at floor"],["layout","mandala"],source_key=label,host=host,motif=motif,
             size_m=[*solid["size"],solid["height"]], origin="Centre of the solid footprint on the host floor."))
    landmark_placements = {
        "Bell comb": [[-9.0,-3.5,0]],
        "Weighbeam": [[33.3,5.7,0]],
        "Fold lintels": [[12,-35.3,0], [28,-36,0], [12,35.3,0], [28,35.3,0]],
    }
    for item in plan["artifacts"]:
        name=item["label"]; motif,study,direction,_=PROPS[name]
        hosts=["temple_s","pyramid_s","temple_n","pyramid_n"] if name=="Fold lintels" else [item["node"]]
        measures = {"Bell comb": {"size_m":[1.10,4.72,4.23]},
                    "Fold lintels":{"size_m":[6.67,1.12,3.96],"clear_width_m":5,"clear_height_m":2.98},
                    "Weighbeam":{"width_m":4.14,"height_m":3.1}}
        extra = {**measures[name], "source_key":name,"host":item["node"],"hosts":hosts,"motif":motif, "placements_xyz":landmark_placements[name]}
        if name=="Fold lintels":
            extra["mouths_xyz"]=[xyz(n) for n in hosts]
            extra["bearing_deg"]=[0,0,180,180]
        out.append(record("artifact-"+slug(name),"artifact",name,landmark_placements[name][0],study,direction,item["cue"],
             ["Landmark elevation","Construction and recognition detail"],["layout","mandala","propmesh","M1" if name=="Fold lintels" else "M2","read"],
             origin="Ground registration for the landmark study in its host court.",**extra))
    arch=plan["architecture"];assembly=Architecture(plan)
    out.append(record("architecture-quarter-turn-pavilion","architecture",arch["name"],xyz(arch["node"]),
        "Four receding cornices and battered stone courses rise over two plinths. A cut V registers the south threshold beneath the public passage.",
        "Keep the 5 m opening in silhouette. Model the projecting cornices and recessed joints as separate parts.",
        arch["play"],["South approach elevation","North-up structure and open bay"],
        ["layout","pavilion","parts","model","M1","read"], source_key="architecture",host=arch["node"],motif="tower",
        size_m=[*arch["footprint"],arch["height"]],clear_width_m=arch["opening"],clear_height_m=assembly.clear_height,
        tiers=arch["tiers"],axis_deg=arch["axis_deg"],parts=[part.name for part in assembly.parts],
        assembly={"plate":"assembly/pavilion.webp","clip":"assembly/pavilion.mp4","parts":"assembly/parts.json"},
        origin="Centre of the 10 × 8 m assembly at the south pyramid sill."))
    for name,host,socket in [("Ember vessel","a",[0,0,.03]),("Water ewer","b",[41.7,0,.03])]:
        motif,study,direction,cue=PROPS[name]
        out.append(record("rite-"+slug(name),"rite",name,socket,study,direction,cue,
             ["Object elevation","Opening and handle detail" if motif=="vessel" else "Spout section"],["rite","objective","propmesh","mandala"],source_key=slug(name),
             host=host,hosts=["a","b"],motif=motif,placements_xyz=[socket], approximate_height_m=.45,
             origin="Movable ritual object. Exemplar socket on the site floor. Runtime placement follows the carrier."))
    return {"schema":1,"district":"Mandala Rift","units":"metres","axes":["east","north","elevation"], "bounds":plan["bounds"],
            "layout_sha256":sha256(SOURCE.read_bytes()).hexdigest(),"floor_sha256":sha256(floor_file.read_bytes()).hexdigest(),"elements":out}


PAPER="#f4eddb"; INK="#283d36"; SOFT="#697268"; OCHRE="#c49357"; SAND="#dfbc86"
LIME="#ebdec0"; DEEP="#5b675a"; RED="#9b4e36"; BLUE="#577f80"; WATER="#92b6ab"; GOLD="#e3b963"

def fnum(n):
    return str(round(float(n),3)).removesuffix(".0")

def tag(name, body="", **attrs):
    attributes=" ".join(key.replace("_","-")+"="+quoteattr(str(val)) for key,val in attrs.items())
    return f"<{name} {attributes}>"+body+f"</{name}>"

def rect(x,y,w,h,fill,stroke="none",sw=1,**attrs):
    return tag("rect", x=fnum(x), y=fnum(y), width=fnum(w), height=fnum(h), fill=fill,
               stroke=stroke, stroke_width=fnum(sw), **attrs)

def line(x,y,X,Y,color=INK,w=1,**attrs):
    return tag("line",x1=fnum(x),y1=fnum(y),x2=fnum(X),y2=fnum(Y),stroke=color,stroke_width=fnum(w),**attrs)

def path(d,fill="none",stroke=INK,w=1.2,**attrs):
    return tag("path",d=d,fill=fill,stroke=stroke,stroke_width=fnum(w),stroke_linejoin="round",stroke_linecap="round",**attrs)

def poly(points,fill,stroke=INK,w=1,**attrs):
    return tag("polygon",points=" ".join(f"{fnum(x)},{fnum(y)}" for x,y in points),
               fill=fill,stroke=stroke,stroke_width=fnum(w),stroke_linejoin="round",**attrs)

def ellipse(x,y,rx,ry,fill="none",stroke=INK,w=1,**attrs):
    return tag("ellipse",cx=fnum(x),cy=fnum(y),rx=fnum(rx),ry=fnum(ry),fill=fill,stroke=stroke,stroke_width=fnum(w),**attrs)

def txt(x,y,s,size=12,colour=INK,align="start",family="sans-serif",**attrs):
    return tag("text",escape(str(s)),x=fnum(x),y=fnum(y),font_size=size,fill=colour,text_anchor=align,font_family=family,**attrs)

def group(s,x=0,y=0,scale=1,**attrs):
    return tag("g",s,transform=f"translate({fnum(x)} {fnum(y)}) scale({fnum(scale)})",**attrs)

def waves(x,y,width,rows=3):
    return "".join(path("M "+fnum(x+(i%2)*3)+" "+fnum(y+i*4)+" "+" ".join(
        "q 4 -2 8 0 t 8 0" for _ in range(max(1,int(width/16)))),stroke=BLUE,w=.9) for i in range(rows))

def slab(x,y,width,height,tone=SAND):
    return rect(x,y,width,height,tone,INK)+path(f"M{x+1} {y+2} h{width-2} M{x+1} {y+height-2} h{width-2}",stroke=LIME,w=.9)

def pier(x,y,w,h):
    s=slab(x-w*.6,y-h,w*1.2,h*.09)+slab(x-w*.52,y-h+h*.09,w*1.04,h*.07)
    s+=poly([(x-w*.4,y-h*.83),(x+w*.4,y-h*.83),(x+w*.45,y-h*.19),(x-w*.45,y-h*.19)],"#c4a57b")
    for dx in (-.25,0,.25):
        s+=line(x+w*dx,y-h*.8,x+w*dx,y-h*.21,"#89795e",.9)
    s+=slab(x-w*.54,y-h*.20,w*1.08,h*.07)+slab(x-w*.65,y-h*.13,w*1.3,h*.13)
    return s

def stairs(x,y,w,n=4):
    return "".join(slab(x+i*3,y-i*5,w-i*6,5,LIME if i%2 else "#ccaf80") for i in range(n))

def jar(x,y,w,h,glaze=RED):
    s=path(f"M{x-w*.28} {y-h} q{w*.10} {h*.22} {-w*.10} {h*.35} C{x-w*.7} {y-h*.46} {x-w*.52} {y-h*.13} {x-w*.24} {y-1} Q{x} {y+2} {x+w*.25} {y-1} C{x+w*.65} {y-h*.23} {x+w*.55} {y-h*.55} {x+w*.4} {y-h*.65} Q{x+w*.22} {y-h*.8} {x+w*.28} {y-h} Z",glaze)
    return s+ellipse(x,y-h,w*.32,2.2,LIME)+path(f"M{x-w*.35} {y-h*.47} q{w*.29} 4 {w*.67} 1 M{x-w*.32} {y-h*.38} q{w*.28} 4 {w*.61} 1",stroke=LIME,w=1)

def reed(x,y,flip=1):
    s=""
    for dx,h in [(-9,28),(-3,38),(4,30),(9,24)]:
        tx=x+flip*dx
        s+=path(f"M{x} {y} Q{x+flip*dx*.4} {y-h*.74} {tx} {y-h}",stroke=DEEP,w=1.4)
        s+=ellipse(tx,y-h,1.5,4.7,OCHRE,DEEP,.65,transform=f"rotate({-dx*1.4} {tx} {y-h})")
    return s

def threshold(north=False,small=False,mark=True):
    w=152 if not small else 122
    x=(240-w)/2
    s=slab(x-8,139,w+16,5)+rect(x+12,60,w-24,78,"#43594f",INK)
    for xx in [x+12,x+w-12]:
        s+=pier(xx,140,17,80)
    s+=slab(x-3,51,w+6,12)+slab(x-8,46,w+16,5,LIME)
    for xx in ((x+20,x+w-20) if mark else ()):
        if north:
            s+=path(f"M{xx-5} 53h10 M{xx-5} 58h10",stroke="#644732",w=2.6)
        else:s+=path(f"M{xx-6} 53l6 6 6 -6",stroke="#644732",w=2.6)
    s+=path(f"M{x+37} 139 V81 q{w*.18} -28 {w*.34} 0v58",stroke="#839385",w=1.4)
    return s

def tower(north=False):
    s=threshold(north,True)
    for i in range(3 if north else 4):
        a=50+10*i;y=47-8*i;b=240-2*a
        s+=poly([(a,y),(a+4,y-6),(a+b-4,y-6),(a+b,y)],SAND if i%2 else "#c29766")
        s+=slab(a-3,y,b+6,3,LIME)
        for j in range(int(b/17)):
            s+=line(a+7+j*17,y-1,a+9+j*17,y-4,SOFT,.75)
    if north:
        s+=slab(77,18,32,7,RED)+slab(131,18,32,7,RED)
    else:s+=poly([(88,17),(98,8),(141,8),(152,17)],OCHRE)+slab(83,17,74,3,LIME)
    return s

def comb(as_screen=False):
    s=slab(32,137,176,8)+slab(39,131,161,6,LIME)
    if as_screen:
        s+=rect(43,42,154,91,"#bd9d74",INK)+slab(37,36,168,10,LIME)+slab(42,118,155,7,OCHRE)
        for xx in (68,120,171):
            s+=path(f"M{xx-16} 111 V77 Q{xx-12} 68 {xx} 54 Q{xx+13} 68 {xx+16} 77 V111Z",DEEP)
            for j in range(6):
                st=j*pi/3
                s+=ellipse(xx+cos(st)*4.3,86+sin(st)*4.3,3.7,2.7,OCHRE,INK,.55,
                           transform=f"rotate({j*60} {xx+cos(st)*4.3} {86+sin(st)*4.3})")
            s+=ellipse(xx,86,2.4,2.4,GOLD,INK,.5)
        return s
    ribs=[(47,56,30),(97,22,35),(156,44,34)]
    for x,y,w in ribs:
        s+=path(f"M{x} 131 V{y+17} Q{x+3} {y+4} {x+w} {y} L{x+w+4} {y+7} Q{x+13} {y+15} {x+12} {y+27} V131Z",SAND)
        s+=path(f"M{x+4} 128V{y+27} Q{x+5} {y+15} {x+w-1} {y+5}",stroke=LIME,w=2)
        for yy in range(y+39,128,18):s+=line(x+1,yy,x+11,yy-1,SOFT,.8)
    if not as_screen:
        for xx,yy,scale in [(69,65,.72),(126,37,.95),(181,56,.75)]:
            bell=line(0,0,0,23,INK,1.5)+path("M-3 23Q-12 26 -12 38L-15 42Q0 48 15 42L12 38Q12 26 3 23Z",OCHRE)+ellipse(0,45,2.3,2.6,INK)
            s+=group(bell,xx,yy,scale)
    return s

def balance(framed=False):
    if framed:
        s=pier(42,139,12,114)+pier(189,139,12,114)+slab(31,23,170,9,OCHRE)
        s+=path("M43 60l24 -27 M186 60l-26 -27",stroke="#826b49",w=5)+line(115,31,115,43,INK,3)
    else:
        s=slab(39,137,163,7)+pier(116,136,15,93)
    s+=poly([(42,47),(183,32),(193,38),(51,54)],"#856c49")
    s+=ellipse(115,42,6,6,OCHRE)+ellipse(115,42,2.4,2.4,INK)
    for x,y in [(56,51),(176,39)]:
        s+=line(x,y,x-17,y+44,SOFT)+line(x,y,x+17,y+44,SOFT)
        s+=path(f"M{x-19} {y+44} q17 20 39 0 Z",OCHRE)
    s+=rect(108,114,17,4,LIME,INK)
    return s

def awning(x,y,w,drop,colour):
    s=poly([(x,y),(x+w,y),(x+w+6,y+drop),(x+w*.77,y+drop-2),(x+w*.55,y+drop+2),(x+w*.35,y+drop-1),(x+2,y+drop+2)],colour)
    for i in range(1,6):
        s+=line(x+w*i/6,y+2,x+w*i/6+2,y+drop-1,LIME,.8)
    return s

def wheel(x,y,r):
    s=ellipse(x,y,r,r,OCHRE)+ellipse(x,y,r-4,r-4,LIME,INK)
    for i in range(10):
        a=i*pi/5
        s+=line(x+cos(a)*4,y+sin(a)*4,x+cos(a)*(r-5),y+sin(a)*(r-5),DEEP,2)
    return s+ellipse(x,y,5,5,SAND,INK)

def vessel(ewer=False):
    if ewer:
        s=path("M129 64 C180 39 193 68 174 89 C166 99 153 105 147 115 L142 105 Q162 87 168 78 Q178 55 134 72Z",BLUE)
        s+=path("M90 94 Q67 95 58 73 Q51 59 31 52 L27 58 Q42 69 45 78 Q58 121 85 126Z",SAND)
        s+=ellipse(30,55,5,2,INK,INK,1,transform="rotate(25 30 55)")
        s+=path("M99 45 Q102 67 91 79 C67 96 66 117 83 129 Q109 148 137 128 C156 116 152 94 133 81 Q119 72 123 45Z",WATER)
        s+=ellipse(111,45,14,4,LIME)+ellipse(111,45,9,2,"#426763",INK,.6)
        s+=path("M79 111q27 18 64 0 M79 115q26 18 63 0",stroke=BLUE,w=1.5)+slab(94,135,32,5,OCHRE)
    else:
        s=path("M75 97 C67 25 105 15 119 14 C160 16 176 53 163 95",stroke=INK,w=4.8)
        s+=path("M99 22q18 -13 39-2",stroke=OCHRE,w=5)+path("M112 78q-7-11 3-23q3 8 5 9l3-16q15 17 7 31Z",GOLD,RED,1.1)
        s+=path("M79 72 Q82 81 72 92 C53 119 91 137 119 138 C154 138 183 118 166 92 Q154 78 158 72Z",OCHRE)
        for x in [77,87,102,120,138,153,163]:
            s+=path(f"M{x} 83 Q{120+(x-120)*1.35} 105 {119+(x-120)*.65} 130",stroke="#855c38",w=1.1)
        s+=slab(85,135,68,7,SAND)+ellipse(119,73,42,7,LIME)
        s+=ellipse(119,73,34,4,"#694d37",INK,.7)+path("M112 73q-5-7 2-17l4 6 5-13q10 11 4 24Z",GOLD,RED,1)
        s+=ellipse(75,94,5,5,SAND,INK)+ellipse(163,94,5,5,SAND,INK)
    return s

def motif(name):
    """A drawn front view in a 240 by 156 field, registered at its floor."""
    drawn=""
    if name in ("tower","northpyramid"): drawn=tower(name=="northpyramid")
    elif name in ("southtemple","northtemple","lintels"): drawn=threshold(name=="northtemple")
    elif name in ("bellcourt","bellcomb","bellscreen"):
        drawn=(stairs(17,144,208,3) if name=="bellcourt" else "")+comb(name=="bellscreen")
    elif name in ("scale","weighbeam"):drawn=balance(name=="weighbeam")
    elif name in ("vessel","ewer"): drawn=vessel(name=="ewer")
    elif name=="spice":
        drawn=threshold(False,mark=False)+awning(18,62,50,21,RED)+awning(168,55,46,17,OCHRE)
        for x,y in ((41,136),(55,139),(176,137)):drawn+=jar(x,y,14,17,OCHRE)
    elif name=="watergate":
        drawn=stairs(28,142,184,2)+pier(52,133,18,83)+pier(184,133,18,83)+slab(35,43,166,10)
        drawn+=path("M132 49v33 M147 49v33 M129 83h21l-3 19h-14Z",OCHRE)+wheel(91,75,23)
        drawn+=waves(41,136,159)
    elif name=="bazaar":
        drawn=group(balance(True),9,16,.85)+pier(27,141,12,65)+pier(210,141,12,65)+awning(15,67,200,14,RED)
        drawn+=slab(152,128,31,16)+slab(150,125,36,4,LIME)
    elif name in ("reeds","jarsteps"):
        drawn=stairs(24,143,192,5)+waves(23,150,191,2)
        if name=="reeds":
            for x,y in [(43,121),(54,116),(187,118),(177,121)]:drawn+=reed(x,y,1 if x<100 else -1)
        else:
            for x,y,w,h in [(55,119,24,35),(77,119,16,27),(168,120,28,41),(191,120,17,28)]:drawn+=jar(x,y,w,h)
    elif name in ("bank","parapet"):
        drawn=poly([(26,134),(55,120),(143,113),(202,122),(220,142),(52,147)],"#b2a584")
        for x,y,w in [(35,118,58),(95,114,52),(149,120,51)]:
            drawn+=slab(x,y-18,w,19)+slab(x-2,y-23,w+4,5,LIME)+line(x+w*.4,y-16,x+w*.4-1,y-1,SOFT,.9)
        if name=="bank":drawn+=reed(187,118,-1)+waves(16,147,180,2)
    elif name=="ford":
        drawn=poly([(12,116),(91,96),(188,89),(228,98),(186,126),(55,142)],WATER,BLUE)
        for x,y,r in [(38,125,12),(65,119,15),(97,113,12),(133,107,14),(171,102,11),(194,98,6)]:
            drawn+=ellipse(x,y,r,r*.25,SAND,DEEP)+path(f"M{x-r+1} {y}q{r} -3 {2*r-3} 0",stroke=LIME,w=1)
        drawn+=reed(32,110)+reed(203,91,-1)+waves(24,142,176,2)
    elif name in ("gearbox","sluice"):
        if name=="sluice":drawn+=stairs(21,145,203,4)+pier(43,128,13,48)+pier(196,128,13,48)+slab(33,77,173,6)
        drawn+=rect(72,73,90,55,"#798d7a",INK)+poly([(162,73),(173,65),(173,113),(162,128)],DEEP)
        drawn+=poly([(72,73),(84,65),(173,65),(162,73)],LIME)+wheel(115,100,21)
        for x,y in ((79,78),(155,78),(79,121),(155,121)):drawn+=ellipse(x,y,2,2,OCHRE)
        drawn+=path("M145 85l-4 8 7 7 -5 9",stroke=INK,w=1.6)
    elif name=="cloth":
        drawn=slab(30,138,177,6)+line(28,58,198,38,INK,3)+line(35,57,35,136,INK,2)+line(191,38,191,138,INK,2)
        for x,y,w,drop,col in [(37,57,32,44,RED),(68,53,36,29,SAND),(105,49,43,55,BLUE),(150,43,36,34,RED)]:drawn+=awning(x,y,w,drop,col)
        drawn+=ellipse(146,132,20,6,BLUE)+path("M126 131l3 8q16 8 33 0l4-8",WATER)
    elif name=="lectern":
        drawn=slab(62,135,122,8)+slab(77,123,90,13)+poly([(85,123),(89,86),(139,80),(147,122)],SAND)
        drawn+=poly([(65,89),(144,64),(170,73),(89,99)],LIME)+poly([(89,99),(170,73),(170,82),(90,108)],OCHRE)
        drawn+=path("M79 87l59-18 M90 88l45-14",stroke="#999273",w=1)
    elif name=="cabinet":
        drawn=rect(64,35,115,99,"#758a81",INK)+poly([(179,35),(192,27),(192,123),(179,134)],DEEP)
        drawn+=poly([(60,35),(74,26),(194,26),(181,36)],SAND)+slab(61,133,122,8)
        for x in [70,106,142]:
            drawn+=rect(x,41,29,82,"#657a77",INK)+rect(x+4,46,21,33,"#8fa093",INK,.8)+rect(x+4,85,21,33,"#789087",INK,.8)
        drawn+=rect(119,79,19,4,OCHRE,INK,.8)
    elif name=="counter":
        drawn=slab(39,131,161,9)+rect(45,97,148,35,SAND,INK)
        for x in (52,99,146):drawn+=path(f"M{x} 130v-22q15-14 31 0v22Z","#967c5b")
        drawn+=poly([(34,98),(49,87),(213,87),(199,99)],LIME)+slab(34,98,167,7)
        drawn+=ellipse(102,93,10,2,DEEP,INK,.65)
    else:raise ValueError("Unillustrated motif "+name)
    return drawn+line(15,149,224,149,SOFT,.85)

def fit(points,box,pad=20):
    left,top,width,height=box
    xs=[p[0] for p in points];zs=[p[1] for p in points]
    x0,x1=min(xs),max(xs);z0,z1=min(zs),max(zs)
    scale=min((width-2*pad)/max(1,x1-x0),(height-2*pad)/max(1,z1-z0))
    def chart(p):
        return (left+width/2+(p[0]-(x0+x1)/2)*scale,top+height/2-(p[1]-(z0+z1)/2)*scale)
    return chart,scale

def route_shape(points,chart,width,colour,**extra):
    return path(" ".join(("M" if i==0 else "L")+fnum(x)+" "+fnum(y)
                         for i,(x,y) in enumerate(map(chart,points))),stroke=colour,w=width,**extra)

def compass(x,y):
    return path(f"M{x} {y+17}v-18l-4 7m4-7 4 7",stroke=DEEP,w=1.25)+txt(x,y-6,"N",10,DEEP,"middle")

def measure_bar(x,y,metres,scale):
    w=metres*scale
    return line(x,y,x+w,y,INK,1.4)+line(x,y-3,x,y+3)+line(x+w,y-3,x+w,y+3)+txt(x+w/2,y+16,f"{compact(metres)} m",10,SOFT,"middle")

def room_plan(r,world):
    box=(458,162,383,243)
    x,z,_=r["center_xyz"];w,d=r["size_m"]
    chart,scale=fit([(x-w/2-5,z-d/2-5),(x+w/2+5,z+d/2+5)],box,10)
    left,top,width,height=box
    floor=rect(*box,"#e9e3ce")
    def square(c,size,fill,stroke=SOFT,sw=.9):
        X,Y=chart((c[0]-size[0]/2,c[1]+size[1]/2))
        return rect(X,Y,scale*size[0],scale*size[1],fill,stroke,sw)
    for link in world["links"]:
        pts=[world["nodes"][link["from"]]["xz"],*link.get("via",[]),world["nodes"][link["to"]]["xz"]]
        if link["kind"]=="fold":continue
        colour=WATER if link["kind"]=="water" else "#cdc29f"
        floor+=route_shape(pts,chart,link["width"]*scale+1.5,"#a39676")+route_shape(pts,chart,link["width"]*scale,colour)
    floor+=square([x,z],[w,d],WATER if r["source_key"]=="ford" else "#e1c697",INK,1.5)
    if r["source_key"] in ("a","b"):
        X,Y=chart((x,z));floor+=ellipse(X,Y,4.5*scale,4.5*scale,"none",SOFT,1,stroke_dasharray="2 4")
        floor+=ellipse(X,Y,3*scale,3*scale,"none",RED,2.3)+txt(X,Y+4,r["source_key"].upper(),13,RED,"middle")
    for cov in world["cover"]:
        floor+=square(cov["xz"],cov["size"],"url(#block)",INK,1.2)
    if r["source_key"] in ("temple_s","pyramid_s","temple_n","pyramid_n"):
        X,Y=chart((x,z))
        floor+=poly([(X,Y-8),(X+8,Y),(X,Y+8),(X-8,Y)],RED)+txt(X,Y+4,"•",10,LIME,"middle")
    if r["source_key"]=="pyramid_s":
        for dx in [-3.75,3.75]:floor+=square([x+dx,z],[2.5,7.52],"url(#block)")
    g=tag("g",floor,clip_path="url(#panel)")
    g+=compass(823,188)+measure_bar(468,406,5,scale)
    g+=txt(458,448,f"{compact(w)} × {compact(d)} m room   ·   {compact(r['floor_m'])} m sill",14,INK)
    return g

def route_plan(r,world):
    pts=[p[:2] for p in r["points_xyz"]]
    fold=r["travel_kind"]=="fold"
    if fold:
        p=next(e for e in world["links"] if e["kind"]=="walk" and e["from"]==r["from"] and e["to"]==r["to"])
        bypass=[pts[0],*p["via"],pts[-1]]
    else:bypass=[]
    box=(36,150,498,255)
    chart,scale=fit(pts+bypass,box,49)
    l=rect(*box,"#eae4d0")
    for e in world["links"]:
        if e["kind"]=="fold":continue
        coords=[world["nodes"][e["from"]]["xz"],*e.get("via",[]),world["nodes"][e["to"]]["xz"]]
        l+=route_shape(coords,chart,max(2,e["width"]*scale),"#d3cbb3")
    if fold:
        l+=route_shape(bypass,chart,5.5*scale+1,SOFT)+route_shape(bypass,chart,5.5*scale,LIME)
        l+=route_shape(pts,chart,2,RED,stroke_dasharray="3 6")
    else:
        l+=route_shape(pts,chart,r["width_m"]*scale+2.2,INK)
        colour=WATER if r["travel_kind"]=="water" else "#c79f69" if r["travel_kind"]=="ramp" else "#d7ab75"
        l+=route_shape(pts,chart,r["width_m"]*scale,colour)
        l+=route_shape(pts,chart,1.25,DEEP,stroke_dasharray="3 4")
        for p in pts[1:-1]:
            X,Y=chart(p);l+=ellipse(X,Y,2.4,2.4,LIME,INK,.8)
    for p,k in [(pts[0],"I"),(pts[-1],"II")]:
        X,Y=chart(p)
        if fold:l+=poly([(X,Y-9),(X+9,Y),(X,Y+9),(X-9,Y)],RED,INK)
        else:l+=ellipse(X,Y,7,7,INK)
        l+=txt(X,Y+3.5,k,9,PAPER,"middle",font_weight="bold")
    result=tag("g",l,clip_path="url(#routebox)")
    result+=compass(516,175)+measure_bar(50,399,5 if scale>5 else 10,scale)
    return result

def direction_diagram(turns):
    s=""
    for x,heading,label in [(608,turns,"Outward"),(773,-turns,"Return")]:
        y=293
        s+=ellipse(x,y,39,39,"none","#c5b897",.8,stroke_dasharray="2 4")
        s+=line(x,y,x,y-28,SOFT,1.4)+path(f"M{x-3} {y-23}l3 -7 3 7",stroke=SOFT)
        end=x+heading*30
        s+=path(f"M{x} {y-24}Q{end} {y-24} {end} {y}",stroke=RED,w=2.6)
        s+=line(x,y,end,y,RED,1.5)+path(f"M{end-5*heading} {y-3}l{5*heading} 3 {-5*heading} 3",stroke=RED,w=1.5)
        s+=txt(x,y+58,label+" · "+("right" if heading>0 else "left"),12,INK,"middle")
    return s

def profile(r):
    x0,y,w=43,484,480
    samples=r["profile_m"];total=samples[-1][0]
    chart=[(x0+station/total*w,y-height*7.8) for station,height in samples]
    s=line(x0,y,x0+w,y,"#a49b81",.8,stroke_dasharray="3 3")
    s+=poly([*chart,(x0+w,y+8),(x0,y+8)],"#cbab79",SOFT,.8)
    for i in (0,-1):
        X,Y=chart[i]; s+=line(X,Y-4,X,Y+5,INK,.9)
    s+=txt(x0,y+25,"I   "+compact(samples[0][1])+" m",11,SOFT)
    s+=txt(x0+w,y+25,"II   "+compact(samples[-1][1])+" m",11,SOFT,"end")
    return s

def prop_detail(r):
    n=r["motif"]
    if r["kind"]=="cover":
        w,d,h=r["size_m"]
        sc=min(46,125/max(w,d))
        a,b=w*sc,d*sc
        s=rect(574-a/2,249-b/2,a,b,"url(#block)",INK,1.7)
        s+=measure_bar(574-a/2,261+b/2,w,sc)
        s+=txt(574,173,"Footprint",12,SOFT,"middle")
        deck=351;vscale=43
        s+=line(707,deck,838,deck,SOFT,1)
        s+=rect(716,deck-h*vscale,56,h*vscale,SAND,INK)
        s+=ellipse(803,deck-1.60*vscale,4.3,5.5,SOFT,"none")
        s+=path(f"M802 {deck-1.46*vscale}l-4 20 6 10 -6 31 m5-30 9 30 M800 {deck-1.28*vscale}l11 16",stroke=SOFT,w=3.4)
        s+=txt(743,deck+20,f"{compact(h)} m",12,INK,"middle")+txt(797,deck+36,"1.70 m eye study",11,SOFT,"middle")
        return s
    if n=="lintels":
        return group(threshold(False),462,170,.75)+group(threshold(True),648,170,.75)+txt(551,306,"South · one cut V",13,INK,"middle")+txt(737,306,"North · two bars",13,INK,"middle")
    if n=="bellcomb":
        s=poly([(474,328),(474,247),(492,210),(512,205),(517,212),(499,233),(492,247),(492,328)],SAND)
        s+=poly([(538,328),(538,225),(556,177),(599,167),(603,175),(578,193),(557,226),(557,328)],OCHRE)
        s+=poly([(628,328),(628,246),(644,204),(676,200),(683,208),(658,221),(649,246),(649,328)],SAND)
        s+=line(585,180,587,235,INK,1.5)+path("M584 228q-12 6 -12 18l-5 5q18 9 38 0l-5 -5q0-13-12-18Z",GOLD)
        s+=txt(580,361,"Three ribs · middle index",13,SOFT,"middle")
        return s
    if n=="weighbeam":
        s=path("M478 253l280-31 4 15-279 31Z",OCHRE)
        s+=ellipse(619,247,13,13,LIME,INK,1.7)+ellipse(619,247,5,5,DEEP)
        for a,b in [(495,263),(739,234)]:
            s+=line(a,b,a-20,b+46,INK)+line(a,b,a+20,b+46,INK)+path(f"M{a-21} {b+46}q20 24 43 0Z",GOLD)
        s+=txt(632,366,"Pivot, hanger and open pan",13,SOFT,"middle")
        return s
    if n=="vessel":
        s=ellipse(649,246,98,24,OCHRE,INK,2)+ellipse(649,242,82,17,LIME,INK,1.5)
        for dx in [-55,-28,0,28,55]:
            s+=path(f"M{649+dx} 233q-7 9 0 18",stroke="#9e8050",w=1.25)
        s+=path("M555 247Q553 145 644 145Q725 147 744 247",stroke=INK,w=5)+path("M613 150q29 -12 62 0",stroke=OCHRE,w=7)
        s+=ellipse(649,242,9,8,RED,INK)
        s+=txt(649,314,"Wrapped bail, rolled rim and ember aperture",13,SOFT,"middle")
        return group(s,y=21)
    if n=="ewer":
        s=path("M489 303Q531 291 562 230 Q590 181 651 171L667 179Q605 211 589 244Q558 311 514 326Z",WATER)
        s+=ellipse(656,175,14,5,INK,INK,1,transform="rotate(-22 656 175)")
        s+=path("M645 183q-50 23-77 82",stroke=LIME,w=2)+path("M668 175q35 9 46 46 m-32 -33q17 6 28 22",stroke=BLUE,w=2)
        s+=txt(640,366,"Hollow spout and pouring lip",13,SOFT,"middle")
        return s
    raise ValueError(n)

def pavilion_views(plan):
    assembly=Architecture(plan)
    palette={"Plinth":"#9c8669","Stone":"#ccac7c","Highlight":"#e8d2a8","Recess":"#826d5c","Copper":"#a7754c"}
    faces=[]
    for part in assembly.parts:
        for indexes in part.faces:
            verts=[part.vertices[i] for i in indexes]
            XZ=[(233+x*24.4,383-z*24.4) for x,_,z in verts]
            area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(XZ,XZ[1:]+XZ[:1])))
            if area>.1:faces.append((sum(p[1] for p in verts)/len(verts),poly(XZ,palette.get(part.material,SAND),INK,.65)))
    front="".join(draw for _,draw in sorted(faces,key=lambda item:-item[0]))+line(64,384,405,384,SOFT,1.2)
    x0,y0,s=655,277,23
    planview=rect(x0-5*s,y0-4*s,10*s,8*s,"#e6d5af",SOFT,1)
    for dx in [-5,2.5]:
        planview+=rect(x0+dx*s,y0-3.76*s,2.5*s,7.52*s,"url(#block)",INK,1.5)
    planview+=path(f"M{x0} {y0+4*s+7}V{y0-4*s-7}",stroke=RED,w=1.4,stroke_dasharray="4 4")
    planview+=txt(x0,395,"5 m clear central opening",13,INK,"middle")
    return front,planview

def svg_plate(r,world):
    first="";second=""
    definitions=tag("defs",'<pattern id="block" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="#a18b68"/><path d="M-1 1l2-2 M0 6l6-6m-1 7 2-2" fill="none" stroke="#766b54" stroke-width=".75"/></pattern>'+
         tag("clipPath",rect(457,161,386,247,"white"),id="panel")+tag("clipPath",rect(36,150,498,255,"white"),id="routebox"))
    kind=r["kind"];x,z,y=r["center_xyz"]
    header=rect(0,0,900,546,PAPER)+line(36,32,864,32,RED,2)
    header+=txt(37,57,"MANDALA RIFT   /   "+{"room":"DISTRICT ROOM","route":"CIRCULATION","cover":"FIXED COVER","artifact":"LANDMARK","architecture":"ARCHITECTURE","rite":"RITUAL OBJECT"}[kind],11,RED,letter_spacing="1.6")
    header+=txt(863,57,"YUGA   ·   EMBER RITE",11,SOFT,"end",letter_spacing="1.25")
    header+=txt(36,102,r["title"],30 if len(r["title"])>34 else 36,INK,family="Georgia, serif")
    header+=line(36,116,864,116,"#c4b79b",1)
    if kind=="route":
        first=txt(36,143,r["views"][1] if r["travel_kind"]=="fold" else r["views"][0],14,INK)
        first+=route_plan(r,world)
        ends=[(r["from"],"I"),(r["to"],"II")]
        if r["travel_kind"]=="fold":
            second+=txt(550,143,r["waymark"]+" · directed turn",14,INK)+direction_diagram(r["quarter_turns"])
            second+=group(threshold(r["quarter_turns"]<0,True),554,155,.5)+group(threshold(r["quarter_turns"]<0,True),718,155,.5)
            first+=txt(43,435,"Dotted chord joins the thresholds. The bent line underfoot is the dry arcade.",12,SOFT)
            first+=txt(43,470,"1.5 s hold  /  "+compact(r["separation_m"])+" m between mouth centres",15,INK)
        else:
            second+=txt(550,143,"Landmarks in travel order",14,INK)
            for i,(key,numeral) in enumerate(ends):
                second+=group(motif(ROOMS[key][0]),552+i*151,177,.61)
                second+=txt(622+i*151,299,numeral+"   "+world["nodes"][key]["label"],11,INK,"middle")
            second+=txt(551,353,f"{compact(r['width_m'])} m clear width",19,INK,family="Georgia, serif")
            second+=txt(551,375,f"{compact(r['length_m'])} m along route · {r['time_s']:.1f} s unopposed",12,SOFT)
            first+=txt(43,443,"Distance and surveyed floor profile",14,INK)+profile(r)
    else:
        first+=txt(38,147,r["views"][0],14,INK)+line(430,143,430,449,"#c4b79b",1)
        second+=txt(458,147,r["views"][1],14,INK)
        if kind=="architecture":
            ff,ss=pavilion_views(world);first+=ff;second+=ss
            first+=txt(46,435,"Four courses   ·   9 m crown height",13,SOFT)
        else:
            first+=group(motif(r["motif"]),53,166,1.48)
            if kind=="room":second+=room_plan(r,world)
            else:second+=prop_detail(r)
            if kind=="room":
                first+=txt(45,438,f"{len(r['route_ids'])} registered connections",13,SOFT)
            elif kind=="cover":
                first+=txt(45,438,f"{compact(r['size_m'][0])} × {compact(r['size_m'][1])} × {compact(r['size_m'][2])} m solid",13,SOFT)
            elif kind=="rite":
                first+=txt(45,438,"Portable object   ·   art exemplar",13,SOFT)
            else:first+=txt(45,438,world["nodes"][r["host"]]["label"]+"   ·   landmark study",13,SOFT)
    footer=line(36,516,864,516,"#c4b79b",1)+txt(36,534,"E "+compact(x)+"   /   N "+compact(z)+"   /   sill "+compact(y)+" m",11,SOFT)
    footer+=txt(864,534,"Metres  ·  north up in plan",11,SOFT,"end")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'+
        tag("svg",tag("title",escape(r["title"]),id="title")+tag("desc",escape(r["art_brief"]),id="desc")+definitions+header+
        tag("g",first,data_view="primary")+tag("g",second,data_view="secondary")+footer,
        xmlns="http://www.w3.org/2000/svg",width=900,height=546,viewBox="0 0 900 546",role="img",aria_labelledby="title desc")+"\n")

def validate(catalog,world):
    es=catalog["elements"]; lookup={e["id"]:e for e in es}
    expected={"room":15,"route":26,"cover":6,"artifact":3,"architecture":1,"rite":2}
    assert len(lookup)==len(es)==53 and Counter(e["kind"] for e in es)==expected
    assert {e["source_key"] for e in es if e["kind"]=="room"}==world["nodes"].keys()
    assert {(e["from"],e["to"],e["travel_kind"]) for e in es if e["kind"]=="route"}=={
        (e["from"],e["to"],e["kind"]) for e in world["links"]}
    for key in ("cover","artifact"):
        source=world["cover" if key=="cover" else "artifacts"]
        assert {e["source_key"] for e in es if e["kind"]==key}=={item["label"] for item in source}
    assert len(lookup["architecture-quarter-turn-pavilion"]["parts"])==62
    assert len(lookup["artifact-fold-lintels"]["placements_xyz"])==4
    for e in es:
        assert re.fullmatch("[a-z0-9_-]+", e["id"]) and len(e["center_xyz"])==3
        assert len(e["views"])==2 and len(e["art_brief"])>40 and len(e["prompt"])>len(e["art_brief"])
        assert all(lookup[route]["kind"]=="route" for route in e.get("route_ids",[]))
        if e.get("travel_kind")=="fold":
            assert lookup[e["dry_bypass"]]["travel_kind"]=="walk" and e["quarter_turns"]==-e["reverse_quarter_turns"]
        for ref in e["source_refs"]:
            if not ref["href"].startswith("https://"):
                assert (STUDIO/ref["href"].split("#")[0]).exists(),ref

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="verify source coverage and byte-identical exports")
    args=parser.parse_args()
    world=json.loads(SOURCE.read_text())
    catalog=make_catalog(world)
    validate(catalog,world)
    outputs={STUDIO/"catalog.json":json.dumps(catalog,indent=2,ensure_ascii=False)+"\n"}
    ns="{http://www.w3.org/2000/svg}"
    seen_plates=set()
    for e in catalog["elements"]:
        svg=svg_plate(e,world)
        root=ET.fromstring(svg)
        views=[g for g in root.findall(ns+"g") if g.get("data-view")]
        assert len(views)==2 and all(len(list(g.iter()))>=4 for g in views),e["id"]
        assert svg not in seen_plates,e["id"]
        seen_plates.add(svg);outputs[STUDIO/e["plate"]]=svg
    wrong=sorted(str(f.relative_to(STUDIO)) for f,s in outputs.items() if not f.is_file() or f.read_bytes()!=s.encode())
    extra=sorted(str(f.relative_to(STUDIO)) for f in (STUDIO/"plates").glob("*.svg") if f not in outputs)
    if extra: sys.exit("Unexpected plates: "+", ".join(extra))
    if args.check:
        if wrong:sys.exit("Regenerate stale exports: "+", ".join(wrong))
    else:
        (STUDIO/"plates").mkdir(exist_ok=True)
        for f,s in outputs.items():f.write_bytes(s.encode())
    print("Verified 53 catalog records and two-view SVGs: 15 rooms, 26 links, 6 covers, 3 artifacts, 1 assembly and 2 ritual objects.")

if __name__=="__main__":main()
