from pathlib import Path
import json, shutil, hashlib, tarfile, gzip, re
ROOT=Path('/workspace/ANDOLAN/games/yuga-native'); E=ROOT/'docs/evidence/desktop-finish'; SRC=Path('/tmp/yuga-desktop-journey-r2/project')
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d): p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def copy(s,d): d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d);assert h(s)==h(d)
for kind,rawname,target in [('journey','yuga-desktop-native-journey-r1','journey-successor/W1-native-r1'),('boot','yuga-desktop-boot-recovery-r1','D02/W1-boot-recovery-r1')]:
 raw=Path('/tmp')/rawname; out=E/target; out.mkdir(parents=True,exist_ok=False)
 run=json.loads((raw/'run.json').read_text()); assert run['complete'] and run['verified_exit_code']==0 and run['cleanup_exit']==0
 assert all(run[k] is True for k in ['source_unchanged','import_cache_unchanged','import_freeze_manifest_unchanged','shader_cache_seed_unchanged','godot_shader_cache_seed_unchanged'])
 # Preserve unchanged raw originals, terminal observer state, full engine/X11 logs and journals.
 for f in sorted(raw.iterdir()):
  if f.is_file(): copy(f,out/('originals' if f.suffix=='.png' or (f.suffix=='.json' and f.with_suffix('.png').exists()) else 'raw')/f.name)
 tools=['run.py','observer.gd','integrated_capture.gd','authority_stage.gd','board.gd','freeze.py','preflight_journey.gd','desktop-journey-plan.json','boot-recovery-plan.json']
 for n in tools: copy(SRC/'tools/ui-campaign'/n,out/'tools'/n)
 copy(SRC/'ui-source-freeze.json',out/'source/ui-source-freeze.json')
 copy(E/'journey-successor/W6/capture-inputs.json',out/'source/capture-inputs.json')
 if kind=='journey':
  for n in ['stage.py','receipt.json','freeze.log']: copy(SRC.parent/n,out/'source/staging'/n)
  # Exact scripts/scenes/code, no duplicated assets or compiled import caches.
  members=[p for p in SRC.rglob('*') if p.is_file() and (p.relative_to(SRC).parts[0] in ['scripts','scenes'] or p.name=='project.godot')]
  manifest=[]
  with (out/'source/runtime-code.tar.gz').open('wb') as dest:
   with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0) as gz:
    with tarfile.open(fileobj=gz,mode='w') as tf:
     for p in sorted(members):
      info=tf.gettarinfo(str(p),arcname=str(p.relative_to(SRC)));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname='';
      with p.open('rb') as f:tf.addfile(info,f)
      manifest.append({'path':str(p.relative_to(SRC)),'sha256':h(p),'bytes':p.stat().st_size})
  write(out/'source/runtime-code.json',manifest)
  for p in raw.rglob('*.cfg'): copy(p,out/'preferences'/p.name)
 else:
  # Tiny fixture's complete source/import closure is portable, including font payloads.
  with (out/'source/fixture.tar.gz').open('wb') as dest:
   with gzip.GzipFile(filename='',mode='wb',fileobj=dest,mtime=0) as gz:
    with tarfile.open(fileobj=gz,mode='w') as tf:
     for p in sorted((raw/'fixture').rglob('*')):
      if not p.is_file():continue
      info=tf.gettarinfo(str(p),arcname=str(p.relative_to(raw/'fixture')));info.mtime=0;info.uid=info.gid=0;info.uname=info.gname=''
      with p.open('rb') as f:tf.addfile(info,f)
 copy(Path(__file__),out/'source/archive.py')
 log=(raw/'godot.log').read_text(); warnings=len(re.findall(r'^WARNING:',log,re.M)); errors=len(re.findall(r'^(?:ERROR:|SCRIPT ERROR:)',log,re.M))
 receipt={'schema':1,'passed':True,'scope':'Native desktop journey with explicitly staged outcomes' if kind=='journey' else 'Isolated missing-scene retry/recovery dismissal and native Quit; not in-flight cancellation', 'raw_output':str(raw),'manual_originals':len(run['shots']),'automatic_originals':len(run['automatic_shots']),'native_events':len(run['events']),'authority_stage_actions':len(run['authority_staging']['stages']),'actual_exit':run['verified_exit_code'],'cleanup_exit':run['cleanup_exit'],'elapsed_seconds':run['finished_unix']-run['started_unix'],'warnings':warnings,'errors':errors,'engine_sha256':run['engine_sha256'],'source_freeze_sha256':h(SRC/'ui-source-freeze.json'),'source_inventory_sha256':h(E/'journey-successor/W6/capture-inputs.json'),'scheduling':run['scheduling'],'source_and_cache_gates':{k:v for k,v in run.items() if k.endswith('_unchanged')},'preservation':{'raw_originals':'Exact byte copies, no processing','runtime':'Exact scripts/scenes in runtime-code archive plus complete input inventory; existing assets/imports remain referenced by source hashes, not duplicated here.' if kind=='journey' else 'Complete tiny fixture preserved in fixture.tar.gz.','cache_seed':'../../G0/template-baseline-cold-600-r1/generated-shader-caches.tar.gz' if kind=='journey' else 'No seed'},'direct_W1_visual_review':['01-title-after-configured-boot','18-STAGED-sun-outcome','22-returned-settings-retained'] if kind=='journey' else ['01-initial-missing-scene','03-usable-boot-recovery','05-back-to-quit'],'limits':['Software renderer; no hardware FPS or listening claim.','No process relaunch persistence claim in this take.','Staged outcomes are actual rules invoked by an explicit fixture; not played victories.'] if kind=='journey' else ['Compatibility tiny component fixture; no 3D world rendered.','Escape dismisses a completed failed load, not cancellation during active loading.','One V-Sync driver warning retained.']}
 review=('The native journey completed 23 manual and 15 automatic original frames, 98 XTest events, actual Quit and cleanup exit 0 in 212.330 seconds. Full engine logs contain no warnings or errors; runtime source, imported payloads, frozen cache inventory and copied seed source hashes remained unchanged.\n\nW1 directly inspected title, staged Sun outcome and returned settings originals. The title/action remains legible with the whole hero; the outcome has the focused Restart action and truthful final cores; returned settings retain 2.50× sensitivity and 0% volume with a visible Done footer. W6 independently inspected all 38 originals and completed a 69-check raw-capture audit plus ten import/owner checks; its separate report owns that broader review.\n\nSix explicit authority fixture actions produced three outcomes and resets. Four manual names mark STAGED outcomes/terminal state. These are not victories played from a full match. Auto filenames are trigger names: auto-loading-2, -4 and -5 actually record constructing, as their pixels and sidecars show.\n\nThis is warm-cache Forward+ llvmpipe using the unmodified public 4.6.3 template-debug engine, not a shipped engine or GPU performance qualification. Native window is 960×600; scene framebuffer originals are 960×540. The raw artifacts and exact observer/plan/runner are preserved here; source code and complete source/import hashes allow reproduction with retained repository assets. Do not treat this as a self-contained packaged game.\n') if kind=='journey' else ('The isolated boot recovery completed five manual and three automatic original frames, actual Quit and cleanup exit 0 in 3.639 seconds. Native Return retries the missing destination; Escape dismisses the failed loader into a usable boot menu; pointer Retry reopens the error and pointer Quit exits. The complete tiny fixture deliberately omits the target courtyard.\n\nW1 directly inspected initial error, usable recovery and return-to-boot originals. Error copy, Retry/Back and the boot Retry/Quit controls are contained and readable; the visible focus ring remains contained. The full log retains one unsupported V-Sync-mode warning and no errors. Source/import checks remained unchanged.\n\nThis is installed-editor Compatibility llvmpipe, 960×600, CPU0 with one rendering thread. It proves recovery after a failed load and native Quit; it does not prove cancellation while loading, 3D rendering, physical-device performance or listening quality. Exact source/import closure is archived in source/fixture.tar.gz.\n')
 (out/'REVIEW.md').write_text(review)
 receipt['artifacts']=[{'path':str(p.relative_to(out)),'sha256':h(p),'bytes':p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file()]
 write(out/'receipt.json',receipt)
 print(json.dumps({'archive':str(out),'receipt_sha256':h(out/'receipt.json'),'review_sha256':h(out/'REVIEW.md'),'artifacts':len(receipt['artifacts']),'bytes':sum(r['bytes'] for r in receipt['artifacts']),'warnings':warnings,'errors':errors}))
