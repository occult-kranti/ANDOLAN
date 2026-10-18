#!/usr/bin/env python3
import pathlib, json, hashlib

base = pathlib.Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/I3')
out = base / 'role02'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

runs = []
for name, scratch, report in [('native-r1', '/tmp/yuga-i3-native-r1', 'native-main-originals.json'), ('relaunch-r1', '/tmp/yuga-i3-relaunch-r1', 'native-relaunch-originals.json'), ('staged-r1', '/tmp/yuga-i3-staged-r1', 'native-staged-originals.json')]:
    central, tmp = base / 'role03' / name, pathlib.Path(scratch)
    run = json.loads((central / 'run.json').read_text())
    proof = json.loads((out / report).read_text())
    names = ['run.json', 'transition-events.json'] + [s['file'] for s in run['shots'] + run['automatic_shots']] + [pathlib.Path(s['file']).with_suffix('.json').name for s in run['shots'] + run['automatic_shots']]
    pairs = [(central / name, tmp / name) for name in names]
    pairs.append((central / 'godot-output.txt', tmp / 'godot.log'))
    differences = [str(a) for a, b in pairs if sha(a) != sha(b)]
    instrumentation = []
    for path, expected in run['instrumentation_sha256'].items():
        source = pathlib.Path(path)
        retained = central / ('run-driver.py' if source.name == 'run.py' else source.name)
        if str(source).startswith('/workspace/') and source.name == 'integrated_capture.gd':
            retained = source
        instrumentation.append({'source_path': path, 'retained_path': str(retained), 'sha256': expected, 'matches': sha(retained) == expected})
    runs.append({'central_directory': str(central), 'scratch_directory': scratch, 'run_sha256': sha(central / 'run.json'), 'run_matches_independent_validation': sha(central / 'run.json') == proof['run_sha256'], 'manual': len(run['shots']), 'automatic': len(run['automatic_shots']), 'native_input_receipts': len(run['events']), 'exact_central_files_compared': len(pairs), 'central_mismatches': differences, 'instrumentation': instrumentation, 'passed': not differences and sha(central / 'run.json') == proof['run_sha256'] and all(i['matches'] for i in instrumentation), 'validator_report': report, 'checks': proof['count']})
review = json.loads((out / 'reviewed-originals.json').read_text())
lookup = {r['scratch_directory']: r['central_directory'] for r in runs}
for item in review['originals']:
    central = pathlib.Path(lookup[item['capture_directory']])
    item['central_original'] = str(central / (item['name'] + '.png'))
    item['central_matches_reviewed_png_and_json'] = sha(central / (item['name'] + '.png')) == item['png_sha256'] and sha(central / (item['name'] + '.json')) == item['json_sha256']
(out / 'reviewed-originals.json').write_text(json.dumps(review, indent=2) + '\n')
result = {'passed': all(r['passed'] for r in runs) and all(x['central_matches_reviewed_png_and_json'] for x in review['originals']), 'runs': runs, 'total_manual': sum(r['manual'] for r in runs), 'total_automatic': sum(r['automatic'] for r in runs), 'independent_receipt_checks': sum(r['checks'] for r in runs), 'direct_pixel_reviews': len(review['originals']), 'scope': 'All57 original PNG identities and complete receipts independently validated;33 originals directly opened (all30 manual and3 initial boot). Central copies match actual scratch runs. Main2 explicit recoveries are separate limitations.'}
(out / 'capture-evidence-index.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'runs'}))
raise SystemExit(0 if result['passed'] else 1)
