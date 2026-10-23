"""Source-pinned Rama-family authoring intake; never promotes a roster hero."""
from __future__ import annotations
import argparse,hashlib,json,math,re,struct
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
DONOR='assets/heroes/rama-hero.glb'
LIBRARY='assets/animations/rama_hero_motion.tres'
CATALOG='assets/design/hero-codex.json'
SOCKETS={'bow_grip':{'bone':'wrist.R','offset':[0,.105,.025]},'string_nock':{'bone':'bowstring','offset':[0,0,0]},'draw_hand':{'bone':'wrist.L','offset':[.012613,.114969,-.042728]},'arrow_muzzle':{'bone':'wrist.R','offset':[0,.160,.025]},'head':{'bone':'head','offset':[0,.10,0]}}
PROFILES={
 'rama':('donor','bow','Accepted source; not a new roster output.'),
 'arjuna':('archer_template','bow','Unique lean silhouette, face, angular bow, quiver, scarf and pivot choreography.'),
 'karna':('archer_template','bow','Unique broad proportions, face, shoulder discs, bow and deliberate draw.'),
 'meghnad':('archer_template','bow','Unique compact bow, face, forked crest, cloud scarf and oblique footwork.'),
 'ravana':('humanoid_seed','chakram','Unique grip, chakram dynamics/release and ten-facet crown; current design has one head.'),
 'duryodhana':('humanoid_seed','mace','Unique heavy grip, swing/recovery, hit contacts and silhouette.'),
 'hanuman':('unique_anatomy','mace','Tail anatomy/rig/secondary motion, mace contacts and airborne/landing choreography.'),
 'bhima':('humanoid_seed','mace','Unique broad proportions, heavy weapon, contact and recovery choreography.'),
 'sita':('humanoid_seed','staff','Unique anatomy/face/mantle, staff grips and protective gestures.'),
 'draupadi':('humanoid_seed','staff','Unique anatomy/face, five-panel cloth, staff and command gestures.'),
 'subhadra':('humanoid_seed','spear','Unique anatomy/face, spear/pennant grip and command gestures.'),
 'hidimbi':('humanoid_seed','spear','Unique broad humanoid design, leaf mantle, spear and grounding.'),
 'chitrangada':('humanoid_seed','spear','Unique anatomy/face, spear transfers and crossing footwork.'),
 'ulupi':('humanoid_seed','staff','Unique humanoid anatomy/face, circular staff grips and garment motion; current design retains legs.'),
}
SOURCE_PATHS=[DONOR,'assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb',LIBRARY,CATALOG,
 'scripts/player.gd','scripts/rama_motion.gd','scripts/rama_lod_binding.gd','scripts/rama_visual_lod.gd',
 'scripts/rama_surface_materials.gd','scripts/rama_secondary_motion.gd','scripts/rama_surface_finish.gd','scripts/rama_facial_performance.gd',
 'shaders/rama_secondary_cloth.gdshader','assets/materials/rama-finish/skin-roughness.png','assets/materials/rama-finish/ivory-roughness.png','assets/materials/rama-finish/woven-roughness.png','assets/hero-finish/s1-hammered-gold-roughness.png','assets/hero-finish/hair-bundle-roughness.png']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pin(path):
 p=PROJECT/path;return {'path':path,'res_path':'res://'+path,'bytes':p.stat().st_size,'sha256':sha(p)}
