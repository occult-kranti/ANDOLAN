"""Stored compact source and exact retained-pose triangle contacts."""
import argparse,gzip,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from build_armour import ROOT,GLB,SOURCE_SHA,sha
from check_source import candidate,transform,collider_parts,contacts,selfcheck
sys.path.insert(0,str(HERE.parent/'articulated-r5'))
from verify_bind_space import skin

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--poses',choices=['none','representative','all'],default='representative');args=ap.parse_args();assert not args.output.exists();began=time.monotonic()
 source=ROOT/'assets/heroes/rama-hero.glb';assert sha(source)==SOURCE_SHA;g=GLB(source);ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);rests=np.linalg.inv(ib)
 manifest=json.loads((args.candidate/'source-manifest.json').read_text());assert manifest['attachment']['index']==49 and manifest['attachment']['bone']=='shoulder01.L';assert g.doc['nodes'][g.doc['skins'][0]['joints'][49]]['name']=='shoulder01.L'
 parts=collider_parts(g);rest_parts={k:p['v'] for k,p in parts.items()};levels={};near=None
 for level,row in manifest['levels'].items():
  path=args.candidate/Path(row['path']).name;assert sha(path)==row['sha256'];v,t=candidate(GLB(path));world=transform(v,rests[49]);check=contacts(world,t,parts,rest_parts)
  levels[level]={'frames_and_uvs_passed':True,'triangles':len(t),'world_rest_bounds_m':[world.min(0).tolist(),world.max(0).tolist()],'contacts':check}
  if level=='near':near=(v,t)
  print(level,'rest',{k:c['crossings'] for k,c in check.items() if c['crossings']},flush=True)
 report={'schema':1,'complete':False,'checker_sha256':sha(__file__),'source_sha256':SOURCE_SHA,'manifest_sha256':sha(args.candidate/'source-manifest.json'),'triangle_controls':selfcheck(),'levels':levels,'pose_rows':[],'scope':'Source-rest and direct-API retained posed triangle contacts of new rigid49 sculpture. Existing imported bind-space proof is separate; no new import/raster or continuous motion claim.'}
 args.output.write_text(json.dumps(report,indent=2)+'\n')
 if args.poses!='none':
  tape=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';native=json.loads(gzip.decompress(tape.read_bytes()));assert native['source_before']==native['source_after'] and native['source_before']['res://assets/heroes/rama-hero.glb']==SOURCE_SHA
  samples=native['samples'] if args.poses=='all' else [native['samples'][i] for i in sorted(set([0,347]+list(range(0,348,29))))];v,t=near;rest_world=transform(v,rests[49])
  report['pose_tape_sha256']=sha(tape);report['motion_sha256']=native['source_before']['res://scripts/rama_motion.gd']
  for s in samples:
   poses=np.array(s['bone_globals']);posed={n:skin(p['v'],p['j'],p['w'],poses@ib) for n,p in parts.items()};moved=transform(v,poses[49]);check=contacts(moved,t,parts,posed)
   report['pose_rows'].append({'id':s['id'],'contacts':check,'rigid_edge_length_maximum_error_m':float(np.max(abs(np.linalg.norm(moved[t[:,1]]-moved[t[:,0]],axis=1)-np.linalg.norm(rest_world[t[:,1]]-rest_world[t[:,0]],axis=1))))})
   print(s['id'],{k:c['crossings'] for k,c in check.items() if c['crossings']},flush=True);args.output.write_text(json.dumps(report,indent=2)+'\n')
 report.update(complete=True,elapsed_s=time.monotonic()-began,source_unchanged=sha(source)==SOURCE_SHA)
 report['body_crossing_free']=all(row['contacts']['Rama warm skin']['crossings']==0 for row in list(levels.values())+report['pose_rows'])
 report['all_listed_colliders_crossing_free']=all(c['crossings']==0 for row in list(levels.values())+report['pose_rows'] for c in row['contacts'].values())
 args.output.write_text(json.dumps(report,indent=2)+'\n');print('complete',report['body_crossing_free'],report['all_listed_colliders_crossing_free'],report['elapsed_s'],flush=True)
if __name__=='__main__':main()
