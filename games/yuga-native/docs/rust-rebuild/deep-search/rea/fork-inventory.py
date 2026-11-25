#!/usr/bin/env python3
"""Enumerate REA's public forks, and export metadata with reproducible game filters."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import csv
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import time

REPO = 'morluto/rea'
PAGE_SIZE = 100
FIELDS = 'map([.id,.full_name,.created_at,.default_branch,.language,.description,.topics])'
GAME = re.compile(r'\b(?:games?|gaming|source[ -]port|playable|shooter|modding|unity|godot|unreal|pok[eé]mon|touhou|valorant|overwatch|deadlock|doom|quake|warcraft|dota|gunz|gta|zombies|bevy|romhack|romhacking|gba|emulator|nintendo|gamecube)\b|游戏|遊戲|ゲーム|게임', re.I)


def api(path, fields):
    command = ['gh', 'api', path, '--jq', fields]
    for attempt in range(4):
        try:
            return json.loads(subprocess.check_output(command, timeout=50, stderr=subprocess.PIPE))
        except (subprocess.SubprocessError, ValueError):
            if attempt == 3:
                raise
            time.sleep(4 * 2**attempt)


def fetch(cache):
    pages = cache / 'pages'
    pages.mkdir(parents=True, exist_ok=True)
    meta_path = cache / 'upstream.json'
    if not meta_path.exists():
        metadata = api('repos/' + REPO, '{forks_count,network_count,full_name,description,updated_at}')
        meta_path.write_text(json.dumps(metadata))
    count = json.loads(meta_path.read_text())['forks_count']

    def page(number):
        path = pages / f'{number:04}.json'
        if not path.exists():
            rows = api(f'repos/{REPO}/forks?sort=oldest&per_page={PAGE_SIZE}&page={number}', FIELDS)
            assert isinstance(rows, list) and all(len(row) == 7 for row in rows)
            temporary = path.with_suffix('.part')
            temporary.write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
            temporary.replace(path)
        return len(json.loads(path.read_text()))

    last = (count + PAGE_SIZE - 1) // PAGE_SIZE + 1
    with ThreadPoolExecutor(max_workers=8) as pool:
        for number, _ in enumerate(pool.map(page, range(1, last + 1)), start=1):
            if number % 100 == 0:
                print(f'Read {number} pages', flush=True)
    while page(last) == PAGE_SIZE:
        last += 1


def export(cache, out):
    meta = json.loads((cache / 'upstream.json').read_text())
    pages = sorted((cache / 'pages').glob('*.json'))
    assert pages and [int(p.stem) for p in pages] == list(range(1, len(pages) + 1))
    unique = {}
    returned = 0
    terminal = False
    for path in pages:
        values = json.loads(path.read_text())
        assert len(values) <= PAGE_SIZE and not (terminal and values), 'Rerun with a fresh cache if page order changed'
        terminal = len(values) < PAGE_SIZE
        returned += len(values)
        unique.update((row[0], row) for row in values)
    assert terminal, 'Last page must have fewer than 100 entries'
    by_name = sorted(unique.values(), key=lambda row: row[1].lower())
    out.mkdir(parents=True, exist_ok=True)
    content = io.StringIO(newline='')
    writer = csv.writer(content, delimiter='\t', lineterminator='\n')
    writer.writerow(['id','repository','created_utc','default_branch','github_language','description','topics'])
    writer.writerows([*row[:6], ','.join(row[6])] for row in by_name)
    dataset = gzip.compress(content.getvalue().encode(), compresslevel=9, mtime=0)
    dest = out / 'direct-forks.tsv.gz'
    dest.write_bytes(dataset)
    candidates = []
    for _, name, _, branch, language, description, topics in by_name:
        # An account handle such as "gamer" is not a claim about this repository.
        fields = [name.split('/')[1].replace('-', ' ').replace('_', ' '), description or '', ' '.join(topics)]
        signals = [s for s, value in zip(['repository name', 'description', 'topics'], fields) if GAME.search(value)]
        if language == 'Rust':
            signals.append('GitHub primary language is Rust')
        if signals:
            candidates.append({'repo':name,'branch':branch,'language':language,'signals':signals})
    report = {'retrieved_at_utc':datetime.now(timezone.utc).isoformat(timespec='seconds'), 'endpoint':f'https://api.github.com/repos/{REPO}/forks?sort=oldest&per_page=100', 'upstream_at_start':meta, 'pages_with_terminal':len(pages), 'returned_rows':returned, 'unique_repository_ids':len(unique),'duplicate_rows':returned-len(unique),'observed_created_utc':[min(r[2] for r in by_name),max(r[2] for r in by_name)],'language_counts':dict(Counter(row[4] or 'unreported' for row in by_name).most_common()),'game_pattern':GAME.pattern,'selected':candidates,'archive':dest.name,'archive_sha256':hashlib.sha256(dataset).hexdigest(),'coverage':'Oldest-first numeric pages to a terminal page. Repositories can be created, renamed or removed during enumeration. Fork branding and GitHub language tags are leads. Separate owner repositories, private projects and individual working branches require additional searches.'}
    (out/'direct-forks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(f'{len(unique)} unique repos; {len(candidates)} metadata candidates')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cache', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--from-cache', action='store_true')
    args = parser.parse_args()
    if not args.from_cache:
        fetch(args.cache)
    export(args.cache, args.output)
