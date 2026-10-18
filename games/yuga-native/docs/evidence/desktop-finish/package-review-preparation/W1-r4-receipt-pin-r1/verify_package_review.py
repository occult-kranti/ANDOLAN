#!/usr/bin/env python3
"""Validate actual package receipts; this does not replace direct image review."""
import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
from package_identity import SOURCE as EXPECTED_SOURCE, RUNTIME, ARCHIVE, PCK, EXPORT_MANIFEST, EXTRACTION_REPORT, exact_selection


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def distance(a, b):
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def normalize(v):
    length = math.sqrt(sum(x*x for x in v))
    if not math.isfinite(length) or length <= 1e-10:
        raise ValueError('Invalid heading vector')
    return [x/length for x in v]


def projected_heading(presentation):
    facing = presentation['visual_forward']
    rect = presentation['atlas_plot_rect']
    bounds = presentation['atlas_world_bounds']
    return normalize([facing[0]*rect[2]/(bounds[1]-bounds[0]),
                      facing[2]*rect[3]/(bounds[3]-bounds[2])])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--phase', choices=['warm', 'cold'], required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--export-manifest', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('Fresh report required')
    exported = read(args.export_manifest)
    export_exact = args.export_manifest.is_file() and sha(args.export_manifest) == EXPORT_MANIFEST
    record = read(args.run/'run.json')
    watchdog = read(args.run.with_name(args.run.name+'-watchdog')/'receipt.json')
    plan = read(HERE/('package-'+args.phase+'-plan.json'))
    names = [step['capture'] for step in plan if 'capture' in step]
    shots = {name: read(args.run/(name+'.json')) for name in names}
    checks = {
        'native_route_complete_and_quit_zero': record.get('complete') is True and record.get('verified_exit_code') == 0,
        'outer_bound_completed': watchdog.get('complete') is True and watchdog.get('overall_timeout') is False,
        'exact_final_export_commit': record.get('export_manifest',{}).get('git',{}).get('head') == EXPECTED_SOURCE == watchdog.get('expected_source_commit'),
        'exact_selected_patched_archive_runtime': record.get('engine_sha256') == RUNTIME == watchdog.get('engine_sha256'),
        'exact_distinct_exporter_and_runtime_proof': export_exact and record.get('export_manifest', {}).get('sha256') == EXPORT_MANIFEST and exact_selection(exported.get('engine_selection', {})) and exact_selection(watchdog.get('engine_selection', {})),
        'exact_qualified_archive_pck_manifest': watchdog.get('package_sha256') == PCK and watchdog.get('archive_sha256') == ARCHIVE and watchdog.get('export_manifest_sha256') == EXPORT_MANIFEST,
        'package_archive_source_tools_unchanged': all(record.get(k) is True for k in [
            'package_unchanged','archive_unchanged','export_manifest_unchanged','instrumentation_unchanged','source_unchanged']),
        'actual_extracted_archive_runtime': watchdog.get('archive_runtime_executed') is True and watchdog.get('diagnostic_runtime_override') is False and watchdog.get('extracted_payloads_unchanged') is True and watchdog.get('extraction_report_sha256') == EXTRACTION_REPORT,
        'expected_manual_count': len(record.get('shots',[])) == len(names),
        'same_declared_plan': record.get('plan_sha256') == sha(HERE/('package-'+args.phase+'-plan.json')),
    }
    original_pins = []
    original_ok = True
    for name, shot in shots.items():
        image = args.run/shot.get('file','MISSING')
        if not shot or not image.is_file() or image.suffix != '.png':
            original_ok = False
            continue
        actual = sha(image)
        original_ok &= actual == shot.get('sha256') and shot.get('png_status') == 0
        original_pins.append({'name':name,'png_sha256':actual,'sidecar_sha256':sha(args.run/(name+'.json'))})
    checks['all_manual_raw_images_match_sidecars'] = bool(original_pins) and original_ok and len(original_pins)==len(names)
    seeds = record.get('shader_cache_seed',{}).get('files_sha256',{})
    godot_seeds = record.get('godot_shader_cache_seed',{}).get('files_sha256',{})
    prior = record.get('shader_cache_seed',{}).get('reused_isolated_cache_sha256',{})
    if args.phase == 'warm':
        checks['warm_seeds_declared_and_unchanged'] = bool(seeds and godot_seeds) and record.get('shader_cache_seed_unchanged') is True and record.get('godot_shader_cache_seed_unchanged') is True
        checks['staged_outcomes_explicit'] = record.get('authority_staging',{}).get('enabled') is True and all(
            'STAGED' in name for name in names if 'outcome' in name or 'terminal' in name)
        labels = ['13-world-ready-live','13b-native-world-rotated','14-world-overview','15-world-overview-details','15b-native-rotated-overview-return']
    else:
        checks['cold_has_no_copied_or_reused_cache'] = not seeds and not godot_seeds and not prior
        checks['cold_has_no_authority_stage'] = record.get('authority_staging',{}).get('enabled') is False
        labels = ['05-package-world-live','06-package-world-rotated','07-package-overview-rotated-a','08-package-overview-rotated-b','09-package-world-overview-return']
    checks['fresh_preferences'] = record.get('user_state',{}).get('before') == {}
    heading = {}
    try:
        initial, rotated, first, second, returned = [shots[name] for name in labels]
        a, b = initial['presentation'], rotated['presentation']
        old = normalize([a['visual_forward'][0],a['visual_forward'][2]])
        new = normalize([b['visual_forward'][0],b['visual_forward'][2]])
        turn = math.acos(max(-1,min(1,sum(x*y for x,y in zip(old,new)))))
        moved = distance(a['player_position'],b['player_position'])
        checks['native_input_actually_moved_and_rotated_hero'] = moved > .5 and turn > .3
        headings = []
        for name in labels[1:]:
            p = shots[name]['presentation']
            expected = projected_heading(p)
            headings.append({'name':name,'expected':expected,'actual':p['atlas_heading'],
                             'error':distance(expected,p['atlas_heading']),
                             'raw_vector_error':distance(p['visual_forward'],p['atlas_forward'])})
        checks['atlas_matches_actual_facing_and_independent_projection'] = all(
            item['error'] < 1e-5 and item['raw_vector_error'] < 1e-5 for item in headings)
        checks['overview_preserves_rotated_facing_on_entry_hold_return'] = all(
            distance(b['visual_forward'],shots[name]['presentation']['visual_forward']) < 1e-5 for name in labels[2:])
        checks['overview_clocks_hold_while_physics_continues'] = (
            second['physics_frame']-first['physics_frame'] >= 15 and
            first['state']['overview'] and second['state']['overview'] and
            first['presentation']['suspended'] and second['presentation']['suspended'] and
            first['army']['elapsed'] == second['army']['elapsed'] and
            first['kit']['elapsed'] == second['kit']['elapsed'] and
            all(first['presentation']['motion'][key] == second['presentation']['motion'][key]
                for key in ['action_elapsed','locomotion_age']))
        checks['overview_return_resumes_live_world'] = returned['state']['overview'] is False and returned['presentation']['suspended'] is False
        heading = {'turn_radians':turn,'movement_meters':moved,'samples':headings}
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        checks['complete_heading_witness'] = False
        heading['error'] = repr(error)
    events = record.get('events',[])
    checks['native_movement_edges_recorded'] = any(e.get('key_down')=='d' for e in events) and any(e.get('key_up')=='d' for e in events)
    log = (args.run/'godot.log').read_text() if (args.run/'godot.log').is_file() else ''
    checks['no_engine_errors_or_object_leak'] = bool(log) and not any(
        line.startswith(('ERROR:','SCRIPT ERROR:')) or 'leaked at exit' in line for line in log.splitlines())
    report = {'passed':all(checks.values()),'phase':args.phase,'checks':checks,
              'heading':heading,'originals':original_pins,
              'warnings':[line for line in log.splitlines() if line.startswith('WARNING:')],
              'visual_review':'Requires direct inspection of originals; these checks alone do not accept art or readability.'}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'checks':len(checks),'failed':[key for key,value in checks.items() if not value]}))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
