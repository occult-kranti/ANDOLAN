from pathlib import Path
import json,hashlib,zipfile,math,re,shutil
root=Path('/workspace/ANDOLAN');p=root/'scratch/visual-round4/role-05';out=root/'games/yuga-native/docs/evidence/visual-rounds/round4/role05';out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(n):return json.loads((p/n).read_text())
def vector(x):return [float(t) for t in re.findall(r'[-+]?\d*\.?\d+(?:e[-+]?\d+)?',x)] if isinstance(x,str) else x
summary={'disposition':'REJECTED_ALL_CANDIDATES_NO_RUNTIME_PROMOTION','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','candidates':{},'broad':{}}
metrics=['name','hz','maximum_joint_step_m','maximum_joint_step_detail','maximum_support_error_m','maximum_anchor_drift_per_frame_m','total_anchor_drift_m','support_frames']
for label in ['r1','r2','r3','r3a','r4']:
 r=read('comparison-'+label+'.json');s=[]
 for t in r['trials']:
  entry={which:{k:t[which][k] for k in metrics} for which in ['candidate','baseline']}
  entry['event_clocks_exact']=t['comparison']['event_clocks_exact'];entry['support_eligible_frames']=t['baseline']['support_frames'];s.append(entry)
 summary['candidates'][label]={'sha256':r['source_sha256'],'comparison':s,'finite_and_clock_checks':r['count'],'finite_and_clock_passed':r['passed']}
for label in ['r3a','r4']:
 r=read('continuity-'+label+'.json');s=[]
 for t in r['trials']:
  entry={}
  for which in ['baseline','candidate']:
   a=t[which];entry[which]={k:a[k] for k in metrics+['sampled_skin_vertices','maximum_skin_step_m','maximum_planted_skin_step_m','minimum_sampled_skin_y_m','floor_contact_frames','support_eligible_frames','duplicate_pose_equal']}
   entry[which]['maximum_release_boundary_step_m']=max([v['step_m'] for v in a['release_steps']]+[0])
   entry[which]['maximum_release_boundary_velocity_change_mps']=max([v['velocity_change_mps'] for v in a['release_steps']]+[0])
  entry['event_clocks_exact']=t['comparison']['event_clocks_exact'];s.append(entry)
 events=read('events-'+label+'.json');release_checks=[]
 for t in events['trials']:
  a=t['candidate'];rows=[]
  for e in a['contact_events']:
   if e['event']=='plant':continue
   row=a['rows'][e['sample']];expected=[b+c/a['hz'] for b,c in zip(vector(e['point']),vector(e['velocity']))];actual=row['feet_world_m'][e['side']]
   rows.append({'frame':e['sample'],'side':e['side'],'event':e['event'],'outgoing_extrapolation_to_actual_solver_error_m':math.dist(expected,actual)})
  release_checks.append({'name':a['name'],'hz':a['hz'],'rows':rows,'maximum_error_m':max([v['outgoing_extrapolation_to_actual_solver_error_m'] for v in rows]+[0])})
 summary['broad'][label]={'trials':s,'release_boundary_checks':release_checks,'finite_and_clock_checks':r['count'],'finite_and_clock_passed':r['passed'],'existing_motion_suite':{'passed':read('motion-cases-'+label+'.json')['passed'],'checks':read('motion-cases-'+label+'.json')['count']}}
