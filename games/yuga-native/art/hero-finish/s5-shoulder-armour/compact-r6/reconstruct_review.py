"""Rebuild the frozen review trio into a fresh directory; never canonical assets."""
import argparse
import json
from pathlib import Path
from replace_left_cap import GLB, sha, replace

HERE = Path(__file__).resolve().parent
MANIFEST_SHA = '886528206ee33e1b3809e0363840ba9e08666883725985796fefbdb8da93ee0e'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    manifest_path = HERE / 'replacement-r7/replacement-manifest.json'
    assert sha(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    assert sha(HERE / 'replace_left_cap.py') == manifest['base_generator_sha256']
    out = args.output.resolve()
    assert not out.exists()
    out.mkdir(parents=True)
    rows = []
    for level, item in manifest['levels'].items():
        source, sculpture = GLB(item['source']), GLB(item['sculpture'])
        assert sha(source.path) == item['source_sha256']
        assert sha(sculpture.path) == item['sculpture_sha256']
        destination = out / Path(item['output']).name
        result = replace(source, sculpture, destination)
        assert result['sha256'] == item['sha256']
        rows.append({'level': level, 'output': str(destination), 'sha256': result['sha256'], 'exact': True})
    (out / 'reconstruction.json').write_text(json.dumps({'passed': True, 'manifest_sha256': MANIFEST_SHA,
        'generator_sha256': sha(__file__), 'levels': rows}, indent=2) + '\n')


if __name__ == '__main__':
    main()
