#!/usr/bin/env python3
"""Read-only independent identity and selected landing-metric audit; no engine."""
import gzip,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[7]
OUT=Path(__file__).resolve().parent
S=ROOT/'games/yuga-native/docs/evidence/desktop-finish/S3'
def pin(p):
 b=p.read_bytes();return {'path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
refs=[];checks=[];data={};metrics={};selected=[]
for case,n,ids in [('landing120',40,[7,8,9,39]),('full',120,[1,18,47,94,95,119])]:
 data[case]={}
 for branch,folder in [('baseline',S/f'W5-actual-motion-r1/{case}/candidate'),('successor',S/f'W5-landing-successor-actual-r1/{case}')]:
  cp=folder/'capture.json.gz';d=json.loads(gzip.decompress(cp.read_bytes()));data[case][branch]=d;refs.append(pin(cp))
  checks.append({'name':f'{case}/{branch} complete, immutable sources and exact shot count','passed':d['complete'] is True and d['source_unchanged'] is True and len(d['shots'])==n})
  valid=True
  for s in d['shots']:
   p=folder/'originals'/(s['id']+'.png'); h=pin(p);valid &= h['sha256']==s['sha256']
   if int(s['id'].split('-')[1]) in ids:selected.append({'case':case,'branch':branch,'physics_frame':s['physics_frame'],'render_frame':s['render_frame'],**h})
  checks.append({'name':f'{case}/{branch} every original PNG agrees with capture SHA','passed':bool(valid),'originals':n})
 cmp=S/f'W5-landing-successor-actual-r1/{case}-comparison.json';c=json.loads(cmp.read_text());refs.append(pin(cmp))
 checks.append({'name':f'{case} owner source/control comparison is explicit true 42/42','passed':c['passed'] is True and len(c['checks'])==42 and all(x['passed'] is True for x in c['checks'])})
 metrics[case]={'selected_frame_pair_png_equal':{f'{i:03}':data[case]['baseline']['shots'][i]['sha256']==data[case]['successor']['shots'][i]['sha256'] for i in ids}}
 if case=='landing120':
  for branch,d in data[case].items():
   a,b=[d['shots'][i] for i in (7,8)];pa,pb=[s['sole_projection']['sides']['R'] for s in (a,b)]
   metrics[case][branch]={'first_grounded_frames':[7,8],'physics':[a['physics_frame'],b['physics_frame']],'on_floor':[a['final_modifier_body']['on_floor'],b['final_modifier_body']['on_floor']],'ankle_world_delta_mm':[(y-x)*1000 for x,y in zip(pa['ankle_world'],pb['ankle_world'])],'ankle_screen_delta_px':[y-x for x,y in zip(pa['ankle_px'],pb['ankle_px'])],'ankle_screen_distance_px':math.dist(pa['ankle_px'],pb['ankle_px'])}
checks.append({'name':'exactly twenty directly inspected original references','passed':len(selected)==20})
r={'passed':all(x['passed'] for x in checks),'check_count':len(checks),'checks':checks,'scope':'Read-only archive identity and selected metric recomputation, not new engine tests or full-speed human playback. All320 PNG hashes checked;20 originals directly inspected. Owner42/42 comparisons cited separately.','original_hash_count':320,'selected_originals':selected,'metrics':metrics,'references':refs}
(OUT/'input-audit.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'passed':r['passed'],'checks':len(checks),'original_hashes':320,'direct_originals':len(selected),'metrics':metrics},indent=2))
