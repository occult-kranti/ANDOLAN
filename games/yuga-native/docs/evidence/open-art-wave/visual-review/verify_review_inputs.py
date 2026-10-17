#!/usr/bin/env python3
"""Independent role12 checks; reads raw captures without editing any image."""
import copy
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image
import numpy as np

RAW = Path(sys.argv[1] if len(sys.argv) > 1 else '/workspace/scratch/open-art-material-r1')
OUT = Path(__file__).parent / 'input-verification.json'
TARGET = 'Cobalt handwoven silk · bounded secondary'
OWNED = set('base_color roughness_value metallic_value normal_strength specular_value rough_channel metal_channel base_texture rough_texture metal_texture normal_texture use_base_texture use_rough_texture use_metal_texture use_normal_texture'.split())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local(root, resource):
    assert resource.startswith('res://')
    return root / resource[6:]

def strip_owned(state):
    result = copy.deepcopy(state)
    for mesh in result['meshes']:
        for material in mesh['materials']:
            if material['material']['name'] == TARGET:
                assert material['material']['class'] == 'ShaderMaterial'
                for field in OWNED:
                    material['uniforms'].pop(field)
    return result

capture = json.loads((RAW / 'material-capture.json').read_text())
identity = json.loads((RAW / 'source-identity.json').read_text())
runner = json.loads((RAW / 'capture-run.json').read_text())
canonical = Path(identity['before']['canonical_project'])
fixture = Path(identity['before']['fixture_project'])
assert capture['complete'] and runner['complete'] and identity['complete']
assert capture['failure'] == ''
assert capture['source_sha256'] == capture['source_after_sha256']
assert identity['before'] == identity['after']
assert sha(RAW / 'material-capture.json') == runner['report_sha256']

sources = capture['source_sha256']
for resource, pin in sources.items():
    assert sha(local(fixture, resource)) == pin, resource
for resource, pin in identity['before']['canonical_source_sha256'].items():
    assert sha(local(canonical, resource)) == pin, resource
    assert sha(local(fixture, resource)) == pin, resource
snapshot_checks = 0
for path in (RAW / 'source').rglob('*'):
    if path.is_file():
        resource = 'res://' + path.relative_to(RAW / 'source').as_posix()
        assert resource in sources, resource
        assert sha(path) == sources[resource], resource
        snapshot_checks += 1
for resource, row in capture['imports'].items():
    assert sha(local(fixture, resource)) == row['source_sha256']
    for path_key, hash_key in [('metadata','metadata_sha256'),('imported','sha256'),('stamp','stamp_sha256')]:
        assert sha(local(fixture,row[path_key])) == row[hash_key]
    if resource.endswith('.png'):
        assert row['mipmaps_generate'] and row['actual_has_mipmaps']
        assert row['dimensions'] == [1024,1024]

expected = [('courtyard-day',780,0),('courtyard-night',780,0),('confluence-day',350,1),('confluence-night',350,1)]
assert len(capture['pairs']) == len(capture['states']) == 4
pair_results = []
image_results = []
for pair, state, (name,target,level) in zip(capture['pairs'],capture['states'],expected):
    assert pair['id'] == state['id'] == name
    assert pair['target_hero_pixels'] == target and pair['selected_level'] == level
    a,b = pair['baseline'],pair['candidate']
    assert a['camera'] == b['camera']
    assert a['lighting'] == b['lighting']
    assert a['state_sha256'] == b['state_sha256']
    before,after,restored = [state[k] for k in ['baseline_full','candidate_full','restored_full']]
    assert before == restored
    frozen = state['frozen_excluding_owned_uniforms']
    assert strip_owned(before) == strip_owned(after) == strip_owned(restored) == frozen
    assert len(before['bones']) == 164 and before['live_rigs'] == before['face_meshes'] == 1
    assert before['paused'] and before['controllers']['motion']['finite'] and before['controllers']['secondary']['finite']
    changed = []
    for old_mesh,new_mesh in zip(before['meshes'],after['meshes']):
        for old_mat,new_mat in zip(old_mesh['materials'],new_mesh['materials']):
            if old_mat != new_mat:
                assert old_mat['material'] == new_mat['material']
                assert old_mat['shader_sha256'] == new_mat['shader_sha256']
                assert old_mat['material']['name'] == TARGET
                fields = [key for key in old_mat['uniforms'] if old_mat['uniforms'][key] != new_mat['uniforms'][key]]
                assert set(fields) <= OWNED
                assert old_mat['uniforms']['secondary_offset'] == new_mat['uniforms']['secondary_offset']
                changed.append({'mesh':old_mesh['path'],'surface':old_mat['surface'],'material_id':old_mat['material']['id'],'changed_fields':fields})
    assert len(changed) == 3
    assert not pair['unbind']['conflicts'] and not pair['unbind']['invalidated_materials']
    arrays=[]
    for shot in [a,b]:
        path=RAW/shot['file']
        assert sha(path)==shot['sha256']
        with Image.open(path) as image:
            assert image.size==(1280,960)
            arrays.append(np.asarray(image.convert('RGB')).astype(np.int16))
            image_results.append({'path':str(path),'width':image.width,'height':image.height,'sha256':sha(path),'viewed_fullframe':True})
    diff=np.abs(arrays[1]-arrays[0]).max(axis=2)
    yy,xx=np.where(diff>8)
    coords=[(658,331),(729,570),(773,590)] if level==0 else [(645,415),(684,520),(728,530)]
    samples=[]
    for x,y in coords:
        samples.append({'xy':[x,y],'baseline_rgb':arrays[0][y,x].tolist(),'candidate_rgb':arrays[1][y,x].tolist()})
    pair_results.append({'id':name,'camera_exact_equal':True,'lighting_exact_equal':True,'recorded_state_sha256':a['state_sha256'],'independently_compared_full_state_except_owned_uniforms':True,'full_restore_exact':True,'bone_count':164,'changed_materials':changed,'projected_rest_aabb_height_pixels':a['camera']['rest_aabb_height_pixels'],'difference_over_8_per_channel_pixels':int((diff>8).sum()),'difference_over_8_bounds_xyxy_exclusive':[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],'sample_pixels':samples,'pixel_metric_limit':'Raw RGB differences include temporal renderer history and indirect light; not a cloth mask or isolated roughness/normal measurement.'})

result={'schema':1,'role':'12 independent image review','verified':True,'raw_capture_dir':str(RAW),'source_commit':'658804fd6e454c6d584ac3245601506b22075c0b','source_identity_receipt_sha256':sha(RAW/'source-identity.json'),'material_capture_receipt_sha256':sha(RAW/'material-capture.json'),'capture_run_receipt_sha256':sha(RAW/'capture-run.json'),'runtime_source_files_verified':len(sources),'canonical_fixture_source_files_verified':len(identity['before']['canonical_source_sha256']),'text_source_snapshots_verified':snapshot_checks,'imports_sha256_verified':len(capture['imports']),'source_unchanged':True,'renderer':capture['renderer'],'display':capture['display'],'adapter':capture['adapter'],'godot':capture['godot']['string'],'uncontrolled_background_TIME':capture['uncontrolled_background_TIME'],'images':image_results,'pairs':pair_results,'method':'Independent file SHA-256 checks and direct full JSON state equality after removing only the 15 named uniforms from exact secondary-owned target material. No renderer validation helper imported. Pillow/NumPy read raw pixels for metrics only; no images written or altered.'}
OUT.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'verified':True,'images':len(image_results),'pairs':len(pair_results),'runtime_source_files':len(sources),'snapshot_files':snapshot_checks,'out':str(OUT)}))
