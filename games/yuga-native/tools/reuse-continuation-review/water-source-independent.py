#!/usr/bin/env python3
"""Reuse the prior raw-module oracle's exact-coordinate whole-piece test."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import struct

parser = argparse.ArgumentParser()
parser.add_argument('--selection', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
if not args.report.is_absolute() or args.report.exists(): parser.error('Fresh absolute report required')
source = Path(__file__).resolve().parents[2] / 'assets/environment/lanka_courtyard.glb'
raw = source.read_bytes(); length = struct.unpack_from('<I', raw, 12)[0]
doc, binary = json.loads(raw[20:20+length]), raw[28+length:]
selection = json.loads(args.selection.read_text())

def accessor(key):
    a = doc['accessors'][key]; v = doc['bufferViews'][a['bufferView']]
    fmt = '<' + {5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']] * {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    stride = v.get('byteStride', struct.calcsize(fmt)); offset = v.get('byteOffset',0)+a.get('byteOffset',0)
    return [struct.unpack_from(fmt,binary,offset+i*stride) for i in range(a['count'])]

def inspect(spec):
    results = []
    for label, prototype in spec['prototypes'].items():
        total = collision = 0
        for row in prototype['selected']:
            node = next(n for n in doc['nodes'] if n.get('name') == row['node'])
            primitive = doc['meshes'][node['mesh']]['primitives'][row['surface']]
            points = accessor(primitive['attributes']['POSITION']); indices = [r[0] for r in accessor(primitive['indices'])]
            chosen = set(row['source_triangle_ids']); touched = collections.defaultdict(int)
            for face in range(len(indices)//3):
                for corner in range(3): touched[points[indices[face*3+corner]]] |= 1 if face in chosen else 2
            shared = sum(value == 3 for value in touched.values())
            valid = bool(chosen) and row['source_triangle_ids'] == sorted(chosen) and min(chosen) >= 0 and max(chosen)*3+2 < len(indices)
            results.append({'prototype':label,'node':row['node'],'triangles':len(chosen),'shared_with_unselected':shared,
                            'passed': valid and shared == 0 and set(node) == {'name','mesh'}})
            total += len(chosen)
            if row['collision']: collision += len(chosen)
        expected = {'column':(852,336,4),'diya':(492,44,3)}[label]
        results.append({'prototype':label,'counts':[total,collision,len(prototype['selected'])],'passed':(total,collision,len(prototype['selected'])) == expected})
    return {'passed': all(r['passed'] for r in results), 'rows': results}

positive = inspect(selection)
bad = copy.deepcopy(selection)
largest = max(bad['prototypes']['column']['selected'], key=lambda row:len(row['source_triangle_ids']))
removed = largest['source_triangle_ids'].pop(len(largest['source_triangle_ids'])//2)
negative = inspect(bad)
sha = lambda data: hashlib.sha256(data).hexdigest()
report = {'source_sha256':sha(raw),'selection_sha256':sha(args.selection.read_bytes()),'original':positive,
          'negative':{'scope':'One selected face removed in memory only','node':largest['node'],'removed_face':removed,'result':negative},
          'passed':positive['passed'] and not negative['passed'] and sha(raw) == selection['source_sha256'],
          'scope':'Independent exact-coordinate whole-source membership and partial-face negative; no render or world collision acceptance.'}
args.report.parent.mkdir(parents=True, exist_ok=True); args.report.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'rows':len(positive['rows']),'negative_detected':not negative['passed']}))
raise SystemExit(0 if report['passed'] else 1)
