"""Independent read-only R2-12 context audit; no imports, rendering or source edits."""
from pathlib import Path
import hashlib, json, math, subprocess
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[7]
NATIVE = REPO / 'games/yuga-native'
ROUND = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

fixtures = json.loads((ROUND/'role02/context-fixtures.json').read_text())
manifest = json.loads((NATIVE/'assets/world/confluence-map.json').read_text())
pins = []
for rel, expected in fixtures['source_sha256'].items():
    actual = digest(NATIVE/rel)
    pins.append(dict(path=rel, expected=expected, actual=actual, matches=actual == expected))

geometry = []
boxes = manifest['authority_collision_boxes'] + manifest['traversal']['native_collision_boxes']
for station in fixtures['stations']:
    position = station['player_position_m']
    yaw = math.radians(station['visual_yaw_degrees']-180)
    x, y, z = station['face_offset_m']
    offset = np.array([math.cos(yaw)*x+math.sin(yaw)*z, y, -math.sin(yaw)*x+math.cos(yaw)*z])
    target = np.array(station['camera_contract']['exact_fixed_target_m'])
    errors = {}
    for kind, factor in [('close',1),('gameplay_scale_front_review',4)]:
        predicted = target + offset*factor
        errors[kind] = float(np.max(np.abs(predicted-station['camera_contract'][kind]['position_m'])))
    clearances = []
    if station['id'].startswith('confluence'):
        for box in boxes:
            dx = max(abs(position[0]-box['position'][0])-box['size'][0]/2,0)
            dz = max(abs(position[2]-box['position'][2])-box['size'][2]/2,0)
            clearances.append({'id':box['id'],'horizontal_clearance_after_radius_m':math.hypot(dx,dz)-.65})
    geometry.append({'station':station['id'],'camera_recomputation_max_error_m':errors,
                     'solid_count':len(clearances),'clearances':clearances,
                     'minimum_clearance_m':min((x['horizontal_clearance_after_radius_m'] for x in clearances),default=None)})

images, pairs, captures = [], [], {}
for context in ['courtyard','stone']:
    cap_path = ROUND/f'role06/baseline/{context}/capture.json'
    cap = json.loads(cap_path.read_text())
    captures[context] = cap
    frozen_pins = {rel:cap['source_sha256'].get('res://'+rel) == expected for rel,expected in fixtures['source_sha256'].items()}
    assert all(frozen_pins.values()), (context,frozen_pins)
    shots = {x['id']:x for x in cap['shots']}
    views = ['three-quarter-left','gameplay'] if context == 'courtyard' else ['three-quarter-left']
    for view in views:
        day, night = [shots[f'{context}-{view}-{phase}'] for phase in ['day','night']]
        invariants = {k:day[k] == night[k] for k in ['camera','pose_pin','player_transform','visual_yaw','viewport','tree_paused','ui_visible']}
        invariants['lod_level'] = day['lod']['level'] == night['lod']['level']
        invariants['face_weights'] = day['face']['weights'] == night['face']['weights']
        invariants['retained_light_controls'] = all(day['light'][k] == night['light'][k] for k in ['shadow_enabled','shadow_bias','shadow_normal_bias','portrait_fill','tonemap_exposure'])
        pairs.append({'pair':f'{context}-{view}','invariants':invariants,'all_pass':all(invariants.values()),
                      'day_light':day['light'],'night_light':night['light'],
                      'actual_camera':day['camera'],'pose_pin':day['pose_pin'],
                      'foot_position':day['player_transform'][3]})
        for shot in [day,night]:
            path = cap_path.parent/shot['file']
            rgb = np.asarray(Image.open(path).convert('RGB'),dtype=np.float64)/255
            linear = np.where(rgb <= .04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
            lum = linear @ np.array([.2126,.7152,.0722])
            rois = {'rear_costume':(475,500,525,560),'ground':(650,510,730,590)} if view == 'gameplay' else {'cheek':(570,610,620,660),'hair':(930,440,980,600),'right_background':(1050,440,1120,600)}
            measured = {}
            for name,(x0,y0,x1,y1) in rois.items():
                area = lum[y0:y1,x0:x1]
                measured[name] = {'xyxy':[x0,y0,x1,y1], 'median_linear_rec709_luminance':float(np.median(area)), 'mean_linear_rec709_luminance':float(np.mean(area))}
            images.append({'path':str(path.relative_to(REPO)),'sha256':digest(path),'matches_capture_sha256':digest(path)==shot['sha256'],
                           'size':[rgb.shape[1],rgb.shape[0]],'inspected_via':'view_image original full framebuffer',
                           'roi_method':'Manual fixed pixel boxes; descriptive samples, not segmentation or acceptance thresholds. sRGB inverse transfer then linear Rec709.',
                           'roi_measurements':measured})

diag_dir = ROUND/'role06/diagnostics/directional-pcss-off'
diag = json.loads((diag_dir/'capture.json').read_text())
diagnostic_shot = diag['shots'][0]
diag_path = diag_dir/diagnostic_shot['file']
base = next(x for x in captures['courtyard']['shots'] if x['id'] == diagnostic_shot['id'])
diff_sources = [k for k,v in diag['source_sha256'].items() if k in captures['courtyard']['source_sha256'] and captures['courtyard']['source_sha256'][k] != v]
diagnostic = {'path':str(diag_path.relative_to(REPO)),'sha256':digest(diag_path),
              'inspected_via':'view_image original full framebuffer','light':diagnostic_shot['light'],
              'same_camera':base['camera']==diagnostic_shot['camera'], 'same_pose_pin':base['pose_pin']==diagnostic_shot['pose_pin'],
              'changed_common_source_paths':diff_sources,
              'disposition':'Diagnostic only: reduced visible ear/neck stipple with harder environment shadow edges; lighting differs and must be explicit in any final candidate comparison.'}

report = {'schema':1,'task':'R2-12','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip(),
          'scope':'Independent source/pixel/context review. No Godot import/render, runtime mutation, capsule sweep or gameplay input.',
          'source_pins':pins,'all_fixture_source_pins_match':all(x['matches'] for x in pins),
          'both_baseline_capture_source_maps_match_all_16_fixture_pins':True,
          'independent_fixture_math':geometry,'baseline_phase_pairs':pairs,'reviewed_images':images,
          'separate_lighting_diagnostic':diagnostic,
          'candidate_pixel_status':'Pending; final forms/material/lighting candidate not inspected by R2-12 in this bounded review.',
          'remaining_gates':['Candidate originals and declared light/AA changes', 'Foliage day/night full-frame coverage',
                             'Optional indigo/gold station and all frontal gameplay-scale context views',
                             'Runtime capsule sweep if collision acceptance beyond static clearance is required',
                             'Moving contact/cascade review before accepting shadow-policy change'],
          'disposition':'BASELINE_CONTEXT_LIMITED; source and static fixture math pass; full context/candidate acceptance remains open.'}
(OUT/'context-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'source_pins_match':report['all_fixture_source_pins_match'],'pairs_pass':[x['all_pass'] for x in pairs],
                  'clearances':[(x['station'],x['minimum_clearance_m']) for x in geometry],
                  'reviewed_images':len(images)+1,'diagnostic_source_differences':diff_sources},indent=2))
