#!/usr/bin/env python3
"""Keep the exported Confluence specification byte-identical to its authoring source."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail on stale or missing runtime data; never modify it')
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[1]
    source = project / 'art/world/confluence-map.json'
    target = project / 'assets/world/confluence-map.json'
    data = source.read_bytes()
    manifest = json.loads(data)
    if manifest.get('schema_version') != 1 or not manifest.get('authority_collision_boxes'):
        raise ValueError('Unrecognized or incomplete map specification')
    if args.check:
        if not target.exists() or target.read_bytes() != data:
            raise ValueError('Runtime map is stale; run tools/stage-world.py before importing or exporting')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    print(json.dumps({'pass': True, 'mode': 'check' if args.check else 'stage',
        'source': str(source.relative_to(project)), 'runtime': str(target.relative_to(project)),
        'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}))


if __name__ == '__main__':
    main()