summary['failures']={'r1':'Support coverage collapsed; ordinary120Hz50→4 frames, rejected.','r2':'Reacquisition snap; ordinary120Hz161.919→491.897mm, rejected.','r3':'Superseded by r3a to make repeated pose evaluation idempotent; never accepted.','r3a':'Ordinary sampled skin penetration worsens−31.584→−47.123mm; start/stop joint step89.431→118.628mm; final constrained C0/C1 release not established.','r4':'Same ordinary penetration and start/stop regression; removing pelvis tail increases release velocity jumps. Rejected.'}
summary['limitations']=['All skin continuity/floor samples in the expanded probe are every96th vertex per imported surface; existing39-check suite separately examines its full sole/finger collections.','Expanded probe pass flag covers only finite state and exact event clocks; explicit floor/continuity/support regressions govern rejection.','Reset intentionally teleports; its large world skin/release deltas are not interpreted as gait discontinuities.','Zero anchor drift measures immutable original world anchors while a plant is active. Release is explicitly unplanted.','No renders, import, movement-authority changes, source publication or commits. No final C1 acceptance.','Same actual imported164-bone rig and clip library; continuous finalR3asset capture remains later work.']
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for name in ['rama_motion.baseline.gd','rama_motion.release-r3a.gd','rama_motion.release-r4.gd','probe-continuity.gd','probe-events.gd']:
 shutil.copy2(p/name,out/name)
shutil.copy2(p/'rama_motion.release-r3a.gd',p/'rama_motion.gd')
sourcepaths=['games/yuga-native/scripts/rama_motion.gd','games/yuga-native/assets/heroes/rama-hero.glb','games/yuga-native/assets/heroes/rama-hero.glb.import','games/yuga-native/.godot/imported/rama-hero.glb-e90b8f8a0719fdd1ab2b89459efcbdac.scn','games/yuga-native/assets/animations/rama_hero_motion.tres','games/yuga-native/scripts/player.gd','games/yuga-native/tests/rama_motion_cases.gd','games/yuga-native/docs/evidence/visual-campaign/motion-reversal-review/reversal-study.zip']
pins={n:sha(root/n) for n in sourcepaths}
pins['scratch/visual-round4/role-05/archived/probe-acceleration.gd']=sha(p/'archived/probe-acceleration.gd')
(out/'source-pins.json').write_text(json.dumps(pins,indent=2)+'\n')
receipt={'engine':'Godot4.6.3.stable.official.7d41c59c4','cpu_affinity':'0,1','successful_reports':{f.name:{'passed':json.loads(f.read_text()).get('passed'),'count':json.loads(f.read_text()).get('count'),'exit_code':0} for f in p.glob('*.json') if f.name not in ['summary.json']},'failed_runs':[{'name':'r2 initial parse','exit_code':124,'reason':'Variant prospective lacked explicit Vector3 annotation; engine remained in erroredSceneTree until timeout; retained source/log.'},{'name':'r3 initial parse','exit_code':124,'reason':'Variant support lacked explicit bool annotation; retained source/log.'},{'name':'dense expanded probe','exit_code':143,'reason':'Explicitly terminated owned run after estimating timeout; retained source/log. Replaced with declared1/96vertex sample and separate existing fullsole suite.'}],'command_template':'taskset -c 0,1 timeout 180s godot --headless --path games/yuga-native --script <probe> -- --candidate-script=<absoluteCandidate> --baseline-script=<absoluteBaseline> --report=<absoluteReport>','scope':'No renderer/import; numerical execution only. Successful runner flags do not mean motion accepted.'}
(out/'test-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
files=[f for f in p.iterdir() if f.is_file() and f.name!='seal.py']+[p/'archived/probe-acceleration.gd']
with zipfile.ZipFile(out/'motion-continuity-study.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for f in sorted(files):z.write(f,f.relative_to(p))
archive_manifest={'archive_sha256':sha(out/'motion-continuity-study.zip'),'members':{str(f.relative_to(p)):sha(f) for f in sorted(files)}}
(out/'archive-manifest.json').write_text(json.dumps(archive_manifest,indent=2)+'\n')
print(json.dumps({'archive_mb':(out/'motion-continuity-study.zip').stat().st_size/1e6,'members':len(files),'runtime_unchanged':sha(root/'games/yuga-native/scripts/rama_motion.gd')==sha(p/'rama_motion.baseline.gd'),'sampled_skin_vertices':summary['broad']['r3a']['trials'][0]['candidate']['sampled_skin_vertices']}))
