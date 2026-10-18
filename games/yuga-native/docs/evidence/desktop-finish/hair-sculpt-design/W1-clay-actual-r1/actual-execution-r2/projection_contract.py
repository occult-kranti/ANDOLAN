"""Read-only evaluated clay + locked head/crown context projection."""
import bpy
from bpy_extras.object_utils import world_to_camera_view
CASES=['front','anatomical-left-profile','rear','cast-angle-authoring']
def points(scene):
    hair=bpy.data.objects['EDITABLE_WholeHair_CoarseClay']
    evaluated=hair.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=evaluated.to_mesh()
    h=[evaluated.matrix_world@v.co for v in mesh.vertices];evaluated.to_mesh_clear()
    context=[]
    materials=['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil','Worked warm gold','Recessed antique gold','Polished sapphire','Swept black hair']
    for obj in bpy.data.objects:
        if obj.type!='MESH'or not obj.name.startswith('LOCKED_')or obj.get('source_material_name')not in materials:continue
        # Source-space head/crown/brows/ear region, not intentionally cropped
        # shoulders or distant quiver/bow. Rigid mapping is x,-z,y.
        context.extend(obj.matrix_world@v.co for v in obj.data.vertices if v.co.z>=1.65 and abs(v.co.x)<=.13 and abs(v.co.y)<=.20)
    assert h and context
    return h,context
def bounds(scene,camera,vertices):
    projected=[world_to_camera_view(scene,camera,v)for v in vertices]
    return [[min(v[i]for v in projected)for i in range(3)],[max(v[i]for v in projected)for i in range(3)]]
def fits(b,margin=.015):return b[0][0]>=margin and b[1][0]<=1-margin and b[0][1]>=margin and b[1][1]<=1-margin and b[0][2]>.01
def census(scene,hair,context):
    return {case:dict(hair=bounds(scene,bpy.data.objects['VIEW_'+case],hair),head_context=bounds(scene,bpy.data.objects['VIEW_'+case],context))for case in CASES}
