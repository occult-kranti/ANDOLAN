#!/usr/bin/env python3
"""Feed fresh private119db/successor traces to the unchanged original27-check comparator."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[4]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inputs=ROOT/'strict-inputs';assert not inputs.exists();inputs.mkdir()
    links={}
    for hz in (30,60,120):
        for role,label in [('legacy','baseline'),('candidate','candidate')]:
            suffix='r4' if role=='legacy' and hz==30 else 'r3'
            source=ROOT/f'{role}-scene-{hz}-{suffix}'/'report.json'
            value=json.loads(source.read_text())
            target=inputs/(f'{label}-60'+('' if label=='baseline' else '-r1')+'.json.gz' if hz==60 else f'{label}-{hz}-r2.json')
            if hz==60:target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))
            else:shutil.copy2(source,target)
            trace=source.parent/value['trace']['path']
            os.link(trace,inputs/trace.name)
            links[target.name]={'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),
                                'alias_sha256':sha(target),'trace_sha256':sha(trace)}
    comparator=PROJECT/'tests/desktop_s3_motion_compare.py'
    command=['python3',str(comparator),'--evidence',str(inputs),'--report',str(ROOT/'strict-comparison.json')]
    completed=subprocess.run(command,capture_output=True,text=True)
    (ROOT/'strict-comparison.log').write_text(completed.stdout+completed.stderr)
    (ROOT/'strict-input-derivation.json').write_text(json.dumps({'command':command,'exit_code':completed.returncode,
        'comparator_sha256':sha(comparator),'inputs':links,'scope':'Only filename aliases and deterministic compression of complete summaries. Every original predicate and threshold executes unchanged; no test reduction.'},indent=2)+'\n')
    print(completed.stdout.strip());raise SystemExit(completed.returncode)


if __name__=='__main__':main()
