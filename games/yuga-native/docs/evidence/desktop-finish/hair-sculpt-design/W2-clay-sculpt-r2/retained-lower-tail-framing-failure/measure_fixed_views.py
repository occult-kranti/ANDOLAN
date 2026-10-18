from pathlib import Path
import sys,json
import bpy
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,'/workspace/scratch/yuga-hair-clay-r2/render-preparation-r1')
from projection_contract import points,bounds,CASES
scene=bpy.context.scene;hair,context=points(scene);rows=[]
for name in CASES:
 cam=bpy.data.objects['VIEW_'+name];p=[world_to_camera_view(scene,cam,x)for x in hair];i=min(range(len(p)),key=lambda i:p[i].y)
 rows.append(dict(id=name,hair_bounds=bounds(scene,cam,hair),head_bounds=bounds(scene,cam,context),lowest_evaluated_point_blender=list(hair[i]),lowest_source_space=[hair[i].x,hair[i].z,-hair[i].y]))
out=Path('/workspace/scratch/yuga-hair-clay-r2/fixed-view-tail-bounds.json');out.write_text(json.dumps(dict(scope='Read-only actual evaluated clay bounds; fixed cameras; no render/save.',views=rows),indent=2)+'\n')
print(json.dumps(rows))
