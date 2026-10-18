"""Verify fresh-loaded framing successor before projection; no edits."""
from pathlib import Path
import json,sys
import bpy
BASE=Path('/workspace/scratch/yuga-hair-clay-r1/framing-r3')
sys.path.insert(0,str(BASE))
from scene_semantics import snapshot,differences,sha
assert sha(Path(bpy.data.filepath))=='71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f'
expected=json.loads((BASE/'semantic-after.json').read_text())
# Compare the same JSON representation on each side. The preserved first
# verifier compared loaded JSON lists with equal in-memory tuples.
actual=json.loads(json.dumps(snapshot(),sort_keys=True,separators=(',',':')))
serialization=[]
# Root-authorized persistent scene comparison: save purges this unused factory
# startup material, and session_uid is an explicitly nonpersistent process ID.
if 'Material' in expected['materials'] and 'Material' not in actual['materials']:
    orphan=expected['materials']['Material']
    assert orphan['properties']['users']==0
    assert all('Material' not in mesh['materials']for mesh in expected['meshes'].values())
    serialization.append(dict(field='materials.Material',effect='Unreferenced factory material omitted on serialization',users=0))
    del expected['materials']['Material']
def persistent(value,path=''):
    if isinstance(value,dict):
        return {key:persistent(item,path+'.'+key)for key,item in value.items()if key!='session_uid'}
    if isinstance(value,list):return [persistent(item,path)for item in value]
    return value
delta=differences(persistent(expected),persistent(actual))
report=dict(scope='Read-only fresh-loaded saved successor persistent scene comparison, before projection helper.',passed=not delta,differences=delta,serialization_notes=serialization,excluded_process_only_field='session_uid',expected_semantic_sha256=sha(BASE/'semantic-after.json'),saved_blend_sha256=sha(Path(bpy.data.filepath)))
(BASE/'fresh-load-semantics.json').write_text(json.dumps(report,indent=2)+'\n')
assert not delta,delta
print('FRESH_LOADED_SCENE_SEMANTICS_EXACT',flush=True)
