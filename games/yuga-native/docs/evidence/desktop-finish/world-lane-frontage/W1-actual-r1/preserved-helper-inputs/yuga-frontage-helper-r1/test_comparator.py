"""Synthetic comparator controls only; never a native/physics/art acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
root=Path(__file__).parent
spec=importlib.util.spec_from_file_location('frontage',root/'compare_frontage.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
I=copy.deepcopy(m.IDENTITY)
body='/root/Confluence/World/authority-solid-2'
target='/root/Confluence/World/CityArt/block-2'
meta={'authority_id':'authority-solid-2','dimensions':[18,15,18],'position_base':[20,0,-28],'native_only':False}
materials=['ivory','glass','indigo']
shapeb={'path':body+'/Shape','class':'BoxShape3D','disabled':False,'transform':I,'size':[18,15,18]}
shapec={'path':body+'/Shape','class':'ConcavePolygonShape3D','disabled':False,'transform':I,'faces':2816,'faces_sha256':'f'*64,'backface_collision':True}
coll={'path':body,'class':'StaticBody3D','layer':1,'mask':0,'transform':I,'metadata':meta,'shapes':[shapeb]}
other={'path':'/root/Confluence/World/Roof','class':'StaticBody3D','layer':1,'mask':0,'transform':I,'metadata':{},'shapes':[copy.deepcopy(shapeb)]}
mesh={'path':'World/CityArt/block-2/Mesh','mesh_path':'res://assets/original.glb::mesh','aabb':[[-.5,0,-.5],[1,1,1]],'surface_vertices':[4944*3],'global_transform':I,'visible':True,'layers':1,'cast_shadow':1,'transparency':0,'material_override':'none','material_overlay':'none','surfaces':materials}
oldroof=copy.deepcopy(mesh);oldroof['path']='World/ReviewBlock2RoofLoggia/LoggiaTwoSharedSurfaces'
basefront={'branch':'baseline','target_path':target,'target_transform':I,'target_visible':True,'body_path':body,'body_transform':I,'body_metadata':meta,'shape_owner_count':1,'active_shape_count':1,'material_ids':materials,'data_sha256':'d'*64,'replacement_present':False,'shape_class':'BoxShape3D','box_size':[18,15,18]}
source={p:'a'*64 for p in ['art/world-finish/lane-frontage-r1/candidate.gd','art/world-finish/lane-frontage-r1/candidate-mesh.json','tools/graphics-six/capture_compact_screens.gd','tools/graphics-six/capture_scene_anchors.gd','scripts/confluence_world.gd']}
source[m.SELECTION]='b'*64;source['res://.graphics-six-snapshot.json']='c'*64
base={'complete':True,'failure':'','case':'lane-frontage-review','outer_transport_alias':'scene-anchors','preflight':True,'branch':'baseline','source_unchanged':True,'source_sha256':source,'source_after_sha256':copy.deepcopy(source),'selection_sha256':'b'*64,'checks':[{'name':'synthetic true','passed':True}],'audio_cleanup':{'observed_mixer_ticks':2,'wait_usec':32000,'budget_usec':250000,'main_cleanup_frames':8},'route_checks':{'hero_position_held':True,'army_resumed':True,'kit_resumed':True,'before':{'camera':I},'after':{'camera':I}},'renderer':'gl_compatibility','adapter':'synthetic','shots':[]}
for id in m.IDS:
    base['shots'].append({'id':id,'process_frame':100,'physics_frame':100,'drawn_frame':0,'serialization_errors':[],'hero_skeleton':{'bone_names':[str(i) for i in range(164)],'bone_global_poses':[copy.deepcopy(I) for i in range(164)]},'nav_manifest_sha256':'n'*64,'environment':{'ssao_enabled':True},'ao':{'ssao_enabled':True},'lights':[{'energy':1}],'materials':{'ivory':{'roughness':.5}},'clocks':{'army':1},'camera':{'transform':I},'frontage':copy.deepcopy(basefront),'collision_objects':[copy.deepcopy(coll),copy.deepcopy(other)],'meshes':[copy.deepcopy(mesh),copy.deepcopy(oldroof)]})
candidate=copy.deepcopy(base);candidate['branch']='candidate';candidate['selection_sha256']='e'*64
for key in ('source_sha256','source_after_sha256'):
    candidate[key][m.SELECTION]='e'*64;candidate[key]['res://.graphics-six-snapshot.json']='9'*64
for shot in candidate['shots']:
    shot['process_frame']=200
    f=shot['frontage'];f.update({'branch':'candidate','target_visible':False,'replacement_present':True,'shape_class':'ConcavePolygonShape3D','material_identity_reused':True,'surface_material_ids':materials,'new_materials':0,'new_textures':0,'new_lights':0,'candidate_transform':[[1,0,0],[0,1,0],[0,0,1],[20,0,-28]],'geometry':{'triangles':2816,'surfaces':3,'local_vertices_exact_raw':True,'body_local_vertices_exact':True,'world_vertices_equal_approx':True,'max_world_vertex_error_m':0.0,'vertex_count_matches':True,'backface_collision':True,'bounds':[[-9,0,-9],[18,15,18]],'body_bounds':[[-9,-7.5,-9],[18,15,18]]}})
    f.pop('box_size');shot['collision_objects'][0]['shapes']=[copy.deepcopy(shapec)]
    shot['meshes'][0]['visible']=False
    new=copy.deepcopy(mesh);new.update({'path':'World/ReviewBlock2Frontage/ClosedCivicFrontage','mesh_path':'','aabb':[[-9,0,-9],[18,15,18]],'surface_vertices':[3000,3000,2448],'global_transform':[[1,0,0],[0,1,0],[0,0,1],[20,0,-28]]});shot['meshes'].append(new)
rows=[]
def test(name,mutator=None):
    b=copy.deepcopy(candidate)
    if mutator: mutator(b)
    result=m.compare(base,b)
    passed=result['passed'] if mutator is None else not result['passed']
    rows.append({'name':name,'passed':passed,'comparator_passed':result['passed']})
    if not passed: print(name,json.dumps(result,indent=2))
test('declared pair with frame-counter differences accepted')
test('164bone pose corruption rejected',lambda b:b['shots'][0]['hero_skeleton']['bone_global_poses'][70][3].__setitem__(0,.001))
test('army clock corruption rejected',lambda b:b['shots'][0]['clocks'].__setitem__('army',2))
test('camera transform corruption rejected',lambda b:b['shots'][1]['camera']['transform'][3].__setitem__(0,.1))
test('light setting corruption rejected',lambda b:b['shots'][1]['lights'][0].__setitem__('energy',2))
test('actual AO toggle rejected',lambda b:b['shots'][1]['ao'].__setitem__('ssao_enabled',False))
test('material roughness corruption rejected',lambda b:b['shots'][0]['materials']['ivory'].__setitem__('roughness',.8))
test('accepted roof mesh change rejected',lambda b:b['shots'][0]['meshes'][1].__setitem__('visible',False))
test('retained roof collider mutation rejected',lambda b:b['shots'][0]['collision_objects'][1].__setitem__('layer',0))
test('extra enabled oldbox rejected',lambda b:b['shots'][0]['collision_objects'][0]['shapes'].append(copy.deepcopy(shapeb)))
test('hidden oldbox left sole shape rejected',lambda b:b['shots'][0]['collision_objects'][0].__setitem__('shapes',[copy.deepcopy(shapeb)]))
test('local geometry mismatch rejected',lambda b:b['shots'][0]['frontage']['geometry'].__setitem__('body_local_vertices_exact',False))
test('wrong raw geometry rejected',lambda b:b['shots'][0]['frontage']['geometry'].__setitem__('local_vertices_exact_raw',False))
test('body broadbounds mismatch rejected',lambda b:b['shots'][0]['frontage']['geometry'].__setitem__('body_bounds',[[-9,-7.5,-9],[18,16,18]]))
test('nonreused material identity rejected',lambda b:b['shots'][0]['frontage'].__setitem__('material_identity_reused',False))
test('new texture rejected',lambda b:b['shots'][0]['frontage'].__setitem__('new_textures',1))
test('new frontage moved from declared body rejected',lambda b:b['shots'][0]['meshes'][2]['global_transform'][3].__setitem__(0,21))
test('lost original target mesh rejected',lambda b:b['shots'][0]['meshes'].pop(0))
test('nav manifest mismatch rejected',lambda b:b['shots'][0].__setitem__('nav_manifest_sha256','changed'))
test('unrelated source edit rejected',lambda b:[b[k].__setitem__('scripts/confluence_world.gd','x'*64) for k in ('source_sha256','source_after_sha256')])
test('missing explicit art dependency rejected',lambda b:[b[k].pop('art/world-finish/lane-frontage-r1/candidate.gd') for k in ('source_sha256','source_after_sha256')])
test('changed collider between shots rejected',lambda b:b['shots'][2]['collision_objects'][0]['shapes'][0].__setitem__('faces_sha256','e'*64))
test('serialization failure rejected',lambda b:b['shots'][0]['serialization_errors'].append('unsupported RID'))
test('NaN control rejected',lambda b:b['shots'][0]['clocks'].__setitem__('army',float('nan')))
test('false native check rejected',lambda b:b['checks'][0].__setitem__('passed',False))
test('overview return failure rejected',lambda b:b['route_checks'].__setitem__('hero_position_held',False))
test('unobserved real mixer tick rejected',lambda b:b['audio_cleanup'].__setitem__('observed_mixer_ticks',1))
result={'passed':all(r['passed'] for r in rows),'count':len(rows),'checks':rows,'scope':'Synthetic JSON comparator tests only. No GDScript parse, native preflight, actual physics or image review executed.'}
(root/'comparator-tests.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'passed':result['passed'],'count':result['count']}))
raise SystemExit(0 if result['passed'] else 1)
