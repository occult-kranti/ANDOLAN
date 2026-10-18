"""Independent, read-only review of the exact packaged native capture receipts."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zipfile

ROOT = Path(__file__).parent
EXPECTED_HEAD = '9e81a7c849837dea477ddb5a8c93f43665774573'
EXPECTED_ZIP = '56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5'
EXPECTED_PCK = 'd387d34ad37fc959f974b9ced0107d5ad2a0e2505e55a090dd20fc583d62aa27'


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def digest_stream(stream):
    h = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b''):
        h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--first', type=Path, required=True)
    parser.add_argument('--second', type=Path)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    checks = []

    def check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    manifest = read(args.package / 'native-package-manifest.json')
    archive = args.package / manifest['packages']['linux']['filename']
    run = read(args.first / 'run.json')
    engine = Path(run['command'][0])
    pck = Path(run['command'][run['command'].index('--main-pack') + 1])
    prefix = 'yuga-native-linux-x86_64/'
    members = {}
    with zipfile.ZipFile(archive) as z:
        embedded = json.loads(z.read(prefix + 'PACKAGE-MANIFEST.json'))
        for info in z.infolist():
            with z.open(info) as f:
                digest = digest_stream(f)
            relative = info.filename.removeprefix(prefix)
            members[relative] = {'bytes': info.file_size, 'sha256': digest,
                                 'extracted_sha256': sha(engine.parent / relative)}
    check('exact archive and embedded source identity',
          sha(archive) == EXPECTED_ZIP == manifest['packages']['linux']['sha256']
          and manifest['git']['head'] == embedded['git']['head'] == EXPECTED_HEAD,
          {'archive_sha256': sha(archive), 'source': embedded['git']['head'], 'member_count': len(members)})
    declared = embedded['payloads']
    check('all archive payloads match declared bytes and actual extraction',
          len(members) == 29 and set(members) == set(declared) | {'PACKAGE-MANIFEST.json'}
          and all(v['sha256'] == v['extracted_sha256'] for v in members.values())
          and all(members[k]['sha256'] == v['sha256'] and members[k]['bytes'] == v['bytes']
                  for k, v in declared.items()),
          {'declared_payloads': len(declared), 'members': members})
    check('actual launched engine/PCK bind to this archive and content6 source proof',
          sha(pck) == EXPECTED_PCK == run['package_sha256'][str(pck)]
          and sha(engine) == run['engine_sha256'] == run['package_sha256'][str(engine)]
          and run['package_archive']['sha256'] == EXPECTED_ZIP
          and embedded['native_contracts']['checks'] == 51
          and run['source_sha256'] == {k: v['sha256'] for k, v in embedded['runtime_source']['files'].items()},
          {'command': run['command'], 'engine_sha256': sha(engine), 'pck_sha256': sha(pck),
           'native_contract_checks': embedded['native_contracts']['checks'],
           'runtime_source_aggregate': embedded['runtime_source']['sha256'], 'runtime_source_count': len(run['source_sha256'])})

    def shot(stem):
        return read(args.first / (stem + '.json'))

    a, b = [shot('0%d-package-title-idle-%s' % (i, letter)) for i, letter in [(1, 'a'), (2, 'b')]]
    check('inactive title animation advances while combat remains suspended',
          not a['state']['player_active'] and not b['state']['player_active']
          and not a['presentation']['suspended'] and not b['presentation']['suspended']
          and b['physics_frame'] > a['physics_frame']
          and b['presentation']['motion']['locomotion_age'] > a['presentation']['motion']['locomotion_age']
          and b['presentation']['secondary']['elapsed'] > a['presentation']['secondary']['elapsed']
          and b['presentation']['face']['elapsed'] > a['presentation']['face']['elapsed']
          and a['kit']['elapsed'] == b['kit']['elapsed'] == 0
          and a['kit']['suspended'] and b['kit']['suspended'],
          {'physics_ticks': b['physics_frame'] - a['physics_frame'],
           'idle_age': [a['presentation']['motion']['locomotion_age'], b['presentation']['motion']['locomotion_age']]})

    film, returned = shot('06-package-film'), shot('07-package-film-return-selection')
    check('film return preserves session training selection and visible primary focus',
          film['scene_path'] == 'res://scenes/combat_film.tscn'
          and returned['scene_path'] == 'res://scenes/courtyard.tscn'
          and returned['launch']['selected_mode'] == 'train'
          and returned['focus_text'] == 'Begin bow training  →'
          and any(c['focus'] and c['interactive'] and c['text'] == returned['focus_text'] for c in returned['controls'])
          and not returned['paused'] and not returned['state']['started'],
          {'selected_mode': returned['launch']['selected_mode'], 'focus': returned['focus'], 'focus_text': returned['focus_text']})

    hold_a, hold_b, resumed = [shot(s) for s in ['09-package-overview-unreleased-a', '10-package-overview-unreleased-b', '11-package-overview-resumed-release']]
    motion_keys = ['action', 'action_elapsed', 'stage', 'release_count', 'cancel_count', 'locomotion_age', 'phase', 'aim_weight', 'nocked']
    motion_equal = all(hold_a['presentation']['motion'][k] == hold_b['presentation']['motion'][k] for k in motion_keys)
    check('overview holds unreleased combat and presentation across progressing native physics',
          hold_b['physics_frame'] - hold_a['physics_frame'] >= 45
          and all(d['state']['overview'] and not d['state']['player_active'] and not d['paused'] and d['presentation']['suspended'] for d in [hold_a, hold_b])
          and motion_equal and hold_a['presentation']['motion']['stage'] == 'windup'
          and hold_a['kit'] == hold_b['kit'] and hold_a['army'] == hold_b['army']
          and hold_a['presentation']['face'] == hold_b['presentation']['face']
          and hold_a['presentation']['secondary'] == hold_b['presentation']['secondary']
          and hold_a['hero_hud'] == hold_b['hero_hud']
          and hold_a['kit']['release_count'] == 0 and hold_a['kit']['casts'][0]['released'] is False,
          {'physics_ticks': hold_b['physics_frame'] - hold_a['physics_frame'],
           'motion_age': hold_a['presentation']['motion']['action_elapsed'],
           'kit_age': hold_a['kit']['casts'][0]['age_s'], 'kit_elapsed': hold_a['kit']['elapsed'],
           'secondary_elapsed': hold_a['presentation']['secondary']['elapsed'],
           'face_elapsed': hold_a['presentation']['face']['elapsed'], 'army_elapsed': hold_a['army']['elapsed']})
    check('native F1 resume releases accepted cast exactly once',
          not resumed['state']['overview'] and resumed['state']['player_active']
          and not resumed['presentation']['suspended'] and not resumed['kit']['suspended']
          and resumed['kit']['accepted_casts'] == 1
          and resumed['kit']['release_count'] == resumed['presentation']['motion']['release_count'] == 1
          and resumed['kit']['active_cast_id'] == hold_a['kit']['active_cast_id']
          and resumed['kit']['generation'] == hold_a['kit']['generation']
          and resumed['kit']['casts'][0]['released'] is True,
          {'kit_cast_age': resumed['kit']['casts'][0]['age_s'], 'motion_stage': resumed['presentation']['motion']['stage'],
           'kit_elapsed': resumed['kit']['elapsed'], 'notice': resumed['hero_hud']['notice']})

    transitions = read(args.first / 'transition-events.json')['events']
    active = [e for e in transitions if e['busy']]
    loader_frames = [read(p) for p in args.first.glob('auto-*.json')]
    check('observed loader uses one owner and processable input across native routes',
          bool(active) and len({e['instance_id'] for e in transitions}) == 1
          and all(e['owner_present'] and e['visible'] and e['scene_process_mode'] == 4 for e in active)
          and bool(loader_frames)
          and all(not d['scene_can_process'] and d['transition_owner_present']
                  and d['loader_count'] == d['transition_layer_count'] == 1
                  and any(c['focus'] and c['interactive'] and c['text'] == 'Back' for c in d['controls'])
                  and not any(c['interactive'] and c['text'] != 'Back' for c in d['controls'])
                  for d in loader_frames),
          {'events': len(transitions), 'active_events': len(active), 'loader_frames': len(loader_frames),
           'destinations': sorted({e['destination'] for e in transitions}),
           'note': 'Synchronous queued signal precedes grab_focus. All displayed loader frames must have focused Back and isolated source input. Only individually listed originals received pixel review.'})

    runs = [args.first] + ([args.second] if args.second else [])
    pngs = {}
    for directory in runs:
        for f in directory.glob('*.png'):
            metadata = read(f.with_suffix('.json'))
            size = list(struct.unpack('>II', f.read_bytes()[16:24]))
            pngs[str(f)] = {'sha256': sha(f), 'metadata_sha256': metadata['sha256'], 'pixels': size, 'native_window': metadata['size']}
    check('all produced originals bind to capture metadata and explicit content dimensions',
          bool(pngs) and all(v['sha256'] == v['metadata_sha256'] and v['pixels'] == [960, 540] and v['native_window'] == [960, 600] for v in pngs.values()),
          {'originals_count': len(pngs), 'originals': pngs, 'note': 'Hash verification is not visual inspection of every original.'})

    lifecycle = []
    run_records = []
    for directory in runs:
        item = read(directory / 'run.json')
        run_records.append(item)
        lifecycle.append({'directory': str(directory), 'complete': item['complete'], 'keys': list(item),
                          'verified_exit': item.get('verified_exit_code'), 'cleanup_exit': item.get('cleanup_exit'),
                          'authority_staging': item['authority_staging'],
                          'user_state': item['user_state'], 'package_archive': item['package_archive'],
                          'run_sha256': sha(directory / 'run.json')})
    if args.second:
        errors = {}
        instrumentation = []
        for directory in runs:
            errors[str(directory)] = [line for line in (directory / 'godot.log').read_text().splitlines()
                                      if line.startswith(('ERROR:', 'WARNING:', 'SCRIPT ERROR:'))]
            for path, expected in read(directory / 'run.json')['instrumentation_sha256'].items():
                actual = Path(path)
                if actual.name == 'run.py' and (directory / 'run-driver.py').exists():
                    actual = directory / 'run-driver.py'
                instrumentation.append({'path': str(actual), 'expected': expected, 'actual': sha(actual)})
        check('two complete native processes quit cleanly using unchanged package and same isolated preferences',
              all(r['complete'] and r.get('verified_exit_code') == 0 and r.get('cleanup_exit') == 0
                  and r.get('package_unchanged') and r.get('instrumentation_unchanged')
                  and not r['authority_staging']['enabled'] and not r['authority_staging']['stages']
                  and r['package_archive']['sha256'] == EXPECTED_ZIP for r in run_records)
              and not any(errors.values())
              and all(p['expected'] == p['actual'] for p in instrumentation)
              and run_records[0]['user_state']['path'] == run_records[1]['user_state']['path']
              and run_records[0]['user_state']['after'] == run_records[1]['user_state']['before']
              and run_records[1]['started_unix'] > run_records[0]['finished_unix'],
              {'runs': lifecycle, 'engine_errors_warnings': errors, 'instrumentation': instrumentation})
        relaunched = read(args.second / 'R00-package-relaunched-title.json')
        check('second process mounts ready title and primary action with persisted preference state',
              relaunched['scene_path'] == 'res://scenes/courtyard.tscn'
              and relaunched['state']['hero_ready'] and not relaunched['state']['started']
              and not relaunched['presentation']['suspended']
              and relaunched['launch']['launch_state'] == 'ready'
              and relaunched['focus_text'] == 'Enter Confluence  →'
              and relaunched['state']['sensitivity'] == 2.5 and relaunched['state']['invert_y']
              and relaunched['state']['volume'] == 0 and relaunched['state']['shadows'] is False,
              {'focus': relaunched['focus_text'], 'selected_mode': relaunched['launch']['selected_mode'],
               'state': relaunched['state'], 'note': 'Mode choice is session context; persisted preferences are separate.'})
        recovery = read(args.first / 'native-recovery.json')
        recovery_title = read(args.first / 'native-recovery-title.json')
        coordinate = read(args.first / 'coordinate-recovery-analysis.json')
        resumed_event = next(e for e in run['events'] if e.get('capture') == '11-package-overview-resumed-release')
        check('late native recoveries remain explicit and occur after the hold/resume witness',
              coordinate['settled_pointer_hits'] == ['Restart lane practice']
              and [e['event'] for e in recovery['events']] == [{'key': 'Escape'}, {'key': 'F3'}]
              and recovery['after']['paused'] and recovery['after']['panels']['rama_panel']
              and recovery_title['after']['panels']['settings_panel']
              and all(e['time_unix'] > resumed_event['time_unix'] for e in recovery['events'] + recovery_title['events'])
              and all(e['window_id'] == resumed_event['window_id'] for e in recovery['events'] + recovery_title['events']),
              {'coordinate_sha256': sha(args.first / 'coordinate-recovery-analysis.json'),
               'world_recovery_sha256': sha(args.first / 'native-recovery.json'),
               'title_recovery_sha256': sha(args.first / 'native-recovery-title.json'),
               'note': 'First run is not an uninterrupted planned route. Original stale guide coordinate hit Restart; native Escape/F3 recovered. Stale title Settings click later missed; a settled native click recovered. No callback/state assignment is claimed.'})
    result = {'passed': all(c['passed'] for c in checks), 'count': len(checks), 'checks': checks,
              'source': EXPECTED_HEAD, 'zip_sha256': EXPECTED_ZIP, 'pck_sha256': EXPECTED_PCK,
              'lifecycle': lifecycle, 'scope': 'Independent package-byte/event/clock checks. Original pixel inspection and final lifecycle disposition are separately enumerated in REVIEW.md.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'count': result['count'], 'failures': [c['name'] for c in checks if not c['passed']]}))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
