#!/usr/bin/env python3
"""Independent screenplay/chronology and resource QA for the scripted duel.
No gameplay simulation is inferred from authored visual receipts.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import wave

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT/'games/yuga-native'
DEFAULT = NATIVE/'assets/cinematics/confluence-duel.json'
CLIPS = {'ready','draw','release','guard','recoil','evade','cast_windup','cast_release','defeat'}
STYLES = {'cast_symbol','counter_shield','solar_arrow','impact_ring','danger_corridor','dash_trail','spectral_fan'}
EVENT_SECTIONS = ('acts','actions','cues','visual_receipts','cameras','captions','audio_cues','counter_windows','contact_windows')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_load(text):
    def pairs(values):
        result={}
        for key,value in values:
            if key in result: raise ValueError('duplicate JSON key: '+key)
            result[key]=value
        return result
    def constant(value): raise ValueError('nonfinite JSON constant: '+value)
    return json.loads(text,object_pairs_hook=pairs,parse_constant=constant)


def finite(value):
    if isinstance(value,(int,float)) and not isinstance(value,bool): return math.isfinite(value)
    if isinstance(value,dict): return all(finite(v) for v in value.values())
    if isinstance(value,list): return all(finite(v) for v in value)
    return True


def interval(item):
    start=item.get('t_seconds',-1)
    end=item.get('end_seconds',start+item.get('duration_seconds',0))
    return start,end


def point_at(data,actor_id,t):
    track=next(x for x in data['motion_tracks'] if x['actor_id']==actor_id)
    keys=track['keys']
    if t<=keys[0]['t_seconds']: return keys[0]['position'],keys[0]['yaw_degrees']
    for a,b in zip(keys,keys[1:]):
        if t<=b['t_seconds']:
            f=(t-a['t_seconds'])/(b['t_seconds']-a['t_seconds'])
            p=[x+(y-x)*f for x,y in zip(a['position'],b['position'])]
            yaw=a['yaw_degrees']+((b['yaw_degrees']-a['yaw_degrees']+180)%360-180)*f
            return p,yaw
    return keys[-1]['position'],keys[-1]['yaw_degrees']


def line_distance_xz(point,a,b):
    dx,dz=b[0]-a[0],b[2]-a[2]
    f=max(0,min(1,((point[0]-a[0])*dx+(point[2]-a[2])*dz)/(dx*dx+dz*dz)))
    return math.hypot(point[0]-a[0]-f*dx,point[2]-a[2]-f*dz)


def resource_path(value):
    if not isinstance(value,str) or not value.startswith('res://'):
        raise ValueError('resource path must use res://')
    path=(NATIVE/value[6:]).resolve()
    if not path.is_relative_to(NATIVE.resolve()): raise ValueError('resource path escapes native project')
    return path


def validate(data,check_assets=True):
    errors=[]
    def need(ok,text):
        if not ok: errors.append(text)
    need(data.get('schema_version')==1,'unsupported schema')
    need(data.get('duration_seconds')==24,'film duration must be exactly 24 seconds')
    if not finite(data): return errors+['nonfinite number']
    duration=data.get('duration_seconds',0)
    actors=data.get('actors',[])
    ids=[x.get('id') for x in actors]
    need(len(ids)==2 and len(set(ids))==2 and set(ids)=={'rama','ravana'},'missing or duplicate actor')
    actor_ids=set(ids)
    resources=[]
    for actor in actors:
        for field in ('model_path','animation_library_path'):
            value=actor.get(field)
            resources.append(value)
            try:
                path=resource_path(value)
                need(not check_assets or path.is_file(),'missing resource: '+str(value))
                if field=='model_path' and path.is_file(): need(path.read_bytes()[:4]==b'glTF','invalid GLB resource')
                if field=='animation_library_path' and path.is_file():
                    text=path.read_text()
                    for clip in CLIPS: need('"'+clip+'"' in text,'animation resource missing clip '+clip)
            except (ValueError,TypeError): need(False,'invalid resource path')
        need(actor.get('animation_namespace')=='film','unexpected animation namespace')
    need(len(set(resources))==len(resources),'duplicate actor resource')
    for value in (data.get('environment_path'),data.get('audio_mix_path')):
        try:
            path=resource_path(value)
            need(not check_assets or path.is_file(),'missing resource: '+str(value))
        except (ValueError,TypeError): need(False,'invalid resource path')
    all_ids=[]
    for section in EVENT_SECTIONS:
        entries=data.get(section,[])
        need(bool(entries),'missing '+section)
        for item in entries:
            ident=item.get('id')
            all_ids.append(ident)
            need(isinstance(ident,str) and bool(ident),'invalid event id')
            if section!='visual_receipts':
                start,end=interval(item)
                need(0<=start<end<=duration+1e-8,'invalid time interval '+str(ident))
            else: need(0<=item.get('t_seconds',-1)<=duration,'invalid receipt time')
            for key in ('actor_id','target_id','aim_target_id'):
                if key in item: need(item[key] in actor_ids,'missing actor reference '+str(ident))
            for key in ('position','from_position','to_position','locked_target_position','look_at'):
                if key in item:
                    p=item[key]
                    need(isinstance(p,list) and len(p)==3 and all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in p),'invalid coordinate '+str(ident))
                    if isinstance(p,list) and len(p)==3:
                        need(abs(p[0])<=200 and -2<=p[1]<=150 and abs(p[2])<=200,'out of bounds coordinate '+str(ident))
    need(len(all_ids)==len(set(all_ids)),'duplicate event id')
    tracks=data.get('motion_tracks',[])
    need(sorted(t.get('actor_id','') for t in tracks)==sorted(actor_ids),'missing or duplicate motion track')
    for track in tracks:
        keys=track.get('keys',[])
        need(len(keys)>=2 and keys[0].get('t_seconds')==0 and keys[-1].get('t_seconds')==24,'motion track endpoints incomplete')
        for a,b in zip(keys,keys[1:]): need(a.get('t_seconds',0)<b.get('t_seconds',0),'nonincreasing motion times')
        for key in keys:
            p=key.get('position',[])
            need(len(p)==3 and abs(p[0])<=67.35 and -0.02<=p[1]<=20 and abs(p[2])<=81.35,'actor motion outside world bounds')
    if errors: return errors
    def coverage(entries,label):
        entries=sorted(entries,key=lambda x:x['t_seconds'])
        need(abs(interval(entries[0])[0])<1e-8 and abs(interval(entries[-1])[1]-24)<1e-8,label+' endpoints not covered')
        for a,b in zip(entries,entries[1:]): need(abs(interval(a)[1]-interval(b)[0])<1e-8,label+' gap or overlap')
    coverage(data['acts'],'acts')
    coverage(data['cameras'],'camera')
    for actor in actors:
        actions=[x for x in data['actions'] if x['actor_id']==actor['id']]
        contacts=[x for x in data['contact_windows'] if x['actor_id']==actor['id']]
        need(bool(actions) and bool(contacts),'actor missing action/contact coverage')
        if actions: coverage(actions,actor['id']+' actions')
        if contacts: coverage(contacts,actor['id']+' contacts')
        p,y=point_at(data,actor['id'],0)
        need(p==actor['position'] and abs(((y-actor['yaw_degrees']+180)%360)-180)<1e-6,'actor initial transform mismatch')
    for action in data['actions']:
        need(action.get('clip_id') in CLIPS,'unknown action clip')
        need(action.get('phase_mapping')=='action_normalized_to_clip_length','unknown phase mapping')
        need(0<=action.get('blend_in_seconds',-1)+action.get('blend_out_seconds',-1)<=action['duration_seconds'],'invalid action blend interval')
    for contact in data['contact_windows']:
        mode=contact.get('mode')
        need(mode in ('planted','moving','pivot'),'unknown contact mode')
        a,b=interval(contact)
        p0,y0=point_at(data,contact['actor_id'],a)
        for t in (a,(a+b)/2,b):
            p,y=point_at(data,contact['actor_id'],t)
            if mode in ('planted','pivot'): need(math.dist(p,p0)<1e-6,'stationary contact has root displacement')
            if mode=='planted': need(abs(((y-y0+180)%360)-180)<1e-6,'planted contact has root yaw change')
    cues={x['id']:x for x in data['cues']}
    actions={x['id']:x for x in data['actions']}
    receipts={x['id']:x for x in data['visual_receipts']}
    for cue in cues.values():
        need(cue.get('style') in STYLES,'unknown effect style')
        need(cue.get('type') in ('telegraph','guard','projectile','impact','trail'),'unknown effect type')
        if 'radius' in cue: need(0<cue['radius']<=10,'invalid effect radius')
        if cue['type']=='projectile':
            tele=cues.get(cue.get('telegraph_event_id'),{})
            need(tele.get('type')=='telegraph' and tele.get('warns_event_id')==cue['id'],'missing reciprocal telegraph link')
            if tele:
                need(tele.get('actor_id')==cue['actor_id'] and tele.get('target_id')==cue.get('target_id'),'telegraph actors mismatch')
                need(tele['t_seconds']+0.2<=cue['t_seconds'],'telegraph reaction lead too short')
                need(abs(interval(tele)[1]-cue['t_seconds'])<1e-8,'telegraph must end at release')
            need(abs(cue.get('impact_t_seconds',-1)-interval(cue)[1])<1e-8,'projectile impact time mismatch')
            need(cue.get('receipt_id') in receipts,'missing projectile receipt')
        if cue['type']=='impact':
            receipt=receipts.get(cue.get('receipt_id'),{})
            need(bool(receipt) and abs(cue['t_seconds']-receipt.get('t_seconds',-1))<1e-8,'impact and receipt chronology mismatch')
    health={a['id']:a['visual_health'] for a in actors}
    last=-1
    for receipt in data['visual_receipts']:
        t=receipt['t_seconds']
        need(t>=last,'receipts out of order'); last=t
        source=cues.get(receipt.get('source_event_id'),{})
        need(source.get('type')=='projectile' and source.get('receipt_id')==receipt['id'],'missing receipt projectile')
        if source:
            need(source.get('actor_id')==receipt['actor_id'] and source.get('target_id')==receipt['target_id'],'receipt actor mismatch')
            need(abs(interval(source)[1]-t)<1e-8,'receipt before or after projectile arrival')
        target=receipt['target_id']
        need(receipt['health_before']==health[target] and receipt['health_after']==receipt['health_before']-receipt['amount'] and 0<=receipt['health_after']<=100,'visual health arithmetic mismatch')
        health[target]=receipt['health_after']
        outcome=receipt.get('outcome')
        need(outcome in ('blocked','evaded','hit'),'unknown receipt outcome')
        if outcome in ('blocked','evaded'): need(receipt['amount']==0,'avoided receipt causes damage')
        if outcome=='hit': need(receipt['amount']>0,'hit receipt lacks damage')
        counter=actions.get(receipt.get('counter_event_id'),{})
        if outcome=='blocked': need(counter.get('clip_id')=='guard' and interval(counter)[0]<=t<interval(counter)[1],'block outside actual guard action')
        if outcome=='evaded':
            need(counter.get('clip_id')=='evade' and interval(counter)[1]<=source['t_seconds'],'evade ends after wave release')
            point,_=point_at(data,target,t)
            need(line_distance_xz(point,source['from_position'],source['to_position'])>source.get('radius',0)+.65,'evaded actor remains inside danger corridor')
    windows=data['counter_windows']
    need(len(windows)==3,'three threat/counter windows required')
    for window in windows:
        threat=cues.get(window.get('threat_event_id'),{})
        receipt=receipts.get(window.get('receipt_id'),{})
        action=actions.get(window.get('action_id'),{})
        need(threat.get('type')=='projectile' and bool(receipt) and bool(action),'missing counter window reference')
        if not threat or not receipt or not action: continue
        need(window['actor_id']==threat.get('target_id')==action['actor_id'],'counter window actor mismatch')
        a,b=interval(window)
        need(a<=receipt['t_seconds']<=b,'receipt outside declared counter window')
        if window['kind']=='guard_active': need(action['clip_id']=='guard' and a>=interval(action)[0] and b<=interval(action)[1],'guard window exceeds action')
        elif window['kind']=='outside_locked_corridor': need(action['clip_id']=='evade' and interval(action)[1]<=threat['t_seconds'],'evade window has no timely evade')
        elif window['kind']=='guard_inactive':
            need(all(not (x['actor_id']==window['actor_id'] and x['clip_id']=='guard' and max(interval(x)[0],a)<min(interval(x)[1],b)) for x in data['actions']),'unguarded window contains guard')
        else: need(False,'unknown counter window kind')
    for camera in data['cameras']:
        need(20<=camera['fov']<=90 and 0<=camera['blend_seconds']<=camera['duration_seconds'],'invalid camera optics or blend')
        need(math.dist(camera['position'],camera['look_at'])>.1,'camera looks at own origin')
    return errors


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=DEFAULT)
    parser.add_argument('--report',type=Path)
    parser.add_argument('--schema-only',action='store_true',help='Do not certify resource presence; useful before asset generation.')
    args=parser.parse_args()
    data=strict_load(args.manifest.read_text())
    errors=validate(data,not args.schema_only)
    checks=[{'name':'independent film chronology and contract','passed':not errors,'errors':errors}]
    mutations=[
        ('missing actor',lambda m:m['actors'].pop(),'missing or duplicate actor'),
        ('invalid negative time',lambda m:m['cues'][0].__setitem__('t_seconds',-1),'invalid time'),
        ('nonfinite coordinate',lambda m:m['motion_tracks'][0]['keys'][0]['position'].__setitem__(0,float('nan')),'nonfinite'),
        ('duplicate event',lambda m:m['cues'].append(copy.deepcopy(m['cues'][0])),'duplicate event'),
        ('duplicate resource',lambda m:m['actors'][1].__setitem__('model_path',m['actors'][0]['model_path']),'duplicate actor resource'),
        ('unknown actor reference',lambda m:m['cues'][0].__setitem__('actor_id','missing'),'missing actor reference'),
        ('unknown clip',lambda m:m['actions'][0].__setitem__('clip_id','missing'),'unknown action clip'),
        ('receipt precedes arrival',lambda m:m['visual_receipts'][0].__setitem__('t_seconds',4),'receipt before or after'),
        ('missing telegraph',lambda m:m['cues'][2].__setitem__('telegraph_event_id','missing'),'missing reciprocal telegraph'),
        ('shifted impact time',lambda m:m['cues'][2].__setitem__('impact_t_seconds',4.2),'impact time mismatch'),
        ('duplicate motion time',lambda m:m['motion_tracks'][0]['keys'][1].__setitem__('t_seconds',0),'nonincreasing'),
        ('planted moving actor',lambda m:m['contact_windows'][1].__setitem__('mode','planted'),'stationary contact'),
        ('late guard window',lambda m:m['counter_windows'][0].__setitem__('t_seconds',5),'receipt outside'),
        ('wrong visual health',lambda m:m['visual_receipts'][2].__setitem__('health_after',90),'health arithmetic'),
        ('unknown resource path',lambda m:m['actors'][0].__setitem__('model_path','res://../../outside.glb'),'invalid resource path'),
    ]
    for label,change,wanted in mutations:
        candidate=copy.deepcopy(data); change(candidate)
        found=validate(candidate,False)
        checks.append({'name':'reject '+label,'passed':any(wanted in e for e in found),'expected_error':wanted,'errors':found})
    for label,text in [('duplicate JSON key','{"id":1,"id":2}'),('JSON NaN','{"x":NaN}'),('JSON infinity','{"x":Infinity}')]:
        rejected=False
        try: strict_load(text)
        except ValueError: rejected=True
        checks.append({'name':'reject '+label,'passed':rejected})
    audio={}
    resources=[]
    if not args.schema_only:
        for actor in data['actors']:
            for field in ('model_path','animation_library_path'):
                p=resource_path(actor[field])
                if p.is_file(): resources.append({'path':actor[field],'sha256':sha(p),'bytes':p.stat().st_size})
        p=resource_path(data['audio_mix_path'])
        if p.is_file():
            with wave.open(str(p),'rb') as wav:
                audio={'channels':wav.getnchannels(),'sample_rate':wav.getframerate(),'sample_width':wav.getsampwidth(),'frames':wav.getnframes(),'duration_seconds':wav.getnframes()/wav.getframerate(),'sha256':sha(p)}
            checks.append({'name':'audio exactly matches film length','passed':audio['channels']==2 and audio['sample_rate']==48000 and audio['sample_width']==2 and audio['frames']==24*48000,'details':audio})
    metrics={'actors':len(data['actors']),'actions':len(data['actions']),'cues':len(data['cues']),'contact_windows':len(data['contact_windows']),'receipt_times':[r['t_seconds'] for r in data['visual_receipts']]}
    report={'passed':all(c['passed'] for c in checks),'scope':'Independent deterministic screenplay validation and malformed fixtures. Authored hits/health/counters are visual receipts, not gameplay damage. Native poses, runtime rejection, effects and UI are separate tests.', 'resources_verified':not args.schema_only,'manifest_sha256':sha(args.manifest),'test_sha256':sha(Path(__file__)),'metrics':metrics,'resources':resources,'audio':audio,'checks':checks}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__': raise SystemExit(main())
