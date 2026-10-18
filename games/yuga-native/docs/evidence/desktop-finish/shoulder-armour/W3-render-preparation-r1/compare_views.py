"""Compare the fresh four-view pair; no timing/pose alignment or engine execution."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

IDS = ['rest-front', 'rest-profile', 'rest-rear', 'cast-three-quarter']
SELECTION = {
    'baseline': {'Worked warm gold': 5896, 'Recessed antique gold': 2498, 'Polished sapphire': 722},
    'candidate': {'Worked warm gold': 3146, 'Cobalt handwoven silk': 850, 'Recessed antique gold': 152}}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cloth_census(folder):
    data = json.loads((folder / 'semantics.json').read_text())
    counts = dict(anchored_vertices=0, masked_vertices=0)
    rows = []
    for lod in data['lods']:
        for node in lod['nodes']:
            if not node['path'].endswith('/RamaHero'):
                continue
            for surface in node['surfaces']:
                name = surface['material']['name']
                if name not in ('Worked warm gold', 'Cobalt handwoven silk'):
                    continue
                array = next(x for x in surface['arrays'] if x['index'] == 3)
                raw = (folder / array['file']).read_bytes()
                assert len(raw) == array['count'] * 16 and sha(folder / array['file']) == array['raw_sha256']
                alpha = [x[3] for x in struct.iter_unpack('<ffff', raw)]
                assert all(math.isfinite(x) and 0 <= x <= 1 for x in alpha)
                anchored = sum(x <= .001 for x in alpha)
                masked = len(alpha) - anchored
                counts['anchored_vertices'] += anchored
                counts['masked_vertices'] += masked
                rows.append(dict(lod=lod['path'], material=name, anchored=anchored, masked=masked, sha256=sha(folder / array['file'])))
    assert len(rows) == 6
    return dict(counts=counts, rows=rows)


def differences(a, b, path=''):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b:
                out.append(path + '/' + key)
            else:
                out += differences(a[key], b[key], path + '/' + key)
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [path + '/length']
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [path]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--mode', choices=('preflight', 'render'), required=True)
    args = parser.parse_args()
    pins = json.loads((Path(__file__).parent / 'inputs.json').read_text())
    work = args.work
    reports, cleaned, census = {}, {}, {}
    output = work / (args.mode + '-comparison.json')
    assert not output.exists()
    for branch in ('baseline', 'candidate'):
        path = work / (args.mode + '-' + branch) / ('preflight.json' if args.mode == 'preflight' else 'capture.json')
        report = json.loads(path.read_text())
        assert report['complete'] and report['source_unchanged']
        assert report['source_sha256'] == report['source_after_sha256']
        assert [x['id'] for x in report['shots']] == IDS
        assert report['audio_cleanup']['observed_mixer_ticks'] == 2 and report['audio_cleanup']['wait_usec'] <= 250000
        clean = copy.deepcopy(report)
        clean.pop('wall_elapsed_ms', None)
        for key in ('samples', 'wait_usec'):
            clean['audio_cleanup'].pop(key)
        for key in ('controls', 'sequence_controls'):
            if key in clean:
                assert clean[key][0]['kind'] == 'shoulder_source_comparison' and clean[key][0]['branch'] == branch
                clean[key][0].pop('branch')
        for field in ('source_sha256', 'source_after_sha256'):
            for raw, expected in pins['raw_pins'][branch].items():
                key = 'res://assets/heroes/' + raw
                assert clean[field].pop(key) == expected
        for shot in clean['shots']:
            assert shot.pop('shoulder_branch') == branch
            assert len(shot['rendered_pose_globals']) == 164
            shot.pop('sha256', None)
            bounds = shot['bounds']
            assert bounds['passed'] and bounds['selection_passed'] and bounds['behind'] == 0 and bounds['margin_pixels'] == 24
            assert bounds['selected_material_vertices'] == bounds['expected_material_vertices'] == SELECTION[branch]
            assert bounds['vertices'] == sum(SELECTION[branch].values())
            for key in ('min', 'max'):
                assert all(math.isfinite(v) for v in bounds[key])
            for key in ('min', 'max', 'vertices', 'selected_material_vertices', 'expected_material_vertices'):
                bounds.pop(key)
            for key in ('anchored_vertices', 'masked_vertices'):
                shot['secondary'][key].pop('cloth')
        reports[branch] = report
        cleaned[branch] = clean
        census[branch] = cloth_census(work / ('semantics-' + branch))
    census_ok = all(
        y['secondary'][kind]['cloth'] - x['secondary'][kind]['cloth'] ==
        census['candidate']['counts'][kind] - census['baseline']['counts'][kind]
        for x, y in zip(reports['baseline']['shots'], reports['candidate']['shots'])
        for kind in ('anchored_vertices', 'masked_vertices'))
    unexpected = differences(cleaned['baseline'], cleaned['candidate'])
    result = {'passed': census_ok and not unexpected, 'mode': args.mode,
              'cloth_census_delta_matches_actual_imports': census_ok, 'imported_changed_material_census': census,
              'unexpected_paths': unexpected,
              'scope': 'Exact report comparison apart from admitted raw/branch/image/wall-cleanup fields, selected shoulder bounds/counts, and independently imported cloth census delta. All164 poses, events, cameras/light/LOD/face/secondary offsets and clocks remain exact.'}
    with output.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    assert result['passed'], unexpected


if __name__ == '__main__':
    main()
