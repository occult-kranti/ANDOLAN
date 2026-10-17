"""Read-only source/import audit; writes only the explicitly supplied report."""
from pathlib import Path
import argparse,hashlib,io,json,re,struct,sys
import numpy as np
from PIL import Image
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
r=a.repo/'games/yuga-native';sys.path.insert(0,str(r/'art/hero-rama-face'))
from validate_face import read,accessor
H=lambda b:hashlib.sha256(b).hexdigest()
def pin(path):
 b=path.read_bytes();return {'path':str(path.relative_to(a.repo)),'sha256':H(b),'bytes':len(b)}
def fingerprint(x):return H(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
def params(path):
 text=path.read_text();return dict(line.split('=',1)for line in text.split('[params]')[1].splitlines() if '=' in line)
def img(b):
 im=Image.open(io.BytesIO(b));q=np.asarray(im.convert('RGBA'))
 return {'mode':im.mode,'size':list(im.size),'rgba_min':q.min(axis=(0,1)).tolist(),'rgba_max':q.max(axis=(0,1)).tolist(),'rgb_equal':bool(np.all(q[:,:,0]==q[:,:,1])and np.all(q[:,:,1]==q[:,:,2])),'sha256':H(b),'bytes':len(b)}
files=['assets/heroes/rama-hero.glb','assets/heroes/rama-hero-mid.glb','assets/heroes/rama-hero-far.glb','art/hero-rama-face/rama-hero-face.blend','art/hero-rama-face/rama-hero-face.glb','art/production/reconstruction-rama.blend','art/production/reconstruction-source.glb','art/production/reconstruction-notes.md','art/production/reconstruction-editable.json','art/hero-rama-face/candidate.json','art/hero-rama-face/build_native_face.py','art/hero-rama-face/sources/source-ledger.json','art/hero-rama-face/sources/face-poseunits.json','art/hero-rama-face/sources/face-poseunits.bvh','art/hero-rama-face/NOTICE.md','art/hero-rama/NOTICE.md','assets/materials/rama-finish/skin-roughness.png','assets/materials/rama-finish/skin-roughness.png.import','assets/materials/rama-finish/manifest.json','assets/materials/rama-finish/build_maps.py','assets/materials/rama-finish/NOTICE.md','scripts/rama_surface_finish.gd','scripts/rama_surface_materials.gd','scripts/rama_facial_performance.gd','scripts/rama_lod_binding.gd','scripts/rama_motion.gd','scripts/player.gd','assets/animations/rama_hero_motion.tres','docs/evidence/visual-campaign/art-review/face-diagnosis/source-check.json']
for level in ['', '-mid','-far']:
 files.append('assets/heroes/rama-hero'+level+'.glb.import')
 for kind in ['basecolor','normal','roughness']:
  stem='assets/heroes/rama-hero'+level+'_rama-warm-skin-'+kind+'.png';files.extend([stem,stem+'.import'])
report={'schema':1,'task':'R2-07','product':'YUGA native','source_commit':'0437ea91edf6989ff78c1eeadb3661f4825b60f2','runtime_baseline_commit':'09dac7220544374a471a11d953b67de20ab99d7d','scope':'Actual GLB/header/accessor/image/import inspection; no import/render/Blender export or visual-cause attribution','file_pins':[pin(r/f)for f in files if (r/f).is_file()],'missing_requested_files':[f for f in files if not (r/f).is_file()]}
levels=[]
for level in ['', '-mid','-far']:
 path=r/('assets/heroes/rama-hero'+level+'.glb');raw,d,b=read(path)
 record={'level':level or 'near','file':pin(path),'header':dict(zip(['magic','version','length'],struct.unpack_from('<4sII',raw[:12]))),'meshes':[],'skin_joint_counts':[len(x['joints'])for x in d['skins']],'nodes_sha256':fingerprint(d['nodes']),'skins_sha256':fingerprint(d['skins']),'materials_sha256':fingerprint(d['materials']),'animations_sha256':fingerprint(d['animations']),'animation_names':[x.get('name')for x in d['animations']],'import_params':params(Path(str(path)+'.import'))}
 record['header']['magic']=record['header']['magic'].decode()
 record['joint_names']=[d['nodes'][j]['name']for j in d['skins'][0]['joints']]
 for ni,node in enumerate(d['nodes']):
  if 'mesh'not in node:continue
  mesh=d['meshes'][node['mesh']];mr={'node':node['name'],'node_index':ni,'mesh_index':node['mesh'],'mesh_name':mesh['name'],'skin_index':node.get('skin'),'target_names':mesh.get('extras',{}).get('targetNames',[]),'primitives':[]}
  for pi,primitive in enumerate(mesh['primitives']):
   at=primitive['attributes'];pr={'primitive':pi,'material':d['materials'][primitive['material']]['name'],'vertices':d['accessors'][at['POSITION']]['count'],'triangles':d['accessors'][primitive['indices']]['count']//3,'attributes':at}
   if node['name']=='RamaFace' or pr['material'] in ['Rama warm skin','Natural lips']:
    arrays={k:accessor(d,b,v)for k,v in at.items()};pr['attribute_array_hashes']={k:H(v.tobytes())for k,v in arrays.items()};pr['position_bounds']=[arrays['POSITION'].min(axis=0).tolist(),arrays['POSITION'].max(axis=0).tolist()];pr['color0_bounds']=[arrays['COLOR_0'].min(axis=0).tolist(),arrays['COLOR_0'].max(axis=0).tolist()];pr['max_abs_tangent_normal_dot']=float(abs((arrays['NORMAL']*arrays['TANGENT'][:,:3]).sum(axis=1)).max());pr['morphs']=[]
    for ti,target in enumerate(primitive.get('targets',[])):
     ta={k:accessor(d,b,v)for k,v in target.items()};delta=ta['POSITION'];pr['morphs'].append({'index':ti,'name':mr['target_names'][ti],'attributes':target,'array_hashes':{k:H(v.tobytes())for k,v in ta.items()},'storage':{k:'sparse'if 'sparse'in d['accessors'][v]else'dense'for k,v in target.items()},'moved_vertices_gt_1e_7':int(np.count_nonzero(np.linalg.norm(delta,axis=1)>1e-7)),'max_position_delta_m':float(np.linalg.norm(delta,axis=1).max())})
   mr['primitives'].append(pr)
  record['meshes'].append(mr)
 if not level:
  skin=next(m for m in d['materials']if m['name']=='Rama warm skin');report['skin_material_glTF']=skin;maps=[]
  for semantic,tx in [('normal',skin['normalTexture']['index']),('basecolor',skin['pbrMetallicRoughness']['baseColorTexture']['index']),('roughness',skin['pbrMetallicRoughness']['metallicRoughnessTexture']['index'])]:
   ii=d['textures'][tx]['source'];im=d['images'][ii];v=d['bufferViews'][im['bufferView']];data=b[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']];external=r/('assets/heroes/rama-hero_rama-warm-skin-'+semantic+'.png');maps.append({'semantic':semantic,'texture_index':tx,'image_index':ii,'name':im.get('name'),'embedded':img(data),'external':pin(external),'external_equals_embedded':external.read_bytes()==data,'import':params(Path(str(external)+'.import'))})
  report['skin_maps']=maps
 levels.append(record)
report['levels']=levels
report['finish_map']={'file':pin(r/'assets/materials/rama-finish/skin-roughness.png'),'pixels':img((r/'assets/materials/rama-finish/skin-roughness.png').read_bytes()),'import':params(r/'assets/materials/rama-finish/skin-roughness.png.import'),'channel':'RED explicit runtime BaseMaterial3D.TEXTURE_CHANNEL_RED','color_space':'linear scalar roughness; albedo sRGB; normal linear tangent-space data','profile':{'roughness':1.0,'metallic_specular':0.34,'subsurf_scatter_enabled':True,'subsurf_scatter_strength':0.08,'subsurf_scatter_skin_mode':True}}
nearface=next(m for m in levels[0]['meshes']if m['node']=='RamaFace')['primitives'][0]
report['lod_agreement']=[{'level':v['level'],'joint_names_equal_near':v['joint_names']==levels[0]['joint_names'],'face_attributes_equal_near':next(m for m in v['meshes']if m['node']=='RamaFace')['primitives'][0]['attribute_array_hashes']==nearface['attribute_array_hashes'],'face_morph_arrays_equal_near':[x['array_hashes']for x in next(m for m in v['meshes']if m['node']=='RamaFace')['primitives'][0]['morphs']]==[x['array_hashes']for x in nearface['morphs']]}for v in levels]
meta=json.load(open(r/'art/hero-rama-face/candidate.json'));report['face_partition']={k:meta[k]for k in ['originalBodyPolygons','selectedPolygons','retainedPolygons','selectedSourceVertices','retainedSourceVertices','sharedBoundaryVertices','heldBoundaryAndRingVertices','originalBodyCoveredExactlyOnce','sourcePartitionChecks','morphNames','boundaryAttributeSeal','sourcePoseUnits']}
report['named_face_bones']=[n for n in levels[0]['joint_names']if any(x in n.lower()for x in ['head','neck','jaw','eye','orbicularis','oris','brow','tongue'])]
report['reconstruction_limits']={'original_modeling_history':'Original rama-authored.blend absent; reconstructed production scene preserves imported merged geometry/actions and textures, not original modifiers/pieces/history.','face_editable':'Prefer pinned native rama-hero-face.blend for native face authoring; full re-export is a new candidate requiring rig/skin/animation/seam equivalence review.','inspected_blends':'Byte identities and retained source manifests only; no new Blender opening claimed.'}
report['permissions_and_routes']=['R2-01: separate scratch skin-only override or import-options candidate, one variable per candidate; preserve accepted map hashes and record values/intent.','R2-08: fresh candidate only, bounded displacement mask on existing face/body-skin/lip principal forms; preserve topology, UV, weights, skeleton, ordered morph identities, unrelated bytes and exact shared boundary.','Morph array byte preservation alone does not prove unchanged closure after a base-form edit; run seam/aperture and continuous blink tests.','Do not copy complete mid/far scenes into runtime: binding admits body/bow only, uses the single existing skeleton and excludes candidate RamaFace/animators. Body cheek/lip edits require rebuilt or explicitly near-only LOD policy.','No optimization, Rigify regeneration, REA bridge rerun, new repositories or Reddit retry needed for the current source question.']
report['runtime_ownership']={'skeleton':'RamaMotion sole existing pose owner; 164 bones; 9 embedded clips and separate 23-state library','face':'RamaFacialPerformance binds exactly one morph mesh <=8000 vertices with ownership metadata; it changes four blink weights and never writes skeleton/eye transforms.','states':'paused freezes; alive false closes lids over 0.28s; reset/teleported clears; effort max closure 0.14; full blink uses full+half arc interpolation. No authored jaw/lips/gaze/brow expressions.','binding_order':'motion -> LOD -> surface calibration -> secondary -> finish -> facial performance'}
a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'report':str(a.report),'pins':len(report['file_pins']),'missing':report['missing_requested_files'],'lod_agreement':report['lod_agreement'],'skin_maps':[{k:x[k]for k in ['semantic','embedded','external_equals_embedded']}for x in report['skin_maps']],'named_face_bones':report['named_face_bones']},indent=2))
