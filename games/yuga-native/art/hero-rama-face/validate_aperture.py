"""Whole visible seated-globe aperture at multiple actual viewing directions."""
from pathlib import Path
import argparse,hashlib,json,math,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from validate_face import read,accessor

def first_hit(tris,origin,direction):
    a=tris[:,0];e1=tris[:,1]-a;e2=tris[:,2]-a;p=np.cross(direction,e2);det=np.sum(e1*p,axis=1);valid=abs(det)>1e-11
    inverse=np.zeros(len(tris));inverse[valid]=1/det[valid];tvec=origin-a;u=np.sum(tvec*p,axis=1)*inverse;q=np.cross(tvec,e1);v=np.sum(q*direction,axis=1)*inverse;t=np.sum(e2*q,axis=1)*inverse
    hits=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>=0)
    return float(np.min(t[hits]))if np.any(hits)else math.inf

def main():
    p=argparse.ArgumentParser();p.add_argument('asset',type=Path);p.add_argument('--partition',type=Path,required=True);p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();_,d,b=read(a.asset);meta=json.loads(a.partition.read_text());node=next(n for n in d['nodes']if n.get('name')=='RamaFace');mesh=d['meshes'][node['mesh']]
    originals=[];closeds=[];triangles=[];offset=0
    for primitive in mesh['primitives']:
        positions=accessor(d,b,primitive['attributes']['POSITION']);closed=positions.copy()
        for target in primitive['targets'][:2]:closed+=accessor(d,b,target['POSITION'])
        originals.append(positions);closeds.append(closed);triangles.append(accessor(d,b,primitive['indices']).reshape(-1,3).astype(np.int64)+offset);offset+=len(positions)
    # Visibility must include the actual nose/head occluding the far eye at an
    # oblique camera; the small orbital partition alone is not the whole head.
    body=next(n for n in d['nodes']if n.get('name')=='RamaHero')
    for primitive in d['meshes'][body['mesh']]['primitives']:
        if d['materials'][primitive['material']]['name']in ['Warm sclera','Deep brown iris','Pupil']:continue
        positions=accessor(d,b,primitive['attributes']['POSITION'])
        originals.append(positions);closeds.append(positions);triangles.append(accessor(d,b,primitive['indices']).reshape(-1,3).astype(np.int64)+offset);offset+=len(positions)
    originals=np.concatenate(originals);closeds=np.concatenate(closeds);indices=np.concatenate(triangles);checks=[]
    for side,eye in meta['eyeOriginsBlender'].items():
        x,y,z=eye;center=np.array([x,z,-y]);tri=originals[indices]
        near=(tri[:,:,1].min(axis=1)<center[1]+.025)&(tri[:,:,1].max(axis=1)>center[1]-.025)&(tri[:,:,2].max(axis=1)>.065)
        open_tris=originals[indices[near]];closed_tris=closeds[indices[near]]
        for angle in [-25,0,25,70]:
            theta=math.radians(angle);viewer=np.array([math.sin(theta),0,math.cos(theta)]);right=np.array([math.cos(theta),0,-math.sin(theta)]);visible=0;failures=[];minimum_margin=1.
            for dx in np.linspace(-.014,.014,29):
                for dy in np.linspace(-.007,.007,15):
                    radius=.0153**2-dx*dx-dy*dy
                    if radius<=0:continue
                    point=center+right*dx+np.array([0,dy,0])+viewer*math.sqrt(radius);origin=point+viewer*.10
                    open_hit=first_hit(open_tris,origin,-viewer)
                    if open_hit<.10-.0002:continue
                    visible+=1
                    closed_hit=first_hit(closed_tris,origin,-viewer);margin=.10-closed_hit;minimum_margin=min(minimum_margin,margin)
                    if margin<-.0002:failures.append([round(float(dx),5),round(float(dy),5),None if not math.isfinite(margin)else margin])
            entry={'name':'Whole visible %s globe closes at %d degrees'%(side,angle),'passed':not failures,'details':{'tested_visible_aperture_points':visible,'grid_points_before_visibility_filter':435,'minimum_margin_m':minimum_margin if math.isfinite(minimum_margin)else None,'uncovered':failures}}
            checks.append(entry);print(('PASS 'if entry['passed']else'FAIL ')+entry['name'],json.dumps(entry['details']))
    report={'passed':all(c['passed']for c in checks),'count':len(checks),'checks':checks,'asset_sha256':hashlib.sha256(a.asset.read_bytes()).hexdigest(),'validator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Whole currently visible globe aperture on 29x15 sphere grids at four camera directions. Open-state skin visibility selects relevant rays; closed skin must precede every visible seated-globe sample. No visual appearance or gameplay/GPU claim.'}
    a.report.write_text(json.dumps(report,indent=2)+'\n');return 0 if report['passed']else 1

if __name__=='__main__':sys.exit(main())
