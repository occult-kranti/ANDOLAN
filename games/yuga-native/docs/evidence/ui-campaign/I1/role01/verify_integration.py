from pathlib import Path
import hashlib,json
ROOT=Path('/workspace/ANDOLAN/games/yuga-native');CAP=Path('/tmp/yuga-u5-integrated-window-r1');FROZEN=Path('/tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native');OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=json.loads((CAP/'run.json').read_text());freeze=json.loads((FROZEN/'ui-source-freeze.json').read_text());prom=json.loads((ROOT/'docs/evidence/visual-rounds/round3/integration/promotion.json').read_text());checks=[];bindings={}
def ck(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
ck('exact provided final combined source freeze',sha(FROZEN/'ui-source-freeze.json')=='720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb')
raw=['assets/heroes/rama-hero.glb','assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb','assets/materials/rama-finish/woven-roughness.png']
for name in raw:bindings[name]={'actual':sha(FROZEN/name),'freeze':freeze['source_sha256'][name],'capture':run['source_sha256'][name],'accepted':prom['source_files'][name]['sha256']}
ck('three accepted R7 GLBs and woven raw bytes agree across actual freeze capture and promotion',all(len(set(v.values()))==1 for v in bindings.values()))
cache={}
for name,r in prom['cache_files'].items():
 expected=freeze['existing_import_sha256'].get(name,freeze['source_sha256'].get(name));cache[name]={'actual':sha(FROZEN/name),'freeze':expected,'accepted':r['sha256']}
ck('all12 accepted import descriptors payloads and MD5 records exact in frozen runtime',len(cache)==12 and all(len(set(v.values()))==1 for v in cache.values()))
ck('retained production motion is unchanged and rejected prototypes excluded',sha(FROZEN/'scripts/rama_motion.gd')==run['source_sha256']['scripts/rama_motion.gd']=='4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1' and not any('release-r3a' in x or 'role-07' in x for x in run['source_sha256']))
def shot(name):return json.loads((CAP/(name+'.json')).read_text())
ends=[shot(n) for n in ['01-final-title','28-world-return-title','37-training-return-title','39-duel-return-title']]
ck('all four captured title endpoints own one idle loader and no stale transition layer content',all(d['loader_count']==1 and d['transition_layer_count']==1 and not d['transition_owner_present'] and not d['transition']['visible'] and not d['transition']['busy'] and d['state']['hero_ready'] and not d['state']['player_active'] and not d['state']['started'] and d['panels']['main_panel'] for d in ends))
live=[shot(n) for n in ['10-world-live-hud','25-native-siege-drill','30-training-live','36-training-reset']]
ck('combined hero live endpoints show ready active player HUD and no residual menu or loader',all(d['state']['hero_ready'] and d['state']['player_active'] and d['hero_hud']['visible'] and not d['paused'] and d['mouse_mode']==2 and not d['transition_owner_present'] and not any(d['panels'].values()) for d in live))
auto=[json.loads(f.read_text()) for f in CAP.glob('auto-*.json')]
ck('all15 recorded transition states isolate input above disabled source scene',len(auto)==15 and all(d['transition_owner_present'] and d['transition_layer_count']==1 and not d['scene_can_process'] and d['scene_process_mode']==4 and d['focus'].startswith('/root/YugaSceneTransitionLayer/') and all(c['path'].startswith('/root/YugaSceneTransitionLayer/') for c in d['controls'] if c['interactive']) for d in auto))
ck('no production-source mutation during complete native navigation capture',run['complete'] and run['source_unchanged'] and run['verified_exit_code']==0)
result={'task':'I1-01','passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'raw_bindings':bindings,'import_bindings':cache,'promotion_receipt_sha256':sha(ROOT/'docs/evidence/visual-rounds/round3/integration/promotion.json'),'run_sha256':sha(CAP/'run.json'),'freeze_sha256':sha(FROZEN/'ui-source-freeze.json'),'script_sha256':sha(Path(__file__)),'scope':'Eight independent combined-source/pixel-route metadata checks, not eight new gameplay executions. Source and imports are read only. Visual geometry/framing is judged separately from opened originals. Fifteen transition metadata records are checked; only auto-constructing-2 is visually opened in this role. Current retained motion has no R4 acceptance.'}
(OUT/'integration-r2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'count':len(checks),'failed':[c for c in checks if not c['passed']]}))
