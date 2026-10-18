from pathlib import Path
import hashlib,importlib.util,json,os,shutil
W=Path(__file__).parent.parent;R=Path('/workspace/ANDOLAN/games/yuga-native');P=Path('/workspace/scratch/yuga-frontage-production-r1/project');H=Path('/workspace/scratch/yuga-frontage-production-r1/harness/snapshot.py')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('snapshot',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
old=m.verify(P);assert h(P/m.MARKER)=='35a0b97e25c5ad1829d296ab115b61aced3e54e267a72737fd92d4a6d32537b9'
pins={'scripts/launch_shell.gd':'69162e5d90a6e594ffaabe5fc2926975d903f47f6e307d4ebe7f3ed63d869681','scripts/loading_presentation.gd':'bdd5c139e9eb70e709aff2b3bbfb396cd9633e073739435fc30898ed30dda1e5'}
assert h(R/'scripts/hero_ui_theme.gd')=='5a7264614f2ec7eccafdaa40620f605e0f016a7f7a3185c60c7c82b66bd85d6a'
deltas=[]
for n,item in old['files'].items():
 if n.startswith(('scripts/','scenes/','shaders/','assets/')) or n=='project.godot':
  if not (R/n).is_file() or h(R/n)!=item['sha256']:deltas.append(n)
assert sorted(deltas)==sorted(pins)
for n,pin in pins.items():assert h(R/n)==pin
assert shutil.disk_usage(W).free>=550*1024**2
ov={n:R/n for n in pins};ov['tools/ui-campaign/observer.gd']=W/'preparation/observer.gd';ov['tools/ui-campaign/run.py']=R/'tools/ui-campaign/run.py';ov['tools/ui-campaign/transition_board.gd']=R/'tools/ui-campaign/transition_board.gd'
N=W/'project';assert not N.exists();N.mkdir();expected=dict(old['files']);origin={};store=Path(old['store'])/'sources'
for n,p in ov.items():
 item=m.metadata(p);blob=store/item['sha256']
 if not blob.exists():shutil.copyfile(p,blob);blob.chmod(0o444)
 assert m.metadata(blob)==item;expected[n]=item;origin[n]=blob
for n,item in expected.items():
 q=N/n;q.parent.mkdir(parents=True,exist_ok=True);src=origin.get(n,P/n)
 if n in m.AUX_FILES or n=='tools/visual-rounds/frontage-review.json':shutil.copyfile(src,q)
 else:os.link(src,q)
r=dict(old);r.update(project=str(N),round='impeccable-title-loading-r1',files=expected,previous_marker_sha256=h(P/m.MARKER),source_bytes=sum(v['bytes'] for n,v in expected.items() if not n.startswith('.godot/')),declared_ui_overlays={n:expected[n] for n in ov})
(N/m.MARKER).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');m.verify(N);m.verify(P)
receipt={'passed':True,'parent':str(P),'parent_marker_sha256':h(P/m.MARKER),'project':str(N),'marker_sha256':h(N/m.MARKER),'files':len(expected),'imports':len(r['validated_imports']),'runtime_deltas':pins,'theme_unchanged':True,'all_other_existing_runtime_equal_canonical':True,'overlays':{n:{'before':old['files'].get(n),'after':expected[n]} for n in ov},'no_import_no_full_clone':True,'parent_and_import_store_unchanged':True,'workspace_free_after':shutil.disk_usage(W).free}
(W/'preparation/staging.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
