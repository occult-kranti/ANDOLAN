#!/usr/bin/env python3
"""Verify every archived raw framebuffer, producer receipt and frozen source pin."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh audit receipt'
    records, failures = [], []
    source_cache = {}
    for capture in sorted(args.evidence.rglob('capture.json')):
        report = json.loads(capture.read_text())
        folder = capture.parent
        relative = str(folder.relative_to(args.evidence))
        rejected = relative.startswith('rejected/') or (folder/'framing-rejection.json').exists()
        row = {'capture': relative, 'classification': 'retained-rejected' if rejected else 'review-evidence',
               'report_sha256': sha(capture), 'raw_pngs': len(report['shots']),
               'native_complete': report['complete'], 'checks': {}}
        checks = row['checks']
        checks['raw_frame_hashes'] = all(sha(folder/s['file']) == s['sha256'] for s in report['shots'])
        checks['raw_frame_count'] = len(list(folder.glob('*.png'))) == len(report['shots'])
        checks['unchanged_source_report'] = report['source_sha256'] == report['source_after_sha256']
        run_path = folder/'run.json'
        if run_path.exists():
            run = json.loads(run_path.read_text())
            checks['producer_report_hash'] = run['report_sha256'] == sha(capture)
            checks['producer_logs'] = all(sha(folder/('producer'+ext)) == run[key]
                for ext, key in [('.godot.log','godot_log_sha256'),('.xvfb.log','xvfb_log_sha256')])
            checks['native_success'] = run['complete'] and run['godot_exit_code'] == 0
            checks['engine_warning_free'] = not run['warnings']
            project = Path(run['command'][run['command'].index('--path')+1])
            exact = True
            for resource, digest in report['source_sha256'].items():
                path = project/resource.removeprefix('res://')
                if path not in source_cache: source_cache[path] = sha(path)
                exact = exact and source_cache[path] == digest
            checks['frozen_sources_still_exact'] = exact
            checks['archived_harness_exact'] = all(
                sha(folder/'harness'/resource.removeprefix('res://tools/visual-rounds/')) == digest
                for resource,digest in report['source_sha256'].items()
                if resource.startswith('res://tools/visual-rounds/'))
        else:
            checks['failed_producer_explicitly_retained'] = rejected and not report['complete']
        for key, passed in checks.items():
            if not passed: failures.append(relative+': '+key)
        records.append(row)
    receipt = {'complete': not failures, 'captures': records, 'capture_groups': len(records),
               'raw_pngs': sum(r['raw_pngs'] for r in records),
               'review_raw_pngs': sum(r['raw_pngs'] for r in records if r['classification']=='review-evidence'),
               'rejected_raw_pngs': sum(r['raw_pngs'] for r in records if r['classification']=='retained-rejected'),
               'unique_frozen_sources_checked': len(source_cache), 'failures': failures,
               'scope': 'Archive integrity and source provenance only; visual acceptance remains with independent reviewers.'}
    args.output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['captures']}))
    return 0 if receipt['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
