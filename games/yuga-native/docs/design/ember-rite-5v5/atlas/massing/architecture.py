"""Parametric district architecture shared by the drawings and Blender exporter.

Local axes are transverse (right), axial (towards the exit) and height. The
footprint, opening and elevations are in metres. A positive bearing is clockwise
from map north. Closed meshes meet at their architectural joints.
"""
from dataclasses import dataclass
import math


PALETTE = {
    "Plinth": "#897764", "Stone": "#c4a377", "Highlight": "#e4cca1",
    "Recess": "#7c665b", "Copper": "#8e5d40", "Slate": "#526568",
    "Water": "#53949a", "WetStone": "#7b9491",
}


@dataclass
class Part:
    name: str
    material: str
    vertices: list
    faces: list


def extrude(name, material, lower, upper):
    n = len(lower)
    faces = [list(reversed(range(n))), list(range(n, 2*n))]
    faces.extend([i, (i+1)%n, n+(i+1)%n, n+i] for i in range(n))
    return Part(name, material, lower + upper, faces)


def rectangle(x, y, z, w, d):
    return [(x-w/2, y-d/2, z), (x+w/2, y-d/2, z),
            (x+w/2, y+d/2, z), (x-w/2, y+d/2, z)]


def block(name, material, x, y, low, high, w, d, top=None):
    return extrude(name, material, rectangle(x,y,low,w,d),
                   rectangle(x,y,high,*(top or (w,d))))


def shaft(name, material, x, y, low, high, r1, r2, facets=12):
    def ring(z, r):
        return [(x+r*math.cos(i*math.tau/facets), y+r*math.sin(i*math.tau/facets), z)
                for i in range(facets)]
    return extrude(name,material,ring(low,r1),ring(high,r2))


def pillar(name, x, y, radius, height):
    pieces = [
        ("bottom course","Plinth",0,.09,1.0,1.0,4),
        ("foot moulding","Highlight",.09,.15,.96,.75,12),
        ("lower band","Copper",.15,.18,.76,.76,12),
        ("shaft","Stone",.18,.78,.66,.57,12),
        ("neck ring","Highlight",.78,.84,.66,.68,12),
        ("capital","Plinth",.84,.96,.68,1.0,8),
        ("bearing","Highlight",.96,1.,1.,1.,4),
    ]
    for label,material,lo,hi,r1,r2,facets in pieces:
        if facets == 4:
            yield block(name+" "+label,material,x,y,height*lo,height*hi,
                        2*radius*r1,2*radius*r1,(2*radius*r2,2*radius*r2))
        else:
            yield shaft(name+" "+label,material,x,y,height*lo,height*hi,
                        radius*r1,radius*r2,facets)


def world_xy(local_x, local_y, node, bearing):
    ang = math.radians(bearing)
    return (node["xz"][0]+local_x*math.cos(ang)+local_y*math.sin(ang),
            node["xz"][1]-local_x*math.sin(ang)+local_y*math.cos(ang))


def threshold_glyph(turns):
    if turns > 0:
        return [[(-.64,.35),(0,-.32),(.64,.35)]]
    return [[(-.56,y),(.56,y)] for y in (-.24,.24)]


