"""Compose the cleared shoulder onto the accepted sash UV parent, without shape edits."""
import copy, json, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from replace_left_cap import GLB, ROOT, sha, replace

UV_PINS = {
    'near': 'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e',
    'mid': 'b5949c9d427e9684a13fa525212eedc87dfa207d2c70fba5ebe6a4b1eda61005',
    'far': 'aef8ae5837c0bf0a9ed5850ae649d6368ec1e87c0728d501f1780bba325a9d6a',
}
RANGES = {'near': (7716, 9790), 'mid': (2211, 3180), 'far': (956, 1389)}
OLD_MANIFEST = 'b6138958b605df8e863cf67d8b424ada90a0e2df08260d53bd78fec185a57cef'


def scale_uv(binary, doc, accessor, first, stop):
    a = doc['accessors'][accessor]
    v = doc['bufferViews'][a['bufferView']]
    assert a['type'] == 'VEC2' and a['componentType'] == 5126
    assert not a.get('sparse') and v.get('byteStride', 8) == 8
    offset = v.get('byteOffset', 0) + a.get('byteOffset', 0) + first * 8
    count = stop - first
    uv = np.frombuffer(binary, dtype='<f4', count=count * 2, offset=offset).copy().reshape(-1, 2)
    binary[offset:offset + count * 8] = (uv.astype(float) * [.20, .95]).astype('<f4').tobytes()
    return {'accessor': accessor, 'first_row': first, 'stop_row_exclusive': stop,
            'byte_offset': offset, 'byte_length': count * 8}


def main():
    out = HERE / 'replacement-r7'
    report_path = HERE / 'accepted-uv-composition-r7.json'
    assert not out.exists() and not report_path.exists()
    old_path = HERE / 'replacement-r6/replacement-manifest.json'
    assert sha(old_path) == OLD_MANIFEST
    old_manifest = json.loads(old_path.read_text())
    admission = HERE / 'source-admission-r6.json'
    rounding = HERE / 'stored-pose-margin-r6.json'
    assert json.loads(admission.read_text())['passed_source_gate']
    assert json.loads(rounding.read_text())['passed']
    out.mkdir()
    levels, proofs = {}, []
    for level, pin in UV_PINS.items():
        prior = old_manifest['levels'][level]
        old = GLB(prior['source'])
        previous = GLB(prior['output'])
        assert sha(old.path) == prior['source_sha256'] and sha(previous.path) == prior['sha256']
        filename = 'rama-hero' + ('' if level == 'near' else '-' + level) + '.glb'
        source = GLB(ROOT / 'art/hero-finish/sash-texel-r1/candidate-r2' / filename)
        assert sha(source.path) == pin and source.doc == old.doc
        first, stop = RANGES[level]
        old_uv = old.doc['meshes'][2]['primitives'][3]['attributes']['TEXCOORD_0']
        expected_parent = bytearray(old.binary)
        parent_range = scale_uv(expected_parent, old.doc, old_uv, first, stop)
        assert bytes(expected_parent) == source.binary, 'Parent differs outside exact accepted sash UV scale'
        sculpture = GLB(prior['sculpture'])
        assert sha(sculpture.path) == prior['sculpture_sha256']
        levels[level] = replace(source, sculpture, out / filename)
        candidate = GLB(out / filename)
        assert candidate.doc == previous.doc, 'Composition changed GLB JSON semantics'
        expected = bytearray(previous.binary)
        retained = scale_uv(expected, previous.doc, old_uv, first, stop)
        active_uv = previous.doc['meshes'][2]['primitives'][3]['attributes']['TEXCOORD_0']
        assert active_uv != old_uv
        active = scale_uv(expected, previous.doc, active_uv, first, stop)
        assert bytes(expected) == candidate.binary, 'Composition changed bytes outside two sash UV copies'
        assert candidate.binary[:len(source.binary)] == source.binary
        proofs.append({'level': level, 'accepted_parent_sha256': pin,
                       'previous_shoulder_sha256': prior['sha256'],
                       'candidate_sha256': levels[level]['sha256'],
                       'parent_uv_edit': parent_range,
                       'replacement_uv_edits': [retained, active],
                       'all_other_BIN_bytes_and_full_JSON_exact': True,
                       'accepted_parent_prefix_exact': True,
                       'new_shoulder_UV_exact': True,
                       'geometry_rig_material_masks_and_contacts_unchanged': True})
        print(level, levels[level]['sha256'], flush=True)
    manifest = copy.deepcopy(old_manifest)
    manifest.update(generator_sha256=sha(__file__), levels=levels,
                    base_generator_sha256=sha(HERE / 'replace_left_cap.py'),
                    accepted_parent='smooth crown R2 plus accepted sash UV R2; no unaccepted hair',
                    previous_shoulder_manifest_sha256=OLD_MANIFEST)
    (out / 'replacement-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = {'schema': 1, 'passed': True, 'checker_sha256': sha(__file__),
              'previous_manifest_sha256': OLD_MANIFEST,
              'replacement_manifest_sha256': sha(out / 'replacement-manifest.json'),
              'source_admission_sha256': sha(admission),
              'stored_pose_margin_sha256': sha(rounding), 'levels': proofs,
              'scope': 'Exact UV-only transitive composition. Every checked geometric position, triangle, skin, frame, mask, material and pose input remains identical to replacement-r6. This transfers its bounded source-contact results, not an imported or rendered acceptance. No hair candidate is included.'}
    report_path.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
