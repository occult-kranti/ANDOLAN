#!/usr/bin/env python3
"""Compare separately executed headless Godot and original TS fixture queries.

A pass accepts the bounded experiment and reports solver divergence. It does not
establish deterministic solver equivalence, a controller or two online clients.
"""
import argparse, hashlib, json, math
from pathlib import Path


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text())
def distance(a,b): return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

def compare(fixture, reference, godot):
    checks=[]; divergences=[]; max_position=0.; max_sweep=0.; max_sweep_m=0.; max_aim=0.
    def check(ok,id,detail=None): checks.append(dict(id=id,passed=bool(ok),detail=detail))
    check(reference['fixture_sha256']==godot['fixture_sha256'],'identical fixture digest')
    check(godot['passed'] and godot['failed']==0,'Godot owner assertions')
    check(len(reference['queries'])==len(godot['queries'])==len(fixture['queries']),'query count')
    tolerance=fixture['query_contract']
    def rays(r,g,id):
        nonlocal max_position,max_aim
        check(r['hit']==g['hit'],id+' hit state')
        if r['hit'] and g['hit']:
            check(r['collider']==g['collider'],id+' collider identity')
            d=distance(r['position'],g['position']);max_position=max(max_position,d)
            check(d<=tolerance['tolerance_position_m'],id+' position metres',d)
            check(distance(r['normal'],g['normal'])<=tolerance['tolerance_normal'],id+' normal')
        if 'direction' in r:
            d=distance(r['direction'],g['direction']);max_aim=max(max_aim,d)
            check(d<=1e-6,id+' shared yaw/pitch direction',d)
    for spec,r,g in zip(fixture['queries'],reference['queries'],godot['queries']):
        check(spec['id']==r['id']==g['id'] and spec['actor']==r['actor']==g['actor'] and spec['kind']==r['kind']==g['kind'],spec['id']+' identical query')
        a,b=r['result'],g['result'];id=spec['id']
        if spec['kind'] in ('ray','aim'):rays(a,b,id)
        elif spec['kind']=='overlap':check(a['colliders']==b['colliders'],id+' overlap set')
        else:
            delta=abs(a['fraction']-b['fraction']);metres=delta*distance(spec['motion'],[0,0,0]);max_sweep=max(max_sweep,delta);max_sweep_m=max(max_sweep_m,metres)
            # Godot's conservative bracket is an observed solver result, not exact SAT.
            check(b['fraction']-1e-5<=a['fraction']<=b['unsafe_fraction']+1e-5,id+' exact SAT inside Godot safe/unsafe interval',dict(reference=a['fraction'],safe=b['fraction'],unsafe=b['unsafe_fraction']))
            if delta>tolerance['tolerance_fraction'] or metres>tolerance['tolerance_position_m']:
                divergences.append(dict(query=id,kind='conservative_sweep_fraction',exact_ts=a['fraction'],godot_safe=b['fraction'],godot_unsafe=b['unsafe_fraction'],fraction_difference=delta,position_difference_m=metres))
    check(len(reference['stream'])==len(godot['stream'])==fixture['paired_stream']['ticks']*2,'paired stream length')
    stream_max=0.;support_mismatches=0
    for r,g in zip(reference['stream'],godot['stream']):
        check(r['tick']==g['tick'] and r['actor']==g['actor'],f"stream {r['tick']} {r['actor']} identity")
        d=distance(r['feet'],g['feet']);stream_max=max(stream_max,d)
        check(d<=tolerance['tolerance_position_m'],f"stream {r['tick']} {r['actor']} feet",d)
        support_mismatches+=r['support'].get('collider')!=g['support'].get('collider')
    check(support_mismatches==0,'all paired stream support identities agree',support_mismatches)
    # Explicit counterexample to any one-height-per-xz map adapter.
    q={q['id']:q['result'] for q in godot['queries']}
    stack=[q[i]['position'][1] for i in ('stack-road-support','stack-lower-support','stack-upper-support')]
    check(len(set(round(x,3) for x in stack))==3,'flattened height field cannot represent all observed same-xz supports',stack)
    return dict(format=1,passed=all(c['passed'] for c in checks),checks=checks,failed=sum(not c['passed'] for c in checks),summary=dict(queries=len(fixture['queries']),paired_actor_samples=len(godot['stream']),query_count_per_implementation=len(fixture['queries'])+len(godot['stream'])*2,max_ray_position_difference_m=max_position,max_paired_feet_difference_m=stream_max,max_sweep_fraction_difference=max_sweep,max_sweep_position_difference_m=max_sweep_m,max_aim_direction_difference=max_aim,support_mismatches=support_mismatches),divergences=divergences,decision='Use a single headless Godot physics authority for the next native online prototype; do not claim TS/Godot solver parity or migrate browser protocol 2 in place.',scope='Bounded offline queries with two logical input streams, not networked clients, character-controller parity, full map collision or production authority adoption.',profiles=dict(typescript=reference['profile'],godot=godot['profile']))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--typescript',required=True);p.add_argument('--godot',required=True);p.add_argument('--report',required=True);a=p.parse_args()
    fixture,reference,godot=map(load,(a.fixture,a.typescript,a.godot));expected=sha(a.fixture)
    if reference['fixture_sha256']!=expected or godot['fixture_sha256']!=expected:raise SystemExit('Reports do not match the selected fixture')
    report=compare(fixture,reference,godot);report['inputs']={name:dict(path=str(Path(path).resolve()),sha256=sha(path)) for name,path in [('fixture',a.fixture),('typescript',a.typescript),('godot',a.godot)]};Path(a.report).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','failed','summary','divergences')}));raise SystemExit(0 if report['passed'] else 1)
