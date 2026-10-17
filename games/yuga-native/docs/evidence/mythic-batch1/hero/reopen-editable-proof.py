import bpy,json,pathlib,hashlib
p=pathlib.Path('/workspace/ANDOLAN/games/yuga-native/art/production/reconstruction-rama.blend')
m=p.with_name('reconstruction-editable.json'); d=json.loads(m.read_text())
assert hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256']
assert len(bpy.data.images)==15 and all(i.packed_file and min(i.size)>0 for i in bpy.data.images)
assert len(bpy.data.actions)==9 and sum(len(a.bones) for a in bpy.data.armatures)==164
assert bpy.context.scene['YUGA_RUNTIME_GLB_SHA256']=='3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc'
d['reopenedVerification']={'passed':True,'imagesPacked':15,'bones':164,'actions':9,'artifactSha256':d['sha256']}
m.write_text(json.dumps(d,indent=2)+'\n')
print('R2_RECONSTRUCTED_SOURCE_REOPEN_PASS')
