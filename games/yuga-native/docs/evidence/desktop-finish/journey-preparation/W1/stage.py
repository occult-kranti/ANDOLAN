from pathlib import Path
import hashlib,json,subprocess
source=Path('/workspace/ANDOLAN/games/yuga-native');work=Path('/tmp/yuga-desktop-journey-r1');child=work/'project'
inp=source/'docs/evidence/desktop-finish/journey-preparation/W6/capture-inputs.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(inp)=='592764bc3e1a9524ba563d7417c52e3cba74b54c59780a9f713c9ae9f22c6bc5'
j=json.loads(inp.read_text());expected=j['files']|j['existing_cache_files']
def verify(root):
 for name,item in expected.items():
  p=root/name;assert p.is_file() and p.stat().st_size==item['bytes'] and sha(p)==item['sha256'],(root,name)
verify(source)
command=['python3',str(source/'tools/ui-campaign/freeze.py'),'--source',str(source),'--output',str(child)]
r=subprocess.run(command,capture_output=True,text=True,timeout=90);(work/'freeze.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
verify(child);verify(source)
record={'passed':True,'scope':'Exact current journey staging only; no engine/import/render. All intended W6 sources and cache/support inputs verified before/after; existing freeze helper also copies extra tests.','command':command,'exit':r.returncode,'project':str(child),'input_sha256':sha(inp),'freeze_sha256':sha(child/'ui-source-freeze.json'),'source_inputs':len(j['files']),'cache_support_inputs':len(j['existing_cache_files']),'all_expected_inputs':len(expected),'freeze_log_sha256':sha(work/'freeze.log'),'stage_script_sha256':sha(Path(__file__))}
(work/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
