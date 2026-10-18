#!/usr/bin/env python3
"""Recover the retained 103-file Godot cache; never import or launch an engine."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    output, receipt = args.output.resolve(), args.receipt.resolve()
    if not args.output.is_absolute() or output.exists() or receipt.exists() or output in receipt.parents:
        parser.error('Use a fresh absolute output and fresh receipt outside it')
    native = Path(__file__).resolve().parents[2]
    evidence = native / 'docs/evidence/desktop-finish'
    base = evidence / 'S1/W1/gold-component-r2'
    delta = evidence / 'S3/lead/paving-palette-r1'
    base_receipt = json.loads((base / 'receipt.json').read_text())
    delta_receipt = json.loads((delta / 'receipt.json').read_text())
    comparison = json.loads((delta / 'comparison.json').read_text())['godot_seed']
    expected = comparison['complete_input_manifest']
    archives = [
        (base / 'godot-shader-cache-seed.tar.gz', base_receipt['artifacts']['godot-shader-cache-seed.tar.gz']),
        (delta / 'godot-seed-delta.tar.gz', delta_receipt['files']['godot-seed-delta.tar.gz']),
    ]
    recovered = {}
    inputs = []
    for archive, pin in archives:
        if sha(archive) != pin['sha256'] or archive.stat().st_size != pin['bytes']:
            raise ValueError('Archive identity mismatch: ' + str(archive))
        with tarfile.open(archive, 'r:gz') as source:
            members = source.getmembers()
            for member in members:
                name = PurePosixPath(member.name)
                if not member.isfile() or name.is_absolute() or '..' in name.parts or not str(name).endswith('.cache'):
                    raise ValueError('Unexpected cache member: ' + member.name)
                data = source.extractfile(member).read()
                digest = hashlib.sha256(data).hexdigest()
                if name.as_posix() in recovered or expected.get(name.as_posix()) != digest:
                    raise ValueError('Duplicate or mismatched cache member: ' + member.name)
                recovered[name.as_posix()] = data
        inputs.append({'path': str(archive.relative_to(native)), 'sha256': pin['sha256'],
                       'bytes': pin['bytes'], 'members': len(members)})
    if set(recovered) != set(expected):
        raise ValueError('Recovered membership does not match retained complete input manifest')
    output.mkdir(parents=True)
    for name, data in recovered.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    actual = {str(path.relative_to(output)): sha(path) for path in output.rglob('*') if path.is_file()}
    if actual != expected or any(sha(path) != pin['sha256'] for path, pin in archives):
        raise ValueError('Recovered cache or archive changed during recovery')
    report = {'passed': True, 'files': actual, 'file_count': len(actual),
              'bytes': sum(len(data) for data in recovered.values()), 'output': str(output),
              'inputs': inputs, 'comparison_sha256': sha(delta / 'comparison.json'),
              'tool_sha256': sha(Path(__file__)), 'engine_started': False,
              'scope': 'Exact Godot shader cache recovery only. Mesa cache and preferences are not recovered; this does not qualify cold startup.'}
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2))


if __name__ == '__main__':
    main()
