"""Verify fresh-loaded framing successor before projection; no edits."""
from pathlib import Path
import json,sys
import bpy
BASE=Path('/workspace/scratch/yuga-hair-clay-r1/profile-framing-r2')
sys.path.insert(0,str(BASE))
from scene_semantics import snapshot,differences,sha
assert sha(Path(bpy.data.filepath))=='538180be0f2eee096535c4414909c8d4543622b53c334fc046e7ac8f3b779cbb'
expected=json.loads((BASE/'semantic-after.json').read_text())
# Compare the same JSON representation on each side. The preserved first
# verifier compared loaded JSON lists with equal in-memory tuples.
actual=json.loads(json.dumps(snapshot(),sort_keys=True,separators=(',',':')))
delta=differences(expected,actual)
report=dict(scope='Read-only fresh-loaded saved successor semantic comparison, before projection helper.',passed=not delta,differences=delta,expected_semantic_sha256=sha(BASE/'semantic-after.json'),saved_blend_sha256=sha(Path(bpy.data.filepath)))
(BASE/'fresh-load-semantics.json').write_text(json.dumps(report,indent=2)+'\n')
assert not delta,delta
print('FRESH_LOADED_SCENE_SEMANTICS_EXACT',flush=True)