def identity():return [[1 if i==j else 0 for j in range(4)] for i in range(4)]
def multiply(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def matrix(node):
 if 'matrix' in node:return [[node['matrix'][j*4+i] for j in range(4)] for i in range(4)]
 x,y,z,w=node.get('rotation',[0,0,0,1]);s=node.get('scale',[1,1,1]);t=node.get('translation',[0,0,0]);m=identity()
 q=[[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]]
 for i in range(3):
  for j in range(3):m[i][j]=q[i][j]*s[j]
  m[i][3]=t[i]
 return m
def glb_contract(path):
 raw=Path(path).read_bytes()
 if raw[:4]!=b'glTF':raise ValueError('Expected a glTF binary')
 length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length]);blob=raw[28+length:]
 nodes=doc.get('nodes',[]);parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
 def world(i):return multiply(world(parents[i]),matrix(nodes[i])) if i in parents else matrix(nodes[i])
 skins=doc.get('skins',[])
 if len(skins)!=1:return {'skin_count':len(skins),'bone_count':0,'bones':[],'materials':[x.get('name','') for x in doc.get('materials',[])],'embedded_actions':[x.get('name','') for x in doc.get('animations',[])]}
 joints=skins[0]['joints'];order={n:i for i,n in enumerate(joints)};bones=[]
 def accessor(index):
  entry=doc['accessors'][index];view=doc['bufferViews'][entry['bufferView']]
  components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[entry['type']];formats={5121:('B',1),5123:('H',2),5125:('I',4),5126:('f',4)};fmt,size=formats[entry['componentType']];stride=view.get('byteStride',size*components);offset=view.get('byteOffset',0)+entry.get('byteOffset',0)
  values=[struct.unpack_from('<'+fmt*components,blob,offset+i*stride) for i in range(entry['count'])]
  if entry.get('normalized'):
   maximum={5121:255,5123:65535}[entry['componentType']];values=[tuple(v/maximum for v in row) for row in values]
  return values
 binds=accessor(skins[0]['inverseBindMatrices']);assert len(binds)==len(joints) and all(math.isfinite(v) for row in binds for v in row)
 for n in joints:
  parent=parents.get(n)
  while parent is not None and parent not in order:parent=parents.get(parent)
  rest=world(n);assert all(math.isfinite(v) for row in rest for v in row)
  bones.append({'name':nodes[n]['name'],'parent':order.get(parent,-1),'global_rest':rest})
 counts={};morphs={};weight_errors=[];unweighted=0;maximum_influences=0;masked=[];mesh_nodes=[];material_roles={};invalid_skin_primitives=0
 for node in nodes:
  if 'mesh' in node:
   mesh=doc['meshes'][node['mesh']];name=node.get('name','');counts[name]=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for p in mesh['primitives']);morphs[name]=mesh.get('extras',{}).get('targetNames',[])
   transform=world(nodes.index(node));assert all(math.isfinite(x) for row in transform for x in row)
   mesh_nodes.append({'name':name,'skin':node.get('skin'),'global_transform':transform});material_roles[name]=[doc['materials'][p['material']].get('name','') if 'material' in p else None for p in mesh['primitives']]
   for primitive in mesh['primitives']:
    attrs=primitive['attributes']
    positions=accessor(attrs['POSITION']);assert all(math.isfinite(v) for row in positions for v in row)
    valid_skin=node.get('skin')==0 and 'JOINTS_0' in attrs and 'WEIGHTS_0' in attrs and 'JOINTS_1' not in attrs and 'WEIGHTS_1' not in attrs
    if valid_skin:
     joint_meta=doc['accessors'][attrs['JOINTS_0']];weight_meta=doc['accessors'][attrs['WEIGHTS_0']];joint_values=accessor(attrs['JOINTS_0']);weight_values=accessor(attrs['WEIGHTS_0'])
     valid_skin=joint_meta['componentType'] in {5121,5123} and joint_meta['type']=='VEC4' and not joint_meta.get('normalized',False) and weight_meta['type']=='VEC4' and (weight_meta['componentType']==5126 or (weight_meta['componentType'] in {5121,5123} and weight_meta.get('normalized',False))) and len(joint_values)==len(weight_values)==len(positions) and len(positions)>0 and all(len(row)==4 and all(0<=v<len(joints) for v in row) for row in joint_values)
    if not valid_skin:invalid_skin_primitives+=1
    if 'WEIGHTS_0' in attrs:
     for row in accessor(attrs['WEIGHTS_0']):
      assert all(math.isfinite(v) and v>=0 for v in row);weight_errors.append(abs(sum(row)-1));unweighted+=sum(row)<=0;maximum_influences=max(maximum_influences,sum(v>0 for v in row))
    if 'material' in primitive:
     material=doc['materials'][primitive['material']].get('name','')
     if material in {'Cobalt handwoven silk','Cobalt lotus brocade','Worked warm gold','Swept black hair'}:
      masked.append({'material':material,'present':'COLOR_0' in attrs,'valid':False})
      if 'COLOR_0' in attrs:
       colors=accessor(attrs['COLOR_0']);masked[-1]['valid']=all(len(c)==4 and all(math.isfinite(x) for x in c) and all(abs(x-1)<.001 for x in c[:3]) and 0<=c[3]<=1 for c in colors)
 return {'skin_count':1,'bone_count':len(bones),'bones':bones,'inverse_bind_matrices':binds,'mesh_nodes':mesh_nodes,'mesh_material_roles':material_roles,'mesh_attribute_vertices':counts,'mesh_morph_targets':morphs,'weight_integrity':{'unweighted':unweighted,'invalid_skin_primitives':invalid_skin_primitives,'max_sum_error':max(weight_errors,default=1.),'max_influences':maximum_influences},'semantic_masks':masked,'materials':[x.get('name','') for x in doc.get('materials',[])],'embedded_actions':[x.get('name','') for x in doc.get('animations',[])]}
