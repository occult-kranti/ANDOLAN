"""Stored source frames and full-triangle contacts on retained native poses."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
import numpy as np
from build_armour import ROOT, GLB, SOURCE_SHA, sha
sys.path.insert(0,str(ROOT/'docs/evidence/visual-rounds/round3/role10'))
from geometry_probe import compare, selfcheck


def transform(v,m):return (np.c_[v,np.ones(len(v))]@m.T)[:,:3]


def collider_parts(g):
    result={}
    for pi in [0,2,3,4,5,6,11]:
        p=g.doc['meshes'][2]['primitives'][pi];a=p['attributes'];v=g.array(a['POSITION']);tri=g.array(p['indices']).reshape(-1,3)
        j=g.array(a['JOINTS_0']);w=g.array(a['WEIGHTS_0']);name=g.doc['materials'][p['material']]['name']
        if pi in [2,5,6]:
            rigid=np.sum(np.where(j==50,w,0),axis=1)>.999
            selected=np.all(rigid[tri],axis=1)
            result['Existing left cap / '+name]={'v':v,'j':j,'w':w,'tri':tri[selected]}
            tri=tri[~selected]
        result[name]={'v':v,'j':j,'w':w,'tri':tri}
    return result


def candidate(g):
    vertices=[];triangles=[];offset=0
    for _,_,p in g.primitives():
        a=p['attributes'];v=g.array(a['POSITION']);n=g.array(a['NORMAL']);t=g.array(a['TANGENT']);uv=g.array(a['TEXCOORD_0']);colors=g.array(a['COLOR_0']);tri=g.array(p['indices']).reshape(-1,3)
        assert all(np.isfinite(x).all() for x in [v,n,t,uv,colors])
        assert np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-6 and np.max(abs(np.linalg.norm(t[:,:3],axis=1)-1))<1e-6
        assert np.max(abs(np.sum(n*t[:,:3],axis=1)))<1e-6
        assert np.all(np.isin(t[:,3],[-1,1])) and np.array_equal(colors,np.tile([1,1,1,0],(len(v),1)))
        assert np.all((uv>=0)&(uv<=1))
        assert 'JOINTS_0' not in a and 'skins' not in g.doc and 'animations' not in g.doc
        vertices.append(v);triangles.append(tri+offset);offset+=len(v)
    return np.concatenate(vertices),np.concatenate(triangles)


def contacts(v,t,parts,posed):
    a=v[t];low=a.min((0,1))-.006;high=a.max((0,1))+.006;result={}
    for name,part in parts.items():
        alltri=posed[name][part['tri']]
        selected=np.all(alltri.max(1)>=low,axis=1)&np.all(alltri.min(1)<=high,axis=1)
        b=alltri[selected]
        result[name]=compare(a,b,band=.006) if len(b) else {'crossings':0,'guaranteed_lower_bound_m':.006,'near_pairs':0}
        result[name]['collider_triangles_after_complete_aabb_filter']=len(b)
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--poses',choices=['none','representative','all'],default='none');ap.add_argument('--split-attachment',action='store_true');args=ap.parse_args()
    assert not args.output.exists();began=time.monotonic()
    source=ROOT/'assets/heroes/rama-hero.glb';assert sha(source)==SOURCE_SHA;g=GLB(source)
    manifest=json.loads((args.candidate/'source-manifest.json').read_text());ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rests=np.linalg.inv(ib)
    parts=collider_parts(g);rest_parts={k:p['v'] for k,p in parts.items()};levels={}
    for level,row in manifest['levels'].items():
        asset=args.candidate/Path(row['path']).name;assert sha(asset)==row['sha256'];v,t=candidate(GLB(asset))
        world=transform(v,rests[50]);check=contacts(world,t,parts,rest_parts)
        levels[level]={'frames_and_uvs_passed':True,'triangles':len(t),'source_rest_bounds_m':[world.min(0).tolist(),world.max(0).tolist()],'contacts':check}
        print(level,'rest crossing pairs',{k:x['crossings'] for k,x in check.items() if x['crossings']},flush=True)
    output={'schema':1,'checker_sha256':sha(__file__),'candidate_manifest_sha256':sha(args.candidate/'source-manifest.json'),'source_sha256':SOURCE_SHA,'triangle_counterexamples':selfcheck(),'levels':levels,
            'scope':'Source candidate rigidly attached to exact upperarm01.L. Rest/source-tape triangle contacts; no new native import/render or claimed motion quality.'}
    args.output.write_text(json.dumps(output,indent=2)+'\n')
    if args.poses!='none':
        tape=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';native=json.loads(gzip.decompress(tape.read_bytes()));assert native['source_before']==native['source_after'];assert native['source_before']['res://assets/heroes/rama-hero.glb']==SOURCE_SHA
        mapping=ROOT/'docs/evidence/desktop-finish/S4/W5/rail-mapping-review.json'
        samples=native['samples'] if args.poses=='all' else [native['samples'][i] for i in sorted(set([0,len(native['samples'])-1]+list(range(0,len(native['samples']),29))))]
        row=manifest['levels']['near'];v,t=candidate(GLB(args.candidate/Path(row['path']).name));rows=[]
        binding=np.full(len(v),50,dtype=int)
        if args.split_attachment:
            offset=0
            for material in range(3):
                for part in row['components']:
                    if part['material']!=material:continue
                    name=part['name'];bone=51 if ('Second overlapping' in name or name=='Rolled gold border 3') else 50 if ('First overlapping' in name or name=='Rolled gold border 2') else 49
                    binding[offset:offset+part['vertices']]=bone;offset+=part['vertices']
            assert offset==len(v)
        rest_world=transform(v,rests[50])
        for sample in samples:
            poses=np.array(sample['bone_globals']);transforms=poses@ib;posed={}
            for name,part in parts.items():
                points=np.c_[part['v'],np.ones(len(part['v']))];result=np.zeros((len(points),3))
                for slot in range(4):result+=np.einsum('nij,nj->ni',transforms[part['j'][:,slot]],points)[:,:3]*part['w'][:,slot,None]
                posed[name]=result
            moved=np.zeros_like(v,dtype=float)
            for bone in np.unique(binding):
                selected=binding==bone;moved[selected]=transform(rest_world[selected],poses[bone]@ib[bone])
            check=contacts(moved,t,parts,posed);rows.append({'id':sample['id'],'contacts':check})
            print('pose',sample['id'],sum(x['crossings'] for x in check.values()),flush=True)
        output['pose_replay']={'tape_sha256':sha(tape),'mapping_receipt_sha256':sha(mapping),'motion_sha256':native['source_before']['res://scripts/rama_motion.gd'],'samples':len(rows),'rows':rows,'attachment_test':'Existing shoulder01.L / upperarm01.L / upperarm02.L split, proposed only' if args.split_attachment else 'Single upperarm01.L','secondary_displacement':'Not applied; separate opposing-mask stress remains open.'}
    output['elapsed_s']=time.monotonic()-began;output['source_unchanged']=sha(source)==SOURCE_SHA
    output['body_crossing_free']=all(x['contacts']['Rama warm skin']['crossings']==0 for x in levels.values()) and all(x['contacts']['Rama warm skin']['crossings']==0 for x in output.get('pose_replay',{}).get('rows',[]))
    args.output.write_text(json.dumps(output,indent=2)+'\n');print('seconds',output['elapsed_s'],flush=True)


if __name__=='__main__':main()
