"""Reconcile the design correspondence with the native Dust census and actual Blender kit."""
import argparse
import csv
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

DESIGN = Path(__file__).resolve().parent
DISTRICT = DESIGN.parent
INVENTORY = DESIGN.parents[2] / 'docs/research/dust2-map-lab/inventory'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    with path.open('rb') as src:
        return hashlib.file_digest(src, 'sha256').hexdigest()


def require(test, issue):
    if not test:
        raise ValueError(issue)


def check_correspondence(survey):
    with (DESIGN / 'dust-callouts.csv').open(newline='', encoding='utf-8') as src:
        rows = list(csv.DictReader(src))
    nav = read_json(INVENTORY / 'nav.json')
    expected = {('' if k == '(unassigned)' else k): v['areas'] for k, v in nav['places'].items()}
    actual = {}
    room_ids = {room['id'] for room in survey['rooms']}
    for row in rows:
        place = row['source_nav_place']
        require(place not in actual, f'Duplicate source place {place!r}')
        actual[place] = int(row['native_area_count'])
        counterparts = set(row['exchange_room_ids'].split())
        require(counterparts <= room_ids, f'Unknown room for {place!r}')
        require(counterparts or not place, f'Missing design counterpart for {place!r}')
        require(row['reuse_decision'] in {'retain function', 'transform', 'reference only'},
                f'Unknown disposition for {place!r}')
        require(row['translation'].strip() and row['design_family'], f'Missing design reading for {place!r}')
    require(actual == expected, 'CSV rows or counts disagree with the native NAV place census')
    require(sum(actual.values()) == nav['areas'] == 1118 and actual[''] == 74,
            'Expected the identified 1,118-area Source edition including 74 unnamed areas')
    return actual


def check_kit(survey):
    register = read_json(DISTRICT / 'scene/scene-register.json')
    placements = register['original_kit_placements']
    room_ids = {room['id'] for room in survey['rooms']}
    cover_ids = {cover['id'] for cover in survey['covers']}
    furnishing_ids = {p['placement_id'].removeprefix('Furnishing.') for p in placements
                      if p['placement_id'].startswith('Furnishing.')}
    require(cover_ids == furnishing_ids, 'The kit does not dress exactly the twenty surveyed covers')
    require(len({p['placement_id'] for p in placements}) == len(placements), 'Repeated kit placement ID')
    sources = {}
    model_dir = (DISTRICT.parent / 'mandala-map-studio/models').resolve()
    for placement in placements:
        path = (DISTRICT / 'scene' / placement['source']).resolve()
        require(path.parent == model_dir and path.stem == placement['asset'], f'Unexpected kit source {path.name}')
        if path not in sources:
            sources[path] = digest(path)
        require(sources[path] == placement['source_sha256'], f'Kit master changed for {path.name}')
        require(placement['element'] in room_ids, f'Unknown room for {path.name}')
        require(len(placement['scale_xyz']) == 3 and all(v > 0 and math.isfinite(v) for v in placement['scale_xyz']),
                f'Invalid source scale for {path.name}')
    require(len(sources) == 10 and len(placements) == 24, 'Update the published source and placement counts')
    cloth = register['cloth']
    require(digest(DISTRICT / 'scene' / cloth['source']) == cloth['sha256'], 'Cloth master hash changed')
    require({p['element'] for p in cloth['placements']} == {'atk', 'dyers', 'mid'}, 'Recheck the three cloth hosts')
    return len(sources), len(placements)


def check_design(survey):
    native_classes = read_json(INVENTORY / 'source.json')['entities']
    radiant_classes = read_json(INVENTORY / 'hanzo.json')['source_entities']
    require(native_classes['count'] == 375 and 'func_door' not in native_classes['classes'],
            'Recheck the Source 1 gates against the native class dictionary')
    require(radiant_classes['count'] == 298 and radiant_classes['classes']['func_door']['count'] == 12,
            'Recheck the door census in Hanzo’s editable map')
    covers = {p['id']: p for p in survey['covers']}
    used = []
    for entry in survey['entries']:
        require(len(entry['covers']) == 2, f'Expected two shelters at {entry["id"]}')
        for cid in entry['covers']:
            cover = covers[cid]
            require(cover['room'] == entry['site'] and cover['size'][2] >= survey['rules']['standing_height_m'],
                    f'The registered shelter {cid} no longer provides standing-height mass at its claimed site')
            used.append(cid)
    require(len(set(used)) == len(used) == 14, 'Update the seven entrances and fourteen shelters in the register')
    require(Counter(e['site'] for e in survey['entries']) == {'a': 4, 'b': 3}, 'Review site entry distribution')
    sources = read_json(DESIGN / 'reference-receipts.json')['sources']
    require(len({s['id'] for s in sources}) == len(sources), 'Repeated source receipt')
    for source in sources:
        require(re.fullmatch('[0-9a-f]{64}', source['sha256']) and source['bytes'] > 0
                and source['url'].startswith('https://'), f'Incomplete receipt for {source["id"]}')
    for doc in (DESIGN / 'architecture.md', DESIGN / 'transfer-register.md'):
        for ref in re.findall(r'\[[^\]]+\]\(([^)]+)\)', doc.read_text(encoding='utf-8')):
            if ref.startswith(('https:', 'http:', '#')):
                continue
            require((DESIGN / ref.partition('#')[0]).exists(), f'Missing target {ref} in {doc.name}')


def check_native_files(lab, actual):
    with (lab / 'evidence/official-nav.csv').open(newline='', encoding='utf-8') as src:
        require(Counter(r['areaName'] for r in csv.DictReader(src)) == actual, 'Extracted NAV differs from the register')
    entities = read_json(lab / 'evidence/source-entities.json')
    counts = Counter(e['classname'] for e in entities)
    source = read_json(INVENTORY / 'source.json')['entities']['classes']
    require(counts == {k: v['count'] for k, v in source.items()}, 'Original Source entities differ from the census')
    text = (lab / 'radiant/q3dust2-jb-beta6.map').read_text(encoding='latin-1')
    counts = Counter(re.findall(r'^\s*"classname"\s+"([^"]+)"', text, re.MULTILINE))
    hanzo = read_json(INVENTORY / 'hanzo.json')['source_entities']['classes']
    require(counts == {k: v['count'] for k, v in hanzo.items()}, 'The editable Radiant class counts differ')
    receipt = next(s for s in read_json(DESIGN / 'reference-receipts.json')['sources'] if s['id'] == 'hanzo')
    require(digest(lab / 'radiant/source/q3dust2-jb-beta6.pk3') == receipt['sha256'], 'Hanzo package hash differs')
    require(digest(lab / 'radiant/source/author-readme.txt') == receipt['member']['sha256'],
            'Hanzo author readme hash differs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-lab', type=Path, help='Also reconcile local original-source extracts and fan package.')
    args = parser.parse_args()
    survey = read_json(DISTRICT / 'plan/survey.json')
    actual = check_correspondence(survey)
    masters, placements = check_kit(survey)
    check_design(survey)
    if args.source_lab:
        check_native_files(args.source_lab, actual)
    print(f'{len(actual) - 1} native place names + unnamed areas, {sum(actual.values())} NAV areas, '
          f'{masters} kit masters, {placements} placements and seven two-cover entries verified.')
    if args.source_lab:
        print('Independent native NAV, both original class lists, Hanzo package and author readme verified.')


if __name__ == '__main__':
    main()