def runtime_clips():
 text=(PROJECT/LIBRARY).read_text();block=text.split('[resource]',1)[1].split('metadata/',1)[0]
 return re.findall(r'&"([^\"]+)"\s*:',block)
def build_manifest():
 catalog=json.loads((PROJECT/CATALOG).read_text());heroes=catalog['heroes'];assert {h['id'] for h in heroes}==set(PROFILES)
 donor=glb_contract(PROJECT/DONOR);clips=runtime_clips();assert donor['bone_count']==164 and len(clips)==23
 return {'schema_version':1,'scope':'Accepted Rama resource contract and authoring compatibility; templates are not completed roster heroes.','source_pins':[pin(p) for p in SOURCE_PATHS],
  'donor':donor,'runtime_clips':clips,'runtime_clip_count':len(clips),'embedded_glb_clip_count':len(donor['embedded_actions']),
  'roster':[{'hero_id':h['id'],'name':h['name'],'reuse_class':PROFILES[h['id']][0],'weapon_family':PROFILES[h['id']][1],'unique_requirements':PROFILES[h['id']][2],'catalog_silhouette':h['art_direction']['silhouette'],'finished_hero':False,'accepted_base_asset':h['id']=='rama','new_hero_accepted':False} for h in heroes],
  'sockets':SOCKETS,'rest_epsilon':.0001,'lod':{'paths':['assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb'],'live_skeletons':1,'mesh_names':['RamaHero','RamaBow'],'face_owner':'near RamaFace only','threshold_pixels':[420,160],'hysteresis':.15,'minimum_hold_seconds':.15,'must_preserve':['bone order/parents/rest','skin bind order/poses','material surface names','semantic vertex alpha masks','mesh transforms']},
  'secondary_motion':{'method':'bounded shader displacement; not physical cloth','cloth_max_m':.075,'hair_max_m':.018,'mask_materials':['Cobalt handwoven silk','Cobalt lotus brocade','Worked warm gold','Swept black hair']},
  'face':{'vertex_limit':8000,'required_shapes':['rama_blink_left','rama_blink_right'],'optional_pair':['rama_blink_left_half','rama_blink_right_half']},
  'source_status':{'accepted_donor_only':True,'generated_rama_source':'rejected for production','nearest_binding_r1':'rejected','anatomy_binding_r2':'rejected'},
  'authoring_gates':['original face and readable silhouette','authored outfit/materials and LODs','weapon/hand/string contacts','unique abilities and counters','continuous motions and physical appendages','independent matched-view art review','real hardware frame/VRAM profiles'],
  'runtime_promoted':False,'new_roster_heroes_completed':0}
def check_pins(manifest):
 errors=[]
 for ref in manifest['source_pins']:
  p=PROJECT/ref['path']
  if not p.is_file() or sha(p)!=ref['sha256']:errors.append('SOURCE_PIN_MISMATCH:'+ref['path'])
 return errors
