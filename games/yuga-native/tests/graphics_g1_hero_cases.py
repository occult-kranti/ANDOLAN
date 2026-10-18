#!/usr/bin/env python3
"""G1 scalar-map continuity, repeatability and filtering intent. No visual claim."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from PIL import Image, ImageChops, ImageStat

PROJECT = Path(__file__).resolve().parents[1]
MAPS = PROJECT / 'assets/hero-finish'
GENERATOR = PROJECT / 'art/hero-finish/build_g1_maps.py'
checks = []


def check(name, passed, details=None):
    checks.append({'name': name, 'passed': bool(passed), 'details': details or {}})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads((MAPS / 'g1-manifest.json').read_text())
    check('manifest pins editable original generator outside runtime assets',
          manifest['generator_sha256'] == sha(GENERATOR)
          and manifest['generator_source'] == 'art/hero-finish/build_g1_maps.py'
          and not (MAPS / 'build_g1_maps.py').exists())
    spec = importlib.util.spec_from_file_location('g1_maps', GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    sys.dont_write_bytecode = True
    spec.loader.exec_module(generator)
    for entry in manifest['maps']:
        path = MAPS / entry['path']
        image = Image.open(path)
        check(entry['path'] + ': exact manifest identity', sha(path) == entry['sha256'] and path.stat().st_size == entry['bytes'])
        check(entry['path'] + ': one bounded 512 linear channel', image.size == (512, 512) and image.mode == 'L'
              and entry['color_space'] == 'linear scalar' and entry['channel'] == 'RED')
        lo, hi = image.getextrema()
        check(entry['path'] + ': useful bounded roughness without black/white clipping', 80 < lo < hi < 190, {'range_u8': [lo, hi]})
        check(entry['path'] + ': horizontal and vertical repeat edges are byte-identical',
              image.crop((0, 0, 1, 512)).tobytes() == image.crop((511, 0, 512, 512)).tobytes()
              and image.crop((0, 0, 512, 1)).tobytes() == image.crop((0, 511, 512, 512)).tobytes())
        field = generator.hair if entry['path'].startswith('hair') else generator.gold
        regenerated = generator.build(field)
        check(entry['path'] + ': editable formula exactly reconstructs decoded pixels', regenerated.tobytes() == image.tobytes())
        descriptor = path.with_name(path.name + '.import').read_text()
        check(entry['path'] + ': lossless linear import requests full mip chain',
              'mipmaps/generate=true' in descriptor and 'mipmaps/limit=-1' in descriptor
              and 'compress/mode=0' in descriptor and 'process/hdr_as_srgb=false' in descriptor
              and 'source_file="res://assets/hero-finish/' + path.name + '"' in descriptor)
        original_mean = ImageStat.Stat(image).mean[0]
        mip = image.copy()
        mip_means = []
        while mip.width > 1:
            mip = mip.resize((max(1, mip.width//2), max(1, mip.height//2)), Image.Resampling.BOX)
            mip_means.append(ImageStat.Stat(mip).mean[0])
        # Quantization may accumulate at most about one u8 step per level.
        check(entry['path'] + ': area filtering keeps distant average stable', max(abs(x-original_mean) for x in mip_means) < 5,
              {'base_mean': original_mean, 'mip_means': mip_means, 'scope': 'CPU area-filter model; actual imported mip payload is a separate check'})
        if entry['path'].startswith('hair'):
            dx = ImageStat.Stat(ImageChops.difference(image, ImageChops.offset(image, 1, 0))).mean[0]
            dy = ImageStat.Stat(ImageChops.difference(image, ImageChops.offset(image, 0, 1))).mean[0]
            check('hair: variation follows retained UV clump direction', dx > 8*dy and dy > 0,
                  {'mean_across_difference': dx, 'mean_length_difference': dy})
    report = {'passed': all(c['passed'] for c in checks), 'checks': checks,
              'source_sha256': sha(PROJECT / 'scripts/rama_surface_finish.gd'),
              'test_sha256': sha(Path(__file__)), 'manifest_sha256': sha(MAPS / 'g1-manifest.json'),
              'scope': 'Original roughness-map identity, reproducibility, wrap continuity, bounded values and filtering intent. No engine import, rendered quality or GPU claim.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps({'passed': sum(c['passed'] for c in checks), 'checks': len(checks), 'report': str(args.report)}))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
