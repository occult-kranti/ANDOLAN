"""Original four-face civic frontage successor; closed geometry, no engine/import."""
import argparse
import json
from pathlib import Path

MATERIALS=['Confluence_warm_ivory','Confluence_opaque_blue_glass','Confluence_transit_indigo']
DEPTHS=[0.,.24,.45,.65]
GRIDS={
 'near':([-9,-8.4,-7.5,-5.1,-4.5,-3.6,-1.8,-1.2,-.12,.12,1.2,1.8,3.6,4.5,5.1,7.5,8.4,9],
         [0,.6,1.2,2.7,3.,3.4,3.8,4.2,4.55,5.4,7.8,8.2,8.6,9.3,11.7,12.1,12.4,14.2,14.6,15]),
 'mid':([-9,-8.4,-7.5,-5.1,-4.5,-3.6,-1.8,-1.2,-.12,.12,1.2,1.8,3.6,4.5,5.1,7.5,8.4,9],
        [0,.6,1.2,2.7,3.4,3.8,4.2,4.55,5.4,7.8,8.2,8.6,9.3,11.7,12.1,12.4,14.6,15])}


def profile(u,y,face):
    """Depth metres inward from broad18m envelope; four wrapped articulated walls."""
    a=abs(u)
    # The only entrance remains physically CLOSED with the native-tested .65m recess.
    if face==0 and a<1.2 and y<3.4:
        if 2.7<=y<3.:return .45,0  # Raised transom rail above actual2.2m hero envelope.
        if .6<=y<2.7 and a<.12:return .65,0  # Flush meeting stile: visibly closed leaves, no new blocker.
        return .65,1 if y>=3. else 2
    # Continuous indigo plinth + upper stone threshold meet actual existing ground.
    if y<.6:return 0.,2
    # Wide cobalt storey belts wrap ALL faces; warm stone lips make them legible.
    if 4.2<=y<4.55 or 8.2<=y<8.6 or 12.1<=y<12.4:return 0.,1
    if y>=14.6:return 0.,2
    if 12.4<=y<14.2:return .24,1
    if 3.8<=y<4.2 or 7.8<=y<8.2 or 11.7<=y<12.1 or 14.2<=y<14.6:return 0.,0
    # Broad lintel bridges both door jambs; existing stone belt above acts as cornice.
    if face==0 and a<1.8 and 3.4<=y<3.8:return 0.,1
    # Large paired pilasters separate bays; corner returns never leave blank side/rear.
    if a>=8.4 or 3.6<=a<4.5:return 0.,0
    if 1.2<=a<1.8:return 0.,0
    lower=(5.1<=a<7.5 or (face!=0 and a<1.2)) and 1.2<=y<3.
    upper=(a<1.2 or 1.8<=a<3.6 or 5.1<=a<7.5) and (5.4<=y<7.8 or 9.3<=y<11.7 or 13.1<=y<14.2)
    if lower or upper:return .45,1
    # Shallow inset stone fields let the larger piers/belts carry shadow and hierarchy.
    return .24,0


def point(face,u,y,d):
    if face==0:return(u,y,-9+d)
    if face==1:return(9-d,y,u)
    if face==2:return(-u,y,9-d)
    return(-9+d,y,-u)


def build(lod):
    xs,ys=GRIDS[lod];surfaces=[[] for _ in MATERIALS]
    def tri(points,mat):surfaces[mat].append([tuple(round(v,6) for v in p) for p in points])
    def quad(points,mat):tri([points[0],points[1],points[2]],mat);tri([points[0],points[2],points[3]],mat)
    def spans(a,b):
        ds=sorted({round(a,6),round(b,6),*(d for d in DEPTHS if a<d<b)})
        return zip(ds,ds[1:])
    for face in range(4):
        cells={(i,j):profile((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2,face) for i in range(len(xs)-1) for j in range(len(ys)-1)}
        for(i,j),(d,mat)in cells.items():
            u0,u1=xs[i:i+2];y0,y1=ys[j:j+2]
            quad([point(face,u0,y0,d),point(face,u0,y1,d),point(face,u1,y1,d),point(face,u1,y0,d)],mat)
            if i<len(xs)-2:
                right=cells[i+1,j][0]
                for da,db in spans(min(d,right),max(d,right)) if d!=right else []:
                    p=[point(face,u1,y0,da),point(face,u1,y1,da),point(face,u1,y1,db),point(face,u1,y0,db)]
                    quad(p if d<right else list(reversed(p)),0)
            if j<len(ys)-2:
                upper=cells[i,j+1][0]
                for da,db in spans(min(d,upper),max(d,upper)) if d!=upper else []:
                    p=[point(face,u0,y1,da),point(face,u0,y1,db),point(face,u1,y1,db),point(face,u1,y1,da)]
                    quad(p if d<upper else list(reversed(p)),0)
    # A central fan matches every perimeter interval without gratuitous cap-grid triangles.
    for y in [0.,15.]:
        center=(0.,y,0.)
        for face in range(4):
            for u0,u1 in zip(xs,xs[1:]):
                a,b=point(face,u0,y,0),point(face,u1,y,0)
                tri([center,a,b] if y==0 else [center,b,a],2 if y==0 else 0)
    return {'lod':lod,'surfaces':[{'material':m,'triangles':t} for m,t in zip(MATERIALS,surfaces)],'triangle_count':sum(map(len,surfaces)),'bounds':[[-9,0,-9],[9,15,9]]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():p.error('fresh output required')
    data={'schema':1,'status':'isolated r2 source successor; native/pixels unrun','target':'CityArt/block-2','authority_id':'authority-solid-2','position':[20,0,-28],'dimensions':[18,15,18],'material_names':MATERIALS,'new_materials':0,'new_textures':0,'new_lights':0,'automatic_lod':False,'geometry':{lod:build(lod) for lod in GRIDS}}
    a.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({lod:g['triangle_count'] for lod,g in data['geometry'].items()}))
if __name__=='__main__':main()