def compatible(manifest,hero,source=None,weapon='bow',sockets=None,extra_anatomy=False,finished=False,motions=None,expected_source_sha=None):
 errors=check_pins(manifest);profile=next((h for h in manifest['roster'] if h['hero_id']==hero),None)
 if not profile:errors.append('UNKNOWN_HERO')
 elif profile['reuse_class']!='archer_template':errors.append('UNIQUE_ANATOMY_REQUIRED' if profile['reuse_class']=='unique_anatomy' else 'WEAPON_OR_IDENTITY_AUTHORING_REQUIRED')
 if weapon!='bow':errors.append('INCOMPATIBLE_WEAPON_FAMILY')
 if extra_anatomy:errors.append('EXTRA_ANATOMY_REQUIRES_NEW_RIG_REVIEW')
 if finished:errors.append('TEMPLATE_CANNOT_BE_FINISHED_HERO')
 for name in sockets or list(SOCKETS):
  if name not in SOCKETS:errors.append('UNKNOWN_SOCKET:'+name)
 for name in motions or manifest['runtime_clips']:
  if name not in manifest['runtime_clips']:errors.append('UNSUPPORTED_MOTION:'+name)
 if source is not None:
  try:path=Path(source).resolve();contract=glb_contract(path)
  except (AssertionError,OSError,ValueError,KeyError,IndexError,TypeError,struct.error,RecursionError) as error:
   errors.append('INVALID_SOURCE_DATA:'+type(error).__name__)
   return {'ok':False,'errors':errors,'hero_id':hero,'status':'blocked','finished_hero':False,'runtime_promoted':False}
  base=manifest['donor']
  actual_sha=sha(path);donor_sha=next(p['sha256'] for p in manifest['source_pins'] if p['path']==DONOR)
  if expected_source_sha is not None and actual_sha!=expected_source_sha:errors.append('SOURCE_HASH_MISMATCH')
  elif actual_sha!=donor_sha and expected_source_sha is None:errors.append('ALTERNATE_SOURCE_REQUIRES_EXPLICIT_HASH_PIN')
  if path!= (PROJECT/DONOR).resolve() and sha(path)==next(p['sha256'] for p in manifest['source_pins'] if p['path']==DONOR):errors.append('DUPLICATE_DONOR_USE_SHARED_REFERENCE')
  if contract['bone_count']!=164:errors.append('INCOMPATIBLE_BONE_COUNT')
  elif [b['name'] for b in contract['bones']]!=[b['name'] for b in base['bones']]:errors.append('INCOMPATIBLE_BONE_ORDER')
  elif [b['parent'] for b in contract['bones']]!=[b['parent'] for b in base['bones']]:errors.append('INCOMPATIBLE_BONE_PARENTS')
  elif any(abs(x-y)>manifest['rest_epsilon'] for a,b in zip(contract['bones'],base['bones']) for ra,rb in zip(a['global_rest'],b['global_rest']) for x,y in zip(ra,rb)):errors.append('INCOMPATIBLE_REST_TRANSFORMS')
  if contract['bone_count']==164:
   if len(contract['inverse_bind_matrices'])!=len(base['inverse_bind_matrices']) or any(abs(x-y)>manifest['rest_epsilon'] for a,b in zip(contract['inverse_bind_matrices'],base['inverse_bind_matrices']) for x,y in zip(a,b)):errors.append('INCOMPATIBLE_SKIN_BINDS')
   if any(name not in contract['mesh_attribute_vertices'] for name in ['RamaHero','RamaFace','RamaBow']):errors.append('INCOMPATIBLE_MESH_BINDING_NAMES')
   if set(contract['materials'])!=set(base['materials']):errors.append('MATERIAL_ROLE_MAPPING_REQUIRED')
   if contract['weight_integrity']['unweighted'] or contract['weight_integrity']['invalid_skin_primitives'] or contract['weight_integrity']['max_sum_error']>1e-4 or contract['weight_integrity']['max_influences']>4:errors.append('INVALID_SKIN_WEIGHTS')
   if not contract['semantic_masks'] or any(not m['present'] or not m['valid'] for m in contract['semantic_masks']) or {m['material'] for m in contract['semantic_masks']}!={m['material'] for m in base['semantic_masks']}:errors.append('INVALID_SEMANTIC_MASKS')
   source_meshes={n['name']:n for n in contract['mesh_nodes']};base_meshes={n['name']:n for n in base['mesh_nodes']}
   if len(contract['mesh_nodes'])!=len(base['mesh_nodes']) or set(source_meshes)!=set(base_meshes):errors.append('EXTRA_OR_MISSING_MESH_REQUIRES_AUTHORING_REVIEW')
   else:
    if any(source_meshes[n]['skin']!=base_meshes[n]['skin'] for n in base_meshes):errors.append('INCOMPATIBLE_MESH_SKIN_BINDING')
    if any(abs(x-y)>manifest['rest_epsilon'] for n in base_meshes for a,b in zip(source_meshes[n]['global_transform'],base_meshes[n]['global_transform']) for x,y in zip(a,b)):errors.append('INCOMPATIBLE_MESH_TRANSFORMS')
   if contract['mesh_material_roles']!=base['mesh_material_roles']:errors.append('INCOMPATIBLE_MATERIAL_ROLE_BINDINGS')
   face_shapes=contract['mesh_morph_targets'].get('RamaFace',[])
   if any(name not in face_shapes for name in manifest['face']['required_shapes']) or contract['mesh_attribute_vertices'].get('RamaFace',8001)>8000:errors.append('INCOMPATIBLE_FACE_CONTRACT')
 return {'ok':not errors,'errors':errors,'hero_id':hero,'status':'authoring_template_only' if not errors else 'blocked','finished_hero':False,'runtime_promoted':False}
