#!/usr/bin/env python3
"""Fit the separate mouth and nostril detail to the v1 lower-face surface.

The published baseline and v1 remain untouched. This is a reversible v2 art
candidate: it aligns the separate line-mesh to the front-most skin triangle at
each vertex's X/Y position in glTF rest space. No UVs, skin or animation change.
It does not prove contact in animated facial expressions or during speech.
"""
from pathlib import Path
import argparse
import json
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'hero-rama-lod'))
from glb_lod import GLB
from refine import Writer, digest


def surface(points, skin, triangles):
    """Frontmost barycentric +Z skin intersection, with local plane slopes."""
    p=skin[triangles]
    p=p[(p[:,:,1].max(axis=1)>1.74)&(p[:,:,1].min(axis=1)<1.88)&
        (p[:,:,2].max(axis=1)>.1)&(np.abs(p[:,:,0]).min(axis=1)<.13)]
    a,b,c=p[:,0,:],p[:,1,:],p[:,2,:]
    cross=np.cross(b-a,c-a)
    den=(b[:,1]-c[:,1])*(a[:,0]-c[:,0])+(c[:,0]-b[:,0])*(a[:,1]-c[:,1])
    valid=np.abs(den)>1e-10
    depth=np.empty(len(points)); gradients=np.empty((len(points),2))
    for i,(x,y,_) in enumerate(points):
        u=np.divide((b[:,1]-c[:,1])*(x-c[:,0])+(c[:,0]-b[:,0])*(y-c[:,1]),den,
                    out=np.zeros_like(den),where=valid)
        v=np.divide((c[:,1]-a[:,1])*(x-c[:,0])+(a[:,0]-c[:,0])*(y-c[:,1]),den,
                    out=np.zeros_like(den),where=valid)
        inside=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
        if not inside.any(): raise ValueError(f'No skin surface under line vertex {i}')
        z=u*a[:,2]+v*b[:,2]+(1-u-v)*c[:,2]
        winner=np.argmax(np.where(inside,z,-np.inf))
        depth[i]=z[winner]
        gradients[i]=(-cross[winner,0]/cross[winner,2],-cross[winner,1]/cross[winner,2])
    return depth,gradients


def stats(v):
    return {'min_mm':round(float(v.min()*1000),5),'median_mm':round(float(np.median(v)*1000),5),
            'p95_mm':round(float(np.quantile(v,.95)*1000),5),'max_mm':round(float(v.max()*1000),5),
            'below_surface_vertices':int((v < -1e-7).sum())}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=HERE/'hanuman-face-candidate.glb')
    parser.add_argument('--output',type=Path,default=HERE/'hanuman-face-contact-candidate.glb')
    parser.add_argument('--report',type=Path,default=HERE/'contact-report.json')
    args=parser.parse_args()
    if args.source.resolve()==args.output.resolve(): raise ValueError('Refusing to overwrite source')
    g=GLB(args.source); w=Writer(g); primitives=g.doc['meshes'][0]['primitives']
    def material(p): return g.doc['materials'][p['material']]['name']
    skin=next(p for p in primitives if material(p)=='Vanara · painted copper anatomy')
    detail=next(p for p in primitives if material(p)=='Face · warm recessed lines')
    skinp=g.array(skin['attributes']['POSITION']).astype(float)
    triangles=g.array(skin['indices']).reshape(-1,3)
    attr=detail['attributes']; p=g.array(attr['POSITION']).astype(float)
    z,gradient=surface(p,skinp,triangles); old=p[:,2]-z
    # Each group is transformed monotonically. A small positive clearance
    # avoids burying the dark surface at rest; both sides use the same offset.
    groups={'mouth':(p[:,1]<1.82,.35), 'nostrils':(p[:,1]>=1.82,.15)}
    new=p.copy();J=np.zeros((len(p),3,3));J[:,0,0]=1;J[:,1,1]=1
    group_reports={}
    for name,(mask,scale) in groups.items():
        base=float(old[mask].min());gap=.00025+scale*(old[mask]-base)
        new[mask,2]=z[mask]+gap
        J[mask,2,0]=(1-scale)*gradient[mask,0]
        J[mask,2,1]=(1-scale)*gradient[mask,1]
        J[mask,2,2]=scale
        group_reports[name]={'vertices':int(mask.sum()),'depth_scale':scale,
                             'before':stats(old[mask]),'after':stats(gap)}
    norm=g.array(attr['NORMAL']).astype(float)
    nn=np.linalg.solve(J.transpose(0,2,1),norm[:,:,None])[:,:,0]
    nn/=np.linalg.norm(nn,axis=1,keepdims=True).clip(1e-10)
    tang=g.array(attr['TANGENT']).astype(float)
    tt=(J@tang[:,:3,None])[:,:,0]
    tt-=nn*np.einsum('ij,ij->i',nn,tt)[:,None]
    tt/=np.linalg.norm(tt,axis=1,keepdims=True).clip(1e-10)
    attr['POSITION']=w.attribute(new,'VEC3',bounds=True)
    attr['NORMAL']=w.attribute(nn,'VEC3')
    attr['TANGENT']=w.attribute(np.column_stack((tt,tang[:,3])),'VEC4')
    args.output.parent.mkdir(parents=True,exist_ok=True);w.save(args.output)
    displacement=np.linalg.norm(new-p,axis=1)
    result={'source_sha256':digest(args.source),'candidate_sha256':digest(args.output),
            'material':'Face · warm recessed lines','coordinate_system':'glTF rest space, +Z face-forward',
            'method':'frontmost skin triangle, per-vertex barycentric front-axis projection; preserve positive depth',
            'target_clearance_mm':.25,'groups':group_reports,'max_adjustment_mm':float(displacement.max()*1000),
            'min_jacobian_determinant':float(np.linalg.det(J).min()),
            'limits':['Rest-space ray-to-skin separation is not proof of render quality or animated clearance.',
                      'No deformation topology, skin weights, gaze, animations, eyebrows or other materials are altered.']}
    args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,indent=2,ensure_ascii=False))

if __name__=='__main__': main()
