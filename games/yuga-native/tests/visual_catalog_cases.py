#!/usr/bin/env python3
"""Catalog dispatch/source-closure regressions; synthetic children never qualify Godot."""
from __future__ import annotations
import argparse
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
    for kind, expected in [('visual', {'desktop-release-continuity'}),
                           ('screens', {'ui-boot-recovery','ui-title-portrait','ui-launch-composition',
                            'ui-world-atlas','ui-action-hud','ui-action-hud-fit',
                            'ui-host-replacement','ui-loading-presentation'})]:
        result = subprocess.run([sys.executable,str(RUNNER),'--catalog',kind,'--list'],capture_output=True,text=True)
        listed = json.loads(result.stdout)
        check(kind+' CLI exposes new contracts with bounded acceptance scope',
              result.returncode == 0 and expected <= {s['id'] for s in listed['suites']}
              and 'no ' in listed['scope'] and 'release acceptance' in listed['scope'])
    result = subprocess.run([sys.executable,str(RUNNER),'--catalog','visual','--suite','ui-boot-recovery','--list'],capture_output=True,text=True)
    check('A screen suite cannot silently run under visual acceptance',result.returncode == 2 and 'selected --catalog' in result.stderr)
    for name, expected in {
        'ui-boot-recovery': {'tests/ui_s1_loading_cases.gd'},
        'ui-host-replacement': {'tests/ui_s2_transition_cases.gd'},
        'ui-action-hud-fit': {'tests/desktop_s1_hud_cases.gd','tests/ui_i1_action_hud_cases.gd'},
        'desktop-release-continuity': {'tests/graphics_g1_motion_cases.gd',
                                     'docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd'},
    }.items():
        pins = catalog.sources([next(s for s in suites if s[0] == name)])
        check(name+' pins its invoked or inherited tests and loading view',
              expected | {'scripts/loading_presentation.gd'} <= pins.keys())
    release = next(s for s in suites if s[0] == 'desktop-release-continuity')
    check('Release CLI pins its tracked baseline and retains full compact evidence',
          '--baseline-script=res://docs/evidence/desktop-finish/S1/W5/baseline/rama_motion.gd' in release[3]
          and '--compact-report' in release[3])

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
