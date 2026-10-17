"""Validate the exported production hero independently of Blender's exporter.

python games/yuga-native/art/production/validate_rama.py
Structural checks do not certify art quality or absence of intersections.
"""
from pathlib import Path
import hashlib, json, math, struct

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
META = HERE / 'rama-production.provenance.json'


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<4sII', data)
    assert magic == b'glTF' and version == 2 and length == len(data)
    json_size, json_kind = struct.unpack_from('<II', data, 12)
    assert json_kind == 0x4E4F534A
    doc = json.loads(data[20:20 + json_size])
    binary_offset = 20 + json_size
    binary_size, binary_kind = struct.unpack_from('<II', data, binary_offset)
    assert binary_kind == 0x004E4942
    binary = data[binary_offset + 8:binary_offset + 8 + binary_size]
    assert len(binary) == binary_size
    return data, doc, binary


def accessor(doc, binary, index):
    item = doc['accessors'][index]
    view = doc['bufferViews'][item['bufferView']]
    code, size = {5120:('b',1),5121:('B',1),5122:('h',2),5123:('H',2),5125:('I',4),5126:('f',4)}[item['componentType']]
    count = {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[item['type']]
    offset = view.get('byteOffset', 0) + item.get('byteOffset', 0)
    stride = view.get('byteStride', count * size)
    assert offset + (item['count'] - 1) * stride + size * count <= len(binary)
    return [struct.unpack_from('<' + code * count, binary, offset + i * stride) for i in range(item['count'])]


def main():
    meta = json.loads(META.read_text())
    data, doc, binary = read_glb(ROOT / meta['output'])
    assert hashlib.sha256(data).hexdigest() == meta['sha256']
    assert len(data) == meta['bytes'] and len(data) < 25 * 1024 * 1024
    assert hashlib.sha256((ROOT/meta['generator']).read_bytes()).hexdigest() == meta['generatorSha256']
    for texture in meta['textureFiles']:
        assert hashlib.sha256((ROOT/texture['file']).read_bytes()).hexdigest() == texture['sha256']
    assert len(doc['skins']) == 1 and len(doc['skins'][0]['joints']) == 164
    assert len(doc['meshes']) == 1
    joint_names = [doc['nodes'][i]['name'] for i in doc['skins'][0]['joints']]
    assert len(set(joint_names)) == 164 and 'bowstring' in joint_names
    expected = {'idle','run','fire','cast','cast1','cast2','cast3','jump','defeat'}
    assert {a['name'] for a in doc['animations']} == expected
    primitives = doc['meshes'][0]['primitives']
    vertex_count = triangles = 0
    for primitive in primitives:
        attributes = primitive['attributes']
        assert {'POSITION','NORMAL','TANGENT','TEXCOORD_0','JOINTS_0','WEIGHTS_0'} <= attributes.keys()
        values = {key:accessor(doc, binary, value) for key, value in attributes.items()}
        count = len(values['POSITION']); vertex_count += count
        assert all(len(v) == count for v in values.values())
        assert all(math.isfinite(c) for value in values.values() for row in value for c in row)
        for normal in values['NORMAL']:
            assert abs(sum(x*x for x in normal)-1) < .005
        for tangent in values['TANGENT']:
            assert abs(sum(x*x for x in tangent[:3])-1) < .005 and abs(abs(tangent[3])-1) < .001
        for weights in values['WEIGHTS_0']:
            assert min(weights) >= 0 and abs(sum(weights)-1) < .001
        for joints in values['JOINTS_0']:
            assert all(0 <= j < 164 for j in joints)
        indices = accessor(doc, binary, primitive['indices'])
        assert len(indices) % 3 == 0 and all(0 <= i[0] < count for i in indices)
        triangles += len(indices)//3
    assert vertex_count == meta['vertices'] and triangles == meta['triangles']
    for animation in doc['animations']:
        for sampler in animation['samplers']:
            times = [x[0] for x in accessor(doc, binary, sampler['input'])]
            assert all(math.isfinite(t) and t >= 0 for t in times)
            assert all(b > a for a,b in zip(times,times[1:]))
            assert all(math.isfinite(c) for v in accessor(doc,binary,sampler['output']) for c in v)
    assert len(meta['poseSamples']) == 45
    assert meta['handAnatomyVerticesPreserved'] > 0 and meta['trousersExcludeHandArmGroups'] is True
    assert meta['lowerLegFaceCoverage']['eligibleFaces'] > 0 and meta['lowerLegFaceCoverage']['omittedFaces'] == 0
    for image in doc['images']:
        assert 'bufferView' in image and 'uri' not in image
    result = dict(status='pass', sha256=meta['sha256'], vertices=vertex_count, triangles=triangles,
                  joints=164, clips=sorted(expected), embeddedImages=len(doc['images']),
                  handAnatomyVerticesPreserved=meta['handAnatomyVerticesPreserved'],
                  lowerLegFaceCoverage=meta['lowerLegFaceCoverage'],
                  checks=['GLB length and hashes','generator and original texture hashes','finite accessors',
                          'normalized normals/tangents/weights','joint and triangle indices',
                          'strictly increasing animation times','45 recorded bounded pose samples',
                          'recorded hand preservation and garment exclusion assertions',
                          'zero omitted eligible lower-leg faces'],
                  limitation='Structural validation does not certify concept likeness, clipping, anatomy or visual quality.')
    (HERE/'rama-production.validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__': main()
