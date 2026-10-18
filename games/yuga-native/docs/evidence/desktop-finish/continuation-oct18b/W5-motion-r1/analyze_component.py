#!/usr/bin/env python3
from pathlib import Path
import json,math,sys,hashlib

def angle(a,b):
    an=math.sqrt(sum(x*x for x in a));bn=math.sqrt(sum(x*x for x in b))
    return math.degrees(2*math.acos(min(1,max(0,abs(sum(x*y for x,y in zip(a,b))/(an*bn))))))
def length(v):return math.sqrt(sum(x*x for x in v))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def metrics(rows,hz):
    peak={'deg':0};air={'deg':0};near={'deg':0};ankle={'m':0};rootrel={'m':0};accel={'deg_s2':0};prior={}
    first=next((i for i,r in enumerate(rows) if i and r['grounded']),None)
    for i in range(1,len(rows)):
        a,b=rows[i-1:i+1]
        for bone in b['legs']:
            deg=angle(a['legs'][bone]['local'],b['legs'][bone]['local'])
            row={'deg':deg,'deg_s':deg*hz,'bone':bone,'tick':b['tick'],'grounded':b['grounded'],'locomotion':b['locomotion']}
            if deg>peak['deg']:peak=row
            if not a['grounded'] and not b['grounded'] and deg>air['deg']:air=row
            if first is not None and first-2<=i<=first+math.ceil(.12*hz) and deg>near['deg']:near=row
            if bone in prior:
                dv=abs(deg*hz-prior[bone])*hz
                if dv>accel['deg_s2']:accel={'deg_s2':dv,'bone':bone,'tick':b['tick']}
            prior[bone]=deg*hz
        for side in ['L','R']:
            d=length(sub(b['feet'][side]['relative_root'],a['feet'][side]['relative_root']))
            if d>rootrel['m']:rootrel={'m':d,'mps':d*hz,'side':side,'tick':b['tick'],'grounded':b['grounded']}
            if i>1: # root placement before an artificial drop is setup, not measured travel
                d=length(sub(b['feet'][side]['world'],a['feet'][side]['world']))
                if d>ankle['m']:ankle={'m':d,'mps':d*hz,'side':side,'tick':b['tick'],'grounded':b['grounded']}
    return {'first_grounded':first,'first_gaps_mm':{s:rows[first]['skin'][s]['minimum_m']*1000 for s in ['L','R']} if first else None,'peak_local_step':peak,'peak_airborne_step':air,'peak_contact_window_step':near,'peak_ankle_world_step':ankle,'peak_ankle_root_relative_step':rootrel,'peak_scalar_angular_speed_change':accel}
p=Path(sys.argv[1]);data=json.loads(p.read_text());out={'input':str(p),'input_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Every declared component timestep. Peak scalar angular-speed changes are unsigned finite differences, not signed vector joint acceleration. No visual acceptance. Artificial initial drop root placement omitted only from world-ankle peak, not joint/root-relative metrics.','cases':[]}
for c in data['cases']:out['cases'].append({'name':c['spec']['name'],'hz':c['hz'],'baseline':metrics(c['baseline'],c['hz']),'candidate':metrics(c['candidate'],c['hz'])})
Path(sys.argv[2]).write_text(json.dumps(out,indent=2)+'\n')
for c in out['cases']:
 b,n=c['baseline'],c['candidate'];print(c['name'],c['hz'],'gapmm',n['first_gaps_mm'],'stepdeg',round(b['peak_local_step']['deg'],3),'->',round(n['peak_local_step']['deg'],3),'airdeg',round(n['peak_airborne_step']['deg'],3),'anklemm',round(n['peak_ankle_root_relative_step']['m']*1000,3))
