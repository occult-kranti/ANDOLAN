import bpy,json
bpy.ops.wm.open_mainfile(filepath='/tmp/yuga-layered-offline.blend',load_ui=False)
s=bpy.context.scene
assert not bpy.data.libraries
files=[im for im in bpy.data.images if im.users and im.source in ('FILE','TILED')]
assert all(im.packed_files for im in files)
for im in files:
 assert len(im.pixels)>=4
rig=next(o for o in s.objects if o.type=='ARMATURE')
assert len(rig.pose.bones)==167
assert len(bpy.data.collections['Ability layers · editable'].objects)==93
s.frame_set(271)
s.render.engine='CYCLES'
s.cycles.samples=2
s.render.threads_mode='FIXED';s.render.threads=1
s.render.resolution_x=320;s.render.resolution_y=180;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
s.render.filepath='/tmp/yuga-layered-offline.png'
bpy.ops.render.render(write_still=True)
print('PACKED',len(files),'JOINTS',len(rig.pose.bones),'FX',93,flush=True)
