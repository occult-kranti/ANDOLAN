#!/usr/bin/env python3
"""Verify the qualified Linux ZIP, then extract its exact payload once."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile

SOURCE = '5542e61610d20e591effbed9dec15fd10398e31d'
ENGINE = 'f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'
PREFIX = 'yuga-native-linux-x86_64/'


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['archive', 'export-manifest', 'package-manifest', 'source', 'destination', 'report']:
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ['archive-sha256', 'export-sha256', 'package-sha256']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    if args.destination.exists() or args.report.exists():
        parser.error('Fresh destination and report required')
    checks, members = {}, {}
    record = {'passed': False, 'checks': checks, 'members': members,
              'source_commit': SOURCE, 'script_sha256': digest(__file__),
              'scope': 'Independent Linux archive/source/payload identity and extraction only; no engine execution.'}

    def check(name, passed):
        checks[name] = bool(passed)
        if not passed:
            raise ValueError(name)

    try:
        before = {str(path): digest(path) for path in [args.archive, args.export_manifest, args.package_manifest]}
        check('qualified_input_hashes', before[str(args.archive)] == args.archive_sha256 and
              before[str(args.export_manifest)] == args.export_sha256 and
              before[str(args.package_manifest)] == args.package_sha256)
        exported = json.loads(args.export_manifest.read_text())
        packaged = json.loads(args.package_manifest.read_text())
        check('exact_clean_source_commit', all(d['git']['head'] == SOURCE and
              d['git']['native_worktree_status'] == '' for d in [exported, packaged]))
        package = packaged['packages']['linux']
        check('archive_outer_identity', package['sha256'] == args.archive_sha256 and
              package['bytes'] == args.archive.stat().st_size and package['filename'] == args.archive.name)
        check('export_package_runtime_identity', exported['source']['sha256'] == packaged['runtime_source_sha256'])
        source_mismatch = [name for name, row in exported['source']['files'].items()
                           if not (args.source/name).is_file() or
                           (args.source/name).stat().st_size != row['bytes'] or digest(args.source/name) != row['sha256']]
        record['source_file_count'] = len(exported['source']['files'])
        record['source_mismatches'] = source_mismatch
        check('all_exported_source_files_exact', not source_mismatch and record['source_file_count'] == 552)
        with zipfile.ZipFile(args.archive) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            check('unique_safe_regular_members', len(names) == len(set(names)) == package['entry_count'] and
                  all(name.startswith(PREFIX) and not PurePosixPath(name).is_absolute() and
                      '..' not in PurePosixPath(name).parts and not info.is_dir() and
                      stat.S_ISREG(info.external_attr >> 16) and not (info.flag_bits & 1)
                      for name, info in zip(names, infos)))
            manifest_name = PREFIX + 'PACKAGE-MANIFEST.json'
            inner = json.loads(archive.read(manifest_name))
            check('inner_exact_source_platform', inner['platform'] == 'linux-x86_64' and
                  inner['git'] == exported['git'] and inner['runtime_source'] == exported['source'])
            check('exact_member_inventory', set(names) == {PREFIX + name for name in inner['payloads']} | {manifest_name})
            check('engine_and_pck_manifest_identity', inner['payloads']['godot']['sha256'] == ENGINE ==
                  package['engine']['sha256'] and inner['payloads']['yuga-native.pck']['sha256'] ==
                  package['pck']['sha256'] == exported['packs']['linux']['sha256'])
            args.destination.mkdir(parents=True)
            for info in infos:
                relative = info.filename.removeprefix(PREFIX)
                target = args.destination/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                value, size = hashlib.sha256(), 0
                with archive.open(info) as source, target.open('xb') as output:
                    for block in iter(lambda: source.read(1024 * 1024), b''):
                        output.write(block)
                        value.update(block)
                        size += len(block)
                mode = stat.S_IMODE(info.external_attr >> 16)
                os.chmod(target, mode)
                members[relative] = {'bytes': size, 'sha256': value.hexdigest(),
                                     'mode': oct(mode), 'zip_crc32': f'{info.CRC:08x}'}
                expected = inner['payloads'].get(relative)
                check('member_' + relative, size == info.file_size and
                      (expected is None or (size == expected['bytes'] and value.hexdigest() == expected['sha256'])))
            check('native_executable_modes', (args.destination/'godot').stat().st_mode & 0o777 == 0o755 and
                  (args.destination/'launch.sh').stat().st_mode & 0o777 == 0o755)
            check('all_extracted_bytes_rehashed', all(digest(args.destination/name) == row['sha256'] for name, row in members.items()))
        check('qualified_inputs_unchanged', all(digest(Path(name)) == checksum for name, checksum in before.items()))
        record.update({'passed': True, 'input_sha256': before, 'destination': str(args.destination),
                       'pck_sha256': members['yuga-native.pck']['sha256'], 'crc_scope': 'Every ZipExtFile read through EOF; Python verifies its stored CRC.',
                       'member_count': len(members), 'extracted_bytes': sum(row['bytes'] for row in members.values())})
    except Exception as error:
        record['error'] = repr(error)
    record['check_count'] = len(checks)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: record.get(key) for key in ['passed', 'check_count', 'member_count', 'extracted_bytes', 'error']}))
    return 0 if record['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
