#!/usr/bin/env python3
"""Pin the authored film's actual resources for portable package inspection."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTICE = ROOT / 'NOTICE/CONFLUENCE-DUEL-PROVENANCE.json'


def record(path):
    return {'asset': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def document():
    actor = json.loads((ROOT/'art/cinematics/actor-manifest.json').read_text())
    audio = json.loads((ROOT/'art/cinematics/audio-manifest.json').read_text())
    paths = sorted(p for p in (ROOT/'assets/cinematics').rglob('*')
                   if p.is_file() and p.suffix not in {'.import','.uid'})
    required = ['confluence-duel.json','ravana-sentinel.glb','duel-motion-rama.tres',
                'duel-motion-ravana.tres','audio/confluence-duel-mix.wav']
    if any(not (ROOT/'assets/cinematics'/p).is_file() for p in required):
        raise ValueError('Film resources are incomplete')
    if record(ROOT/'assets/cinematics/ravana-sentinel.glb')['sha256'] != actor['actors']['ravana']['sha256']:
        raise ValueError('Sentinel provenance differs from actual GLB')
    if record(ROOT/audio['track']['path'])['sha256'] != audio['track']['sha256']:
        raise ValueError('Audio provenance differs from actual WAV')
    return {'schema':1,'title':'Confluence: a duel of timing',
        'scope':'Original 24-second choreographed film. Not a live match or commercial-game reconstruction.',
        'anatomy':'Existing MakeHuman CC0 anatomy, rig and skin weights from the original YUGA Rama production asset. See MAKEHUMAN-ASSET-LICENSE.md and RAMA-PRODUCTION-PROVENANCE.json.',
        'new_work':'Original sentinel costume, crown and armour; film-specific authored/IK animation libraries; deterministic effects; timeline, camera direction and captions.',
        'audio':'Original deterministic mathematical synthesis. No downloaded recordings, samples, voices or commercial game music.',
        'runtime_rama_sha256':record(ROOT/'assets/heroes/rama-production.glb')['sha256'],
        'rama_revision_scope':'Current playable film resource; historical rendered films retain their own source hashes. Surface reconstruction and rig-preservation evidence are in RAMA-PRODUCTION-PROVENANCE.json.',
        'source_records':[record(ROOT/'art/cinematics/actor-manifest.json'),record(ROOT/'art/cinematics/audio-manifest.json')],
        'assets':[record(p) for p in paths]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    value=document()
    if args.check:
        if json.loads(NOTICE.read_text()) != value:
            raise ValueError('Film package notice is stale; review source records and regenerate')
    else:
        NOTICE.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'passed':True,'check':args.check,'assets':len(value['assets']),'notice':str(NOTICE)}))


if __name__=='__main__':
    main()
