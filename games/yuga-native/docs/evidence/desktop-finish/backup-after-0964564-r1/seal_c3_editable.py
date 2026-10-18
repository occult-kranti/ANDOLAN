import hashlib,json,os,stat,subprocess
from pathlib import Path
R=Path('/workspace/ANDOLAN'); B=R/'games/yuga-native'; A=B/'art/hero-finish/hair-sculpt-design/clay-volume-r3'; S=Path('/workspace/scratch/yuga-hair-volume-r3/build-r1'); D=A/'authoring-payload/build-r1'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,o): p.write_text(json.dumps(o,indent=2)+'\n')
def meta(p): return dict(sha256=sha(p),bytes=p.stat().st_size,mode=oct(stat.S_IMODE(p.stat().st_mode)),git_mode='100755' if p.stat().st_mode&0o111 else '100644')
assert not (A/'source-receipt.json').exists()
manifest=json.loads((S/'manifest.json').read_text()); assert len(manifest)==8
for name,m in manifest.items():
 p=S/name; assert p.is_file() and not p.is_symlink(); assert sha(p)==m['sha256'] and p.stat().st_size==m['bytes']
D.mkdir(parents=True,exist_ok=True)
rows=[]
inputs=[(S/n,D/n) for n in sorted(manifest)]+[(S/'manifest.json',D/'manifest.json'),(S.parent/'source-01-inner-wall-classification.json',A/'authoring-payload/source-01-inner-wall-classification.json')]
for p,q in inputs:
 assert p.is_file() and not p.is_symlink(); before=meta(p); s=p.stat()
 if q.exists(): assert os.path.samefile(p,q) and meta(q)==before
 else: os.link(p,q)
 assert os.path.samefile(p,q) and meta(q)==before and meta(p)==before
 rows.append(dict(original=str(p),retained=str(q.relative_to(R)),**before,same_device_inode=True,device=s.st_dev,inode=s.st_ino,physical_bytes_added=0))
prior=A/'authoring-payload/README.before-recovery.md'
old=prior.read_bytes() if prior.exists() else (A/'README.md').read_bytes()
if not prior.exists(): prior.write_bytes(old)
text=old.decode(); oldline='Current source save: `/workspace/scratch/yuga-hair-volume-r3/build-r1/`.'
assert text.count(oldline)==1
text=text.replace(oldline,'The exact source save is retained at [authoring-payload/build-r1](authoring-payload/build-r1/).\nThe original `/workspace/scratch/yuga-hair-volume-r3/build-r1/` paths remain intact as\nhardlink aliases. [The recovery map](authoring-payload/recovery-map.json) pins every\nmanifest member and the separate inner-wall classification; no payload bytes were\nchanged or physically duplicated. [The source receipt](source-receipt.json) seals\nthis rejected editable construction and its dependencies.')
(A/'README.md').write_text(text)
deps=[]
for name in ['whole-hair-clay-framing-r3.blend','scene_semantics.py','projection_contract.py']:
 p=A.parent/'clay-framing-r3'/name; rel=str(p.relative_to(R)); recovery=rel.replace('/clay-framing-r3/','/clay-framing-r2/') if name=='scene_semantics.py' else rel
 blob=subprocess.check_output(['git','--no-optional-locks','-C',str(R),'rev-parse','HEAD:'+recovery],text=True).strip(); data=subprocess.check_output(['git','--no-optional-locks','-C',str(R),'cat-file','blob',blob]); assert hashlib.sha256(data).hexdigest()==sha(p)
 deps.append(dict(path=rel,recovery_source_path=recovery,**meta(p),git_blob=blob,available_at_commit='0964564d1ba283a5ac0aee8eab0a6cccd8f443f3'))
dump(A/'authoring-payload/recovery-map.json',dict(schema=1,scope='Exact frozen C3 authoring payload recovery; no geometry mutation, engine, render or activation',method='Same-filesystem hardlinks; original scratch aliases retained. Git backup can recover each retained path independently.',files=rows,dependencies=deps,total_payload_bytes=sum(r['bytes'] for r in rows),new_payload_physical_bytes=0))
artifacts={str(p.relative_to(A)):meta(p) for p in sorted(A.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
assert sha(A/'build_volume.py')=='315065fc1201f6a4a86747d8485335715a0acf7a2b850e473feea9e00b8b323d'
assert sha(A/'capture_volume.py')=='0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7'
dump(A/'source-receipt.json',dict(schema=1,scope='Editable C3 original coarse hair construction and exact failed-art source recovery',disposition='REJECTED after all four actual views; inactive, no runtime or mesh acceptance',source_head='0964564d1ba283a5ac0aee8eab0a6cccd8f443f3',scene_sha256=manifest['whole-hair-volume-r3.blend']['sha256'],payload_count=len(rows),payload_bytes=sum(r['bytes'] for r in rows),physical_payload_bytes_added=0,artifacts=artifacts,artifact_count=len(artifacts),dependencies=deps,actual_receipt=dict(path='games/yuga-native/docs/evidence/desktop-finish/hair-volume-r3/W1-actual-r1/receipt.json',sha256='9bb1021c905d35d0ed99202f61eee438d049ec661ccc05faceff53148c832edb'),limits=['Rest-space editable authoring only; not weighted or runtime LOD geometry.','Buried scalp contacts and hardware fit remain reported by W2; this seal makes no new fit or art claim.','Historical construction receipt retains its original unrendered status; the separate actual receipt records later rejection.'],operations=['Verified all 8 manifest members exact','Retained 10 payload files via hardlink, including original manifest and separate classification','Verified source builder and capture helper unchanged','Verified 3 dependencies against current committed Git bytes','Only README recovery links changed; prior README retained byte-exact']))
print(json.dumps(dict(receipt=str(A/'source-receipt.json'),sha256=sha(A/'source-receipt.json'),artifacts=len(artifacts),payload_bytes=sum(r['bytes'] for r in rows),physical_payload_bytes_added=0),indent=2))
