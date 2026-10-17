#!/usr/bin/env python3
"""Independent design-placement checks; does not certify art or multiplayer."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT = ROOT / 'games/yuga-native/art/world/confluence-map.json'


def bounds(prop):
    x, _, z = prop['position']
    sx, _, sz = prop['scale']
    angle = math.radians(prop['yaw_degrees'])
    dx = (abs(math.cos(angle)) * sx + abs(math.sin(angle)) * sz) / 2
    dz = (abs(math.sin(angle)) * sx + abs(math.cos(angle)) * sz) / 2
    return x-dx, x+dx, z-dz, z+dz


def box_bounds(box):
    x, _, z = box['position']; sx, _, sz = box['size']
    return x-sx/2, x+sx/2, z-sz/2, z+sz/2


def inside(inner, outer, epsilon=1e-8):
    return inner[0] >= outer[0]-epsilon and inner[1] <= outer[1]+epsilon and inner[2] >= outer[2]-epsilon and inner[3] <= outer[3]+epsilon


def overlaps(a, b):
    return a[0] < b[1] and a[1] > b[0] and a[2] < b[3] and a[3] > b[2]


def point_clear(x, z, radius, data):
    x0, x1, z0, z1 = data['bounds']['authority_xz']
    if not (x0+radius <= x <= x1-radius and z0+radius <= z <= z1-radius):
        return False
    for box in data['authority_collision_boxes']:
        bx0, bx1, bz0, bz1 = box_bounds(box)
        # Matches the current authority's axis-expanded rectangle convention.
        if bx0-radius < x < bx1+radius and bz0-radius < z < bz1+radius:
            return False
    return True


def validate(data):
    errors=[]
    def require(condition, message):
        if not condition: errors.append(message)
    require(data.get('schema_version') == 1, 'schema_version')
    require(data['coordinate_contract']['ground_y'] == 0, 'flat ground contract')
    require(data['coordinate_contract']['controller_radius'] == data['bounds']['hero_radius'], 'controller radius contract')
    collections=['lanes','rotations','spawns','objectives','camps','authority_collision_boxes','districts','props','lights','waters']
    for key in collections:
        ids=[item['id'] for item in data[key]]
        require(len(ids)==len(set(ids)), key+' duplicate id')
    presets={preset for source in data['kit_sources'] for preset in source['presets']}
    presets.update(preset for values in data['builtin_presets'].values() for preset in values)
    boxes={box['id']:box for box in data['authority_collision_boxes']}
    arena=data['bounds']['authority_xz']
    for prop in data['props']:
        ident=prop['id']
        numbers=prop['position']+prop['scale']+[prop['yaw_degrees']]
        require(all(isinstance(n,(float,int)) and math.isfinite(n) for n in numbers), ident+' nonfinite transform')
        if not all(isinstance(n,(float,int)) and math.isfinite(n) for n in numbers): continue
        require(all(n>0 for n in prop['scale']), ident+' nonpositive scale')
        require(prop['preset'] in presets, ident+' unknown preset')
        require(prop['collision'] in ['none','authority'], ident+' collision enum')
        footprint=bounds(prop)
        if prop['collision']=='authority':
            require(prop.get('authority_collision_id') in boxes, ident+' missing collision association')
            continue
        if prop['kit']=='ground_inlay':
            require(prop['position'][1] + prop['scale'][1] <= .03, ident+' raised inlay becomes obstacle')
            continue
        if prop.get('placement_class')=='soft_vegetation':
            require(prop['scale'][1] <= 1.5, ident+' tall foliage obscures route')
            radius=math.hypot(prop['scale'][0],prop['scale'][2])/2
            for camp in data['camps']:
                distance=math.hypot(prop['position'][0]-camp['position'][0],prop['position'][2]-camp['position'][2])
                require(distance-radius >= camp['clear_radius'], ident+' vegetation in camp clearance')
            # The cross-mid link is a deliberately quiet east-west strip.
            require(abs(prop['position'][2])-radius >= 2, ident+' vegetation in mid crossing')
            continue
        if 'mount' in prop:
            mount=prop['mount'];box=boxes.get(mount['authority_collision_id'])
            require(box is not None, ident+' mount without box')
            if box:
                b=box_bounds(box);expanded=[b[0]-.22,b[1]+.22,b[2]-.22,b[3]+.22]
                require(inside(footprint,expanded), ident+' mount projects beyond exclusion')
                require(prop['position'][1] >= 1.9, ident+' low mounted obstacle')
            continue
        on_existing=any(inside(footprint,box_bounds(box)) for box in boxes.values())
        outside=not overlaps(footprint,arena)
        require(on_existing or outside, ident+' hard decorative prop in free traversal area')
    # Coarse whole-floor sampling identifies unthemed, omitted corners.
    for x in range(-68,69,4):
        for z in range(-82,83,4):
            require(any(area['bounds_xz'][0] <= x <= area['bounds_xz'][1] and area['bounds_xz'][2] <= z <= area['bounds_xz'][3] for area in data['districts']),f'unthemed floor {x},{z}')
    for route in data['rotations']:
        points=route['points']
        require(len(points)>=3 if route['closed'] else len(points)>=2, route['id']+' too few route points')
        pairs=list(zip(points,points[1:]))
        if route['closed']:pairs.append((points[-1],points[0]))
        clearance=route['clear_half_width']+data['bounds']['hero_radius']
        for start,end in pairs:
            distance=math.dist(start,end)
            require(distance>0,route['id']+' duplicate consecutive route point')
            for step in range(max(1,math.ceil(distance/.25))+1):
                fraction=step/max(1,math.ceil(distance/.25))
                x=start[0]+(end[0]-start[0])*fraction;z=start[2]+(end[2]-start[2])*fraction
                if not point_clear(x,z,clearance,data):
                    errors.append(route['id']+' corridor intersects authority collision');break
    for water in data['waters']:
        require(water['collision']=='none',water['id']+' water changes collision')
        if water['style']=='swamp':
            require(0 < water['position'][1] <= .02 and water['traversal']=='cosmetic_wet_ground_overlay',water['id']+' ambiguous swamp traversal')
    require(all(feature['status']=='not_active' for feature in data['reserved_future_features']),'future geometry silently active')
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map',type=Path,default=DEFAULT)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    raw=args.map.read_bytes();data=json.loads(raw)
    checks=[]
    def check(name,passed,details):checks.append(dict(name=name,passed=passed,details=details))
    errors=validate(data)
    check('canonical_layout_placement_and_route_contract',not errors,errors)
    cases=[]
    def case(name,mutate,expected):cases.append((name,mutate,expected))
    case('reject_unknown_kit',lambda d:d['props'][0].update(preset='missing_kit'),'unknown preset')
    case('reject_hard_prop_in_open_route',lambda d:d['props'].append(dict(id='bad-hard',kit='skyline',preset='lanka_shikhara',position=[0,0,0],yaw_degrees=0,scale=[3,10,3],collision='none')),'hard decorative prop')
    case('reject_route_through_building',lambda d:d['rotations'][0]['points'].__setitem__(0,[-20,0,-28]),'corridor intersects')
    case('reject_unreadable_camp_foliage',lambda d:next(p for p in d['props'] if p.get('placement_class')=='soft_vegetation').update(position=[-54,0,0]),'vegetation in camp')
    case('reject_hidden_swamp_water',lambda d:next(w for w in d['waters'] if w['style']=='swamp')['position'].__setitem__(1,-.03),'ambiguous swamp traversal')
    case('reject_oversized_wall_fixture',lambda d:next(p for p in d['props'] if 'mount' in p).update(scale=[4,4,4]),'mount projects')
    case('reject_activated_future_geometry',lambda d:d['reserved_future_features'][0].update(status='active'),'future geometry')
    case('reject_omitted_base_corners',lambda d:next(x for x in d['districts'] if x['id']=='sun-base').update(bounds_xz=[-55,55,-82,-60]),'unthemed floor')
    for name,mutate,expected in cases:
        bad=copy.deepcopy(data);mutate(bad);detected=validate(bad)
        check(name,any(expected in item for item in detected),detected[:5])
    protected={}
    for path in ['games/yuga-native/docs/GAME_DESIGN_MASTER.md','games/yuga-native/docs/FULL_GAME_PRODUCTION_ROADMAP.md']:
        protected[path]=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
    report=dict(passed=all(c['passed'] for c in checks),scope='Canonical planning: district coverage, route clearance and decorative placement. No rendered art, dynamic-authority physics, GPU or multiplayer acceptance.',map_sha256=hashlib.sha256(raw).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),protected_design_observed_hashes=protected,counts={key:len(data[key]) for key in ['props','lights','districts','rotations','authority_collision_boxes']},checks=checks)
    if args.report:args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
