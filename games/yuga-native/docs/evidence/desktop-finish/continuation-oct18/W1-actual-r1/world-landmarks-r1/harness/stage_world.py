from pathlib import Path
import hashlib,importlib.util,json,os,shutil
W=Path(__file__).parent.parent;R=Path('/workspace/ANDOLAN/games/yuga-native');P=Path('/workspace/scratch/yuga-frontage-production-r1/project')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('snapshot',W/'harness/snapshot.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.verify(P);assert shutil.disk_usage(W).free>600*1024**2
canonical=m.inventory(R);runtime={n:v for n,v in canonical.items() if n.startswith(('scripts/','scenes/','shaders/','assets/')) or n in m.ROOT_FILES}
expected=dict(old['files']);origins={}
for n,item in runtime.items():
 if expected.get(n)!=item:expected[n]=item;origins[n]=R/n
# Freeze every canonical script including new helpers, while all unchanged assets/cache reuse immutable parent bytes.
for n,item in expected.items():
 if n.startswith(('assets/','.godot/imported/')):assert (R/n).is_file() and m.metadata(R/n)==item,(n,'asset mismatch')
projects={}
for role in ['baseline','candidate']:
 new=W/('world-'+role+'-project');assert not new.exists();new.mkdir();files=dict(expected)
 ov=dict(origins)
 if role=='baseline':
  p=R/'docs/evidence/desktop-finish/continuation-oct18/W4-world-r1/baseline-traversal_landmarks.gd.txt';assert sha(p)=='ee070b0a4b1c0bb07ac645681e6ef3dcf0311adb88afe07ece3ecc75b4ab971b';ov['scripts/traversal_landmarks.gd']=p;files['scripts/traversal_landmarks.gd']=m.metadata(p)
 for n,item in files.items():
  target=new/n;target.parent.mkdir(parents=True,exist_ok=True)
  if n in ov or n in m.AUX_FILES:shutil.copyfile(ov.get(n,P/n),target)
  else:os.link(P/n,target)
 record=dict(old);record.update(project=str(new),round='continuation-oct18-world-'+role,files=files,frozen_source_commit='d199f6071d67ae5072fde0359361ec64b81844d1',canonical_runtime=runtime)
 (new/m.MARKER).write_text(json.dumps(record,indent=2,sort_keys=True)+'\n');m.verify(new)
 projects[role]={'path':str(new),'seal_sha256':sha(new/m.MARKER),'files':len(files),'runtime_changed':list(ov)}
m.verify(P)
(W/'world-staging.json').write_text(json.dumps({'projects':projects,'source_files':runtime,'scope':'Frozen before army changes; hardlinks only verified unchanged parent files; small runtime overlays copied privately; no imports'},indent=2)+'\n')
print(json.dumps({r:{k:v for k,v in x.items() if k!='runtime_changed'} for r,x in projects.items()}))