class Architecture:
    def __init__(self, data):
        spec = data["architecture"]
        self.name = spec["name"]
        self.form = spec["form"]
        self.w, self.d = spec["footprint"]
        self.height = spec["height"]
        self.opening = spec["opening"]
        self.tiers = spec["tiers"]
        self.bearing = spec["axis_deg"]
        self.node = data["nodes"][spec["node"]]
        self.source_id = spec["source_id"]
        self.play = spec["play"]
        self.fold = next((link for link in data["links"] if link["kind"] == "fold" and
                          spec["node"] in (link["from"],link["to"])), None)
        dimensions = [self.w,self.d,self.height,self.opening,self.bearing]
        if not all(math.isfinite(n) for n in dimensions):
            raise ValueError(self.name+" has a non-finite dimension")
        if not (2 <= self.tiers <= 8 and int(self.tiers) == self.tiers and
                1.2 <= self.opening < self.w-.8 and self.height >= 2.5 and self.d >= 3):
            raise ValueError(self.name+" has invalid thresholds or proportions")
        self.level = self.node["y"]
        self.clear_height = max(2.3, self.height * (.42 if self.form == "gatehouse" else .47))
        if self.form == "stepwell":
            self.clear_height = None
        self.water_level = -min(1.2, .20*(self.tiers+1)) if self.form == "stepwell" else None
        makers = {"terraced_tower":self.tower, "pillared_hall":self.hall,
                  "stepwell":self.stepwell, "gatehouse":self.gate}
        self.parts = list(makers[self.form]())
        self.cut_axial = (-.43+.86/self.tiers)*self.d if self.form=="pillared_hall" else 0
        self.thresholds = [world_xy(0,y,self.node,self.bearing) for y in (-self.d/2,self.d/2)]
        # The registered study fits its host floor even when the local axes rotate.
        for x in (-self.w/2,self.w/2):
            for y in (-self.d/2,self.d/2):
                p = world_xy(x,y,self.node,self.bearing)
                if any(abs(v-c)>span/2+.001 for v,c,span in zip(p,self.node["xz"],self.node["size"])):
                    raise ValueError(self.name+" projects beyond its host room")

    def tower(self):
        w,d,h,bay,lintel = self.w,self.d,self.height,self.opening,self.clear_height
        wing=(w-bay)/2
        pier=min(.42*wing,.1*d)
        for side in (-1,1):
            x = side*(bay/2+wing/2)
            yield block(f"Wing {side} plinth","Plinth",x,0,0,.12*lintel,wing,d*.94)
            yield block(f"Wing {side} inner return","Stone",side*(w/2-.16*wing),0,
                        .12*lintel,lintel,.28*wing,d*.72)
            for i,y in enumerate((-.37*d,0,.37*d)):
                yield from pillar(f"Pier {side}.{i}",x,y,pier,lintel)
        if self.fold:
            # Inlaid brass runs across the entrance face of the west plinth.
            xc,yc=-bay/2-wing/2,-d*.47
            for i,stroke in enumerate(threshold_glyph(self.fold["quarter_turns"])):
                for j,((x1,z1),(x2,z2)) in enumerate(zip(stroke,stroke[1:])):
                    dx,dz=x2-x1,z2-z1
                    norm=math.hypot(dx,dz)
                    dx,dz=.042*dx/norm,.042*dz/norm
                    coords=[(x1-dz,z1+dx),(x1+dz,z1-dx),(x2+dz,z2-dx),(x2-dz,z2+dx)]
                    verts=[(xc+rx*.75,yc-depth,lintel*.063+rz*.41)
                           for depth in (.004,.019) for rx,rz in coords]
                    faces=[[3,2,1,0],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
                    yield Part(f"Fold threshold inlay {i+1}.{j+1}","Highlight",verts,faces)
        for i in range(self.tiers):
            t, end = i/self.tiers, (i+1)/self.tiers
            z = lintel+(h-lintel)*.87*t
            z1 = lintel+(h-lintel)*.87*end
            ww,dd = w*(1-.63*t),d*(1-.65*t)
            yield block(f"Course {i+1} cornice","Highlight",0,0,z,z+(z1-z)*.18,ww,dd)
            yield block(f"Course {i+1} shadow","Recess",0,0,z+(z1-z)*.18,z+(z1-z)*.28,ww*.96,dd*.96)
            yield block(f"Course {i+1} battered wall","Stone",0,0,z+(z1-z)*.28,z1,
                        ww*.94,dd*.94,(w*(1-.63*end),d*(1-.65*end)))
        z=lintel+(h-lintel)*.87
        yield block("Crown saddle","Plinth",0,0,z,z+(h-z)*.23,w*.39,d*.37)
        yield block("Ridge crown","Copper",0,0,z+(h-z)*.23,h,w*.33,d*.31,(w*.14,d*.22))

    def hall(self):
        w,d,h,bay,lintel = self.w,self.d,self.height,self.opening,self.clear_height
        wing=(w-bay)/2
        r=min(wing*.48,d/(3*(self.tiers+1)))
        count=self.tiers+1
        for side in (-1,1):
            x=side*(bay/2+r)
            for i in range(count):
                y=(-.43+.86*i/(count-1))*d
                yield from pillar(f"Column {side}.{i+1}",x,y,r,lintel)
            yield block(f"Long beam {side}","Recess",x,0,lintel,lintel*1.09,2*r,d*.92)
            canopy_h=lintel+(h-lintel)*.48
            yield block(f"Gallery eave {side}","Highlight",side*(bay/2+wing/2),0,
                        lintel*1.09,canopy_h,wing,d,(wing*.78,d*.90))
        # The central passage remains daylit between the two transverse frames.
        frame_h = lintel+(h-lintel)*.28
        for side in (-1,1):
            y=side*.34*d
            yield block(f"Crossbeam {side}","Stone",0,y,lintel,frame_h,w*.91,d*.09)
            yield block(f"Monitor cap {side}","Copper",0,y,frame_h,h,w*.63,d*.10,
                        (w*.40,d*.035))

    def gate(self):
        w,d,h,bay,spring = self.w,self.d,self.height,self.opening,self.clear_height
        wing=(w-bay)/2
        rise=(h-spring)*.47
        thick=min(.7*wing,.23*(h-spring))
        for side in (-1,1):
            x=side*(bay/2+wing/2)
            yield block(f"Gate plinth {side}","Plinth",x,0,0,spring*.16,wing,d)
            yield block(f"Archive pier {side}","Stone",x,0,spring*.16,spring,wing,d*.92)
            for i in range(self.tiers):
                z=spring+(h-spring)*i/self.tiers
                z1=spring+(h-spring)*(i+1)/self.tiers
                foot=1-.28*i/self.tiers
                yield block(f"Bastion cornice {side}.{i}","Highlight",x,0,z,z+.12*(z1-z),
                            wing*foot,d*foot)
                yield block(f"Bastion crown {side}.{i}","Slate",x,0,z+.12*(z1-z),z1,
                            wing*foot*.94,d*foot*.90,(wing*(foot-.10),d*(foot-.10)))
        for side in (-1,1):
            depth=d*.14
            mid=side*(d/2-depth/2)
            for i in range(11):
                a,b=math.pi*i/11,math.pi*(i+1)/11
                outer=(bay/2+thick,rise+thick)
                inner=(bay/2,rise)
                outline=[(rx*math.cos(t),spring+ry*math.sin(t))
                         for (rx,ry),t in ((inner,a),(outer,a),(outer,b),(inner,b))]
                # This cross-section has its outward normal towards the entrance.
                v=[(x,mid-depth/2,z) for x,z in outline]+[(x,mid+depth/2,z) for x,z in outline]
                yield Part(f"Arch voussoir {side}.{i+1}","Highlight" if i%2 else "Stone",v,
                           [[0,1,2,3],[7,6,5,4],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]])
        z=spring+rise+thick
        yield block("Watch gallery","Plinth",0,0,z,z+min(.3,(h-z)*.5),w*.9,d*.53)

    def stepwell(self):
        w,d,h,bay = self.w,self.d,self.height,self.opening
        water=self.water_level
        wing=(w-bay)/2
        curb=min(.15*wing,.34)
        yield block("Dry causeway","Stone",0,0,water-.24,0,bay,d)
        for side in (-1,1):
            x=side*(bay/2+wing/2)
            for sign in (-1,1):
                y=sign*(d/2)
                tread=d*.32/self.tiers
                for i in range(self.tiers):
                    z=water*(i/self.tiers)
                    yi=y-sign*(i+.5)*tread
                    yield block(f"Landing {side}.{sign}.{i+1}","Stone" if i%2==0 else "WetStone",
                                x,yi,water-.28,z,wing,tread)
            yield block(f"Basin bed {side}","WetStone",x,0,water-.28,water-.15,wing,d*.36)
            yield block(f"Water surface {side}","Water",x,0,water-.04,water,wing,d*.36)
            yield block(f"Long coping {side}","Highlight",side*(w/2-curb/2),0,water-.28,.22,curb,d)
            # Stagger the two gauge posts so the player can distinguish the banks.
            py=side*.36*d
            r=min(.22*wing,.065*d)
            yield block(f"Gauge foot {side}","Plinth",x,py,-.12,.28,2*r,2*r)
            yield block(f"Flood staff {side}","Slate",x,py,.28,h*.89,1.5*r,1.6*r,(r,1.22*r))
            for i in range(1,self.tiers+1):
                z=.28+(h*.78-.28)*i/(self.tiers+1)
                yield block(f"Gauge notch {side}.{i}","Highlight",x,py,z,z+.052,1.55*r,1.65*r)
            yield shaft(f"Staff capital {side}","Copper",x,py,h*.89,h,.9*r,.46*r,8)
