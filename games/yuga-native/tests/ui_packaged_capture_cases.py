#!/usr/bin/env python3
"""Validate exact-package native, persistence and dynamic clock receipts."""
import argparse, hashlib, json, pathlib, struct
P=pathlib.Path
p=argparse.ArgumentParser();p.add_argument('--first',type=P,required=True);p.add_argument('--relaunch',type=P,required=True);p.add_argument('--staged',type=P,required=True);p.add_argument('--report',type=P,required=True);a=p.parse_args()
def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
checks=[]
def check(name,value,details=None):checks.append({'name':name,'passed':bool(value),'details':details or {}})
runs=[read(folder/'run.json') for folder in [a.first,a.relaunch,a.staged]]
def shot(folder,name):return read(folder/(name+'.json'))
for folder,run in zip([a.first,a.relaunch,a.staged],runs):
 check(folder.name+' completed native Quit0',run.get('complete') and run.get('verified_exit_code')==0 and run.get('cleanup_exit')==0)
 check(folder.name+' exact package/source/instrumentation stayed unchanged',all(run.get(key) is True for key in ['package_unchanged','source_unchanged','instrumentation_unchanged','archive_unchanged','export_manifest_unchanged']))
 shots=run['shots']+run['automatic_shots']
 check(folder.name+' all original PNG hashes and actual dimensions',all(sha(folder/s['file'])==s['sha256'] and struct.unpack('>II',(folder/s['file']).read_bytes()[16:24])==(960,540) for s in shots),{'manuals':len(run['shots']),'automatic':len(run['automatic_shots'])})
 check(folder.name+' one persistent layer/loader on manual frames',all(s['loader_count']==1 and s['transition_layer_count']==1 for s in run['shots']))
 check(folder.name+' clean engine diagnostics',not any(t in (folder/'godot.log').read_text() for t in ['ERROR:','WARNING:','ObjectDB instances leaked']))
 trace=read(folder/'transition-events.json')['events'];phases=[e for e in trace if e['kind']=='phase'];done=[e for e in trace if e['kind']=='completed']
 sig=[(e['phase'],e['message'],e['resource_progress'],e['attempt']) for e in phases]
 check(folder.name+' exactly once completion/dedup and one runtime owner',len({e['instance_id'] for e in trace})==1 and len(done)==len({e['attempt'] for e in done}) and all(x!=y for x,y in zip(sig,sig[1:])))
 check(folder.name+' construction has no invented aggregate progress',all(e['resource_progress']==-1 for e in phases if e['phase']=='constructing'))
check('All three processes execute identical package/PCK/archive identity',all(r['package_sha256']==runs[0]['package_sha256'] and r['package_archive']==runs[0]['package_archive'] for r in runs))
check('Main and relaunch contain only native actions',all(not r['authority_staging']['enabled'] and not r['authority_staging']['stages'] for r in runs[:2]))
check('Shared isolated save bytes persist across native Quit and relaunch',bool(runs[0]['user_state']['after']) and runs[0]['user_state']['after']==runs[1]['user_state']['before'] and runs[0]['user_state']['path']==runs[1]['user_state']['path'])
def saved_values(s):
 prefs=s['preferences'];return prefs['controls']['sensitivity']==2.5 and prefs['controls']['invert_y'] is True and prefs['controls']['bindings']['pulse']==74 and prefs['audio']['volume']==0 and prefs['video']['shadows'] is False
for folder,name in [(a.first,'P06-returned-title-settings'),(a.relaunch,'R01-relaunched-settings')]:
 s=shot(folder,name);check(name+' live and saved settings agree',saved_values(s) and s['state']['sensitivity']==2.5 and s['state']['volume']==0 and s['state']['invert_y'] and not s['state']['shadows'] and s['audio_state']['action_audio']['volume']==0)
for folder,name in [(a.first,'P03-native-guide-preferences-saved'),(a.first,'P04-world-guide-loaded-preferences'),(a.relaunch,'R03-relaunched-guide-preferences')]:
 s=shot(folder,name);check(name+' J and both receiver options persist',s['guide']['key_text']=='J  /  ABILITY' and s['guide']['reduced_effects'] and s['guide']['reduced_motion'] and s['effect_options']['reduced_effects'] and s['effect_options']['reduced_motion'] and saved_values(s))
