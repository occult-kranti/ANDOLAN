import hashlib,json,shutil,subprocess,time,zipfile
from pathlib import Path
out=Path('/tmp/yuga-desktop-integrated-package-r3');build=out/'build';repo=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN');project=repo/'games/yuga-native';commit='f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1'
def rec(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'bytes':path.stat().st_size,'sha256':h.hexdigest()}
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
export=json.loads((build/'native-export-manifest.json').read_text());package=json.loads((build/'native-package-manifest.json').read_text())
assert export['git']['head']==commit and export['git']['native_worktree_status']==''
assert package['git']==export['git'];assert export['engine_selection']==package['engine_selection']
engines=export['engine_selection'];assert engines['exporter']['sha256']=='f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3';assert engines['linux_runtime']['sha256']=='dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f'
assert export['godot_version']==engines['exporter']['version'];assert engines['linux_runtime']['provenance']['source_patches']==0
tracked=json.loads((out/'tracked-source-before.json').read_text());runtime=json.loads((out/'runtime-source-before.json').read_text())
for name,value in tracked.items():assert rec(repo/name)==value,name
for name,value in runtime.items():assert rec(project/name)==value,name
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()==commit
assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=repo,text=True).strip()
assert not subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=repo,text=True).strip()
audit=json.loads((repo.parent/'uid-generation-audit.json').read_text())
for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
assert (repo/'.git/info/exclude').read_bytes()==(out/'git-info-exclude.txt').read_bytes()
prior=json.loads((out/'preserved-prior-outputs.json').read_text())
for attempt,entries in prior.items():
 for name,value in entries.items():assert rec(Path('/tmp/yuga-desktop-integrated-package-'+attempt)/name)==value
archives={}
for platform in ['linux','windows']:
 path=build/f'yuga-native-{platform}-x86_64.zip';staging=build/f'yuga-native-{platform}-x86_64';pm=json.loads((staging/'PACKAGE-MANIFEST.json').read_text())
 assert pm['git']==export['git'];assert pm['runtime_source']==export['source'];assert pm['exporter']==engines['exporter']
 expected={str(p.relative_to(build)):rec(p) for p in staging.rglob('*') if p.is_file()}
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None;assert len(z.namelist())==len(set(z.namelist()))==len(expected);assert set(z.namelist())==set(expected)
  for name,value in expected.items():
   data=z.read(name);assert len(data)==value['bytes'];assert hashlib.sha256(data).hexdigest()==value['sha256']
  base=staging.name+'/';engine='godot' if platform=='linux' else 'godot.exe'
  assert hashlib.sha256(z.read(base+engine)).hexdigest()==pm['runtime']['sha256']
  assert hashlib.sha256(z.read(base+'yuga-native.pck')).hexdigest()==export['packs'][platform]['sha256']
  for name,value in pm['payloads'].items():assert expected[base+name]==value
  if platform=='linux':
   assert pm['runtime']==engines['linux_runtime'];assert 'unmodified-public-template-debug' in pm['packaging']
   assert json.loads(z.read(base+'NOTICE/GODOT-RUNTIME-PROVENANCE.json'))==engines
   assert b'community-built, unmodified' in z.read(base+'START-HERE.txt')
   assert (z.getinfo(base+'godot').external_attr>>16)&0o111
   assert (z.getinfo(base+'launch.sh').external_attr>>16)&0o111
  else:
   assert base+'NOTICE/GODOT-RUNTIME-PROVENANCE.json' not in z.namelist()
   assert b'bundled official Godot' in z.read(base+'START-HERE.txt')
 archives[platform]={**rec(path),'filename':path.name,'members':len(expected),'all_crc_and_payload_hashes_verified':True,'runtime':pm['runtime'],'pck':{k:export['packs'][platform][k] for k in ['bytes','sha256','entry_count']}}
logs=[*sorted((out/'logs').glob('*')),*sorted(build.glob('*.log'))]
diagnostics={str(p.relative_to(out)):[line for line in p.read_text(errors='replace').splitlines() if any(x in line for x in ['ERROR:','WARNING:','SCRIPT ERROR:'])] for p in logs}
assert not any(diagnostics.values()),diagnostics
write(out/'export-review-r2.json',{'passed':True,'git':export['git'],'engine_selection':engines,'diagnostics':diagnostics,'prior_reviewer_error':'export-review-r1-failure.json'})
files=[build/'yuga-native-linux-x86_64.zip',build/'yuga-native-windows-x86_64.zip',build/'native-export-manifest.json',build/'native-package-manifest.json']
(build/'SHA256SUMS.txt').write_text(''.join(rec(p)['sha256']+'  '+p.name+'\n' for p in files))
cache_before=json.loads((out/'cache-before-inventory.json').read_text());cache_after={str(p.relative_to(project/'.godot')):rec(p) for p in (project/'.godot').rglob('*') if p.is_file()}
cache_changes={p:{'before':cache_before.get(p),'after':cache_after.get(p)} for p in sorted(set(cache_before)|set(cache_after)) if cache_before.get(p)!=cache_after.get(p)}
write(out/'cache-after-delta.json',cache_changes)
result={'passed':True,'commit':commit,'project':str(project),'build':str(build),'tracked_files_unchanged':len(tracked),'runtime_files_unchanged':len(runtime),'generated_metadata_preserved':len(audit['new_files']),'exact_exclusion_unchanged':True,'prior_r1_r2_outputs_unchanged':True,'exporter':engines['exporter'],'packages':archives,'export_manifest':rec(build/'native-export-manifest.json'),'package_manifest':rec(build/'native-package-manifest.json'),'checksums':rec(build/'SHA256SUMS.txt'),'diagnostics':diagnostics,'cache_delta_count':len(cache_changes),'tmp_free_bytes':shutil.disk_usage('/tmp').free,'completed_unix':time.time(),'scope':'Exact source/PCK/archive qualification only; public runtime actual packaged execution pending W1; official r2 blocked run preserved.'}
write(out/'qualification-receipt.json',result)
print(json.dumps(result))
