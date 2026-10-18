#!/usr/bin/env python3
"""Assert native XTest evidence and observer-only transition state, not scripted UI labels."""
import argparse, hashlib, json, pathlib
P=pathlib.Path
p=argparse.ArgumentParser();p.add_argument('--capture',type=P,required=True);p.add_argument('--report',type=P,required=True);a=p.parse_args()
root=a.capture.resolve();run=json.loads((root/'run.json').read_text());events=json.loads((root/'transition-events.json').read_text())['events'];checks=[]
def check(name,value):checks.append({'name':name,'passed':bool(value)})
def shot(name):return json.loads((root/(name+'.json')).read_text())
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
check('Native plan completed on unchanged sources',run.get('complete') and run.get('source_unchanged'))
check('All eleven manual original frames retain hashes',len(run['shots'])==11 and all(sha(root/s['file'])==s['sha256'] for s in run['shots']))
check('All manual frames have native window focus',all(s['window_focused'] for s in run['shots']))
check('Actions include real duplicate-click and Escape burst',any(len(e.get('burst',[]))==3 for e in run['events']))
queued=shot('02-queued-duplicate-cancel');paused=shot('03-paused-cancel');threaded=shot('04-threaded-cancel');back=shot('10-error-back-focus');final=shot('11-final-reentry')
check('Queued cancel restores exact opener and live caller',queued['focus'].endswith('/OpenLocalSample') and queued['scene_can_process'] and not queued['transition_owner_present'])
check('Paused cancellation restores prior pause and explicit caller mode',paused['paused'] and paused['scene_process_mode']==3 and paused['scene_can_process'] and paused['focus'].endswith('/OpenLocalSample'))
phases=[e for e in events if e['kind']=='phase'];cancelled=[e for e in events if e['kind']=='cancelled'];completed=[e for e in events if e['kind']=='completed'];failed=[e for e in events if e['kind']=='failed']
first_cancel=next(i for i,e in enumerate(phases) if e['phase']=='cancelled')
check('Duplicate native activation creates one queued attempt',sum(e['phase']=='queued' for e in phases[:first_cancel])==1 and first_cancel==1)
cancel_phases=[i for i,e in enumerate(phases) if e['phase']=='cancelled']
check('Threaded cancellation follows a real loading phase',len(cancel_phases)>=3 and phases[cancel_phases[2]-1]['phase']=='loading' and threaded['state']['page_title']=='Sample A')
check('No cancelled early request completes later',all(e['attempt']>threaded['transition']['attempt'] for e in completed))
check('Each successful replacement completes exactly once',len(completed)==4 and len({e['attempt'] for e in completed})==4)
check('All return paths reuse the same persistent loader',len({e['instance_id'] for e in events})==1 and all(s['loader_count']==1 and s['transition_layer_count']==1 for s in run['shots']))
check('Missing scene and keyboard Retry each fail once',len(failed)==2 and len({e['attempt'] for e in failed})==2 and all(e['scene_process_mode']==4 and e['owner_present'] for e in failed))
check('Error Back restores its exact opener and owner lease',back['focus'].endswith('/OpenMissingSample') and back['scene_can_process'] and not back['transition_owner_present'])
check('Every cancellation emits one terminal callback',len(cancelled)==4 and len({e['attempt'] for e in cancelled})==4)
check('Final reentry is a usable unpaused caller',final['state']['page_title']=='Sample A' and final['scene_can_process'] and not final['paused'] and not final['transition']['visible'] and not final['transition_owner_present'])
signatures=[(e['phase'],e['message'],e['resource_progress'],e['attempt']) for e in phases]
check('Observed phase notifications contain no exact adjacent duplicates',all(a!=b for a,b in zip(signatures,signatures[1:])))
check('Construction never reports aggregate percentage',all(e['resource_progress']==-1 for e in phases if e['phase']=='constructing'))
check('Resource progress is unknown or an actual bounded loading value',all(e['resource_progress']==-1 or (e['phase']=='loading' and 0<=e['resource_progress']<=1) for e in phases))
check('Scheduling stays in the authorized tiny-fixture lane',run['scheduling']['cpu_affinity']==[2] and run['scheduling']['render_threads']==1 and run['scheduling']['OMP_NUM_THREADS']=='1' and run['scheduling']['OPENBLAS_NUM_THREADS']=='1')
seed=run['shader_cache_seed'];check('Shader cache is isolated and source seed unchanged',P(seed['copied_to']).is_relative_to(root) and run['shader_cache_seed_unchanged'])
check('Native engine reports no errors','ERROR:' not in (root/'godot.log').read_text())
result={'passed':all(c['passed'] for c in checks),'passed_count':sum(c['passed'] for c in checks),'count':len(checks),'checks':checks,'run_sha256':sha(root/'run.json'),'event_trace_sha256':sha(root/'transition-events.json'),'scope':'Actual isolated 2D XTest actions, observer-only phase trace and original PNG hashes. No 3D scene or hardware-performance claim.'}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'passed_count':result['passed_count'],'count':result['count']}));raise SystemExit(0 if result['passed'] else 1)
