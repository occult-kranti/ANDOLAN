#!/usr/bin/env python3
import hashlib,io,json,pathlib,subprocess,tarfile
repo=pathlib.Path('/workspace/ANDOLAN');project=repo/'games/yuga-native';freeze=pathlib.Path('/tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native');before='4bd82ad5909ce949df536b2809d8b37a7f9d20f8';after='83f88f840c59934155aec19d95b41d920d15c6c1';out=project/'docs/evidence/ui-campaign/I3/role02/uid-overlay-review.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def runtime(name):return name.startswith(('scripts/','shaders/','scenes/','assets/')) or name in ['project.godot','export_presets.cfg']
manifest=json.loads((freeze/'ui-source-freeze.json').read_text());base={name:{'bytes':(freeze/name).stat().st_size,'sha256':h} for name,h in manifest['source_sha256'].items() if runtime(name)}
paths=['games/yuga-native/'+s for s in ['scripts','shaders','scenes','assets','project.godot','export_presets.cfg']]
raw=subprocess.check_output(['git','-C',str(repo),'archive','--format=tar',after,'--',*paths]);committed={};uid_text={}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:') as tar:
 for member in tar:
  if not member.isfile():continue
  name=member.name.removeprefix('games/yuga-native/');data=tar.extractfile(member).read();committed[name]={'bytes':len(data),'sha256':sha(data)}
  if name.endswith('.uid') and name not in base:uid_text[name]=data.decode()
missing=sorted(set(base)-set(committed));changed=[name for name in base if name in committed and base[name]!=committed[name]];additions={name:committed[name] for name in sorted(set(committed)-set(base))}
diff=subprocess.check_output(['git','-C',str(repo),'diff','--name-status',before,after,'--',*paths],text=True).splitlines()
existing=json.loads((project/'docs/evidence/ui-campaign/I3/role06/uid-overlay.json').read_text())
base_sig=sha(json.dumps(base,sort_keys=True).encode());new_sig=sha(json.dumps(committed,sort_keys=True).encode())
checks={'base_count_518':len(base)==518,'committed_count_525':len(committed)==525,'all_original_runtime_bytes_unchanged':not missing and not changed,'only_seven_uid_additions':len(additions)==7 and all(n.endswith('.uid') for n in additions),'uids_have_native_identity':all(x.startswith('uid://') and x.endswith('\n') for x in uid_text.values()),'git_delta_is_exact_additions':diff==['A\tgames/yuga-native/'+n for n in sorted(additions)],'independent_signatures_match_owner':base_sig==existing['base_runtime_signature'] and new_sig==existing['runtime_signature'] and additions==existing['only_additions']}
result={'passed':all(checks.values()),'checks':checks,'before_commit':before,'after_commit':after,'freeze_manifest_sha256':sha((freeze/'ui-source-freeze.json').read_bytes()),'base_runtime_signature':base_sig,'runtime_signature':new_sig,'original_runtime_files':len(base),'committed_runtime_files':len(committed),'missing':missing,'changed':changed,'additions':additions,'uid_text':uid_text,'git_runtime_diff':diff,'scope':'Independent read of committed Git archive bytes compared with every runtime file in the tested I1 freeze. Only runtime roots/project/export configuration are scoped; docs/tests also changed between commits and are not called UID-only. No import or export executed by this reviewer.'}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':checks,'runtime_signature':new_sig}))
