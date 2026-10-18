#!/usr/bin/env python3
"""Read-only audit of the deliberate missing-scene boot fixture and its originals."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def value_at(value, path):
    for key in path.split('.'):
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    run = json.loads((args.capture / 'run.json').read_text())
    fixture = args.capture / 'fixture'
    checks, originals = [], []

    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail))

    check('Actual native run reached Quit0 and cleanup0', run.get('complete') is True and
          run.get('verified_exit_code') == 0 and run.get('cleanup_exit') == 0 and
          run.get('source_unchanged') is True)
    plan = args.source / 'tools/ui-campaign/boot-recovery-plan.json'
    check('Original six-step plan executed unchanged', sha(plan) == run['plan_sha256'] and
          json.loads(plan.read_text()) == run['plan'] and len(run['shots']) == 5)
    differences = []
    for name, checksum in run['source_sha256'].items():
        if not (fixture / name).is_file() or sha(fixture / name) != checksum:
            differences.append('fixture:' + name)
        if name != 'project.godot' and (not (args.source / name).is_file() or
                                       sha(args.source / name) != checksum):
            differences.append('source:' + name)
    check('All 27 recorded fixture files are exact; 26 copied inputs match frozen source',
          not differences and len(run['source_sha256']) == 27, differences)
    expected_project = ('[application]\nconfig/name="YUGA UI component fixture"\n'
                        'run/main_scene="res://scenes/boot.tscn"\n[display]\n'
                        'window/size/viewport_width=960\nwindow/size/viewport_height=600\n'
                        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    check('Deliberate missing-courtyard fixture has the declared lightweight configuration',
          (fixture / 'project.godot').read_text() == expected_project and
          not (fixture / 'scenes/courtyard.tscn').exists() and
          (fixture / 'scripts/loading_presentation.gd').is_file())
    all_shots = run['shots'] + run['automatic_shots']
    bad_originals = []
    for shot in all_shots:
        png = args.capture / shot['file']
        sidecar = png.with_suffix('.json')
        pixels = list(struct.unpack('>II', png.read_bytes()[16:24]))
        if sha(png) != shot['sha256'] or json.loads(sidecar.read_text()) != shot or pixels != [960, 600]:
            bad_originals.append(shot['file'])
        originals.append(dict(file=shot['file'], png_sha256=sha(png), sidecar_sha256=sha(sidecar),
                              pixels=pixels, phase=shot['transition']['phase'],
                              attempt=shot['transition']['attempt'], focus=shot.get('focus')))
    check('All eight raw originals and sidecars match recorded bytes and framebuffer dimensions',
          not bad_originals and len(all_shots) == 8 and
          {p.name for p in args.capture.glob('*.png')} == {s['file'] for s in all_shots}, bad_originals)
    mismatches = []
    for step in run['plan']:
        if 'capture' not in step:
            continue
        shot = next(s for s in run['shots'] if s['file'] == step['capture'] + '.png')
        for key, expected in step.get('expect', {}).items():
            if value_at(shot, key) != expected:
                mismatches.append(dict(file=shot['file'], key=key, expected=expected,
                                       actual=value_at(shot, key)))
    check('Error, actual Retry attempt2, Escape recovery and reopen expectations hold in pixels receipts',
          not mismatches, mismatches)
    check('One persistent layer and usable focus survive each recovery',
          all(s.get('transition_layer_count') == 1 and s.get('focus') for s in all_shots) and
          all(any(c.get('text') == 'Retry opening YUGA' and c.get('interactive') is True and
                  c.get('focus') is True for c in s['controls']) for s in run['shots']
              if s['transition']['phase'] == 'cancelled'))
    engine = Path(run['command'][0])
    check('Installed engine identity and isolated unseeded fixture are explicit',
          sha(engine) == run['engine_sha256'] ==
          'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3' and
          run['mode'] == 'boot_recovery' and
          not run['shader_cache_seed']['files_sha256'] and
          not run['godot_shader_cache_seed']['files_sha256'] and
          run['scheduling']['render_threads'] == 1)
    log = (args.capture / 'godot.log').read_text()
    errors = re.findall(r'^.*(?:ERROR:|ObjectDB instances leaked).*$', log, re.M)
    warnings = [line for line in log.splitlines() if 'WARNING:' in line]
    expected_warning = 'WARNING: Could not set V-Sync mode, as changing V-Sync mode is not supported by the graphics driver.'
    check('No engine errors/leaks; the single driver V-Sync warning is retained',
          not errors and warnings == [expected_warning], dict(errors=errors, warnings=warnings))
    report = dict(passed=all(c['passed'] for c in checks), count=len(checks), checks=checks,
                  originals=originals, run_sha256=sha(args.capture / 'run.json'),
                  source_freeze_sha256=sha(args.source / 'ui-source-freeze.json'),
                  script_sha256=sha(Path(__file__)),
                  scope='Actual native input in an explicit tiny missing-scene fixture. Five manual and three '
                        'queued originals directly reviewed. Escape dismisses an errored transition; this does '
                        'not exercise cancellation of an in-flight heavy resource load. Driver warning retained.')
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], count=report['count'])))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
