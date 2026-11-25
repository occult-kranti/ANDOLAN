#!/usr/bin/env python3
"""Index actual Confluence timings from the two checked-in native kit profiles."""

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HZ = 20
NATIVE = ROOT / 'games/yuga-native/assets/design'
RUST = ROOT / 'games/yuga-rust/src'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hanuman_ticks(seconds):
    # Rust f64::round rounds nonnegative half values away from zero.
    return math.floor(seconds * HZ + 0.5)


def rama_ticks(seconds):
    return max(0, math.ceil(seconds * HZ - 1e-8))


def build():
    paths = {
        'hanuman_profile': NATIVE / 'hanuman-ability-kit.json',
        'rama_profile': NATIVE / 'rama-ability-kit.json',
        'hanuman_authority': RUST / 'combat.rs',
        'rama_authority': RUST / 'rama.rs',
    }
    hanuman_src = paths['hanuman_authority'].read_text()
    rama_src = paths['rama_authority'].read_text()
    if '(seconds * HZ as f64).round() as u32' not in hanuman_src:
        raise ValueError('Hanuman quantization changed; recheck this index')
    if '(s * 20.0 - 1e-8).ceil().max(0.0) as u32' not in rama_src:
        raise ValueError('Rama quantization changed; recheck this index')
    stage_body = rama_src.split('const STAGES:', 1)[1].split('];', 1)[0]
    stages = {
        hero_id: [draw, release]
        for hero_id, draw, release in re.findall(
            r'\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"\)', stage_body
        )
    }
    result = {'hz': HZ, 'scope': 'Confluence authoritative profiles; future abilities are excluded',
              'sources': {key: {'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}
                          for key, path in paths.items()}, 'heroes': {}}
    hanuman = json.loads(paths['hanuman_profile'].read_text())
    items = []
    for a in hanuman['abilities']:
        timing = a['timing']
        release = hanuman_ticks(timing['windup_s'])
        impact = release + hanuman_ticks(timing['travel_s'])
        items.append({'id': a['id'], 'slot': a['slot'], 'clip': a['motion'],
                      'release_tick': release, 'nominal_impact_tick': impact,
                      'unlock_tick': impact + hanuman_ticks(timing['recovery_s']),
                      'field_end_tick': impact + hanuman_ticks(timing['active_s']),
                      'cooldown_ticks': hanuman_ticks(a['cooldown_s']),
                      'geometry': a['geometry'], 'effects': a['effects']})
    result['heroes']['hanuman'] = items
    rama = json.loads(paths['rama_profile'].read_text())
    items = []
    for a in rama['abilities']:
        if a['id'] not in stages:
            raise ValueError('Missing Rama stage mapping: ' + a['id'])
        release = rama_ticks(a['windup_s'])
        item = {'id': a['id'], 'slot': a['slot'], 'clips': stages[a['id']],
                'release_tick': release,
                'unlock_tick': rama_ticks(a['windup_s'] + a['recovery_s']),
                'cooldown_ticks': rama_ticks(a['cooldown_s'])}
        for key in ('range_m', 'speed_mps', 'radius_m', 'damage', 'max_hits',
                    'movement_s', 'active_s', 'shield', 'heal_per_s', 'yaw_offsets_rad', 'stagger_s'):
            if key in a:
                item[key] = a[key]
        if a.get('movement_s'):
            item['nominal_move_end_tick'] = release + rama_ticks(a['movement_s'])
        if a.get('active_s'):
            item['field_end_tick'] = rama_ticks(a['windup_s'] + a['active_s'])
        if a.get('yaw_offsets_rad'):
            item['projectile_release_ticks'] = [
                release + rama_ticks(i * a['stagger_s'])
                for i in range(len(a['yaw_offsets_rad']))
            ]
        items.append(item)
    if set(stages) != {a['id'] for a in rama['abilities']}:
        raise ValueError('Rama stage set and native profile differ')
    result['heroes']['rama'] = items
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    options = parser.parse_args()
    path = HERE / 'baseline.json'
    content = json.dumps(build(), indent=2, ensure_ascii=False) + '\n'
    if options.check:
        if path.read_text() != content:
            raise ValueError('Baseline differs from the current authoritative profiles')
        print('Baseline matches both current kits, stage names and timing sources.')
    else:
        path.write_text(content)
        print(path)


if __name__ == '__main__':
    main()
