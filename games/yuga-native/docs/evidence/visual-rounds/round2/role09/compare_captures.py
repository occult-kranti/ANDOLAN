#!/usr/bin/env python3
"""Verify actual paired capture controls; numerical differences are not visual approval."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
 a=json.loads((args.baseline/'capture.json').read_text());b=json.loads((args.candidate/'capture.json').read_text());ar={s['id']:s for s in a['shots']}; rows=[]
 keys=('camera','context','face','light','lod','motion','night','player_transform','pose_pin','tree_paused','ui_visible','viewport','visual_yaw')
 for shot in b['shots']:
  source=ar[shot['id']]; controls={k:source[k]==shot[k] for k in keys}
  # The newer recorder adds angular_distance to its light metadata. Compare
  # every field recorded by the baseline and retain additions explicitly.
  controls['light']=all(k in shot['light'] and v==shot['light'][k] for k,v in source['light'].items())
  extra_light={k:v for k,v in shot['light'].items() if k not in source['light']}
  first=args.baseline/source['file'];second=args.candidate/shot['file']
  hashes_ok=sha(first)==source['sha256'] and sha(second)==shot['sha256']
  ia=np.asarray(Image.open(first).convert('RGB')).astype(float);ib=np.asarray(Image.open(second).convert('RGB')).astype(float);delta=abs(ia-ib)
  rows.append({'id':shot['id'],'matched_controls':controls,'extra_candidate_light_metadata':extra_light,'hashes_verified':hashes_ok,'baseline_sha256':sha(first),'candidate_sha256':sha(second),'mean_abs_rgb_byte_delta':float(delta.mean()),'different_pixels':int(np.any(delta>0,axis=2).sum()),'scope':'Delta quantifies difference only; individual original-image review required'})
 common=set(a['source_sha256'])&set(b['source_sha256']); changed={k:{'baseline':a['source_sha256'][k],'candidate':b['source_sha256'][k]}for k in sorted(common) if a['source_sha256'][k]!=b['source_sha256'][k]}
 result={'task':'R2-09','passed':bool(rows) and all(x['hashes_verified'] and all(x['matched_controls'].values())for x in rows) and a['complete'] and b['complete'] and a['source_unchanged'] and b['source_unchanged'],'baseline':str(args.baseline),'candidate':str(args.candidate),'baseline_capture_sha256':sha(args.baseline/'capture.json'),'candidate_capture_sha256':sha(args.candidate/'capture.json'),'rows':rows,'changed_common_source_pins':changed,'candidate_extra_source_pins':sorted(set(b['source_sha256'])-set(a['source_sha256'])),'limitation':'Early baseline excludes import pins; actual baseline mip state independently checked by imported_material_review.gd. Paired controls do not establish visual improvement or performance.'}
 args.report.write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps({'passed':result['passed'],'pairs':len(rows),'changed_common_source_pins':changed,'failed_controls':{r['id']:[k for k,v in r['matched_controls'].items()if not v]for r in rows}},indent=2));raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
