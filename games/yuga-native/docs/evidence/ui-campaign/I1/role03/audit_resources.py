#!/usr/bin/env python3
"""Read-only frozen-source/import mapping audit; no Godot/import/export runs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess


def digest(path, algorithm='sha256'):
    value = hashlib.new(algorithm)
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def record(path):
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def safe(root, relative):
    if relative.startswith('/') or '..' in Path(relative).parts or '\\' in relative:
        raise ValueError('Unsafe resource path: ' + relative)
    path = root / relative
    if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError('Missing/unsafe resource: ' + relative)
    return path


def import_sections(text):
    result, section = {}, None
    for line in text.splitlines():
        header = re.fullmatch(r'\[([^\]]+)\]', line.strip())
        if header:
            section = header[1]
            if section in result:
                raise ValueError('Duplicate section')
            result[section] = {}
        elif section:
            value = re.fullmatch(r'([A-Za-z0-9_./]+)=(.*)', line.strip())
            if value:
                if value[1] in result[section]:
                    raise ValueError('Duplicate key')
                result[section][value[1]] = value[2]
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True, help='Canonical project with package tools')
    parser.add_argument('--freeze', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project, frozen = args.project.resolve(), args.freeze.resolve()
    manifest_path = frozen / 'ui-source-freeze.json'
    manifest = json.loads(manifest_path.read_text())
    checks, imports = [], []
    def check(name, passed, **facts):
        checks.append({'name': name, 'passed': bool(passed), **facts})
    for category in ('source_sha256', 'existing_import_sha256'):
        wrong = []
        for relative, expected in manifest[category].items():
            try:
                actual = digest(safe(frozen, relative))
                if actual != expected:
                    wrong.append(relative)
            except ValueError:
                wrong.append(relative)
        check(category + ' complete frozen pins', not wrong, count=len(manifest[category]), mismatches=wrong)
    for descriptor in sorted((frozen / 'assets').rglob('*.import')):
        relative = str(descriptor.relative_to(frozen))
        fields = import_sections(descriptor.read_text())
        source = json.loads(fields['deps']['source_file']).removeprefix('res://')
        check(relative + ' names its exact raw source', relative == source + '.import')
        destinations = [value.removeprefix('res://') for value in json.loads(fields['deps']['dest_files'])]
        remaps = {key: json.loads(value).removeprefix('res://') for key, value in fields['remap'].items() if key == 'path' or key.startswith('path.')}
        check(relative + ' remaps match destination set', bool(remaps) and set(remaps.values()) == set(destinations))
        raw = safe(frozen, source)
        destination_records = {value: record(safe(frozen, value)) for value in destinations}
        stems = {re.match(r'(.godot/imported/[^/]+-[0-9a-f]{32})', value)[1] for value in destinations}
        if len(stems) != 1:
            raise ValueError('Unexpected imported destination stems: ' + relative)
        md5_path = safe(frozen, next(iter(stems)) + '.md5')
        md5 = dict(re.findall(r'(source_md5|dest_md5)="([0-9a-f]{32})"', md5_path.read_text()))
        computed_dest = hashlib.md5()
        for destination in destinations:
            with (frozen / destination).open('rb') as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    computed_dest.update(block)
        check(relative + ' cache source MD5 matches raw bytes', md5.get('source_md5') == digest(raw, 'md5'))
        check(relative + ' cache destination MD5 matches imported bytes', md5.get('dest_md5') == computed_dest.hexdigest())
        imports.append({'source': source, 'raw': record(raw), 'descriptor': {'path': relative, **record(descriptor)},
                        'remaps': remaps, 'destinations': destination_records,
                        'md5_receipt': {'path': str(md5_path.relative_to(frozen)), **record(md5_path)}})
    # Boot's immediate static dependency closure deliberately excludes world GLBs.
    def closure(initial):
        pending, found = list(initial), {}
        while pending:
            relative = pending.pop()
            if relative in found:
                continue
            path = safe(frozen, relative)
            found[relative] = record(path)
            if path.suffix in ('.gd', '.tscn', '.tres', '.gdshader'):
                text = path.read_text()
                if path.suffix == '.gd':
                    refs = re.findall(r'preload\("res://([^"\n]+)"\)', text)
                else:
                    refs = re.findall(r'path="res://([^"\n]+)"', text)
                pending.extend(refs)
        return found
    boot = closure(['scenes/boot.tscn'])
    check('boot immediate preload closure contains bundled fonts', all(path in boot for path in (
        'assets/fonts/NotoSans-Regular.ttf', 'assets/fonts/NotoSerif-Regular.ttf', 'assets/fonts/DejaVuSans.ttf')))
    check('boot immediate preload closure excludes world/hero GLBs', not any(path.endswith('.glb') for path in boot))
    transition = (frozen / 'scripts/scene_transition.gd').read_text()
    routes = dict(re.findall(r'&"(courtyard|confluence|combat_film)": "res://([^"]+)"', transition))
    check('all three runtime scene routes exist', set(routes) == {'courtyard', 'confluence', 'combat_film'} and all((frozen / path).is_file() for path in routes.values()))
    route_dependencies = {name: closure([path]) for name, path in routes.items()}
    spec = importlib.util.spec_from_file_location('packaging', project / 'tools/package-native.py')
    packaging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packaging)
    provenance = packaging.validate_rama_hero_notice(project)
    check('canonical accepted hero provenance has complete66 sources', len(provenance['sources']) == 66)
    check('runtime freeze carries exact accepted hero NOTICE', record(safe(frozen, 'NOTICE/RAMA-HERO-PROVENANCE.json')) == provenance['notice'])
    runtime_provenance = {path: expected for path, expected in provenance['sources'].items()
                          if path.startswith(('assets/', 'scripts/', 'shaders/'))}
    for path, expected in runtime_provenance.items():
        check('runtime freeze accepted provenance: ' + path, record(safe(frozen, path)) == expected)
    fonts = packaging.validate_bundled_font_sources(frozen)
    check('three pinned fonts and five notice files present', len(fonts) == 8)
    important = [item for item in imports if item['source'].startswith('assets/fonts/') or item['source'] in (
        'assets/heroes/rama-hero.glb', 'assets/heroes/rama-hero-mid.glb', 'assets/heroes/rama-hero-far.glb',
        'assets/materials/rama-finish/woven-roughness.png')]
    prior_path = project / 'docs/evidence/visual-rounds/round3/role06/proposal-reconciliation.json'
    prior = json.loads(prior_path.read_text())
    for item in prior['unchanged_imported_resources']:
        check('rendered accepted imported resource: ' + item['source'],
              digest(safe(frozen, item['resource'])) == item['resource_sha256']
              and digest(safe(frozen, item['source'])) == item['source_sha256']
              and digest(safe(frozen, item['source'] + '.import')) == item['descriptor_sha256'])
    result = {'task': 'I1-03-resource-provenance-preflight', 'passed': all(item['passed'] for item in checks),
              'canonical_head_at_audit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=project, text=True).strip(),
              'freeze': str(frozen), 'freeze_manifest': record(manifest_path), 'audit_script': record(Path(__file__)),
              'checks': checks, 'check_count': len(checks), 'import_count': len(imports), 'imports': imports,
              'boot_immediate_dependency_closure': boot, 'route_dependencies': route_dependencies,
              'accepted_hero_provenance': provenance, 'fonts_and_notices': fonts, 'important_runtime_imports': important,
              'runtime_provenance_bindings': runtime_provenance, 'prior_actual_import_receipt': record(prior_path),
              'authoring_boundary': 'The U5 runtime freeze intentionally excludes historical editable/GLB authoring files and package tools. The full66-source gate ran against canonical source; its exact runtime subset and NOTICE bind this freeze. This runtime snapshot is not a complete package-authoring checkout.',
              'scope': 'Read-only raw/descriptor/cache mapping and source SHA/MD5 identities. Existing cache freshness is verified against raw bytes; no new import, resource decoding, first-load execution, lifecycle, rendering, PCK export or publication is claimed. U5 final source changes need a new freeze/audit.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': result['passed'], 'checks': len(checks), 'imports': len(imports), 'failures': [c for c in checks if not c['passed']]}, indent=2))


if __name__ == '__main__':
    main()
