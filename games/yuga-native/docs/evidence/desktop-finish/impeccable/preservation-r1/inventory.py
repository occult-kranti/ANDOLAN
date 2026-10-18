from pathlib import Path
import hashlib,json,os,re,stat,subprocess,gzip
repo=Path('/workspace/ANDOLAN'); native=repo/'games/yuga-native'; out=Path('/workspace/scratch/yuga-final-preservation-r1')
scopes=[native/x for x in ['PRODUCT.md','DESIGN.md','docs/research/impeccable','docs/evidence/desktop-finish/impeccable','docs/evidence/desktop-finish/impeccable-pass','docs/evidence/desktop-finish/next-motion/W5-landing-preparation-candidate-r1','docs/evidence/desktop-finish/CI/W6-0964564-r1','docs/evidence/desktop-finish/CI/W6-1b2e6f5-r1']]
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for chunk in iter(lambda:f.read(524288),b''):h.update(chunk)
 return h.hexdigest()
def rel(p):
 try:return str(p.relative_to(repo))
 except ValueError:return str(p)
def allfiles():return sorted(p for s in scopes for p in ([s] if s.is_file() else s.rglob('*')) if p.is_file())
initial={p:(p.stat().st_size,digest(p)) for p in allfiles()}
selected={scopes[0],scopes[1]}; checks=[]; refs=[]; missing=[]; mismatches=[]
def resolve(v,owner):
 if v.startswith('res://'):return native/v[6:]
 p=Path(v)
 if p.is_absolute():return p
 if v.startswith('games/yuga-native/'):return repo/p
 if v.startswith(('docs/','scripts/','tests/','assets/','tools/')) and (native/p).exists():return native/p
 return owner.parent/p

def verify(p,h=None,size=None,owner=None,kind='artifact',blob=None):
 row={'owner':rel(owner) if owner else None,'path':rel(p),'kind':kind,'exists':p.is_file()}
 if p.is_file():
  row.update(bytes=p.stat().st_size,sha256=digest(p))
  row['sha256_match']=h is None or row['sha256']==h
  row['size_match']=size is None or row['bytes']==size
  if blob:
   hh=hashlib.sha1();hh.update(('blob '+str(row['bytes'])+'\0').encode());hh.update(p.read_bytes()); row['git_blob_match']=hh.hexdigest()==blob
  if not all(row.get(k,True) for k in ['sha256_match','size_match','git_blob_match']):mismatches.append(row)
 else:missing.append(row)
 checks.append(row);return row
receipts=sorted(p for p in initial if p.name=='receipt.json')
for receipt in receipts:
 selected.add(receipt);data=json.loads(receipt.read_text()); arts=data.get('artifacts',data.get('files',[]))
 if isinstance(arts,dict): arts=[dict(v,path=k) for k,v in arts.items()]
 for a in arts:
  p=resolve(a['path'],receipt);verify(p,a.get('sha256'),a.get('bytes',a.get('size')),receipt)
  if p in initial and not any(part in ['user','users','cache','caches','.godot','__pycache__'] for part in p.parts):selected.add(p)
 for key in ['actual_failure','baseline_headless']:
  a=data.get(key)
  if isinstance(a,dict) and 'path' in a:verify(resolve(a['path'],receipt),a.get('sha256'),a.get('bytes'),receipt,'external-evidence-reference')
 for key in ['raw_failed_log','raw_job_log']:
  a=data.get(key)
  if a:
   p=receipt.parent/a['storage'];hh=hashlib.sha256();n=0
   with gzip.open(p,'rb') as f:
    for chunk in iter(lambda:f.read(524288),b''):hh.update(chunk);n+=len(chunk)
   rr={'owner':rel(receipt),'path':rel(p),'kind':'decompressed-log','bytes':n,'sha256':hh.hexdigest(),'sha256_match':hh.hexdigest()==a['sha256'],'size_match':n==a['bytes']};checks.append(rr)
   if not rr['sha256_match'] or not rr['size_match']:mismatches.append(rr)
research=native/'docs/research/impeccable';manifest=research/'source-manifest.json'
for p in [research/'README.md',manifest,research/'download-source-manifest.json']:selected.add(p)
for a in json.loads(manifest.read_text())['files']:
 p=resolve(a['path'],manifest);verify(p,a['sha256'],a['bytes'],manifest,'vendored-source',a['git_blob']);selected.add(p)
