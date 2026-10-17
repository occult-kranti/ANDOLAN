#!/usr/bin/env python3
"""Read-only source resource census; never imports GLBs into an engine."""
import argparse, hashlib, json, struct
from pathlib import Path

SIZES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
WIDTHS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16, 'MAT3': 9, 'MAT2': 4}
def sha(data): return hashlib.sha256(data).hexdigest()
def objsha(value): return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
def census(path):
    raw = Path(path).read_bytes()
    magic, version, length = struct.unpack_from('<III', raw)
    assert (magic, version, length) == (0x46546c67, 2, len(raw))
    offset, doc, binary = 12, None, None
    while offset < length:
        size, kind = struct.unpack_from('<II', raw, offset); offset += 8
        chunk = raw[offset:offset+size]; offset += size
        if kind == 0x4e4f534a: doc = json.loads(chunk)
        elif kind == 0x004e4942: binary = chunk
    assert doc is not None and binary is not None
    def view(i):
        v = doc['bufferViews'][i]; start = v.get('byteOffset', 0)
        assert v.get('buffer', 0) == 0
        return binary[start:start+v['byteLength']]
    def accessor(i):
        a = doc['accessors'][i]
        width = SIZES[a['componentType']] * WIDTHS[a['type']]
        result = bytearray(width*a['count'])
        if 'bufferView' in a:
            v = doc['bufferViews'][a['bufferView']]
            step = v.get('byteStride', width); start = a.get('byteOffset', 0)
            data = view(a['bufferView'])
            result[:] = b''.join(data[start+j*step:start+j*step+width] for j in range(a['count']))
        if 'sparse' in a:
            s = a['sparse']; ix = s['indices']; val = s['values']
            indices, values = view(ix['bufferView']), view(val['bufferView'])
            fmt = {5121:'B',5123:'H',5125:'I'}[ix['componentType']]
            for j in range(s['count']):
                index = struct.unpack_from('<'+fmt, indices, ix.get('byteOffset',0)+j*SIZES[ix['componentType']])[0]
                begin = val.get('byteOffset',0)+j*width
                result[index*width:(index+1)*width] = values[begin:begin+width]
        return bytes(result)
    morph_ids, geometry_ids, skin_ids, index_ids = set(), set(), set(), set()
    rows = []
    for mesh in doc['meshes']:
        row = {'name': mesh.get('name'), 'vertices': 0, 'triangles': 0, 'primitives': len(mesh['primitives']), 'morph_names': mesh.get('extras', {}).get('targetNames', [])}
        for primitive in mesh['primitives']:
            assert primitive.get('mode', 4) == 4
            row['vertices'] += doc['accessors'][primitive['attributes']['POSITION']]['count']
            count = doc['accessors'][primitive['indices']]['count'] if 'indices' in primitive else doc['accessors'][primitive['attributes']['POSITION']]['count']
            assert count % 3 == 0
            row['triangles'] += count // 3
            geometry_ids.update(primitive['attributes'].values())
            skin_ids.update(i for k, i in primitive['attributes'].items() if k.startswith(('JOINTS_', 'WEIGHTS_')))
            if 'indices' in primitive: index_ids.add(primitive['indices'])
            for target in primitive.get('targets', []): morph_ids.update(target.values())
        rows.append(row)
    images = []
    for image in doc.get('images', []):
        assert 'bufferView' in image, 'External image needs explicit accounting'
        data = view(image['bufferView'])
        dims = list(struct.unpack_from('>II', data, 16)) if data[:8] == b'\x89PNG\r\n\x1a\n' else None
        images.append({'name': image.get('name'), 'mime': image.get('mimeType'), 'encoded_bytes': len(data), 'dimensions': dims, 'sha256': sha(data)})
    def total(ids): return sum(len(accessor(i)) for i in ids)
    def ahash(ids): return objsha([(i, sha(accessor(i))) for i in sorted(ids)])
    def stored(ids):
        views = set()
        for i in ids:
            a = doc['accessors'][i]
            if 'bufferView' in a: views.add(a['bufferView'])
            if 'sparse' in a:
                views.update(a['sparse'][k]['bufferView'] for k in ['indices','values'])
        return sum(len(view(i)) for i in views)
    inverse = {s['inverseBindMatrices'] for s in doc.get('skins', []) if 'inverseBindMatrices' in s}
    return {'path': str(Path(path).resolve()), 'sha256': sha(raw), 'file_bytes': len(raw),
        'vertices': sum(r['vertices'] for r in rows), 'triangles': sum(r['triangles'] for r in rows),
        'primitives': sum(r['primitives'] for r in rows), 'meshes': rows,
        'material_count': len(doc.get('materials', [])), 'texture_count': len(doc.get('textures', [])), 'images': images,
        'encoded_texture_bytes': sum(x['encoded_bytes'] for x in images),
        'source_skin_count': len(doc.get('skins', [])), 'joint_counts': [len(s['joints']) for s in doc.get('skins', [])],
        'unique_joint_nodes': len({i for s in doc.get('skins', []) for i in s['joints']}),
        'animation_count': len(doc.get('animations', [])),
        'geometry_attribute_logical_bytes': total(geometry_ids), 'index_logical_bytes': total(index_ids),
        'morph_accessor_count': len(morph_ids), 'morph_logical_bytes': total(morph_ids),
        'morph_stored_view_bytes': stored(morph_ids),
        'skin_attribute_logical_bytes': total(skin_ids), 'inverse_bind_logical_bytes': total(inverse),
        'identity': {'materials': objsha(doc.get('materials', [])), 'textures': objsha(doc.get('textures', [])),
            'nodes': objsha(doc.get('nodes', [])), 'skins': objsha(doc.get('skins', [])),
            'animations': objsha(doc.get('animations', [])), 'morph_bytes': ahash(morph_ids),
            'skin_bytes': ahash(skin_ids | inverse), 'index_bytes': ahash(index_ids)}}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--baseline', required=True); ap.add_argument('--near', required=True)
    ap.add_argument('--lod-directory'); ap.add_argument('--output', required=True); args = ap.parse_args()
    rows = {}
    for lod, suffix in [('near', ''), ('mid', '-mid'), ('far', '-far')]:
        rows['baseline_'+lod] = census(Path(args.baseline)/('rama-hero'+suffix+'.glb'))
    rows['candidate_near'] = census(args.near)
    if args.lod_directory:
        for lod in ['mid', 'far']:
            rows['candidate_'+lod] = census(Path(args.lod_directory)/('rama-hero-'+lod+'.glb'))
    comparisons = {}
    numeric = ['file_bytes','vertices','triangles','primitives','material_count','texture_count','encoded_texture_bytes','source_skin_count','unique_joint_nodes','animation_count','geometry_attribute_logical_bytes','index_logical_bytes','morph_accessor_count','morph_logical_bytes','morph_stored_view_bytes','skin_attribute_logical_bytes','inverse_bind_logical_bytes']
    for lod in ['near','mid','far']:
        if 'candidate_'+lod not in rows: continue
        a,b = rows['baseline_'+lod], rows['candidate_'+lod]
        comparisons[lod] = {'delta': {k:b[k]-a[k] for k in numeric}, 'identity_equal': {k:a['identity'][k]==b['identity'][k] for k in a['identity']}, 'images_byte_exact': a['images']==b['images']}
    out = {'schema':1,'scope':'Source GLB census. Logical accessor bytes are not GPU allocations; encoded images are not decoded or GPU resident texture memory. Vertices summed over mesh primitives; source skins do not imply live rigs.', 'candidate_revision':'r6','assets':rows,'comparisons':comparisons,
        'pending': ['actual imported candidate lifecycle','physical GPU frame time'] + ([] if args.lod_directory else ['corrected r6 mid/far source census'])}
    Path(args.output).write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({'output':args.output,'comparisons':comparisons,'near':{k:rows['candidate_near'][k] for k in numeric}},indent=2))
if __name__ == '__main__': main()