def create_template(manifest,hero,output):
 verdict=compatible(manifest,hero,PROJECT/DONOR)
 if not verdict['ok']:raise ValueError(','.join(verdict['errors']))
 output=Path(output);output.mkdir(parents=True,exist_ok=False)
 data={**verdict,'schema_version':1,'source_contract_sha256':hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),'name':hero.title()+' Rama-family AUTHORING TEMPLATE','appearance':'unchanged Rama donor; no new hero art claimed','shared_resources':manifest['source_pins'],'runtime_clips':manifest['runtime_clips'],'sockets':manifest['sockets'],'lod_constraints':manifest['lod'],'unique_art_and_physics_required':next(h['unique_requirements'] for h in manifest['roster'] if h['hero_id']==hero),'art_gates_passed':False,'gameplay_enabled':False}
 (output/(hero+'-template.json')).write_text(json.dumps(data,indent=2)+'\n')
 scene='[gd_scene load_steps=3 format=3]\n\n[ext_resource type="PackedScene" path="res://'+DONOR+'" id="1_donor"]\n[ext_resource type="Script" path="res://tools/hero-family-reuse/family_template.gd" id="2_setup"]\n\n[node name="'+hero.title()+'AuthoringTemplate" type="Node3D"]\nscript = ExtResource("2_setup")\nhero_id = "'+hero+'"\nmetadata/authoring_template_only = true\nmetadata/finished_hero = false\n\n[node name="SharedRamaDonor" parent="." instance=ExtResource("1_donor")]\n'
 (output/(hero+'-template.tscn')).write_text(scene)
 return data
def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','create','validate']);p.add_argument('--manifest',type=Path);p.add_argument('--output',type=Path);p.add_argument('--hero',default='arjuna');p.add_argument('--source',type=Path);p.add_argument('--weapon',default='bow');p.add_argument('--source-sha256');p.add_argument('--motion',action='append');a=p.parse_args()
 if a.command=='audit':
  data=build_manifest();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data,indent=2)+'\n');print('HERO_FAMILY_AUDIT_PASS',len(data['roster']),data['runtime_clip_count']);return
 manifest=json.loads(a.manifest.read_text())
 if a.command=='create':data=create_template(manifest,a.hero,a.output);print('HERO_FAMILY_TEMPLATE_CREATED',data['hero_id']);return
 verdict=compatible(manifest,a.hero,a.source,a.weapon,motions=a.motion,expected_source_sha=a.source_sha256);print(json.dumps(verdict));raise SystemExit(0 if verdict['ok'] else 2)
if __name__=='__main__':main()
