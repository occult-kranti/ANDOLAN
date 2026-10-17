#!/usr/bin/env python3
"""Source-backed world contract and navigation checks; no visual quality claim.

Runs the real TypeScript authority to obtain data and a half-metre navigation
occupancy grid (including living objective circles). Native rendering/physics
is checked separately by world_scene_cases.gd.
"""
from __future__ import annotations
import argparse
from collections import deque
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / 'games/yuga-native'
DEFAULT_MAP = NATIVE / 'art/world/confluence-map.json'
AUTHORITY_SCRIPT = r'''
import { ARENA, LANES, LANE_X, SPAWNS, SOLIDS, JUNGLE_CAMPS, JUNGLE_RULES, blocked } from './games/yuga/shared/map.ts';
import { ArenaSimulation, ARENA_RULES } from './games/yuga/shared/simulation.ts';
const sim = new ArenaSimulation({botsPerTeam:0});
const grid = {minX:-67,minZ:-81,step:.5,width:269,height:325,rows:[] as string[]};
for(let iz=0;iz<grid.height;iz++) {
 let row=''; for(let ix=0;ix<grid.width;ix++) row += (sim as any).blockedAt(grid.minX+ix*grid.step,grid.minZ+iz*grid.step) ? '#' : '.';
 grid.rows.push(row);
}
const boundProbes = [-68,-67.36,-67.35,0,67.35,67.36,68].map(x=>({x,z:0,blocked:blocked(x,0)}));
const depthProbes = [-82,-81.36,-81.35,0,81.35,81.36,82].map(z=>({x:0,z,blocked:blocked(0,z)}));
console.log(JSON.stringify({ARENA,LANES,LANE_X,SPAWNS,SOLIDS,JUNGLE_CAMPS,JUNGLE_RULES,ARENA_RULES,structures:sim.structures,grid,boundProbes,depthProbes}));
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authority_snapshot():
    proc = subprocess.run([str(ROOT/'node_modules/.bin/tsx'), '--eval', AUTHORITY_SCRIPT], cwd=ROOT,
                          text=True, capture_output=True, timeout=60)
    if proc.returncode:
        raise RuntimeError('Authority probe failed: ' + proc.stderr[-3000:])
    return json.loads(proc.stdout)


def finite_tree(value):
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    return True


def validate(candidate, authority):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    require(candidate.get('schema_version') == 1, 'unsupported schema')
    require(finite_tree(candidate), 'nonfinite number')
    if not finite_tree(candidate):
        return errors
    contract = candidate.get('coordinate_contract', {})
    require(contract.get('units') == 'metres' and contract.get('up_axis') == '+Y' and contract.get('forward_axis') == '+Z', 'coordinate contract mismatch')
    b = candidate.get('bounds', {})
    require(b.get('nominal_size_xz') == [authority['ARENA']['width'], authority['ARENA']['depth']], 'nominal arena dimensions mismatch')
    require(b.get('authority_xz') == [-68,68,-82,82], 'authority movement bounds mismatch')
    require(b.get('hero_radius') == authority['ARENA_RULES']['heroRadius'], 'hero radius mismatch')
    require(b.get('floor_y') == 0, 'flat authority floor mismatch')
    for probe in authority['boundProbes']+authority['depthProbes']:
        expected = abs(probe['x'])>67.35 or abs(probe['z'])>81.35
        require(probe['blocked'] == expected, 'executed authority boundary mismatch')
    source = candidate.get('source', {})
    for label in ('map','simulation'):
        path = ROOT / source.get(label+'_path', '')
        require(path.is_file() and source.get(label+'_sha256') == digest(path), label+' source hash mismatch')
    boxes = candidate.get('authority_collision_boxes', [])
    require(len(boxes) == len(authority['SOLIDS']), 'authority box count mismatch')
    require(len({x.get('id') for x in boxes}) == len(boxes), 'duplicate authority box id')
    for i, solid in enumerate(authority['SOLIDS']):
        box = next((x for x in boxes if x.get('source_index') == i), {})
        require(box.get('position') == [solid['x'],0,solid['z']] and box.get('size') == [solid['w'],solid['height'],solid['d']], f'authority box {i} geometry mismatch')
        require(box.get('anchor') == 'base_center' and box.get('collision_layer') == 1, f'authority box {i} collision metadata mismatch')
        require(box.get('style') == solid['style'], f'authority box {i} style mismatch')
    lanes = candidate.get('lanes', [])
    require(sorted(x.get('id',-1) for x in lanes) == [0,1,2], 'three lane identity mismatch')
    for lane in lanes:
        key = str(lane.get('id'))
        expected = [[v['x'],0,v['z']] for v in authority['LANES'].get(key,[])]
        require(lane.get('points') == expected, 'lane '+key+' waypoints mismatch')
        require(lane.get('center_x') == authority['LANE_X'][int(key)] if key in ('0','1','2') else False, 'lane '+key+' center mismatch')
    spawns = candidate.get('spawns', [])
    require(len(spawns) == 2, 'spawn count mismatch')
    for team, expected in authority['SPAWNS'].items():
        matches = [s for s in spawns if s.get('team') == team]
        require(len(matches) == 1 and matches[0].get('position') == [expected['x'],0,expected['z']], team+' spawn mismatch')
    camps = candidate.get('camps', [])
    require(len(camps) == len(authority['JUNGLE_CAMPS']), 'camp count mismatch')
    for expected in authority['JUNGLE_CAMPS']:
        camp = next((x for x in camps if x.get('id') == expected['id']), {})
        require(camp.get('position') == [expected['x'],0,expected['z']] and camp.get('species') == expected['species'], expected['id']+' camp mismatch')
    objectives = candidate.get('objectives', [])
    require(len(objectives) == len(authority['structures']), 'objective count mismatch')
    for expected in authority['structures']:
        obj = next((x for x in objectives if x.get('id') == expected['id']), {})
        require(obj.get('position') == [expected['x'],0,expected['z']] and all(obj.get(k) == expected[k] for k in ('team','kind','lane')), expected['id']+' objective mismatch')
        require(obj.get('radius') == authority['ARENA_RULES'][expected['kind']+'Radius'], expected['id']+' radius mismatch')
        require(obj.get('visual_only') is True, expected['id']+' review scope must be explicit')
    for section in ('props','lights','waters','districts','rotations'):
        values = candidate.get(section, [])
        require(len({x.get('id') for x in values}) == len(values), section+' duplicate ids')
        for value in values:
            for field in ('position','scale'):
                if field in value:
                    vector = value[field]
                    require(isinstance(vector,list) and len(vector)==3 and all(isinstance(v,(int,float)) and not isinstance(v,bool) for v in vector), value['id']+' invalid '+field)
                    if field=='scale':
                        require(all(v>0 for v in vector), value['id']+' nonpositive scale')
            if section in ('props','waters'):
                require(value.get('collision') in ('none','authority'), value['id']+' unknown collision policy')
            if section=='props' and value.get('collision')=='authority':
                match = next((x for x in boxes if x.get('id')==value.get('authority_collision_id')), {})
                require(match and value.get('position')==match.get('position') and value.get('scale')==match.get('size') and value.get('yaw_degrees')==0, value['id']+' rendered authority footprint mismatch')
    return errors


def flood(grid, origin):
    width, height = grid['width'], grid['height']
    start = point_cell(grid, origin)
    if grid['rows'][start[1]][start[0]] != '.':
        return {}
    distances = {start:0}
    queue = deque([start])
    while queue:
        x,z = queue.popleft()
        for nx,nz in ((x-1,z),(x+1,z),(x,z-1),(x,z+1)):
            if 0<=nx<width and 0<=nz<height and grid['rows'][nz][nx]=='.' and (nx,nz) not in distances:
                distances[nx,nz]=distances[x,z]+1
                queue.append((nx,nz))
    return distances


def point_cell(grid, point):
    return round((point[0]-grid['minX'])/grid['step']), round((point[2]-grid['minZ'])/grid['step'])


def navigation(authority, candidate):
    grid = authority['grid']
    maps = {s['team']:flood(grid,s['position']) for s in candidate['spawns']}
    checks = []
    for team, distances in maps.items():
        targets=[]
        for anchor in candidate['spawns']+candidate['camps']:
            targets.append((anchor['id'],anchor['position']))
        for lane in candidate['lanes']:
            for i, point in enumerate(lane['points']):
                targets.append((f'lane-{lane["id"]}-point-{i}',point))
        for obj in candidate['objectives']:
            # Approach ring is outside live structure + hero radii, including
            # .5m grid quantization margin. Centers must remain blocked.
            r = obj['radius']+candidate['bounds']['hero_radius']+.6
            for i in range(8):
                angle=i*math.pi/4
                targets.append((f'{obj["id"]}-approach-{i}',[obj['position'][0]+r*math.cos(angle),0,obj['position'][2]+r*math.sin(angle)]))
        unreachable = [name for name,point in targets if point_cell(grid,point) not in distances]
        checks.append({'name':team+' source authority navigation', 'passed':not unreachable,
                       'grid_step_m':grid['step'],'reachable_cells':len(distances),'anchors_and_approaches':len(targets),'unreachable':unreachable})
    open_count = sum(row.count('.') for row in grid['rows'])
    checks.append({'name':'all source-authority walkable sampled cells connected','passed':all(len(d)==open_count for d in maps.values()),'open_cells':open_count})
    centers = [obj['id'] for obj in candidate['objectives'] if grid['rows'][point_cell(grid,obj['position'])[1]][point_cell(grid,obj['position'])[0]]!='#']
    checks.append({'name':'living objective centers blocked in authority','passed':not centers,'incorrect_open':centers})
    # Independent topology failure fixture: sever the central horizontal row.
    cut = copy.deepcopy(grid)
    cut['rows'][round((0-cut['minZ'])/cut['step'])]='#'*cut['width']
    sun = next(s for s in candidate['spawns'] if s['team']=='sun')['position']
    moon = next(s for s in candidate['spawns'] if s['team']=='moon')['position']
    reached = flood(cut,sun)
    checks.append({'name':'negative disconnected-world fixture is detected','passed':point_cell(cut,moon) not in reached,'reachable_cells_after_cut':len(reached)})
    return checks


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path,default=DEFAULT_MAP)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    candidate=json.loads(args.manifest.read_text())
    source_hashes={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'games/yuga/shared/map.ts', ROOT/'games/yuga/shared/simulation.ts')}
    authority=authority_snapshot()
    errors=validate(candidate,authority)
    checks=[{'name':'manifest equals executed authority snapshot','passed':not errors,'errors':errors}]
    if not errors:
        checks+=navigation(authority,candidate)
    mutations=[
        ('missing blocker',lambda m:m['authority_collision_boxes'].pop(),'box count'),
        ('shifted blocker',lambda m:m['authority_collision_boxes'][0]['position'].__setitem__(0,-19),'geometry mismatch'),
        ('height mismatch',lambda m:m['authority_collision_boxes'][0]['size'].__setitem__(1,9),'geometry mismatch'),
        ('stale source',lambda m:m['source'].__setitem__('map_sha256','0'*64),'source hash'),
        ('blocked camp anchor',lambda m:m['camps'][0].__setitem__('position',[-20,0,-28]),'camp mismatch'),
        ('shifted spawn',lambda m:m['spawns'][0].__setitem__('position',[0,0,-70]),'spawn mismatch'),
        ('wrong objective radius',lambda m:m['objectives'][0].__setitem__('radius',0.2),'radius mismatch'),
        ('rotated authority visual',lambda m:m['props'][0].__setitem__('yaw_degrees',45),'footprint mismatch'),
        ('nonfinite placement',lambda m:m['props'][0]['position'].__setitem__(0,float('nan')),'nonfinite'),
        ('zero scale',lambda m:m['props'][0]['scale'].__setitem__(1,0),'nonpositive scale'),
        ('narrow native capsule',lambda m:m['bounds'].__setitem__('hero_radius',.29),'hero radius'),
        ('changed bounds',lambda m:m['bounds'].__setitem__('authority_xz',[-70,70,-85,85]),'movement bounds'),
    ]
    for name,mutate,wanted in mutations:
        fixture=copy.deepcopy(candidate)
        mutate(fixture)
        found=validate(fixture,authority)
        checks.append({'name':'reject '+name,'passed':any(wanted in e for e in found),'expected_error':wanted,'errors':found})
    unchanged=all(digest(ROOT/p)==h for p,h in source_hashes.items())
    checks.append({'name':'authority sources unchanged during checks','passed':unchanged})
    report={'passed':all(c['passed'] for c in checks),'scope':'Executed TypeScript authority data and .5m cardinal grid; live objective blockers included. Does not prove continuous navigation, gameplay AI, native physics, renders or performance.',
            'manifest':str(args.manifest.resolve().relative_to(ROOT)), 'manifest_sha256':digest(args.manifest),
            'test_sha256':digest(Path(__file__)), 'authority_sha256':source_hashes,'checks':checks}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
