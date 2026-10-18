from pathlib import Path
import json,hashlib,shutil,tarfile,gzip
import numpy as np
from PIL import Image
R=Path('/workspace/ANDOLAN/games/yuga-native');E=R/'docs/evidence/desktop-finish';B=Path('/tmp/yuga-desktop-boot-dedup-native-r1');OLD=Path('/tmp/yuga-desktop-boot-recovery-r1');S=Path('/tmp/yuga-desktop-boot-dedup-r1/source');O=E/'D02/W1-boot-dedup-native-r1';O.mkdir(parents=True,exist_ok=False)
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b);assert h(a)==h(b)
r=json.loads((B/'run.json').read_text());prior=json.loads((OLD/'run.json').read_text());assert r['complete']and r['verified_exit_code']==0 and r['cleanup_exit']==0 and r['source_unchanged']
source_delta=[k for k in r['source_sha256']if r['source_sha256'][k]!=prior['source_sha256'].get(k)];assert source_delta==['scripts/loading_presentation.gd'];assert set(r['source_sha256'])==set(prior['source_sha256'])
for f in B.iterdir():
 if f.is_file():cp(f,O/('originals' if f.suffix=='.png'or f.with_suffix('.png').exists()else'raw')/f.name)
for n in ['run.py','observer.gd','board.gd','boot-recovery-plan.json']:cp(S/'tools/ui-campaign'/n,O/'tools'/n)
cp(S/'ui-source-freeze.json',O/'source/ui-source-freeze.json');cp(E/'D02/W6-copy-dedup/capture-inputs.json',O/'source/capture-inputs.json');cp(S/'scripts/loading_presentation.gd',O/'source/loading_presentation.gd')
with (O/'source/fixture.tar.gz').open('wb')as out:
 with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0)as gz:
  with tarfile.open(fileobj=gz,mode='w')as tf:
   for f in sorted((B/'fixture').rglob('*')):
    if f.is_file():
     info=tf.gettarinfo(str(f),arcname=str(f.relative_to(B/'fixture')));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
     with f.open('rb')as src:tf.addfile(info,src)
comparison=[]
for p in sorted(B.glob('*.png')):
 a=OLD/p.name;z=np.abs(np.array(Image.open(a)).astype(np.int16)-np.array(Image.open(p)).astype(np.int16));comparison.append({'file':p.name,'before_sha256':h(a),'after_sha256':h(p),'changed_pixels':int(np.any(z,axis=-1).sum()),'max_channel_delta':int(z.max())})
(O/'comparison.json').write_text(json.dumps({'source_delta':source_delta,'before_receipt':'../W1-boot-recovery-r1/receipt.json','after_source_sha256':r['source_sha256']['scripts/loading_presentation.gd'],'images':comparison},indent=2)+'\n')
cp(Path(__file__),O/'tools/archive.py')
(O/'REVIEW.md').write_text('''The duplicate generic guidance is removed from the missing-scene error card. W1 directly opened the new initial-error original: the destination-specific instruction remains once, with Retry/Back and a contained focus ring. The already-failed loader can still be dismissed into the usable boot screen.\n\nThe same native plan completed five manual plus three queued automatic originals, actual Quit and cleanup exit0, in3.574 seconds. The27-file fixture closure differs from the prior actual run only in loading_presentation.gd (a01b5289…). Exact plan, controller, callbacks, font imports and runner remain fixed. Source identity remained unchanged during capture. Full logs retain one expected unsupported V-Sync-mode warning, with no errors.\n\nThis is the isolated960×600 Compatibility fixture using the installed editor, fresh XDG and CPU0/LP1, not a3D world render or process-relaunch test. The missing courtyard is deliberate. Escape is dismissal after a completed failed load, not in-flight cancellation. Both old and new original takes are retained; no broad graphics or hardware-performance acceptance is implied.\n''')
lines=(B/'godot.log').read_text().splitlines();warnings=[x for x in lines if x.startswith('WARNING:')];errors=[x for x in lines if x.startswith(('ERROR:','SCRIPT ERROR:'))];assert not errors
receipt={'schema':1,'passed':True,'manual_originals':5,'automatic_originals':3,'actual_exit':r['verified_exit_code'],'cleanup_exit':r['cleanup_exit'],'elapsed_seconds':r['finished_unix']-r['started_unix'],'source_delta':source_delta,'source_unchanged':True,'engine_sha256':r['engine_sha256'],'warnings':warnings,'errors':errors,'source_input_receipt_sha256':h(E/'D02/W6-copy-dedup/capture-inputs.json'),'scope':'Duplicate error guidance removed; native Retry/recovery dismissal/Quit preserved. No in-flight cancellation claim.','artifacts':[{'path':str(p.relative_to(O)),'sha256':h(p),'bytes':p.stat().st_size}for p in sorted(O.rglob('*'))if p.is_file()]};(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'archive':str(O),'receipt':h(O/'receipt.json'),'review':h(O/'REVIEW.md'),'artifacts':len(receipt['artifacts']),'pixel_changes':{x['file']:x['changed_pixels']for x in comparison}}))
