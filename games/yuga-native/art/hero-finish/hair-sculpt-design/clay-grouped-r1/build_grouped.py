"""C8 broad closed elliptical clump study, fixed rest-space references.

Fresh authoring geometry only. No cap sheet, C7 cords, source helper/photo,
UV, material edit, weights, GLB, rig change, raster or canonical promotion.
"""
import argparse,gzip,hashlib,json,math,shutil,sys
from pathlib import Path
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'clay-framing-r3'))
from scene_semantics import snapshot,differences
from projection_contract import points,census,fits
HAIR='EDITABLE_WholeHair_CoarseClay'
PARENT='0acb259a6a5b1c538fa050cc5b42125e31399ed0a8ea41eaae33b24b7ac84b07'
ORIGIN=Vector((0,1.765,.045))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def js(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def gz(p,x):
 with gzip.GzipFile(filename=str(p),mode='wb',mtime=0)as f:f.write(json.dumps(x,separators=(',',':')).encode())
def gltf(v):return Vector((v.x,v.z,-v.y))
def blender(v):return (v[0],-v[2],v[1])
def tree(objects):
 vv=[];ff=[]
 for obj in objects:
  first=len(vv);vv.extend(gltf(obj.matrix_world@v.co)for v in obj.data.vertices);ff.extend([[i+first for i in f.vertices]for f in obj.data.polygons])
 return BVHTree.FromPolygons(vv,ff,all_triangles=False)
def curve(controls,t):
 p=[Vector(v)for v in controls];u=min(len(p)-1-1e-9,max(0,t)*(len(p)-1));i=int(u);u-=i
 a,b,c,d=p[max(0,i-1)],p[i],p[min(i+1,len(p)-1)],p[min(i+2,len(p)-1)]
 return .5*((2*b)+(-a+c)*u+(2*a-5*b+4*c-d)*u*u+(-a+3*b-3*c+d)*u*u*u)

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
 out=args.output;assert not out.exists()and out.is_absolute()and out.is_relative_to(Path('/workspace/scratch'))
 assert not bpy.context.preferences.filepaths.use_scripts_auto_execute
 assert sha(bpy.data.filepath)==PARENT and shutil.disk_usage('/workspace').free>=500*1024**2
 before=snapshot();clay=bpy.data.objects[HAIR].data.materials[0]
 skin=tree([bpy.data.objects[n]for n in ['LOCKED_1_0_Rama warm skin','LOCKED_2_11_Rama warm skin']])
 canonical=tree([bpy.data.objects['LOCKED_2_0_Swept black hair']])
 # Use an outer-to-inner ray so an overlapping inner skin cannot bury hair.
 def support(direction):
  d=Vector(direction).normalized();hit,normal,_,_=skin.ray_cast(ORIGIN+d*.45,-d,.45)
  assert hit is not None,('outer scalp ray miss',list(d))
  return hit,d
 posterior_fallbacks=[]
 def posterior(x,y):
  hit,_,_,_=skin.ray_cast(Vector((x,y,-.40)),Vector((0,0,1)),.60)
  if hit is None:
   # Wide falling clumps may sit beside the neck silhouette. There is no
   # skin to clip there; continue the nearby posterior envelope explicitly.
   for factor in [.90,.75,.50,.25,0]:
    hit,_,_,_=skin.ray_cast(Vector((x*factor,y,-.40)),Vector((0,0,1)),.60)
    if hit is not None:posterior_fallbacks.append((x,y,factor));break
  assert hit is not None,('posterior ray missed',x,y)
  return hit.z
 bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=16,v_segments=10,radius=1)
 bm.verts.ensure_lookup_table();bm.verts.index_update();unit=[v.co.copy()for v in bm.verts];unit_faces=[[v.index for v in f.verts]for f in bm.faces];bm.free()
 vv=[];ff=[];groups={};records=[]
 def add(name,verts,recipe):
  start=len(vv);vv.extend([list(v)for v in verts]);ff.extend([[start+i for i in f]for f in unit_faces]);groups[name]=list(range(start,len(vv)));records.append(dict(name=name,recipe=recipe))
 def scalp(name,controls,width,depth,relief=.006):
  verts=[]
  for p in unit:
   t=(p.z+1)/2;center=curve(controls,t);hit,d=support(center-ORIGIN)
   eps=.002;ta=curve(controls,max(0,t-eps));tb=curve(controls,min(1,t+eps));tangent=(tb-ta).normalized()
   across=tangent.cross(d).normalized()
   q=hit+d*relief+across*(p.x*width)
   # Seat every lateral vertex independently, retaining elliptical depth.
   sh,sd=support(q-ORIGIN)
   verts.append(sh+sd*(relief+p.y*depth))
  add(name,verts,dict(kind='closed broad rounded scalp ellipse',controls=controls,width_m=width,depth_m=depth,outer_skin_relief_m=relief))
 for i,x in enumerate([-.075,-.050,-.024,.003,.030,.056,.079]):
  controls=[[x,1.792,.132-.20*abs(x)],[x*.87+.005,1.837,.093],[x*.62+.009,1.852,.028],[x*.32+.006,1.818,-.060],[x*.12+.003,1.763,-.073]]
  scalp('Broad crown sweep '+str(i),controls,[.0285,.0325,.0355,.0365,.0355,.0325,.0285][i],[.009,.011,.012,.013,.012,.011,.009][i])
 for side in [-1,1]:
  for i,(height,front,back)in enumerate([(1.796,.106,-.065),(1.777,.081,-.071),(1.753,.035,-.075)]):
   controls=[[side*.074,height,front],[side*.097,height+.006,front*.45],[side*.093,height-.010,-.026],[side*.067,height-.028,back],[side*.038,height-.035,back-.004]]
   scalp(('Left'if side<0 else'Right')+' temple-occiput '+str(i),controls,.033 if i<2 else .030,.010,.005)
 for i,x in enumerate([-.062,-.031,.002,.035,.065]):
  controls=[[x*.6,1.829,-.054],[x,1.788,-.080],[x*.94+.006,1.743,-.085],[x*.75+.008,1.695,-.071]]
  scalp('Overlapping rear volume '+str(i),controls,.033,.012,.006)
 # Three solid interlocking lobes, deliberately low, oblique and filled.
 for i,(center,axes,angle)in enumerate([((-.010,1.859,-.044),(.034,.020,.029),-22),((.003,1.878,-.044),(.029,.017,.025),25),((-.014,1.871,-.021),(.023,.019,.020),-35)]):
  verts=[];a=math.radians(angle)
  for p in unit:
   x,y,z=p.x*axes[0],p.y*axes[1],p.z*axes[2]
   x,y=math.cos(a)*x-math.sin(a)*y,math.sin(a)*x+math.cos(a)*y
   q=Vector((center[0]+x,center[1]+y,center[2]+z));dy=abs(q.y-1.868)
   if dy<.010:
    radius=math.hypot(q.x,q.z+.040);limit=.0295+.15*dy
    if radius>limit:q.x*=limit/radius;q.z=-.040+(q.z+.040)*limit/radius
   verts.append(q)
  add('Filled oblique gather lobe '+str(i),verts,dict(kind='solid filled folded gather lobe',center=center,axes_m=axes,oblique_degrees=angle,tie_band_radius_control_m=.0295))
 falls=[(-.066,1.795,1.615,.026,.015,.012),(-.039,1.803,1.565,.031,.017,-.014),(-.009,1.808,1.535,.033,.018,.014),(.022,1.802,1.557,.032,.017,-.012),(.051,1.790,1.595,.028,.016,.012),(.071,1.775,1.633,.024,.015,-.010)]
 fall_probe=[]
 for i,(cx,root,tip,width,depth,bend)in enumerate(falls):
  verts=[]
  for p in unit:
   t=(p.z+1)/2;cross=math.sqrt(max(0,1-p.z*p.z));yy=root+(tip-root)*t
   centerx=cx+bend*4*t*(1-t)*(1-2*t);xx=centerx+p.x*width*(1-.32*t)
   back=posterior(xx,yy)
   # Every surface point is outside the actual posterior anatomy. Rounded
   # thickness survives seating; unlike C7 no side of a fall can be buried.
   zz=back-(.017+.008*cross+p.y*depth)
   verts.append(Vector((xx,yy,zz)))
  add('Exposed asymmetric S fall '+str(i),verts,dict(kind='closed volumetric unequal S fall',center_x=cx,root_y=root,tip_y=tip,width_m=width,depth_m=depth,bend_m=bend,posterior_front_surface_clearance_target_m=.002,pre_save_subdivision_margin_m=.005))
  fall_probe.append(dict(name=records[-1]['name'],minimum_cage_posterior_gap_m=min(posterior(v.x,v.y)-v.z for v in verts)))
 allowed=[]
 for old in list(bpy.data.objects):
  if old.name!=HAIR and not old.name.startswith('SOURCE_LOFT_'):continue
  mesh=old.data;allowed+=['.objects.'+old.name,'.meshes.'+mesh.name];bpy.data.objects.remove(old,do_unlink=True);bpy.data.meshes.remove(mesh)
 mesh=bpy.data.meshes.new(HAIR);mesh.from_pydata([blender(v)for v in vv],[],ff);mesh.update()
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bad=sum(not e.is_manifold for e in bm.edges);assert bad==0;bm.to_mesh(mesh);bm.free()
 obj=bpy.data.objects.new(HAIR,mesh);bpy.context.scene.collection.objects.link(obj);mesh.materials.append(clay)
 for poly in mesh.polygons:poly.use_smooth=True
 for name,ids in groups.items():obj.vertex_groups.new(name=name).add(ids,1,'REPLACE')
 obj['role']='C8 broad overlapping closed volumes; original new coarse authoring geometry'
 obj['not_runtime']=True;obj['C7_geometry_reused']=False
 sub=obj.modifiers.new('Coarse volume subdivision','SUBSURF');sub.levels=1;sub.render_levels=1
 allowed+=['.objects.'+HAIR,'.meshes.'+mesh.name];bpy.context.view_layer.update()
 after=snapshot();delta=differences(before,after)
 unexpected=[row[0]for row in delta if not any(row[0]==q or row[0].startswith(q+'.')for q in allowed)and not row[0].endswith('.properties.users')];assert not unexpected,unexpected
 h,c=points(bpy.context.scene);projection=census(bpy.context.scene,h,c);assert all(fits(b)for row in projection.values()for b in row.values()),projection
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();evalv=[gltf(v.co)for v in em.vertices];evalf=[list(f.vertices)for f in em.polygons];ht=BVHTree.FromPolygons(evalv,evalf,all_triangles=False)
 coverage=[]
 for i in range(72):
  theta=i/72*2*math.pi;angle=abs((theta+math.pi)%(2*math.pi)-math.pi)
  floor=.48 if angle<.70 else (.03 if angle<1.90 else -.48)
  for j in range(14):
   phi=floor+(1.48-floor)*(j+.5)/14;d=Vector((math.sin(theta)*math.cos(phi),math.sin(phi),math.cos(theta)*math.cos(phi)))
   sh,_=support(d);hh,_,_,_=ht.ray_cast(ORIGIN+d*.45,-d,.45);ch,_,_,_=canonical.ray_cast(ORIGIN+d*.45,-d,.45)
   relief=(hh-sh).dot(d)if hh is not None else None
   coverage.append(dict(theta=theta,phi=phi,head_surface_gltf=list(sh),covered=relief is not None and -.0005<=relief<=.065,radial_hair_relief_m=relief,canonical_hair_relief_m=(ch-sh).dot(d)if ch is not None else None))
 exposure=[]
 for group in obj.vertex_groups:
  if not group.name.startswith('Exposed asymmetric S fall '):continue
  ids=[v.index for v in em.vertices if any(g.group==group.index and g.weight>.5 for g in v.groups)]
  gaps=[];outside=0
  for index in ids:
   v=evalv[index];hit,_,_,_=skin.ray_cast(Vector((v.x,v.y,-.40)),Vector((0,0,1)),.60)
   if hit is None:outside+=1
   else:gaps.append(hit.z-v.z)
  exposure.append(dict(name=group.name,evaluated_vertices=len(ids),outside_anatomy_side_silhouette_vertices=outside,minimum_posterior_gap_m=min(gaps),maximum_posterior_gap_m=max(gaps),all_vertices_exposed=min(gaps)>.001))
 out.mkdir(parents=True);gz(out/'source-cage.json.gz',dict(vertices=vv,faces=ff,groups=groups));gz(out/'semantic-before.json.gz',before);gz(out/'semantic-after.json.gz',after);gz(out/'evaluated-clay.json.gz',dict(vertices=[list(v)for v in evalv],faces=evalf));ev.to_mesh_clear()
 js(out/'shape-design.json',dict(parts=records,source_geometry='New original closed coarse ellipses; no source BraidStrands mesh, C7 cords, smooth cap, connector or fine grooves',combined_skin_outermost_rays=True,canonical_hair_used_as_envelope_reference=True))
 js(out/'coverage-and-exposure.json',dict(scope='Finite outer-skin ray coverage and per-vertex evaluated-fall exposure; eligibility only, no artistic acceptance. Side points with no anatomy ray use nearby posterior envelope in construction and are reported separately from actual skin-gap probes.',coverage_count=len(coverage),covered_count=sum(x['covered']for x in coverage),coverage_fraction=sum(x['covered']for x in coverage)/len(coverage),rays=coverage,fall_cage_probes=fall_probe,evaluated_fall_exposure=exposure,construction_outside_anatomy_fallback_count=len(posterior_fallbacks),all_six_evaluated_falls_exposed=all(x['all_vertices_exposed']for x in exposure)))
 assert all(x['all_vertices_exposed']for x in exposure),exposure
 js(out/'projection.json',dict(passed=True,views=projection))
 js(out/'construction-receipt.json',dict(parent_sha256=PARENT,builder_sha256=sha(__file__),vertices=len(vv),faces=len(ff),closed_components=len(records),nonmanifold_edges=bad,protected_reference_changes=unexpected,projection_passed=True,source_coverage_fraction=sum(x['covered']for x in coverage)/len(coverage),all_six_evaluated_falls_exposed=True,subdivision=1,no_render=True,no_export=True,actual_review='pending'))
 assert shutil.disk_usage('/workspace').free>=500*1024**2
 destination=out/'whole-hair-grouped-r1.blend';bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
 js(out/'manifest.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p))for p in sorted(out.iterdir())if p.is_file()})
 print('C8_GROUPED_SOURCE_SAVED',destination,sha(destination),flush=True)
if __name__=='__main__':main()