a0=shot(a.first,'01-package-title-idle-a');b0=shot(a.first,'02-package-title-idle-b')
check('Inactive title presentation advances as negative control',not a0['state']['started'] and not b0['state']['player_active'] and not b0['presentation']['suspended'] and b0['presentation']['motion']['locomotion_age']>a0['presentation']['motion']['locomotion_age'])
x=shot(a.first,'09-package-overview-unreleased-a');y=shot(a.first,'10-package-overview-unreleased-b');z=shot(a.first,'11-package-overview-resumed-release')
check('Real accepted unreleased cast held across advancing native frames',x['kit']['accepted_casts']==1 and x['kit']['release_count']==0 and x['presentation']['motion']['action']=='piercing_dawn' and x['presentation']['motion']['stage']=='windup' and y['physics_frame']-x['physics_frame']>=45 and y['frame']>x['frame'],{'physics_ticks':y['physics_frame']-x['physics_frame'],'render_frames':y['frame']-x['frame']})
check('Overview owns suspension while world is unpaused',all(s['state']['overview'] and not s['state']['player_active'] and s['presentation']['suspended'] and s['kit']['suspended'] and not s['paused'] for s in [x,y]))
check('Overview HUD reports unavailable ability slots',all(s['hero_hud']['notice']=='Practice paused' and all(slot.split('·',1)[1].splitlines()[0].strip()=='—' for slot in s['hero_hud']['slots']) for s in [x,y]))
check('Kit army motion secondary face clocks hold exactly',x['kit']==y['kit'] and x['army']['elapsed']==y['army']['elapsed'] and all(x['presentation']['motion'][k]==y['presentation']['motion'][k] for k in ['action_elapsed','phase','locomotion_age','release_count']) and x['presentation']['secondary']['elapsed']==y['presentation']['secondary']['elapsed'] and x['presentation']['face']['elapsed']==y['presentation']['face']['elapsed'])
check('Actual F1 resume releases once and clocks advance',not z['state']['overview'] and z['state']['player_active'] and not z['presentation']['suspended'] and not z['kit']['suspended'] and z['kit']['release_count']==z['presentation']['motion']['release_count']==1 and z['kit']['elapsed']>y['kit']['elapsed'] and z['army']['elapsed']>y['army']['elapsed'])
check('Overview atlas marker follows actual player x/z',all(all(abs(s['presentation']['atlas_position'][i]-s['presentation']['player_position'][i])<.00001 for i in [0,2]) for s in [x,y]))
check('Training selection survives native film round trip',shot(a.first,'07-package-film-return-selection')['launch']['selected_mode']=='train' and shot(a.first,'07-package-film-return-selection')['focus_text']=='Begin bow training  →')
night=shot(a.first,'P05-world-muted-sound-and-return');check('Native night settled with zero live audio receiver volume',night['state']['night'] and night['state']['phase']==1 and night['audio_state']['action_audio']['volume']==0)
stages=runs[2]['authority_staging']['stages'];check('Supplement is explicitly staged through actual authority',len(stages)==9 and all(s['passed'] for s in stages) and all(s['fixture_sha256'] for s in stages))
for winner,n in [('sun',6),('moon',7),('draw',8)]:
 s=shot(a.staged,f'S0{n}-STAGED-{winner}-outcome');check(winner+' actual terminal summary is labeled staged',s['army']['winner']==winner and s['world']['outcome_visible'] and s['paused'] and s['authority_staging']['simulation_hold'])
end=shot(a.staged,'S09-native-restart-after-STAGED-outcomes');check('Native Restart and fixture release restore usable world',end['army']['winner']=='' and not end['paused'] and end['state']['player_active'] and not end['authority_staging']['simulation_hold'])
result={'passed':all(c['passed'] for c in checks),'passed_count':sum(c['passed'] for c in checks),'count':len(checks),'checks':checks,'runs_sha256':{str(folder):sha(folder/'run.json') for folder in [a.first,a.relaunch,a.staged]},'scope':'Actual extracted Linux package with external observer and native XTest; third process has separately labeled actual-rule staging. Warm software rendering; no hardware/FPS or cold-start claim.'}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({key:result[key] for key in ['passed','passed_count','count']}));raise SystemExit(0 if result['passed'] else 1)
