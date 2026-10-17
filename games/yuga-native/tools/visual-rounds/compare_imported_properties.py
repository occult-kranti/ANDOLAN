#!/usr/bin/env python3
"""Compare full imported scene properties, retaining generated-ID differences."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(path):
    text = path.read_text()
    for resource, alias in re.findall(r'\[ext_resource [^\n]*path="([^"]+)" id="([^"]+)"\]', text):
        text = text.replace('id="'+alias+'"', 'id="'+resource+'"')
        text = text.replace('ExtResource("'+alias+'")', 'ExtResource("'+resource+'")')
    return re.sub(r'(?m)^(\[node [^\n]*) unique_id=\d+(\])$', r'\1\2', text).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh receipt'
    rows = []
    for lod in ['rama-hero','rama-hero-mid','rama-hero-far']:
        a, b = args.before/(lod+'.tscn'), args.after/(lod+'.tscn')
        ca, cb = canonical(a), canonical(b)
        rows.append({'lod':lod,'before':str(a),'after':str(b),
                     'raw_before_sha256':sha(a.read_bytes()),'raw_after_sha256':sha(b.read_bytes()),
                     'canonical_before_sha256':sha(ca),'canonical_after_sha256':sha(cb),
                     'all_resource_properties_equal':ca==cb})
    report = {'complete':all(row['all_resource_properties_equal'] for row in rows),'rows':rows,
              'normalization':'External texture aliases become exact declared resource paths; generated node unique_id attributes alone are removed. All other property values and relationships compare byte for byte. Raw file hashes remain preserved.',
              'tool_sha256':sha(Path(__file__).read_bytes())}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'complete':report['complete'],'lods':len(rows)}))
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
