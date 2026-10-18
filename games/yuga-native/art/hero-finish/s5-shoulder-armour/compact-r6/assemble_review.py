"""Fail-closed source gate before isolated shoulder replacement assembly."""
import argparse,gzip,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from check_candidate import ROOT,PINS,sha

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();assert not args.output.exists()and not args.report.exists()
 candidate=HERE/'candidate-r5';mh=sha(candidate/'source-manifest.json');native=json.loads(gzip.decompress((ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz').read_bytes()));expected=sorted(s['id']for s in native['samples']);reports={};summary={}
 for level in PINS:
  rows=[];paths=sorted(HERE.glob('full-smooth-'+level+'-r5-*.json'));assert paths
  for p in paths:
   j=json.loads(p.read_text());assert j['complete']and j['all_listed_colliders_crossing_free']and j['nocked_arrow_conservative_bounds_clear'];assert j['source_sha256']==PINS[level]and j['manifest_sha256']==mh and j['checker_sha256']==sha(HERE/'check_candidate.py');rows+=j['pose_rows'];reports[str(p.relative_to(ROOT))]=sha(p)
  assert sorted(r['id']for r in rows)==expected and len(rows)==348
  gaps=[(c.get('guaranteed_lower_bound_m',c.get('minimum_distance_m')),r['id'],name)for r in rows for name,c in r['contacts'].items()];gaps=[g for g in gaps if g[0]is not None]
  summary[level]={'pose_rows':len(rows),'minimum_guaranteed_source_gap_m':min(gaps)[0],'gap_pose_and_collider':min(gaps)[1:],'maximum_rigid_edge_error_m':max(r['rigid_edge_length_maximum_error_m']for r in rows),'minimum_arrow_aabb_bound_m':min(r['nocked_arrow_bound']['clearance_lower_bound_m']for r in rows)}
 p=HERE/'full-smooth-three-lods-pose37-r5.json';j=json.loads(p.read_text());assert j['complete']and j['passed']and len(j['rows'])==111 and j['candidate_manifest_sha256']==mh and j['checker_sha256']==sha(HERE/'check_pose37.py');reports[str(p.relative_to(ROOT))]=sha(p)
 for level in PINS:
  rows=[r for r in j['rows']if r['level']==level];assert len(rows)==37;gaps=[c.get('guaranteed_lower_bound_m',c.get('minimum_distance_m'))for r in rows for c in r['contacts'].values()];summary[level]['additional_pose_rows']=37;summary[level]['minimum_additional_pose_gap_m']=min(x for x in gaps if x is not None)
 command=[sys.executable,str(HERE/'replace_left_cap.py'),'--sculpture',str(candidate),'--source',str(ROOT/'art/hero-finish/s4-diadem-smooth/candidate-r2'),'--output',str(args.output)]
 subprocess.run(command,check=True)
 result={'schema':1,'passed_source_gate':True,'candidate_manifest_sha256':mh,'source_pins':PINS,'reports':reports,'summary':summary,'assembly_command':command,'assembly_manifest_sha256':sha(args.output/'replacement-manifest.json'),'scope':'Exact nominal source contact admission on348draw+37additional direct-API poses at3LODs. Stored replacement/import/secondary/pixel gates remain separate.'}
 args.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
