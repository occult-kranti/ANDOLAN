"""Measure the fitted back strap's clearance above the rigid harness.

Run with Blender in background using the authored .blend as the input. For
each strap/trim vertex that has the shell below it, the check measures contact
along the unchanged rest-space dorsal axis and confirms identical bone
attachment on both surfaces. Thus the local clearance carries through rotation
or translation of that bone. This measures the source assembly and does not
test excursions against other armor or the decimated surface.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy


def check(name, shell, parts):
    measurements = []
    counts = {}
    for part in parts:
        count = 0
        for vertex in part.data.vertices:
            x, y, z = vertex.co
            hits = []
            for panel in shell:
                hit, location, _, _ = panel.ray_cast((x, .75, z), (0, -1, 0))
                if hit:
                    hits.append(location.y)
            if not hits:
                continue
            count += 1
            groups = {part.vertex_groups[influence.group].name: influence.weight
                      for influence in vertex.groups}
            if groups != {'spine01': 1.0}:
                raise ValueError(f'{part.name} does not share harness motion at vertex {vertex.index}: {groups}')
            measurements.append(y-max(hits))
        counts[part.name] = count
    if min(counts.values()) == 0:
        raise ValueError(f'Missing measured crossing: {counts}')
    minimum = min(measurements)
    if minimum < .006:
        raise ValueError(f'Under 6 mm dorsal protection margin in {name}: {minimum:.7f}')
    return {'blend':name,'sample_count':len(measurements),'minimum_clearance_m':minimum,
            'measured_vertices_by_surface':counts,'common_crossing_bone':'spine01'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    objects=list(bpy.data.objects)
    rig=next(obj for obj in objects if obj.type=='ARMATURE')
    rig.data.pose_position='REST'
    bpy.context.view_layer.update()
    shell=[obj for obj in objects if obj.name.startswith(('Shaped scapula harness','Rear harness piping'))]
    parts=[obj for obj in objects if obj.name.startswith(('Continuous sacred cross-back strap','Strap bound edge'))]
    if len(shell)!=3 or len(parts)!=3:
        raise ValueError('Expected one fitted shell and sash, two shell pipes and two selvedges')
    for obj in shell:
        for vertex in obj.data.vertices:
            influence = {obj.vertex_groups[g.group].name:g.weight for g in vertex.groups}
            if influence != {'spine01': 1.0}:
                raise ValueError(f'{obj.name} attachment changed at {vertex.index}')
    receipt=check(Path(bpy.data.filepath).name,shell,parts)
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print('HANUMAN_DORSAL '+json.dumps(receipt))


if __name__=='__main__':
    main()
