"""Locate collision regions on the retained r4 plate components."""
import gzip
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from build_armour import ROOT,GLB,sha
from check_source import candidate,transform,collider_parts
from geometry_probe import narrow
from verify_bind_space import skin

def crossing_faces(a,b):
    low=a.min((0,1));high=a.max((0,1))
    b=b[np.all(b.max(1)>=low,axis=1)&np.all(b.min(1)<=high,axis=1)]
    if len(b)==0:return np.array([],int),0
    ac=a.mean(1);bc=b.mean(1);ar=np.linalg.norm(a-ac[:,None],axis=2).max(1);br=np.linalg.norm(b-bc[:,None],axis=2).max(1)
    lists=cKDTree(bc).query_ball_point(ac,ar+br.max())
    ia=np.repeat(np.arange(len(a)),[len(x) for x in lists]);ib=np.concatenate(lists).astype(int)
    keep=np.all(a[ia].max(1)>=b[ib].min(1),axis=1)&np.all(b[ib].max(1)>=a[ia].min(1),axis=1)
    ia,ib=ia[keep],ib[keep]
    if len(ia)==0:return np.array([],int),0
    _,cross=narrow(a[ia],b[ib]);return np.unique(ia[cross]),int(cross.sum())

def main():
    output=HERE/'component-contact-r1.json';assert not output.exists()
    g=GLB(ROOT/'assets/heroes/rama-hero.glb');ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib)
    manifest=json.loads((HERE.parent/'candidate-r4/source-manifest.json').read_text())
    v,t=candidate(GLB(HERE.parent/'candidate-r4/shoulder-armour-near.glb'));world=transform(v,rest[50])
    groups=[];offset=0
    for material in range(3):
        for part in manifest['levels']['near']['components']:
            if part['material']!=material:continue
            count=part['vertices'];faces=t[np.all((t>=offset)&(t<offset+count),axis=1)]
            groups.append((part['name'],faces));offset+=count
    parts=collider_parts(g)
    native=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()))
    samples=[x for x in native['samples'] if x['id'] in ['dawn_volley-pitch0.0-step35','kodanda_shot-pitch-0.3-step0']]
    if len(samples)<2:samples=[native['samples'][0],next(x for x in native['samples'] if x['id']=='dawn_volley-pitch0.0-step35')]
    rows=[]
    for sample in samples:
        poses=np.array(sample['bone_globals']);posed={name:skin(p['v'],p['j'],p['w'],poses@ib)[p['tri']] for name,p in parts.items()}
        for mode in ['single50','split49-50-51']:
            for name,faces in groups:
                bone=50 if mode=='single50' else 51 if ('Second overlapping' in name or name=='Rolled gold border 3') else 50 if ('First overlapping' in name or name=='Rolled gold border 2') else 49
                moved=transform(world,poses[bone]@ib[bone]);collisions={}
                for collider in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']:
                    ids,count=crossing_faces(moved[faces],posed[collider])
                    if len(ids):
                        points=v[np.unique(faces[ids])];angles=np.rad2deg(np.arctan2(points[:,0],points[:,2]))
                        collisions[collider]={'pairs':count,'crossing_faces':len(ids),'axial_range_m':[float(points[:,1].min()),float(points[:,1].max())],'angles_degrees':[float(angles.min()),float(angles.max())]}
                rows.append({'pose':sample['id'],'binding':mode,'component':name,'bone':bone,'contacts':collisions})
                if collisions:print(sample['id'],mode,name,collisions,flush=True)
    output.write_text(json.dumps({'schema':1,'script_sha256':sha(__file__),'candidate_manifest_sha256':sha(HERE.parent/'candidate-r4/source-manifest.json'),'rows':rows,'scope':'Localized retained r4 source triangle crossing regions. Diagnostic, no new geometry or clearance acceptance.'},indent=2)+'\n')

if __name__=='__main__':main()
