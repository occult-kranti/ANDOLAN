from pathlib import Path
import gzip,hashlib,json
HERE=Path(__file__).resolve().parent; OWNER=HERE.parent/'W5-actual-motion-r1/landing120'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reports={};sources={};reviewed={}
for branch in ['baseline','candidate']:
 p=OWNER/branch;z=p/'capture.json.gz';raw=gzip.decompress(z.read_bytes());j=json.loads(raw);reports[branch]=j
 assert j['complete'] is True and len(j['shots'])==40 and all(c['passed'] is True for c in j['checks'])
 for shot in j['shots']: assert sha(p/'originals'/shot['file'])==shot['sha256']
 sources[branch]={'report':str(z.relative_to(HERE.parent.parent.parent)),'compressed_sha256':sha(z),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'motion_sha256':j['source_sha256']['res://scripts/rama_motion.gd'],'all_original_hashes_verified':40,'run_sha256':sha(p/'run.json')}
 reviewed[branch]=[{ 'frame':i,'path':str((p/'originals'/j['shots'][i]['file']).relative_to(HERE.parent.parent.parent)),'sha256':j['shots'][i]['sha256']} for i in [7,8,9,39]]
b,c=reports['baseline'],reports['candidate'];assert all(x['camera']==y['camera'] and x['player_transform']==y['player_transform'] and x['physics_frame']==y['physics_frame'] and x['render_frame']==y['render_frame'] for x,y in zip(b['shots'],c['shots']))
rows={}
for branch,j in reports.items():
 rows[branch]=[]
 for i in [7,8,9,39]:
  shot=j['shots'][i];rows[branch].append({'frame':i,'physics_frame':shot['physics_frame'],'render_frame':shot['render_frame'],'on_floor':shot['draw_observed_body']['on_floor'],'gait':shot['motion']['locomotion'],'R_lowest_sole_projected_px':shot['sole_projection']['sides']['R']['lowest_sole_px'],'R_minimum_signed_m':shot['sole_contacts']['sides']['R']['minimum_signed_m']})
 a,z=rows[branch][:2];assert z['physics_frame']-a['physics_frame']==1 and j['physics_hz']==120
 rows[branch].append({'transition':'007->008','physics_seconds':1/120,'R_projected_dy_px':z['R_lowest_sole_projected_px'][1]-a['R_lowest_sole_projected_px'][1]})
r={'schema':1,'path_base':'games/yuga-native/docs/evidence','evidence_verified':True,'motion_smoothness_accepted':False,'sources':sources,'directly_viewed_originals':reviewed,'selected_observations':rows,'scope':'Eight directly inspected original stills; all80 PNG hashes verified. Projection values are observed skinned-vertex projections, not image-edge tracking. No normal-speed video/human perception or hardware FPS acceptance.'}
(HERE/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(sha(HERE/'receipt.json'))
