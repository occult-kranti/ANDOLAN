#!/usr/bin/env python3
"""Cold font-only export check; never imports a world or claims a full game build."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project, output = args.project.resolve(), args.output.resolve()
    if output.exists():
        raise ValueError('Use a fresh output directory')
    output.mkdir(parents=True)
    packaging = module('packaging', project / 'tools/package-native.py')
    fixture = module('fixture', project / 'tests/traversal_security_cases.py')
    tiny = output / 'font-only'
    sources = packaging.validate_bundled_font_sources(project)
    for relative in sources:
        target = tiny / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(project / relative, target)
    (tiny / 'project.godot').write_text('config_version=5\n[application]\nconfig/name="Cold font-only package verification"\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n')
    (tiny / 'export_presets.cfg').write_text('[preset.0]\nname="Font only"\nplatform="Linux"\nrunnable=true\nexport_filter="all_resources"\ninclude_filter=""\nexclude_filter="NOTICE/*"\nexport_path=""\n[preset.0.options]\nbinary_format/architecture="x86_64"\n')
    def run(label, command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        log = result.stdout + result.stderr
        (output / (label + '.log')).write_text(log)
        if result.returncode or 'SCRIPT ERROR:' in log or '\nERROR:' in log:
            raise ValueError(label + ' failed')
    run('cold-font-import', [str(packaging.DEFAULT_LINUX), '--headless', '--path', str(tiny), '--editor', '--import'])
    binding = packaging.prove_imported_font_bindings(packaging.DEFAULT_LINUX, output / 'cold-fontfile-data.json', tiny)
    packaging.json_write(output / 'font-bindings.json', binding)
    pck = output / 'fonts-only.pck'
    run('font-export', [str(packaging.DEFAULT_LINUX), '--headless', '--path', str(tiny), '--export-pack', 'Font only', str(pck)])
    after = packaging.prove_imported_font_bindings(packaging.DEFAULT_LINUX, output / 'exported-fontfile-data.json', tiny)
    if after != binding:
        raise ValueError('Font binding changed during isolated export')
    # Parse the actual tiny PCK directory, then use its exact payloads in the
    # existing structural native-pack fixture to exercise production inspection.
    data = pck.read_bytes()
    version = struct.unpack_from('<I', data, 4)[0]
    base = struct.unpack_from('<Q', data, 24)[0]
    pos = struct.unpack_from('<Q', data, 32)[0] if version == 3 else 96
    count = struct.unpack_from('<I', data, pos)[0]
    pos += 4
    entries = []
    for _ in range(count):
        length = struct.unpack_from('<I', data, pos)[0]
        pos += 4
        name = data[pos:pos + length].rstrip(b'\0').decode().removeprefix('res://')
        pos += length
        offset, size = struct.unpack_from('<QQ', data, pos)
        pos += 36
        if name.endswith(('.fontdata', '.ttf.import')):
            entries.append((name, data[base + offset:base + offset + size]))
    if len(entries) != 6:
        raise ValueError('Actual font-only export must contain three resources and three remaps')
    native_fixture = [(name, ('structural fixture only: ' + name).encode()) for name in fixture.NAMES] + entries
    fixture_pack = output / 'structural-native-with-real-fonts.pck'
    fixture_pack.write_bytes(fixture.pack(native_fixture)[0])
    qualified = packaging.qualify_bundled_font_package(packaging.inspect_pack(fixture_pack), binding, tiny)
    # Real exported remap substitution remains valid PCK/MD5 yet must fail.
    changed = list(native_fixture)
    index = next(i for i, (name, _) in enumerate(changed) if name == 'assets/fonts/NotoSans-Regular.ttf.import')
    changed[index] = (changed[index][0], changed[index][1].replace(b'NotoSans-Regular.ttf-', b'NotoSerif-Regular.ttf-'))
    adversary = output / 'substituted-runtime-remap.pck'
    adversary.write_bytes(fixture.pack(changed)[0])
    rejected = None
    try:
        packaging.qualify_bundled_font_package(packaging.inspect_pack(adversary), binding, tiny)
    except ValueError as error:
        rejected = str(error)
    if rejected is None:
        raise ValueError('Substituted exported remap was accepted')
    report = {'task': 'R3-14-fonts', 'passed': True, 'cold_import_only_three_fonts': True,
              'actual_exported_font_payloads': len(entries), 'sources': sources,
              'actual_font_only_pack': packaging.record(pck), 'qualification': qualified,
              'wrong_packed_remap_rejected': rejected, 'bindings_stable_across_export': True,
              'packager': packaging.record(project / 'tools/package-native.py'),
              'probe': packaging.record(Path(__file__)),
              'scope': 'Actual cold font-only import/export and FontFile.data identities; structural native fixture carries those six exact payloads. No complete YUGA export, gameplay, art or platform acceptance.'}
    packaging.json_write(output / 'result.json', report)
    print(json.dumps({'passed': True, 'actual_font_payloads': len(entries), 'output': str(output)}))


if __name__ == '__main__':
    main()
