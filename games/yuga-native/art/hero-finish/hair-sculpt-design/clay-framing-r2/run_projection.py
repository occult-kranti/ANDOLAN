"""Bounded no-render fresh-load/4-camera projection executor."""
from pathlib import Path
import json,os,subprocess,time,hashlib
base=Path(__file__).resolve().parent;output=base/'projection-preflight-r2'
assert not output.exists()
blend=base/'whole-hair-clay-profile-r2.blend';helper=base/'capture_clay_profile_r2.py'
source=Path('/workspace/scratch/yuga-hair-clay-r1/clay-save-r1/whole-hair-clay.blend')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=dict(successor_blend=sha(blend),successor_helper=sha(helper),original_blend=sha(source))
cmd=['blender','--background',str(blend),'--threads','1','--python-exit-code','1','--python',str(base/'verify_saved_scene.py'),'--python',str(helper),'--','--output',str(output),'--preflight']
env=os.environ.copy();env['TMPDIR']=str(base/'temp');started=time.monotonic()
with(base/'preflight.log').open('w')as log:
    try:p=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=45);code=p.returncode
    except subprocess.TimeoutExpired:code=124
record=dict(scope='Fresh-loaded lens-only successor semantics and four-view projection, no rendering/import/export.',
    command=cmd,exit_code=code,elapsed_seconds=time.monotonic()-started,hashes_before=before,
    hashes_after=dict(successor_blend=sha(blend),successor_helper=sha(helper),original_blend=sha(source)),
    png_count=len(list(output.glob('*.png'))) if output.exists() else 0)
(base/'preflight-execution.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record));print((base/'preflight.log').read_text()[-6500:]);raise SystemExit(code)
