"""Check exact Backup B Git tree against its retained stage manifest, read-only."""
from pathlib import Path
import hashlib,json,shutil,subprocess,datetime
ROOT=Path('/workspace/ANDOLAN');OUT=Path(__file__).resolve().parent/'backup-B-verification';SRC=Path('/workspace/scratch/yuga-backup-B-stage');COMMIT='0412db42f0a3da8afa1c30b33be6239d04f7afe8';BASE='37bb953503a1a374f7c0c6aae1ef3d43cfba8867'
def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=ROOT)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==COMMIT
before={'head':COMMIT,'index_sha256':sha(ROOT/'.git/index')}
manifest=json.loads((SRC/'manifest.json').read_text());assert manifest['parent']==BASE
rows={r['path']:r for r in manifest['files']};assert len(rows)==len(manifest['files'])==211
tree={}
for b in git('ls-tree','-r','-l','-z',COMMIT).split(b'\0'):
 if b:
  a,p=b.split(b'\t',1);mode,kind,blob,size=a.decode().split()
  if kind=='blob':tree[p.decode()]={'mode':mode,'blob':blob,'bytes':int(size)}
assert git('rev-parse',COMMIT+'^').decode().strip()==BASE
changed=set(x.decode()for x in git('diff-tree','--no-commit-id','--name-only','-r','-z',COMMIT).split(b'\0')if x)
assert changed==set(rows)
for p,r in rows.items():
 t=tree[p];assert (t['mode'],t['blob'],t['bytes'])==(r['git_mode'],r['git_blob'],r['bytes']),p
runtime_prefixes=('games/yuga-native/scripts/','games/yuga-native/scenes/','games/yuga-native/shaders/','games/yuga-native/assets/','games/yuga-native/NOTICE/')
runtime_files={'games/yuga-native/project.godot','games/yuga-native/export_presets.cfg'}
assert not[p for p in changed if p.startswith(runtime_prefixes)or p in runtime_files]
proofs={}
for n in ['manifest.json','stage-verification.json','commit-verification.json','remote-verification.json']:
 shutil.copyfile(SRC/n,OUT/n);proofs[n]={'bytes':(OUT/n).stat().st_size,'sha256':sha(OUT/n)}
owner_remote=json.loads((OUT/'remote-verification.json').read_text());assert owner_remote['commit']==COMMIT and owner_remote['verified'] and owner_remote['response'].split()[0]==COMMIT
checks={'exact_parent':True,'manifest_unique_paths':True,'exact_changed_path_set':True,'all211_committed_blob_modes_sizes_match_stage_manifest':True,'no_active_runtime_notice_config_changed':True,'retained_owner_remote_response_matches_commit':True}
after={'head':git('rev-parse','HEAD').decode().strip(),'index_sha256':sha(ROOT/'.git/index')};assert before==after
result={'schema':1,'scope':'Independent read-only Git tree/path/mode/size comparison against exact retained Backup B stage manifest; owner stage proof carries SHA256 byte verification. No repeated36MB content hash campaign, no new network push/read, no engine.','commit':COMMIT,'parent':BASE,'paths':len(rows),'logical_bytes':sum(r['bytes']for r in rows.values()),'checks':checks,'passed':len(checks),'normal_head_index_unchanged':True,'owner_remote_proof_not_new_network_check':True,'proofs':proofs,'git_before':before,'git_after':after}
(OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'README.md').write_text(f'Backup B `{COMMIT}` independently matches all211 committed file paths, Git blob IDs, modes and sizes in the retained stage manifest ({result["logical_bytes"]:,} bytes), with exact parent `{BASE}`. No active runtime/config/notice path changed. The small original stage/commit/remote proof files are retained here; remote verification is the owner-recorded response, not a new network query. SHA-256 content verification was performed by the original owner stage proof, not rerun as a new broad campaign. HEAD/index stayed unchanged. This is source/evidence backup proof, not acceptance of inactive art.\n')
files=[p for p in OUT.iterdir()if p.is_file()and p.name!='receipt.json'];receipt={'schema':1,'sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':COMMIT,'checks_passed':len(checks),'git_or_source_mutations':False,'artifacts':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)}for p in files}};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'checks':len(checks),'paths':len(rows),'bytes':result['logical_bytes'],'receipt_sha256':sha(OUT/'receipt.json')}))
