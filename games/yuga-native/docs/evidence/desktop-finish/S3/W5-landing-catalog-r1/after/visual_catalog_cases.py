#!/usr/bin/env python3
"""Catalog dispatch/source-closure regressions; synthetic children never qualify Godot."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT / 'tools/run-visual-checks.py'
spec = importlib.util.spec_from_file_location('visual_catalog', RUNNER)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists(): parser.error('Use a fresh report path')
    checks = []

    def check(name, ok, detail=None):
        checks.append({'name':name, 'passed':bool(ok), 'detail':detail})

    suites = (*catalog.SUITES, *catalog.SCREEN_SUITES)
    check('Catalog identifiers are unique and every entry exists',
          len({s[0] for s in suites}) == len(suites) and all((PROJECT/s[2]).is_file() for s in suites))
    for kind, expected in [('visual', {'desktop-release-continuity','desktop-motion-scene-entry',
                                     'desktop-motion-transition-guard','desktop-world-route-parity',
                                     'desktop-volley-feedback','desktop-landing-support-boundary',
                                     'desktop-landing-pause'}),
                           ('screens', {'ui-boot-recovery','ui-title-portrait','ui-launch-composition',
                            'ui-world-atlas','ui-action-hud','ui-action-hud-fit',
                            'ui-host-replacement','ui-loading-presentation',
                            'ui-loading-readiness','ui-hud-readability','ui-atlas-layout','ui-cancel-focus',
                            'ui-preferences-relaunch','ui-compact-navigation-routes','ui-world-compact-title',
                            'ui-title-identity','ui-outcome-shortcuts','ui-world-compact-first-entry'})]:
        result = subprocess.run([sys.executable,str(RUNNER),'--catalog',kind,'--list'],capture_output=True,text=True)
        listed = json.loads(result.stdout)
        check(kind+' CLI exposes new contracts with bounded acceptance scope',
              result.returncode == 0 and expected <= {s['id'] for s in listed['suites']}
              and 'no ' in listed['scope'] and 'release acceptance' in listed['scope'])
    result = subprocess.run([sys.executable,str(RUNNER),'--catalog','visual','--suite','ui-boot-recovery','--list'],capture_output=True,text=True)
    check('A screen suite cannot silently run under visual acceptance',result.returncode == 2 and 'selected --catalog' in result.stderr)
    result = subprocess.run([sys.executable,str(RUNNER),'--catalog','screens','--suite','desktop-volley-feedback','--list'],capture_output=True,text=True)
    check('A combat presentation suite cannot silently run under screen acceptance',result.returncode == 2 and 'selected --catalog' in result.stderr)
    for name, expected in {
        'ui-boot-recovery': {'tests/ui_s1_loading_cases.gd'},
        'ui-host-replacement': {'tests/ui_s2_transition_cases.gd'},
        'ui-cancel-focus': {'tests/ui_s3_cancel_focus_cases.gd'},
        'ui-preferences-relaunch': {'tests/desktop_d05_preferences_fixture.py',
                                    'tests/desktop_d05_preferences_cases.gd',
                                    'scripts/input_bindings.gd','scripts/rama_hero_panel.gd'},
        'ui-compact-navigation-routes': {'tests/desktop_d03_d05_navigation_audit_cases.gd',
                                        'scenes/courtyard.tscn','scenes/combat_film.tscn',
                                        'scripts/controls_overlay.gd','scripts/launch_shell.gd'},
        'ui-world-compact-title': {'tests/desktop_world_compact_title_cases.gd',
                                   'scenes/confluence_world.tscn','scripts/confluence_world.gd',
                                   'scripts/rama_hero_hud.gd','scripts/lane_army.gd'},
        'ui-title-identity': {'tests/desktop_d01_title_identity_cases.gd',
                              'scripts/launch_shell.gd','scripts/hero_ui_theme.gd'},
        'ui-outcome-shortcuts': {'tests/desktop_d08_outcome_shortcut_cases.gd',
                                 'scenes/confluence_world.tscn','scripts/confluence_world.gd',
                                 'scripts/input_bindings.gd','scripts/world_outcome_summary.gd'},
        'ui-world-compact-first-entry': {'tests/desktop_world_compact_first_entry_cases.gd',
                                        'scenes/confluence_world.tscn','scripts/confluence_world.gd',
                                        'scripts/rama_hero_hud.gd','scripts/hero_ui_theme.gd',
                                        'scripts/lane_army.gd'},
        'ui-action-hud-fit': {'tests/desktop_s1_hud_cases.gd','tests/ui_i1_action_hud_cases.gd'},
        'ui-hud-readability': {'tests/ui_i1_action_hud_cases.gd'},
        'desktop-world-route-parity': {'tests/desktop_world_route_parity_cases.gd',
                                       'scenes/confluence_world.tscn','assets/world/confluence-map.json',
                                       'scripts/confluence_world.gd','scripts/world_atlas.gd',
                                       'scripts/player.gd','scripts/player_traversal.gd'},
        'desktop-volley-feedback': {'tests/desktop_i02_volley_feedback_cases.gd',
                                    'scenes/confluence_world.tscn','scripts/rama_ability_effects.gd',
                                    'scripts/rama_ability_kit.gd','scripts/rama_action_audio.gd',
                                    'scripts/rama_vitals.gd','scripts/rama_action_buffer.gd',
                                    'scripts/rama_hero_hud.gd','assets/heroes/rama-hero.glb.import'},
        'desktop-release-continuity': {'tests/graphics_g1_motion_cases.gd',
                                     'docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd'},
        'desktop-motion-scene-entry': {'tests/graphics_g2_support_cases.gd',
                                      'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd'},
        'desktop-motion-transition-guard': {'tests/graphics_g2_support_cases.gd',
                                           'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd',
                                           'docs/evidence/desktop-finish/S3/W5/guard-witness.json'},
        'desktop-landing-support-boundary': {'tests/desktop_landing_support_boundary_cases.gd',
                                            'tests/graphics_g2_support_cases.gd',
                                            'scripts/rama_motion.gd','assets/heroes/rama-hero.glb.import'},
        'desktop-landing-pause': {'tests/desktop_landing_pause_cases.gd',
                                 'tests/graphics_g2_support_cases.gd',
                                 'docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd',
                                 'scenes/courtyard.tscn','scripts/player.gd','scripts/rama_motion.gd'},
    }.items():
        pins = catalog.sources([next(s for s in suites if s[0] == name)])
        check(name+' pins its invoked or inherited tests and loading view',
              expected | {'scripts/loading_presentation.gd'} <= pins.keys())
    release = next(s for s in suites if s[0] == 'desktop-release-continuity')
    check('Release CLI pins its tracked baseline and retains full compact evidence',
          '--baseline-script=res://docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd' in release[3]
          and '--compact-report' in release[3])
    scene_entry = next(s for s in suites if s[0] == 'desktop-motion-scene-entry')
    check('Native scene-entry CLI requests a bounded summary and explicit rate',
          '--summary-report' in scene_entry[3] and '--hz=60' in scene_entry[3])
    volley = next(s for s in suites if s[0] == 'desktop-volley-feedback')
    check('Volley combined-boundary CLI retains the nonzero authority warmup',
          volley[3] == ('--warmup-ticks=200',))
    check('Landing boundaries and pause retain120Hz fixed sampling without changing other suites',
          catalog.SUITE_FIXED_FPS == {'desktop-landing-support-boundary':120,'desktop-landing-pause':120}
          and all(next(s for s in suites if s[0] == name)[3] == () for name in catalog.SUITE_FIXED_FPS))

    with tempfile.TemporaryDirectory(prefix='yuga-motion-trace-cases-') as temporary:
        report = Path(temporary)/'result.json'
        trace = report.with_name(report.name+'.trace.json.gz')
        full = {'passed':True,'count':1,'checks':[{'name':'synthetic trace binding','passed':True}],
                'rows':[{'poses':[[0,0,0,0,0,0,1]]}],'bone_names':['fixture-bone']}
        raw = json.dumps(full).encode()
        encoded = gzip.compress(raw)
        trace.write_bytes(encoded)
        data = {key:value for key,value in full.items() if key not in ('rows','bone_names')}
        data['trace'] = {'path':trace.name,'encoding':'gzip','sha256':hashlib.sha256(encoded).hexdigest(),
                         'bytes':len(encoded),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),
                         'uncompressed_bytes':len(raw),'rows':1,'bones':1}
        check('Bounded motion summary retains a portable lossless trace',not catalog.motion_trace_problems(report,data))
        trace.unlink()
        check('Passing summary without its declared trace is rejected',catalog.motion_trace_problems(report,data)==['motion_trace_missing_or_symlink'])
        trace.write_bytes(encoded+b'tampered')
        check('Changed compressed trace is rejected before decompression',catalog.motion_trace_problems(report,data)==['motion_trace_compressed_identity_mismatch'])
        trace.write_bytes(encoded)
        data['checks']=[{'name':'different summary assertion','passed':True}]
        check('Matching byte hashes cannot substitute different summary assertions',catalog.motion_trace_problems(report,data)==['motion_trace_summary_mismatch'])

    # Execute the real catalog CLI in a tiny copied repository. The fake engine
    # tests forwarding/version dispatch only; this is not a gameplay fixture.
    with tempfile.TemporaryDirectory(prefix='yuga-catalog-cases-') as temporary:
        root = Path(temporary)
        project = root/'repo/games/yuga-native'
        for folder in ['tools','tests','scripts','shaders','scenes','assets','tests/fixtures/contracts']:
            (project/folder).mkdir(parents=True,exist_ok=True)
        for relative in ['tools/run-visual-checks.py','tools/run-authoring-checks.py']:
            shutil.copy2(PROJECT/relative,project/relative)
        for name in ['project.godot','export_presets.cfg','tests/ui_s1_loading_cases.gd']:
            (project/name).write_text('catalog fixture source\n')
        engine = root/'explicit-engine'
        engine.write_text('#!'+sys.executable+'\nimport sys\nprint("4.6.3.stable.catalog_fixture")\nsys.exit(0 if sys.argv[1:]==["--version"] else 9)\n')
        engine.chmod(0o755)
        (project/'tests/ui_s1_loading_fixture.py').write_text('''import argparse,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--engine');p.add_argument('--report');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1]
version=subprocess.check_output([a.engine,'--version'],text=True).strip()
if (root/'mutate').exists(): (root/'tests/ui_s1_loading_cases.gd').write_text('changed during suite')
pathlib.Path(a.report).write_text(json.dumps({'passed':True,'count':1,'checks':[{'name':'synthetic dispatch only','passed':True}],'engine':a.engine,'version':version}))
''')
        for mutate in [False,True]:
            if mutate: (project/'mutate').touch()
            output=root/('mutated' if mutate else 'clean')
            command=[sys.executable,str(project/'tools/run-visual-checks.py'),'--catalog','screens',
                     '--suite','ui-boot-recovery','--engine',str(engine),'--output',str(output),'--max-cpus','1']
            result=subprocess.run(command,capture_output=True,text=True,timeout=20)
            summary=json.loads((output/'summary.json').read_text())
            child=json.loads((output/'reports/ui-boot-recovery.json').read_text())
            if mutate:
                check('Invoked fixture test mutation rejects a passing child report',
                      result.returncode == 1 and not summary['passed'] and not summary['checked_sources_unchanged'])
            else:
                check('Fixture dispatch forwards the selected engine executable',
                      result.returncode == 0 and summary['passed'] and child['engine'] == str(engine)
                      and child['version'] == '4.6.3.stable.catalog_fixture')
                before=json.loads((output/'source-before.json').read_text())
                check('Real CLI source receipt includes the fixture-invoked test',
                      'tests/ui_s1_loading_cases.gd' in before and summary['checked_sources_unchanged'])
    passed=all(item['passed'] for item in checks)
    report={'passed':passed,'count':len(checks),'checks':checks,
            'scope':'Catalog selection, transitive test source closure and explicit-engine forwarding only. Synthetic child processes are not Godot, art or gameplay acceptance.',
            'source_sha256':{str(p.relative_to(PROJECT)):catalog.helper.sha(p) for p in [RUNNER,Path(__file__),catalog.HELPER_PATH]}}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':passed,'count':len(checks),'failures':[c for c in checks if not c['passed']]}))
    return 0 if passed else 1


if __name__ == '__main__': raise SystemExit(main())
