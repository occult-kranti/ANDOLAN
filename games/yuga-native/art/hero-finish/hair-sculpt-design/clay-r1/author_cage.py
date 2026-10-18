"""Coarse editable principal-hair cage. No GLB writer, engine, or rendering."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
import numpy as np

PROJECT = Path(__file__).resolve().parents[4]
READER = PROJECT / 'art/hero-rama-lod/glb_lod.py'
FITTER = PROJECT / 'art/hero-finish/hair-silhouette-r1/build_candidate.py'
SOURCE = PROJECT / 'art/hero-finish/sash-texel-r1/candidate-r2/rama-hero.glb'
SOURCE_SHA = 'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e'
CONCEPT_SHA = 'dc3e42d25777233dba653ecd9223c63711fc5c73135660ffa69e1b577a6556c8'
ORIGIN = np.array([0., 1.765, .045])

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
def obj(path, vertices, faces):
    with path.open('w') as stream:
        stream.write('# Original editable whole-hair clay cage; glTF metres. Not runtime evidence.\n')
        for p in vertices: stream.write('v %.9f %.9f %.9f\n' % tuple(p))
        for f in faces: stream.write('f ' + ' '.join(str(int(i)+1) for i in f) + '\n')

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--output', type=Path, required=True)
    args=ap.parse_args(); out=args.output.resolve()
    if out.exists() or out.is_relative_to(PROJECT/'assets'): raise ValueError('Fresh authoring output required')
    assert sha(SOURCE)==SOURCE_SHA
    source=load('clay_glb',READER).GLB(SOURCE)
    fitter=load('anatomical_ray_support',FITTER).OuterHead(source)
    n, rows = 64, 18
    anchors=np.array([0,.40,.80,1.15,1.57,1.90,2.25,2.65,math.pi])
    elevations=np.array([.30,.27,.19,.06,-.03,-.12,-.26,-.49,-.59])
    directions=[]; parameters=[]
    for j in range(rows):
        for i in range(n):
            theta=2*math.pi*i/n
            angle=abs((theta+math.pi)%(2*math.pi)-math.pi)
            low=np.interp(angle, anchors, elevations)+.018*math.sin(theta)*math.sin(angle)
            elevation=low+(math.pi/2-low)*j/rows
            # Coarse part/sweep is in edge flow and broad relief only.
            theta += .055*math.sin(math.pi*j/rows)*(1-.30*math.cos(theta))
            directions.append([math.sin(theta)*math.cos(elevation), math.sin(elevation), math.cos(theta)*math.cos(elevation)])
            parameters.append([i,j])
    d=np.array(directions); fitted=fitter.rays(d)
    relief=.006+np.array([.0020*math.sin(math.pi*j/rows)*(.5+.5*math.sin(i/n*2*math.pi+.6)) for i,j in parameters])
    vertices=(fitted+d*relief[:,None]).tolist(); faces=[]; groups={}
    idx=lambda i,j: j*n+i%n
    # One crown patch is replaced by a continuous shared-edge folded gather.
    left,right,lo,hi=25,39,11,16
    for j in range(rows-1):
        for i in range(n):
            if left<=i<right and lo<=j<hi: continue
            faces.append([idx(i,j),idx(i+1,j),idx(i+1,j+1),idx(i,j+1)])
    apex=len(vertices); vertices.append((fitter.rays(np.array([[0.,1.,0.]]))[0]+[0,.006,0]).tolist())
    for i in range(n): faces.append([idx(i,rows-1),idx(i+1,rows-1),apex])
    groups['Scalp sweep']=list(range(rows*n))+[apex]
    boundary=([idx(i,lo) for i in range(left,right)]+
              [idx(right,j) for j in range(lo,hi)]+
              [idx(i,hi) for i in range(right,left,-1)]+
              [idx(left,j) for j in range(hi,lo,-1)])
    b=np.array(vertices)[boundary]; center=b[:,[0,2]].mean(0)
    # Boundary order is retained around the original opening. Map each corner
    # to a corresponding ring angle; no disconnected overlap or second writer.
    phi=np.unwrap(np.arctan2((b[:,2]-center[1])/.045, b[:,0]/.050))
    # Low folded cross-sections, metres: y, rx, rz, x offset, z center.
    sections=[(1.851,.044,.035,-.001,-.033),
              (1.860,.034,.029,-.001,-.040),
              (1.868,.032,.029, .000,-.040),
              (1.881,.038,.030, .003,-.039),
              (1.892,.031,.024, .009,-.034),
              (1.898,.017,.013, .011,-.030)]
    previous=boundary; fold=[]
    for k,(height,rx,rz,x,z) in enumerate(sections):
        ring=[]
        for angle in phi:
            ring.append(len(vertices))
            # One oblique folded contour rather than a stack of round lobes.
            tilt=.002*math.sin(angle+.65)*(k/max(1,len(sections)-1))
            vertices.append([x+rx*math.cos(angle),height+tilt,z+rz*math.sin(angle)])
        for i in range(len(ring)):
            q=(i+1)%len(ring); faces.append([previous[i],previous[q],ring[q],ring[i]])
        fold.extend(ring); previous=ring
    end=len(vertices); vertices.append([.010,1.893,-.030])
    for i in range(len(previous)): faces.append([previous[i],previous[(i+1)%len(previous)],end])
    fold.append(end); groups['Folded gather']=fold
    # Rear hairline continues into two broad S falls using the exact same
    # boundary vertices. No clump tubes, separate root caps, or narrow bridge.
    for label,start,stop,longer in [('Dominant S fall',21,32,True),('Returning S fall',32,43,False)]:
        root=[idx(i,0) for i in range(start,stop+1)]; rootv=np.array(vertices)[root]
        previous=root; group=list(root); width=len(root)
        for j in range(1,10):
            t=j/9; ring=[]
            blend=t*t*(3-2*t)
            xmid=(-.010 if longer else .030)+(.025 if longer else -.018)*math.sin(2*math.pi*t-.3)
            halfwidth=(.047 if longer else .040)*(1-.12*t)*(1-.65*max(0,(t-.72)/.28)**1.4)
            cy=(1.697 if longer else 1.705)-(.180 if longer else .160)*t
            cz=-.100-(.054 if longer else .034)*math.sin(math.pi*.82*t)
            for k in range(width):
                u=k/(width-1)*2-1
                target=np.array([xmid+halfwidth*u,cy+.009*u*(1 if longer else -1),cz+.013*u*u])
                target[1]+=.004*(1-u*u)*math.sin(math.pi*t)
                p=rootv[k]*(1-blend)+target*blend
                # Local attachment seating only: the interpolated first few
                # fall rows otherwise take a chord through the posterior neck.
                # Preserve the authored lower S silhouette and every scalp/
                # gather vertex; do not inflate the whole anatomical envelope.
                if p[1]>1.670 and j<=4:
                    radial=p-ORIGIN;radius=float(np.linalg.norm(radial));radial/=radius
                    support=fitter.rays(radial[None])[0]
                    required=float(np.linalg.norm(support-ORIGIN))+.008
                    if radius<required:p=ORIGIN+radial*required
                ring.append(len(vertices)); vertices.append(p.tolist())
            for k in range(width-1): faces.append([previous[k],ring[k],ring[k+1],previous[k+1]])
            group.extend(ring); previous=ring
        groups[label]=group
    v=np.asarray(vertices,dtype='<f8')
    # Remove unreferenced control points inside the original crown opening.
    used=np.unique(np.concatenate([np.array(f)for f in faces])); remap=np.full(len(v),-1,int);remap[used]=np.arange(len(used))
    faces=[[int(remap[i])for i in f]for f in faces];v=v[used]
    groups={name:sorted(set(int(remap[i])for i in g if remap[i]>=0))for name,g in groups.items()}
    # Explicit clay reference extraction: source arrays untouched, no reexport.
    references=[]
    for mi,pi,p in source.primitives():
        material=source.doc['materials'][p['material']]['name']
        pv=source.array(p['attributes']['POSITION']);pt=source.array(p['indices']).reshape(-1,3)
        if(mi,pi)==(2,0):
            brow=(pv[:,1]>1.740)&(pv[:,1]<1.755)&(pv[:,2]>.139)&(abs(pv[:,0])<.060)
            selected=pt[np.all(brow[pt],axis=1)]
        else:
            selected=pt[np.all(pv[pt,1]>1.42,axis=1)]
        if not len(selected):continue
        rused,inv=np.unique(selected,return_inverse=True)
        references.append(dict(name=f'LOCKED_{mi}_{pi}_{material}',material=material,mesh=mi,primitive=pi,
                               vertices=pv[rused].astype(float).tolist(),faces=inv.reshape(-1,3).tolist(),
                               source_rows=rused.tolist(),source_indices_sha256=hashlib.sha256(selected.tobytes()).hexdigest()))
    data=dict(schema=1,kind='editable whole-hair coarse clay cage, not runtime evidence',source_glb=str(SOURCE),source_glb_sha256=SOURCE_SHA,
              concept_sha256=CONCEPT_SHA,generator_sha256=sha(__file__),reader_sha256=sha(READER),fitter_sha256=sha(FITTER),
              source_commit='96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12',coordinate_system='glTF metres, +Y up, +Z face; Blender x,-z,y',
              vertices=v.tolist(),faces=faces,groups=groups,reference_meshes=references,
              fold_cross_sections=sections,modifiers=dict(subdivision_levels=1,render_levels=2,solidify_thickness_m=.002,solidify_offset=-1),
              limits=['No runtime export, UV, skin weights, fine strands, LOD, engine/import or render.',
                      'References are rest-space source extraction, not an animated rig transfer.',
                      'Four-view rendered clay review pending; counts/contact checks cannot accept shape.'])
    out.mkdir(parents=True);(out/'clay-cage.json').write_text(json.dumps(data,separators=(',',':'))+'\n');obj(out/'whole-hair-cage.obj',v,faces)
    manifest=dict(schema=1,inactive=True,source_glb_sha256=SOURCE_SHA,generator_sha256=sha(__file__),vertices=len(v),faces=len(faces),
                  bounds_m=[v.min(0).tolist(),v.max(0).tolist()],files={p.name:sha(p)for p in sorted(out.iterdir())})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    assert sha(SOURCE)==SOURCE_SHA
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':main()
