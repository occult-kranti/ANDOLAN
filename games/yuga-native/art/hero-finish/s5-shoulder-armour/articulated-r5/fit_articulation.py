"""Bounded rigid plate/pivot study; no bone writes or source modifications."""
import argparse
import gzip
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import build_armour as original
from build_armour import ROOT,GLB,sha
from check_source import transform,collider_parts,contacts
from verify_bind_space import skin


def surface_fn(layer):
    # Open the medial root edge and relieve the rear under-arm lip. Preserve
    # front width, rolled edge thickness and actual source-supported radii.
    starts=[-.005,.050,.115];ends=[.092,.157,.200]
    radii=[.111,.091,.076];angle_pairs=[(-50,90),(-45,90),(-42,88)]
    def point(u,v):
        degrees=angle_pairs[layer][0]*(1-u)+angle_pairs[layer][1]*u
        theta=math.radians(degrees)
        end=ends[layer]+.009*math.cos(3*theta)+.006*math.cos(theta)
        s=starts[layer]*(1-v)+end*v
        radius=radii[layer]+.010*max(math.sin(theta),0)-.009*max(-math.sin(theta),0)
        radius+=.009*math.sin(math.pi*v)-.006*v+.004*math.cos(theta)*math.sin(math.pi*v)
        radius=max(radius,float(original.ENVELOPE([[s,degrees]])[0])+[.018,.012,.008][layer])
        return np.array([radius*math.sin(theta),s,radius*math.cos(theta)])
    return point


def plate_for(name):
    return 2 if ('Second overlapping' in name or name=='Rolled gold border 3') else 1 if ('First overlapping' in name or name=='Rolled gold border 2') else 0


def prepare_geometry(level,g,ib):
    original.fit_envelope(g,ib[50]);original.surface_fn=surface_fn
    shapes=original.geometry(level);rest=np.linalg.inv(ib)
    groups=[]
    for plate in range(3):
        positions=[];triangles=[];offset=0
        for shape in shapes:
            if plate_for(shape.name)!=plate:continue
            arrays,_=shape.arrays();v=arrays['POSITION'];tri=arrays['indices'].reshape(-1,3)
            positions.append(transform(v,rest[50]));triangles.append(tri+offset);offset+=len(v)
        groups.append((np.concatenate(positions),np.concatenate(triangles)))
    return shapes,groups


def deform(poses,ib,weight,mode='swing'):
    rest=np.linalg.inv(ib)
    parent=poses[49]@ib[49];arm=poses[50]@ib[50]
    rotation_parent=Rotation.from_matrix(parent[:3,:3]).as_matrix()
    if mode=='full':
        difference=Rotation.from_matrix(arm[:3,:3]@rotation_parent.T).as_rotvec()
    else:
        start=rotation_parent@rest[50,:3,1];start/=np.linalg.norm(start)
        end=poses[50,:3,1];end=end/np.linalg.norm(end)
        axis=np.cross(start,end);length=np.linalg.norm(axis);angle=math.atan2(length,np.dot(start,end))
        if length<1e-9:
            axis=rotation_parent@rest[50,:3,0];axis/=np.linalg.norm(axis)
        else:axis/=length
        difference=axis*angle
    rotation=Rotation.from_rotvec(difference*weight).as_matrix()@rotation_parent
    pivot=rest[50,:3,3];current=transform(pivot[None,:],parent)[0]
    result=np.eye(4);result[:3,:3]=rotation;result[:3,3]=current-rotation@pivot
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();assert not args.output.exists()
    began=time.monotonic();g=GLB(ROOT/'assets/heroes/rama-hero.glb')
    ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
    _,groups=prepare_geometry('far',g,ib)
    parts=collider_parts(g)
    native=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()))
    samples=[native['samples'][i] for i in sorted(set([0,len(native['samples'])-1]+list(range(0,len(native['samples']),29))))]
    selected={name:p for name,p in parts.items() if name in ['Rama warm skin','Cobalt handwoven silk','Cobalt lotus brocade']}
    prepared=[]
    for sample in samples:
        poses=np.array(sample['bone_globals']);posed={name:skin(p['v'],p['j'],p['w'],poses@ib) for name,p in selected.items()}
        prepared.append((sample['id'],poses,posed))
    rows=[]
    for plate,(v,t) in enumerate(groups):
        options=[('swing',0)] if plate==0 else [(mode,w) for mode in ['swing','full'] for w in [0.,.35,.65,1.]]
        for mode,weight in options:
            pose_rows=[]
            for label,poses,posed in prepared:
                matrix=deform(poses,ib,weight,mode)
                moved=transform(v,matrix)
                result=contacts(moved,t,selected,posed)
                pose_rows.append({'pose':label,'contacts':result})
            counts={name:sum(row['contacts'][name]['crossings'] for row in pose_rows) for name in selected}
            row={'plate':plate,'mode':mode,'weight':weight,'crossing_pairs':counts,'failed_poses':sum(any(v['crossings'] for v in row['contacts'].values()) for row in pose_rows),'poses':pose_rows}
            rows.append(row);print(plate,mode,weight,counts,'poses',row['failed_poses'],flush=True)
            args.output.write_text(json.dumps({'schema':1,'script_sha256':sha(__file__),'complete':False,'rows':rows},indent=2)+'\n')
    args.output.write_text(json.dumps({'schema':1,'script_sha256':sha(__file__),'complete':True,'source_sha256':sha(ROOT/'assets/heroes/rama-hero.glb'),'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Finite far-LOD rigid articulation trials on13retained poses. Original source and r4 sealed; no final asset, runtime controller or rendered acceptance.'},indent=2)+'\n')


if __name__=='__main__':main()
