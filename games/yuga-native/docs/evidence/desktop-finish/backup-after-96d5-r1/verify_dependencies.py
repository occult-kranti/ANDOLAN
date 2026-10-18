"""Read-only closure for source dependencies declared by the frozen R6 producer."""
from pathlib import Path
import gzip,hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;REPO=Path('/workspace/ANDOLAN');N=REPO/'games/yuga-native';HEAD='96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
receipt=N/'docs/evidence/desktop-finish/hair-collected-r6/W2/receipt.json';doc=json.loads(receipt.read_text());plan=json.loads((OUT/'inventory-and-recovery.json').read_text());rows={r['path']:r for r in plan['files']+plan['historical_exclusions']};tree={}
for raw in subprocess.check_output(['git','--no-optional-locks','ls-tree','-r','-l','-z',HEAD],cwd=REPO).split(b'\0'):
 if raw:
  meta,p=raw.split(b'\t',1);mode,kind,blob,size=meta.decode().split()
  if kind=='blob':tree[p.decode()]={'git_blob':blob,'bytes':int(size),'mode':mode}
byblob={}
for p,x in tree.items():byblob.setdefault(x['git_blob'],[]).append(p)
checks=[]
for d in doc['dependencies']:
 p=N/d['path'];raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest();blob=hashlib.sha1(('blob '+str(len(raw))+'\0').encode()+raw).hexdigest();r={'path':str(p.relative_to(REPO)),'sha256':sha,'bytes':len(raw),'git_blob':blob,'passed':sha==d['sha256']}
 if blob in byblob:r['recovery']={'kind':'git_blob','commit':HEAD,'source':sorted(byblob[blob])[0]}
 elif r['path']in rows:r['recovery']=rows[r['path']]['recovery']
 else:r['recovery']={'kind':'UNRESOLVED'}
 if r['recovery']['kind']=='historical_lossless_gzip_mapping':
  prior=r['recovery']['prior_recovery'];r['gzip_recovery']=prior
  source=prior.get('source')or prior.get('path')or prior.get('gzip')
  if source:
   gp=REPO/source
   if not gp.exists():gp=N/source
   assert hashlib.sha256(gzip.decompress(gp.read_bytes())).hexdigest()==sha
 r['passed']=r['passed']and r['recovery']['kind']!='UNRESOLVED';checks.append(r)
assert all(r['passed']for r in checks)
readiness=json.loads((N/'docs/evidence/desktop-finish/hair-collected-r6/W2-render-preparation-r1/source-readiness.json').read_text())
result={'scope':'R6 declared source dependency byte/recovery verification only; no generator/import/raster executed','source_receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'checks':checks,'passed':len(checks),'total':len(checks),'external_runtime_dependencies_from_sealed_recipe':{k:readiness[k]for k in ['baseline','baseline_marker_sha256','engines','seeds']},'external_limit':'Recipe baseline/import store and warm Godot/Mesa cache seeds are external execution aids, not recreated or bundled by this backup. Archived raw originals, exact controls and semantic payloads remain included. Compiled candidate-import-cache tar deliberately excluded; regenerate using pinned inputs/engine if execution is needed.'}
(OUT/'dependency-recovery.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':len(checks),'total':len(checks),'external_keys':list(result['external_runtime_dependencies_from_sealed_recipe'])}))
