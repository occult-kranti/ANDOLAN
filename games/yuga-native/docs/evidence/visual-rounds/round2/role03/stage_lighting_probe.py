#!/usr/bin/env python3
"""Stage one deferred diagnostic overlay; never imports, renders or edits runtime."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stage(variant, project, output):
    project = project.resolve()
    output = output.resolve()
    checkout = PROJECT.parents[1]
    if output == checkout or checkout in output.parents or output == project or project in output.parents:
        raise ValueError('Diagnostic outputs must stay outside the checkout')
    if output.exists():
        raise ValueError('Fresh output required; preserve earlier diagnostics')
    pins = json.loads((HERE / 'source-pins.json').read_text())['runtime_sources']
    for relative, expected in pins.items():
        if sha((project / relative).read_bytes()) != expected:
            raise ValueError('Pinned input changed: ' + relative)
    relative = 'scripts/production_lighting.gd' if variant == 'directional-pcss-off' else 'project.godot'
    before = (project / relative).read_text()
    if variant == 'directional-pcss-off':
        old, new = '\tsun.light_angular_distance = 0.7', '\tsun.light_angular_distance = 0.0'
        if '\tsun.shadow_bias = 0.2' not in before or '\tsun.shadow_normal_bias = 0.35' not in before:
            raise ValueError('Accepted bias baseline missing')
        variable, previous, candidate = 'sun.light_angular_distance', 0.7, 0.0
    else:
        old = 'anti_aliasing/quality/msaa_3d=1'
        new = old + '\nanti_aliasing/quality/use_taa=true'
        if 'anti_aliasing/quality/use_taa' in before:
            raise ValueError('Baseline already declares TAA; re-audit instead of guessing')
        variable, previous, candidate = 'root Viewport use_taa (startup setting)', False, True
    if before.count(old) != 1:
        raise ValueError('Expected exactly one edit target')
    after = before.replace(old, new, 1)
    target = output / 'overlay' / relative
    target.parent.mkdir(parents=True)
    target.write_text(after)
    patch = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='a/' + relative, tofile='b/' + relative))
    (output / 'candidate.patch').write_text(patch)
    manifest = {
        'schema': 1, 'task': 'R2-03', 'variant': variant,
        'status': 'deferred diagnostic; not rendered or accepted', 'runtime_promoted': False,
        'source_commit': '0437ea91edf6989ff78c1eeadb3661f4825b60f2',
        'project': str(project), 'source_pins_sha256': sha((HERE / 'source-pins.json').read_bytes()),
        'generator_sha256': sha(Path(__file__).read_bytes()),
        'changes': [{'file': relative, 'variable': variable, 'before': previous, 'after': candidate,
                     'source_sha256': sha(before.encode()), 'candidate_sha256': sha(after.encode())}],
        'changed_variable_count': 1,
        'restore': 'Use independent frozen baseline project copies; discard this overlay binding before the other probe. Never combine variants.',
        'retained': {'shadow_enabled': True, 'shadow_bias': 0.2, 'shadow_normal_bias': 0.35, 'msaa_3d': 1},
        'required_runtime_observation': 'Record root.use_taa, root.msaa_3d and sun.light_angular_distance with every captured frame.',
        'limits': 'A single still cannot approve contact or TAA motion. TAA internally affects jitter/history and mip LOD bias despite one explicit setting.'
    }
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', required=True, choices=['directional-pcss-off', 'taa-on'])
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not args.output.is_absolute():
        parser.error('Absolute fresh output required')
    try:
        print(json.dumps(stage(args.variant, args.project, args.output), indent=2))
    except (OSError, ValueError) as error:
        parser.error(str(error))
