#!/usr/bin/env python3
from pathlib import Path
import json,gzip,math,hashlib
OWNER=Path(__file__).resolve().parent
INPUTS={'997':OWNER.parent/'W5-motion-r1/component-r3/report.json.gz','5731':OWNER/'component-r1/report.json.gz'}
def angle(p,q):
 dot=abs(sum(a*b for a,b in zip(p,q))/math.sqrt(sum(a*a for a in p)*sum(a*a for a in q)))
 return 2*math.degrees(math.acos(min(1,dot)))
rows=[]
for source,path in INPUTS.items():
 data=json.load(gzip.open(path,'rt'))
 for case in data['cases']:
  for branch in ['baseline','candidate']:
   angular={'all':{'degrees':0},'airborne':{'degrees':0},'grounded':{'degrees':0}};ankle={'m':0};last=None
   for row in case[branch]:
    if last:
     for name,q in row['leg_rotations'].items():
      value=angle(last['leg_rotations'][name],q)
      for scope in ['all','grounded' if row['grounded'] else 'airborne']:
       if value>angular[scope]['degrees']:angular[scope]={'degrees':value,'bone':name,'tick':row['tick'],'grounded':row['grounded']}
     for side,v in row['feet'].items():
      delta=[a-b for a,b in zip(v,last['feet'][side])];length=math.sqrt(sum(a*a for a in delta))
      if length>ankle['m']:ankle={'m':length,'side':side,'tick':row['tick'],'grounded':row['grounded'],'delta_m':delta,'velocity_mps':[x*30 for x in delta]}
    last=row
   first=next(r for r in case[branch] if r['grounded'])
   rows.append({'source':source,'case':case['case'],'branch':branch,'first_grounded_tick':first['tick'],'first_sole_mm':{s:first['skin'][s]['minimum_m']*1000 for s in ['L','R']},'peak_local_joint_rotation':angular,'peak_ankle_step':ankle})
result={'scope':'All retained30Hz pose evaluations under prescribed30/60/120Hz component updates. Local joint angles differ from prior natural global-matrix angles. World ankle displacement includes shared root. No aesthetic pass from numerical endpoints.','inputs':{k:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for k,p in INPUTS.items()},'rows':rows}
(OWNER/'rate-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{'source':r['source'],'case':r['case']['name'],'airborne_deg':r['peak_local_joint_rotation']['airborne']['degrees'],'overall_deg':r['peak_local_joint_rotation']['all']['degrees'],'ankle_mm':r['peak_ankle_step']['m']*1000} for r in rows if r['branch']=='candidate']))
