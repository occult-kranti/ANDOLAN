"""Verify a scenic map candidate against the original authoritative layout."""
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[2]
ROOT = NATIVE.parents[1]
base_path = NATIVE / 'assets/world/confluence-map.json'
candidate_path = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/yuga-ghat-candidate/map-candidate.json')
base = json.loads(base_path.read_text())
candidate = json.loads(candidate_path.read_text())
plan = json.loads((HERE / 'candidate-plan.json').read_text())
if hashlib.sha256(base_path.read_bytes()).hexdigest() != plan['base_map_sha256']:
    raise ValueError('Use the pinned base map for this candidate')
extra = [p for p in candidate['props'] if p['id'].startswith('panel-coast-rock-')]
if len(extra) != len(plan['placements']):
    raise ValueError('Unexpected scenic placement count')
for p in extra:
    if p['kit'] != 'nature' or p['preset'] != plan['asset'] or p['collision'] != 'none':
        raise ValueError('Unexpected added asset or collision')
    planned = next((item for item in plan['placements'] if item['id'] == p['id']), None)
    if not planned or {key: p[key] for key in planned} != planned:
        raise ValueError('Scenic placement differs from the approved plan')

# AABB matches the normalized unit-footprint hierarchy in build-candidate.mjs.
actor = base['bounds']['actor_xz']
art = base['bounds']['art_xz']
footprints = []
for prop in extra:
    x, _, z = prop['position']
    sx, _, sz = prop['scale']
    angle = math.radians(prop['yaw_degrees'])
    hx = (abs(math.cos(angle)) * sx + abs(math.sin(angle)) * sz) / 2
    hz = (abs(math.sin(angle)) * sx + abs(math.cos(angle)) * sz) / 2
    footprint = [x-hx, x+hx, z-hz, z+hz]
    outside = (footprint[1] <= actor[0] or footprint[0] >= actor[1] or
               footprint[3] <= actor[2] or footprint[2] >= actor[3])
    inside_art = (footprint[0] >= art[0] and footprint[1] <= art[1] and
                  footprint[2] >= art[2] and footprint[3] <= art[3])
    if not outside or not inside_art:
        raise ValueError(f"{prop['id']}: invalid scenery footprint {footprint}")
    footprints.append({'id':prop['id'], 'xz_m':[round(v, 4) for v in footprint],
                       'west_boundary_gap_m':round(actor[0] - footprint[1], 4)})

# Remove precisely the new metadata and instances and compare all original
# fields, including spawn, lane, deck, water, and collision authoring.
candidate['props'] = [p for p in candidate['props'] if p not in extra]
kit = next(item for item in candidate['kit_sources'] if item['id'] == 'nature')
kit['presets'].remove(plan['asset'])
if candidate != base:
    raise ValueError('An original map value changed')

spec = importlib.util.spec_from_file_location('world_plan_cases', NATIVE / 'tests/world_plan_cases.py')
world = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world)
actual = json.loads(candidate_path.read_text())
errors = world.validate(actual)
if errors:
    raise ValueError('Candidate failed existing world validation: ' + repr(errors))
result = {
    'base_sha256':hashlib.sha256(base_path.read_bytes()).hexdigest(),
    'candidate_sha256':hashlib.sha256(candidate_path.read_bytes()).hexdigest(),
    'original_fields_identical':True,
    'world_plan_errors':errors,
    'original_lanes':len(base['lanes']),
    'original_blocks':len(base['authority_collision_boxes']),
    'original_decks':len(base['traversal']['native_collision_boxes']),
    'actor_envelope':actor,
    'footprints':footprints,
    'method':'Transformed unit-footprint AABBs checked against the existing actor and art envelopes. The existing world-plan validator checked original lane and rotation contracts. Actual GPU camera occlusion is a separate test.'
}
out = candidate_path.parent / 'layout-review.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