# The original download receipt remains provenance only; validate its external paths without selecting them.
download=research/'download-source-manifest.json'
for a in json.loads(download.read_text())['files']:verify(Path(a['local']),a['sha256'],a['bytes'],download,'external-download-source',a['git_blob'])
for p in initial:
 if p.name in ['W6-title-source-review-r1.json','W6-loading-source-review-r1.json']:
  selected.add(p);a=json.loads(p.read_text())['owner_receipt'];verify(resolve(a['path'],p),a['sha256'],None,p,'owner-receipt-reference')
# Resolve image identities from closed incumbent review, without copying/selecting out-of-scope originals.
inc=native/'docs/evidence/desktop-finish/impeccable/W1-incumbent-r1/review.json'
for a in json.loads(inc.read_text())['originals']:verify(resolve(a['path'],inc),a['sha256'],a.get('bytes'),inc,'external-incumbent-original')
loss=native/'docs/evidence/desktop-finish/next-motion/W5-landing-preparation-candidate-r1/lossless-reports.json'
for a in json.loads(loss.read_text()):
 c=a['compressed'];p=resolve(c['path'],loss);verify(p,c['sha256'],c['bytes'],loss,'compressed-report')
 original=a['original'];hh=hashlib.sha256();n=0
 with gzip.open(p,'rb') as f:
  for chunk in iter(lambda:f.read(524288),b''):hh.update(chunk);n+=len(chunk)
 rr={'owner':rel(loss),'path':rel(p),'kind':'lossless-report-payload','original_path':original['path'],'bytes':n,'sha256':hh.hexdigest(),'sha256_match':hh.hexdigest()==original['sha256'],'size_match':n==original['bytes']};checks.append(rr)
 if not rr['sha256_match'] or not rr['size_match']:mismatches.append(rr)
 refs.append({'owner':rel(loss),'path':original['path'],'exists':Path(original['path']).is_file(),'disposition':'scratch original excluded; byte-exact payload verified through selected gzip'})
# Resolve ordinary markdown file links; out-of-scope targets are never selected automatically.
for p in sorted(selected):
 if p.suffix=='.md':
  for raw in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   v=raw.strip('<>').split('#',1)[0]
   if not v or re.match(r'^[A-Za-z]+://',v):continue
   dest=(p.parent/v).resolve();row={'owner':rel(p),'target':raw,'resolved':rel(dest),'exists':dest.exists(),'selected':dest in selected};refs.append(row)
   if not dest.exists():missing.append(dict(row,kind='markdown-file-reference'))
# Git index mode takes precedence for tracked files; otherwise retain actual executable intent.
git_modes={}
for entry in subprocess.check_output(['git','-C',str(repo),'ls-files','--stage','-z']).decode().split('\0'):
 if entry:
  left,path=entry.split('\t',1);git_modes[path]=left.split()[0]
rows=[]
for p in sorted(selected):
 if not p.is_file():continue
 mode=git_modes.get(rel(p),'100755' if p.stat().st_mode&0o111 else '100644')
 rows.append({'path':rel(p),'sha256':digest(p),'bytes':p.stat().st_size,'gitmode':mode})
end={p:(p.stat().st_size,digest(p)) for p in allfiles()};changed=[rel(p) for p in set(initial)|set(end) if initial.get(p)!=end.get(p)]
excluded=[{'path':rel(p),'reason':'unreferenced by a closed receipt or selected context/provenance document'} for p in initial if p not in selected]
report={'schema':1,'source_commit':subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD']).decode().strip(),'scope':[rel(s) for s in scopes],'read_only_repository':True,'engines_imports_staging_commits':False,'active_W1_merged_UI_and_C4_excluded':True,'selected_count':len(rows),'selected_bytes':sum(r['bytes'] for r in rows),'receipt_count':len(receipts),'verification_count':len(checks),'mismatches':mismatches,'absent_references':missing,'scope_changed_during_inventory':changed,'excluded':excluded,'checks':checks,'resolved_other_references':refs,'limits':['Only explicit closed artifact lists, named context/provenance documents and standalone W6 closed source reviews selected. No closure inferred from recursive directory membership.','Source pins in execution histories identify their historical source and are not assertions that live current source must equal old snapshots.','No active merged UI/C4 archive, cache, userstate, unreferenced artifacts, source staging or bulk copying performed.']}
(out/'allowlist.json').write_text(json.dumps({'source_commit':report['source_commit'],'files':rows},indent=2)+'\n')
(out/'allowlist.tsv').write_text('gitmode\tsha256\tbytes\tpath\n'+''.join(f"{x['gitmode']}\t{x['sha256']}\t{x['bytes']}\t{x['path']}\n" for x in rows))
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['source_commit','selected_count','selected_bytes','receipt_count','verification_count','mismatches','absent_references','scope_changed_during_inventory','excluded']},indent=2))
