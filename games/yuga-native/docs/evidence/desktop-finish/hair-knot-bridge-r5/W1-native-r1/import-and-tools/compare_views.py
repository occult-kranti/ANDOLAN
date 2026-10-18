from pathlib import Path
import json,sys,hashlib,struct,copy
mode=sys.argv[1];base=Path('/tmp/yuga-hair-r5-review-r1')
paths={b:base/((('preflight-' if mode=='preflight' else 'render-')+b+'-r1'))/('preflight.json' if mode=='preflight' else 'capture.json') for b in ['baseline','candidate']}
r={b:json.loads(p.read_text())for b,p in paths.items()}
def diff(a,b,p=''):
 if isinstance(a,dict)and isinstance(b,dict):return sum((diff(a.get(k),b.get(k),p+'/'+str(k))for k in sorted(a.keys()|b.keys())),[])
 if isinstance(a,list)and isinstance(b,list):
  if len(a)!=len(b):return [{'path':p,'lengths':[len(a),len(b)]}]
  return sum((diff(x,y,p+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))),[])
 return []if a==b else [{'path':p,'baseline':a,'candidate':b}]
census={}
for branch in ['baseline','candidate']:
 root=Path('/tmp/yuga-hair-r5-import-r1/semantics-'+branch)
 semantics=json.loads((root/'semantics.json').read_text())
 rows=[]
 for lod in semantics['lods']:
  for node in lod['nodes']:
   for surf in node.get('surfaces',[]):
    if surf['material']['name']!='Swept black hair':continue
    array=next(a for a in surf['arrays'] if a['index']==3)
    data=(root/array['file']).read_bytes()
    assert array['type']=='PackedColorArray' and len(data)==array['count']*16
    digest=hashlib.sha256(data).hexdigest()
    # Probe digest includes Godot Variant serialization; this SHA pins raw packed bytes.
    alpha=[v[3] for v in struct.iter_unpack('<ffff',data)]
    rows.append({'lod':lod['path'],'array_file':array['file'],'sha256':digest,'vertices':array['count'],'masked':sum(v>.001 for v in alpha),'anchored':sum(v<=.001 for v in alpha)})
 assert len(rows)==3
 census[branch]={'rows':rows,'masked':sum(v['masked'] for v in rows),'anchored':sum(v['anchored'] for v in rows)}
changes=diff(r['baseline'],r['candidate']);allowed={'/wall_elapsed_ms','/sequence_controls/0/branch','/controls/0/branch'}
for i in range(4):allowed.update({f'/shots/{i}/sha256',f'/shots/{i}/hair_branch',f'/shots/{i}/secondary/anchored_vertices/hair',f'/shots/{i}/secondary/masked_vertices/hair'})
for i in range(4):
 for field in ['min','max','head_min','head_max']:
  for axis in range(2):allowed.add(f'/shots/{i}/bounds/{field}/{axis}')
 for field in ['vertices','head_vertices']:allowed.add(f'/shots/{i}/bounds/{field}')
for k in ['source_sha256','source_after_sha256']:
 for lod in ['', '-mid','-far']:allowed.add(f'/{k}/res://assets/heroes/rama-hero{lod}.glb')
unexpected=[d for d in changes if d['path'] not in allowed and d['path'] != '/audio_cleanup/wait_usec' and not d['path'].startswith('/audio_cleanup/samples')]
checks={'both_complete':all(x['complete']is True and len(x['shots'])==4 for x in r.values()),'only_declared_report_differences':not unexpected,'all164_final_bones_exact':all(x['rendered_pose_globals']==y['rendered_pose_globals'] and len(x['rendered_pose_globals'])==164 for x,y in zip(r['baseline']['shots'],r['candidate']['shots']))}
checks['bounded_real_mixer_cleanup']=all(x['audio_cleanup']['observed_mixer_ticks']==2 and x['audio_cleanup']['wait_usec']<=250000 for x in r.values())
if mode=='preflight':
 keys=['camera','secondary','motion','player_transform']
else:
 keys=['camera','light','secondary','face','motion','lod','physics_frame','render_frame','tree_paused']
 checks['sources_unchanged']=all(x['source_unchanged']is True for x in r.values())
def controls(shot):
 result={k:copy.deepcopy(shot[k]) for k in keys}
 for category in ['anchored_vertices','masked_vertices']:result['secondary'][category].pop('hair')
 return result
checks['all_recorded_controls_except_import_proven_hair_census_exact']=all(controls(x)==controls(y) for x,y in zip(r['baseline']['shots'],r['candidate']['shots']))
checks['hair_census_matches_imported_alpha_each_shot']=all(s['secondary']['anchored_vertices']['hair']==census[b]['anchored'] and s['secondary']['masked_vertices']['hair']==census[b]['masked'] for b,report in r.items() for s in report['shots'])
checks['all_changed_head_bounds_stay_inside_margin']=all(s['bounds']['passed'] is True and s['bounds']['behind']==0 and s['bounds']['margin_pixels']==24 for report in r.values() for s in report['shots'])
near_delta=census['candidate']['rows'][0]['vertices']-census['baseline']['rows'][0]['vertices']
checks['head_vertex_delta_matches_imported_hair_delta']=all(y['bounds']['head_vertices']-x['bounds']['head_vertices']==near_delta for x,y in zip(r['baseline']['shots'],r['candidate']['shots']))
out={'mode':mode,'passed':all(checks.values()),'checks':checks,'imported_hair_census':census,'differences':changes,'unexpected_differences':unexpected};(base/(mode+'-comparison-r1.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':out['passed'],'checks':checks,'difference_count':len(changes),'unexpected_paths':[x['path']for x in unexpected]}));raise SystemExit(0 if out['passed']else 1)
