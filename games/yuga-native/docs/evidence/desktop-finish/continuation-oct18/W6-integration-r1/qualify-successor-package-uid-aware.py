#!/usr/bin/env python3
"""Audit the fresh exact-source successor PCKs/ZIPs; never execute or extract."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time
import zipfile
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
WINDOWS_ENGINE = {'bytes': 172409864, 'sha256': 'ef90e929ba1a6a4322860285d97f40f4aa349c90329a91b0e8b55b8df0f4cb00'}
WINDOWS_PROOF = Path('/workspace/tooling/native-engine/godot-windows-provenance.json')
WINDOWS_PROOF_SHA = 'c83f2555fdd573e3ef090d4575185596d1a9c908a321c8c61632e727d9c2703e'
UID_ALLOWLIST = HERE / 'uid-regeneration-allowlist.json'
UID_ALLOWLIST_SHA = '4d8cda1a7bb658459fdacf4eae0493f20edd9d6cff10a13507af028d6d7bc705'


def admit_uid_regeneration(diagnostics, expected, repo, canonical, prep, preparation_sha, phases, runtime_uids):
    """Admit only the exact reviewed75 cached nonruntime UID recreations."""
    if (expected.get('schema') != 1 or expected.get('source_commit') != prep['source_commit'] or
            expected.get('preparation_sha256') != preparation_sha or
            expected.get('approved_exclusion_sha256') != prep['exclude_sha256'] or
            expected.get('log') != 'build/export-linux.log' or expected.get('expected_warning_count') != 75):
        raise ValueError('UID observation does not bind this exact source/preparation/exclusion/log')
    observed = [(name, line) for name, lines in diagnostics.items() for line in lines]
    rows = expected.get('warnings', [])
    if len(rows) != 75 or len(observed) != 75 or observed != [(expected['log'], row['line']) for row in rows]:
        raise ValueError('Unknown, missing, duplicate, relocated or changed diagnostics')
    tracked = {row['path']: row for row in prep['entries']}
    approved = {line[1:] for line in prep['exclude_text'].splitlines() if line.startswith('/')}
    seen_paths, seen_ids, admitted = set(), set(), []
    for row in rows:
        match = re.fullmatch(r'WARNING: Missing \.uid file for path "(res://(?:tests|tools)/[^"\r\n]+\.gd)"\. The file was re-created from cache\.', row['line'])
        if not match:
            raise ValueError('Unknown warning grammar or runtime warning')
        source = 'games/yuga-native/' + match[1][6:]
        name = PurePosixPath(source)
        uid_path = source + '.uid'
        if (name.is_absolute() or '..' in name.parts or '\\' in source or name.as_posix() != source or
                name.parts[:3] not in [('games', 'yuga-native', 'tests'), ('games', 'yuga-native', 'tools')] or
                source != row['source_path'] or uid_path != row['uid_path'] or source not in tracked or
                uid_path in tracked or uid_path not in approved or uid_path in seen_paths):
            raise ValueError('Warning source/sidecar is outside exact approved untracked nonruntime metadata')
        seen_paths.add(uid_path)
        source_record = {'bytes': row['source_bytes'], 'sha256': row['source_sha256']}
        if ({key: tracked[source][key] for key in ['bytes', 'sha256']} != source_record or
                tracked[source]['blob'] != row['source_blob'] or rec(repo / source) != source_record):
            raise ValueError('Warning source script differs from reviewed tracked blob')
        sidecars = [repo / uid_path, canonical / uid_path]
        if not all(path.is_file() and not path.is_symlink() and path.resolve() == path.absolute() for path in sidecars):
            raise ValueError('Generated UID sidecar must be a regular private path')
        if (sidecars[0].stat().st_dev, sidecars[0].stat().st_ino) == (sidecars[1].stat().st_dev, sidecars[1].stat().st_ino):
            raise ValueError('Generated UID metadata must not share canonical mutable inodes')
        payload = sidecars[0].read_bytes()
        if (not re.fullmatch(rb'uid://(?:a|[b-y0-8][a-y0-8]{0,12})\n', payload) or
                payload.decode().strip() != row['uid'] or row['uid'] in seen_ids or row['uid'] in runtime_uids):
            raise ValueError('Generated UID is malformed, substituted, duplicated or collides with runtime metadata')
        numeric = 0
        for character in row['uid'].removeprefix('uid://'):
            numeric = numeric * 34 + 'abcdefghijklmnopqrstuvwxy012345678'.index(character)
        if numeric > 0x7FFFFFFFFFFFFFFF:
            raise ValueError('Generated UID exceeds canonical signed63 range')
        seen_ids.add(row['uid'])
        if (any(rec(path) != row['metadata'] for path in sidecars) or
                any(phases[phase]['generated_ignored_uid_files'].get(uid_path) != row['metadata'] for phase in ['export', 'package'])):
            raise ValueError('Generated metadata differs from exact reviewed ID/canonical sidecar/phase bindings')
        admitted.append({'log': expected['log'], **row})
    return admitted


def expected_phase_command(repo, out, native, phase):
    return ['taskset', '-c', '0,1', 'python3', 'games/yuga-native/tools/package-native.py',
            '--linux-engine', '/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64',
            '--linux-runtime', '/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority',
            '--linux-runtime-variant', 'pipeline-low-priority', '--linux-runtime-provenance',
            str(repo / native / 'docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json'),
            '--windows-engine', '/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe',
            '--build-dir', str(out / 'build'), '--' + phase + '-only']


def phase_binding_matches(receipt, phase, preparation_sha, commit, repo, out, native):
    expected_environment = {name: str(out / 'user' / suffix) for name, suffix in
                            [('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache')]}
    expected_environment.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    return (receipt.get('exit_code') == 0 and receipt.get('after_source_passed') is True and
            not receipt.get('failure') and not receipt.get('terminated_reason') and
            receipt.get('source_commit') == commit and receipt.get('preparation_sha256') == preparation_sha and
            receipt.get('cwd') == str(repo) and receipt.get('command') == expected_phase_command(repo, out, native, phase) and
            receipt.get('environment') == expected_environment)


def contract_proof_matches(proof, raw, actual_record, expected_sources, expected_report_sources, required_names):
    checks = raw.get('checks', [])
    return (proof.get('schema') == 1 and proof.get('report') == actual_record and
            proof.get('sources') == expected_sources and raw.get('source_sha256') == expected_report_sources and
            raw.get('passed') is True and isinstance(checks, list) and bool(checks) and
            len(checks) == proof.get('checks') and all(isinstance(c, dict) and c.get('passed') is True and isinstance(c.get('name'), str) for c in checks) and
            len({c['name'] for c in checks}) == len(checks) and required_names.issubset({c['name'] for c in checks}))


def windows_provenance_matches(pm, expected_proof):
    return (pm.get('windows_engine_provenance') == expected_proof and
            pm.get('runtime', {}).get('provenance') == expected_proof and
            {key: pm.get('runtime', {}).get(key) for key in ['bytes', 'sha256']} == WINDOWS_ENGINE)


def required_log_names():
    return ['logs/export.stdout', 'logs/export.stderr', 'logs/package.stdout', 'logs/package.stderr',
            'build/export-linux.log', 'build/export-windows.log',
            'build/native-contracts-export.log', 'build/native-contracts-package.log',
            'build/font-bindings-export.log', 'build/font-bindings-package.log']

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

def rec(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}

def member_rec(archive, name):
    h, size = hashlib.sha256(), 0
    with archive.open(name) as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
            size += len(block)
    return {'bytes': size, 'sha256': h.hexdigest()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preparation', type=Path, required=True)
    p.add_argument('--preparation-sha256', required=True)
    p.add_argument('--expected-commit', required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args()
    if a.report.exists():
        p.error('Fresh report required; preserve earlier successes and failures')
    if rec(a.preparation)['sha256'] != a.preparation_sha256:
        p.error('Exact preparation receipt required')
    prep = json.loads(a.preparation.read_text())
    if (not prep.get('materialized') or prep.get('failure') or
            prep['source_commit'] != a.expected_commit or len(a.expected_commit) != 40):
        p.error('Exact successful materialized source preparation required')
    s = module('snapshot_auditor', HERE / 'prepare-package-snapshot.py')
    out, repo = Path(prep['artifact_root']), Path(prep['repository'])
    if out.parent != s.AREA or repo != out / 'ANDOLAN' or out.resolve() != out:
        p.error('Unexpected artifact root')
    build, project = out / 'build', repo / s.NATIVE
    result = {'schema': 1, 'source_commit': a.expected_commit, 'passed': False,
              'preparation_sha256': a.preparation_sha256, 'checks': [],
              'scope': 'Full tracked source/index/isolation/cache and exact PCK/ZIP/member/provenance qualification only. No extraction, engine execution, cleanup, transport or publication; actual warm/cold qualification remains separate.'}
    def check(name, okay):
        result['checks'].append({'name': name, 'passed': bool(okay)})
        if not okay:
            raise ValueError(name)
    try:
        phase_records = {}
        for phase in ['export', 'package']:
            receipt = json.loads((out / (phase + '-execution.json')).read_text())
            check(phase + ' exact preparation source cwd command environment and successful after-audit', phase_binding_matches(receipt, phase, a.preparation_sha256, a.expected_commit, repo, out, s.NATIVE))
            phase_records[phase] = rec(out / (phase + '-execution.json'))
        s.audit(s.SOURCE, prep['entries']); s.audit(repo, prep['entries'])
        s.audit_index(s.SOURCE, prep['entries']); s.audit_index(repo, prep['entries'])
        s.audit_isolation(s.SOURCE, repo, prep['entries'])
        check('complete tracked source index modes and private/shared inode policy exact', True)
        check('artifact HEAD exact and native/full status clean', s.git(repo, 'rev-parse', 'HEAD').decode().strip() == a.expected_commit and not s.git(repo, 'status', '--porcelain', '--untracked-files=all'))
        check('approved exact nonruntime exclusions unchanged', rec(repo / '.git/info/exclude')['sha256'] == prep['exclude_sha256'] == s.APPROVED_EXCLUDE_SHA256)
        check('canonical cache seed unchanged and mutable cache inodes private', s.cache_records(Path(prep['cache_seed']['path'])) == prep['cache_seed']['files'] and all((Path(prep['cache_seed']['path']) / row['path']).stat().st_ino != (project / '.godot' / row['path']).stat().st_ino for row in prep['cache_seed']['files']))
        # Never execute artifact Python until the full declared tracked source,
        # index and phase/preparation bindings have passed independently.
        tool = module('audited_packager', project / 'tools/package-native.py')
        exported = json.loads((build / 'native-export-manifest.json').read_text())
        packaged = json.loads((build / 'native-package-manifest.json').read_text())
        check('export and package bind the same exact clean source', exported['git']['head'] == a.expected_commit and exported['git']['native_worktree_status'] == '' and exported['git'] == packaged['git'])
        check('runtime source closure exact and unchanged', tool.source_state() == exported['source'] and packaged['runtime_source_sha256'] == exported['source']['sha256'])
        engines = exported['engine_selection']
        check('official exporter and explicit reviewed patched runtime remain distinct', engines == packaged['engine_selection'] and engines['exporter']['sha256'] == 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3' and engines['linux_runtime']['sha256'] == 'e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e' and engines['linux_runtime']['kind'] == 'patched-public-source-template-debug' and engines['linux_runtime']['provenance']['variant'] == 'pipeline-low-priority-v1' and engines['linux_runtime']['provenance']['source_patches'] == 1 and len(engines['linux_runtime']['provenance']['evidence']) == 11)
        check('runtime UID preflight remains exact', tool.validate_runtime_script_uids() == exported['runtime_uids'])
        check('native contract checks nonempty passed and same at export/package', packaged['native_contracts'] == exported['native_contracts'] and exported['native_contracts']['checks'] > 0)
        expected_contract_sources = tool._native_contract_inputs(project)
        expected_report_sources = {str(s.NATIVE / relative): rec(project / relative)['sha256'] for relative in
                                   ['assets/contracts/native-contracts-v1.json', 'assets/contracts/native-envelope-v1.schema.json',
                                    'tools/check-native-contracts.py', 'scripts/native_contracts.gd']}
        contract_catalog = json.loads((project / 'assets/contracts/native-contracts-v1.json').read_text())
        required_contract_names = {'three_exact_profiles', 'per_profile_content_revisions', 'wire_versions_unchanged'}
        for profile in contract_catalog['profiles']:
            required_contract_names.add(profile['id'] + '_content_aggregate')
            required_contract_names.update(profile['id'] + '_content_' + name for name in profile['content_sources'])
        contract_records = {}
        for phase in ['export', 'package']:
            proof_path = build / ('native-contracts-' + phase + '.json')
            raw_proof = json.loads(proof_path.read_text())
            check(phase + ' exact raw contract proof all gates passed and source closure bound', contract_proof_matches(exported['native_contracts'], raw_proof, rec(proof_path), expected_contract_sources, expected_report_sources, required_contract_names))
            contract_records[phase] = rec(proof_path)
        check('fixed official Windows engine provenance source proof exact', rec(WINDOWS_PROOF)['sha256'] == WINDOWS_PROOF_SHA and rec(Path('/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe')) == WINDOWS_ENGINE)
        windows_proof = json.loads(WINDOWS_PROOF.read_text())
        archives = {}
        for platform in ['linux', 'windows']:
            raw = build / f'yuga-native-{platform}.pck'
            pack = tool.inspect_pack(raw)
            pack['font_qualification'] = tool.qualify_bundled_font_package(pack, exported['font_bindings'])
            pack['frontage_qualification'] = tool.qualify_world_frontage_package(pack, exported['source']['files'])
            check(platform + ' full PCK reparse hash MD5 closure fonts and exact frontage', pack == exported['packs'][platform] and pack['all_entry_md5_verified'] and pack['frontage_qualification']['exact_source_payload'])
            check(platform + ' new scroll-focus and world-resource script remaps present', 'scripts/ui_scroll_focus.gd' in pack['first_load_resources'] and 'scripts/world_render_resources.gd' in pack['graphics_resources'])
            staging = build / f'yuga-native-{platform}-x86_64'
            archive_path = build / (staging.name + '.zip')
            before_archive = rec(archive_path)
            pm = json.loads((staging / 'PACKAGE-MANIFEST.json').read_text())
            check(platform + ' inner source platform and exporter exact', pm['git'] == exported['git'] and pm['runtime_source'] == exported['source'] and pm['exporter'] == engines['exporter'] and pm['platform'] == platform + '-x86_64')
            staged = {f.relative_to(build).as_posix(): rec(f) for f in staging.rglob('*') if f.is_file()}
            with zipfile.ZipFile(archive_path) as archive:
                infos = archive.infolist()
                names = [info.filename for info in infos]
                check(platform + ' CRC safe unique regular exact member census', archive.testzip() is None and len(names) == len(set(names)) == len(staged) == packaged['packages'][platform]['entry_count'] and set(names) == set(staged) and all(not info.is_dir() and not info.flag_bits & 1 and stat.S_ISREG(info.external_attr >> 16) and not PurePosixPath(info.filename).is_absolute() and '..' not in PurePosixPath(info.filename).parts and info.filename.startswith(staging.name + '/') for info in infos))
                actual = {name: member_rec(archive, name) for name in names}
                check(platform + ' every archive member hash and size equals staging', actual == staged)
                base = staging.name + '/'
                check(platform + ' inner payload inventory and every pinned member exact', set(names) == {base + name for name in pm['payloads']} | {base + 'PACKAGE-MANIFEST.json'} and all(actual[base + name] == value for name, value in pm['payloads'].items()))
                engine_name = 'godot' if platform == 'linux' else 'godot.exe'
                check(platform + ' archive engine and PCK exact', actual[base + engine_name] == {key: pm['runtime'][key] for key in ['bytes', 'sha256']} == packaged['packages'][platform]['engine'] and actual[base + 'yuga-native.pck'] == rec(raw) == {key: packaged['packages'][platform]['pck'][key] for key in ['bytes', 'sha256']})
                if platform == 'linux':
                    provenance = engines['linux_runtime']['provenance']
                    proof_map = provenance['bundled_evidence']
                    check('Linux declares exact patched runtime and source build proof mapping', pm['runtime'] == engines['linux_runtime'] and 'patched-public-template-debug' in pm['packaging'] and json.loads(archive.read(base + 'NOTICE/GODOT-RUNTIME-PROVENANCE.json')) == engines and set(proof_map) == set(provenance['evidence']) and len(set(proof_map.values())) == len(proof_map) == 11 and all(member_rec(archive, base + target) == provenance['evidence'][source] for source, target in proof_map.items()))
                    check('Linux modified-runtime notice and executable modes explicit', b'This is a modified runtime' in archive.read(base + 'START-HERE.txt') and b'Source patches: 1' in archive.read(base + 'NOTICE/GODOT-RUNTIME.txt') and all(stat.S_IMODE(archive.getinfo(base + name).external_attr >> 16) == 0o755 for name in ['godot', 'launch.sh']))
                else:
                    check('Windows fixed official engine provenance and no Linux patch declaration', windows_provenance_matches(pm, windows_proof) and base + 'NOTICE/GODOT-RUNTIME-PROVENANCE.json' not in names and b'bundled official Godot' in archive.read(base + 'START-HERE.txt'))
            check(platform + ' archive unchanged through audit and outer manifest exact', rec(archive_path) == before_archive == {key: packaged['packages'][platform][key] for key in ['bytes', 'sha256']} and packaged['packages'][platform]['filename'] == archive_path.name)
            archives[platform] = {**before_archive, 'filename': archive_path.name, 'members': len(staged), 'member_records': staged, 'pck': {key: pack[key] for key in ['bytes', 'sha256', 'entry_count']}}
        required_logs = [out / name for name in required_log_names()]
        check('all required phase contract font and platform export logs present', all(f.is_file() and not f.is_symlink() for f in required_logs))
        log_records = {str(f.relative_to(out)): rec(f) for f in required_logs}
        logs = [*sorted((out / 'logs').glob('*')), *sorted(build.glob('*.log'))]
        diagnostics = {str(f.relative_to(out)): [line for line in f.read_text(errors='replace').splitlines() if any(marker in line for marker in ['ERROR:', 'WARNING:', 'SCRIPT ERROR:'])] for f in logs}
        result['diagnostics'] = diagnostics
        check('exact independently reviewed UID observation bytes', rec(UID_ALLOWLIST)['sha256'] == UID_ALLOWLIST_SHA)
        uid_observation = json.loads(UID_ALLOWLIST.read_text())
        phase_data = {phase: json.loads((out / (phase + '-execution.json')).read_text()) for phase in ['export', 'package']}
        runtime_uid_values = {row['uid'] for row in exported['runtime_uids']['sidecars'].values()}
        uid_regeneration = admit_uid_regeneration(diagnostics, uid_observation, repo, s.SOURCE, prep, a.preparation_sha256, phase_data, runtime_uid_values)
        check('only75 exact approved cached nonruntime UID warnings and no unknown warnings or errors', len(uid_regeneration) == 75)
        result['admitted_nonruntime_uid_regeneration'] = uid_regeneration
        files = [build / name for name in ['yuga-native-linux-x86_64.zip', 'yuga-native-windows-x86_64.zip', 'native-export-manifest.json', 'native-package-manifest.json']]
        checksums = ''.join(rec(f)['sha256'] + '  ' + f.name + '\n' for f in files)
        checksum_file = build / 'SHA256SUMS.txt'
        if checksum_file.exists():
            check('existing checksums unchanged and exact', checksum_file.read_text() == checksums)
        else:
            with checksum_file.open('x') as stream:
                stream.write(checksums)
        s.audit(s.SOURCE, prep['entries']); s.audit(repo, prep['entries'])
        s.audit_index(s.SOURCE, prep['entries']); s.audit_index(repo, prep['entries'])
        s.audit_isolation(s.SOURCE, repo, prep['entries'])
        check('all source and index guards still pass after complete archive audit', True)
        check('phase receipts raw contract proofs official Windows proof and required logs unchanged through audit',
              all(rec(out / (phase + '-execution.json')) == value for phase, value in phase_records.items()) and
              all(rec(build / ('native-contracts-' + phase + '.json')) == value for phase, value in contract_records.items()) and
              rec(WINDOWS_PROOF)['sha256'] == WINDOWS_PROOF_SHA and
              all(rec(out / name) == value for name, value in log_records.items()))
        check('reviewed UID observation and every generated sidecar unchanged through audit',
              rec(UID_ALLOWLIST)['sha256'] == UID_ALLOWLIST_SHA and
              admit_uid_regeneration(diagnostics, uid_observation, repo, s.SOURCE, prep, a.preparation_sha256, phase_data, runtime_uid_values) == uid_regeneration)
        check('approved export free-space reserve remains', s.free_bytes(s.AREA) >= prep['reserve_bytes'])
        result.update({'passed': True, 'tracked_files': len(prep['entries']), 'runtime_files': len(exported['source']['files']), 'archives': archives, 'engine_selection': engines, 'diagnostics': diagnostics, 'phase_receipts': phase_records, 'raw_contract_proofs': contract_records, 'required_logs': log_records, 'windows_proof_sha256': WINDOWS_PROOF_SHA, 'five_assets': {f.name: rec(f) for f in [*files, checksum_file]}, 'free_bytes_after': s.free_bytes(s.AREA)})
    except Exception as error:
        result['failure'] = repr(error)
    result['finished_unix'] = time.time()
    s.dump_new(a.report, result)
    print(json.dumps({key: result.get(key) for key in ['passed', 'source_commit', 'tracked_files', 'runtime_files', 'free_bytes_after', 'failure']}))
    return 0 if result['passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
