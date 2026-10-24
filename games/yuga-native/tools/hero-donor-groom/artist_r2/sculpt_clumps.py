"""Second artist pass: reshape nine existing clean nape clumps, no new mesh.

Shape-key authoring leaves all original topology/material/skin data available.
Build-only is the default. --render requires a separately granted heavy lane.
"""
import argparse,hashlib,json,math,struct,sys,time
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'artist_r1'))
from sculpt_existing import sha,smooth,aim,positions,uv_digest

def curve(values,t):
 t=max(0.,min(1.,t));index=min(4,int(t*5));f=smooth(0,1,t*5-index);return Vector(values[index]).lerp(Vector(values[index+1]),f)
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--ancestor-scene',type=Path,required=True);p.add_argument('--ancestor-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--render',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);parent=json.loads(a.ancestor_report.read_text());assert sha(a.source)==parent['source_sha256'] and sha(a.ancestor_scene)==parent['scene']['sha256'];a.output.mkdir(parents=True,exist_ok=False);start=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(a.ancestor_scene.resolve()));scene=bpy.context.scene;body=bpy.data.objects['APPROVED BASELINE Rama'];old=bpy.data.objects['W3 posterior-hair sculpt CANDIDATE'];old_data=old.data;bpy.data.objects.remove(old,do_unlink=True)
 if old_data.users==0:bpy.data.meshes.remove(old_data)
 cage=bpy.data.objects.get('EDITABLE lower-hair sculpt cage')
 if cage is not None:bpy.data.objects.remove(cage,do_unlink=True)
 body.name='W3 existing-clump sculpt';body.hide_render=False;mesh=body.data;hair_mats={i for i,m in enumerate(mesh.materials) if m.name=='Swept black hair'};hair_ids={v for f in mesh.polygons if f.material_index in hair_mats for v in f.vertices};members=defaultdict(list);adj=defaultdict(set)
 for i in hair_ids:members[tuple(mesh.vertices[i].co)].append(i)
 for face in mesh.polygons:
  if face.material_index not in hair_mats:continue
  pp=[tuple(mesh.vertices[i].co) for i in face.vertices]
  for x,y in [(pp[0],pp[1]),(pp[1],pp[2]),(pp[2],pp[0])]:adj[x].add(y);adj[y].add(x)
 remaining=set(members);clumps=[]
 while remaining:
  todo=[remaining.pop()];points=[]
  while todo:
   point=todo.pop();points.append(point)
   for other in adj[point]:
    if other in remaining:remaining.remove(other);todo.append(other)
  lo=[min(p[j] for p in points) for j in range(3)];hi=[max(p[j] for p in points) for j in range(3)]
  if lo[2]<1.61 and hi[2]>1.79 and hi[1]>.13:clumps.append({'points':points,'lo':lo,'hi':hi,'ids':sorted(i for p in points for i in members[p])})
 clumps.sort(key=lambda c:(c['lo'][0]+c['hi'][0])*.5);assert len(clumps)==9,('Unexpected source clump set',len(clumps));base=body.shape_key_add(name='Basis');sculpt=body.shape_key_add(name='W3 two unequal nape flow families');sculpt.value=0.;original_uv=uv_digest(mesh);all_ids=list(range(len(mesh.vertices)));original_positions=positions(mesh,all_ids)
 left_path=[(0,0),(-.014,.004),(-.022,.016),(.016,.025),(.025,.008),(.008,.003)];right_path=[(0,0),(.008,-.003),(.022,.003),(.008,.013),(-.018,.008),(-.025,.001)];widths=[.85,.80,.78,.88,.90,.78,.75,.86,.84];depths=[1.10,1.16,1.15,1.12,1.08,1.16,1.18,1.12,1.10];twists=[8,16,22,-8,12,-18,-26,-12,-8];raises=[.020,.008,.050,0,.030,.065,.035,.060,.040];records=[];selected=set()
 for rank,clump in enumerate(clumps):
  group=body.vertex_groups.new(name='W3 editable original nape '+str(rank));group.add(clump['ids'],1.,'REPLACE');center=Vector(((clump['lo'][0]+clump['hi'][0])*.5,(clump['lo'][1]+clump['hi'][1])*.5,0));left=rank<5;path=left_path if left else right_path;max_move=0.;moved=[]
  for i in clump['ids']:
   co=base.data[i].co;t=(clump['hi'][2]-co.z)/(clump['hi'][2]-clump['lo'][2]);weight=smooth(.10,.30,t)
   if weight==0:continue
   phase=max(0.,min(1.,t+.035*((rank%5)-2)*math.sin(math.pi*t)));shift=curve(path,phase);x=(co.x-center.x)*(1+(widths[rank]-1)*weight);y=(co.y-center.y)*(1+(depths[rank]-1)*weight);angle=math.radians(twists[rank])*math.sin(math.pi*t)*weight;new=Vector((center.x+x*math.cos(angle)-y*math.sin(angle)+shift.x*weight,center.y+x*math.sin(angle)+y*math.cos(angle)+shift.y*weight,co.z+raises[rank]*weight*t*t));sculpt.data[i].co=new;distance=(new-co).length;max_move=max(max_move,distance);selected.add(i)
   if distance>1e-8:moved.append(i)
  records.append({'rank':rank,'family':'dominant-left' if left else 'shorter-right','source_bounds_min':clump['lo'],'source_bounds_max':clump['hi'],'source_vertex_ids':clump['ids'],'source_unique_positions':len(clump['points']),'width_scale':widths[rank],'depth_scale':depths[rank],'twist_degrees':twists[rank],'terminal_raise_metres':raises[rank],'delta_station_xy':path,'actual_max_delta':max_move,'changed_vertices':len(moved)})
 protected=sorted(set(all_ids)-selected);assert all(tuple(base.data[i].co)==tuple(sculpt.data[i].co) for i in protected);assert positions(mesh,all_ids)==original_positions and uv_digest(mesh)==original_uv
 # Neutral paired lighting is reduced to expose sculpt ridges; no source
 # material is changed and both R2 variants use this exact same studio.
 scene.view_settings.exposure=-.7
 for name,energy in [('Fixed large key',260),('Fixed fill',120),('Fixed rear rim',320)]:bpy.data.objects[name].data.energy=energy
 target=Vector(parent['render']['target']);views=[('front',(1.2,-3,.3)),('profile',(3,0,.25)),('rear',(-1.2,3,.3)),('oblique',(-2.5,2.5,.2))];cameras={}
 for view,offset in views:
  data=scene.camera.data.copy();camera=bpy.data.objects.new('R2 locked '+view,data);scene.collection.objects.link(camera);camera.location=target+Vector(offset);aim(camera,target);cameras[view]=camera
 scene.camera=cameras['front'];sculpt.value=1.;body['source_sha256']=parent['source_sha256'];body['scope']='R2 actual existing-clump shape-key sculpt; no canonical promotion';scene_path=a.output/'rama-existing-nape-clumps.blend';bpy.ops.wm.save_as_mainfile(filepath=str(scene_path.resolve()));report={'schema_version':1,'scope':'Direct sculpt of nine existing closed nape components; no new hair primitives, source cut, body or crown edit.','source_sha256':parent['source_sha256'],'ancestor_scene_sha256':sha(a.ancestor_scene),'script_sha256':sha(__file__),'clump_count':len(records),'clumps':records,'source_vertices':len(mesh.vertices),'source_faces':len(mesh.polygons),'selected_vertex_ids':sorted(selected),'protected_vertex_count':len(protected),'protected_shape_key_positions_exact':True,'basis_positions_unchanged':positions(mesh,all_ids)==original_positions,'uv_unchanged':uv_digest(mesh)==original_uv,'scene':{'path':str(scene_path),'bytes':scene_path.stat().st_size,'sha256':sha(scene_path)},'render':{'threads':2,'samples':32,'resolution':[640,800],'exposure':-.7,'target':list(target),'lighting':'Reduced from R1 for ridge readability, same for BOTH R2 variants'},'frames':[],'runtime_promoted':False,'artistic_decision':'pending actual four-view originals','positive_completion':False}
 (a.output/'source-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
 if a.render:
  for view,offset in views:
   scene.camera=cameras[view]
   for variant,value in [('baseline',0.),('candidate',1.)]:
    sculpt.value=value;path=a.output/(view+'-'+variant+'.png');scene.render.filepath=str(path.resolve());begin=time.monotonic();bpy.ops.render.render(write_still=True);report['frames'].append({'path':path.name,'view':view,'variant':variant,'camera_offset':offset,'sha256':sha(path),'bytes':path.stat().st_size,'seconds':time.monotonic()-begin})
  report['positive_completion']=len(report['frames'])==8
 report['elapsed_seconds']=time.monotonic()-start;(a.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('W3_CLUMP_SCULPT='+json.dumps({k:v for k,v in report.items() if k not in ['clumps','selected_vertex_ids']},separators=(',',':')))
if __name__=='__main__':main()
