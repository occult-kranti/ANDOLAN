"""Original closed civic frontage, source-only review data; no Blender/engine/import."""
import argparse
import json
from pathlib import Path

MATERIALS = ['Confluence_warm_ivory', 'Confluence_opaque_blue_glass', 'Confluence_transit_indigo']
Z = [-9., -8.88, -8.76, -8.55, -8.35, 9.]
GRIDS = {
 'near': ([-9,-8.4,-7.5,-5.1,-4.5,-3.6,-1.8,-1.2,1.2,1.8,3.6,4.5,5.1,7.5,8.4,9],
          [0,.18,.6,1.2,3.0,3.4,3.8,4.2,4.55,5.4,7.8,8.2,8.6,9.3,11.7,12.1,12.4,12.65,13.1,14.2,14.6,15]),
 'mid': ([-9,-7.5,-5.1,-3.6,-1.8,-1.2,1.2,1.8,3.6,5.1,7.5,9],
         [0,.6,1.2,3.4,4.2,5.4,7.8,8.6,9.3,11.7,12.4,13.1,14.6,15])}


def profile(x,y):
    """Metres in block-local space; one continuous solid, not a hollow facade."""
    ax=abs(x)
    if ax < 1.2 and y < 3.4:
        return -.65, 2  # Closed indigo door behind a deep, open-to-street reveal.
    if y < .6:
        return 0., 2 if y < .18 else 0  # Grounded plinth, no second floor plane.
    if y >= 14.6 or 4.2 <= y < 4.55 or 8.2 <= y < 8.6 or 12.1 <= y < 12.4:
        return 0.,0  # Broad stone cornices define three unequal-height masses.
    if 12.4 <= y < 12.65:
        return -.24,2
    if 1.2 <= ax < 1.8 or 3.6 <= ax < 4.5 or 7.5 <= ax < 8.4:
        return 0.,0  # Structural piers, not added freestanding repeating props.
    if ax < 1.8 and 3.4 <= y < 3.8:
        return 0.,0
    lower_window = 5.1 <= ax < 7.5 and 1.2 <= y < 3.0
    upper_window = (ax < 1.2 or 1.8 <= ax < 3.6 or 5.1 <= ax < 7.5) and any(a<=y<b for a,b in [(5.4,7.8),(9.3,11.7),(13.1,14.2)])
    if lower_window or upper_window:
        return -.45,1
    return -.12,0


def build(lod):
    xs,ys=GRIDS[lod]
    # Depth is positive into the body (+Z); all reachable niches have closed backs.
    cells={(i,j):(-9-profile((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2)[0],
                  profile((xs[i]+xs[i+1])/2,(ys[j]+ys[j+1])/2)[1])
           for i in range(len(xs)-1) for j in range(len(ys)-1)}
    surfaces=[[] for _ in MATERIALS]
    def quad(points,material):
        p=[tuple(round(v,6) for v in item) for item in points]
        surfaces[material].extend([[p[0],p[1],p[2]],[p[0],p[2],p[3]]])
    def spans(lo,hi):
        values=sorted({round(lo,6),round(hi,6),*(z for z in Z if lo<z<hi)})
        return zip(values,values[1:])
    for (i,j),(z,mat) in cells.items():
        x0,x1=xs[i:i+2]; y0,y1=ys[j:j+2]
        quad([(x0,y0,z),(x0,y1,z),(x1,y1,z),(x1,y0,z)],mat)
        quad([(x0,y0,9),(x1,y0,9),(x1,y1,9),(x0,y1,9)],0)
        if i==0:
            for za,zb in spans(z,9):quad([(x0,y0,za),(x0,y0,zb),(x0,y1,zb),(x0,y1,za)],0)
        if i==len(xs)-2:
            for za,zb in spans(z,9):quad([(x1,y0,za),(x1,y1,za),(x1,y1,zb),(x1,y0,zb)],0)
        if j==0:
            for za,zb in spans(z,9):quad([(x0,y0,za),(x1,y0,za),(x1,y0,zb),(x0,y0,zb)],0)
        if j==len(ys)-2:
            for za,zb in spans(z,9):quad([(x0,y1,za),(x0,y1,zb),(x1,y1,zb),(x1,y1,za)],0)
        if i<len(xs)-2:
            right=cells[i+1,j][0]
            if z!=right:
                for za,zb in spans(min(z,right),max(z,right)):
                    p=[(x1,y0,za),(x1,y1,za),(x1,y1,zb),(x1,y0,zb)]
                    quad(p if z<right else list(reversed(p)),0)
        if j<len(ys)-2:
            upper=cells[i,j+1][0]
            if z!=upper:
                for za,zb in spans(min(z,upper),max(z,upper)):
                    p=[(x0,y1,za),(x0,y1,zb),(x1,y1,zb),(x1,y1,za)]
                    quad(p if z<upper else list(reversed(p)),0)
    return {'lod':lod,'surfaces':[{'material':name,'triangles':tris} for name,tris in zip(MATERIALS,surfaces)],
            'triangle_count':sum(map(len,surfaces)),'bounds':[[-9,0,-9],[9,15,9]]}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if args.output.exists():p.error('fresh output required')
    data={'schema':1,'status':'isolated source candidate; native and pixels unrun','target':'CityArt/block-2',
          'authority_id':'authority-solid-2','position':[20,0,-28],'dimensions':[18,15,18],
          'material_names':MATERIALS,'new_materials':0,'new_textures':0,'new_lights':0,
          'automatic_lod':False,'geometry':{lod:build(lod) for lod in GRIDS}}
    args.output.write_text(json.dumps(data,separators=(',',':'))+'\n')
    print(json.dumps({lod:data['geometry'][lod]['triangle_count'] for lod in GRIDS}))

if __name__=='__main__':main()
