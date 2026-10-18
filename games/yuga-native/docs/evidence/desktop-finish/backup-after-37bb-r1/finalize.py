"""Seal the read-only Backup B proposal after owner paths are frozen."""
from pathlib import Path
import json,hashlib,datetime
OUT=Path(__file__).resolve().parent
s=json.loads((OUT/'summary.json').read_text());scope=json.loads((OUT/'scope.json').read_text());c=json.loads((OUT/'receipt-closure.json').read_text());before=json.loads((OUT/'git-before.json').read_text());after=json.loads((OUT/'git-after.json').read_text());assert before==after;a=json.loads((OUT/'allowlist.json').read_text());ignored=sum(r['ignored_but_explicit_frozen_artifact']for r in a['files']);cats='\n'.join(f"| {k} | {v['files']} | {v['bytes']:,} |"for k,v in s['categories'].items());limits='\n'.join(f"- `{x.get('path',x.get('prefix',''))}` ({x['owner']}): {x['reason']}."for x in scope['active_exclusions'])
readme=f'''Backup B is a prepared exact-file proposal against `{s['head']}`. No staging, Git writes, source edits, deletion, engine, import or build was performed. Root owns the final documentation, stage, commit and push. This records sources and evidence without changing any art/runtime disposition.

`allowlist.json` / `allowlist.paths0` / `allowlist.paths` select **{s['selected_files']} unique files, {s['selected_bytes']:,} logical bytes**. Every row has SHA-256, Git blob ID, byte count and physical/Git modes; no selected file exceeds 95 MiB. {ignored} explicitly sealed log/artifact files are normally ignored and require deliberate exact-list staging if admitted. Root's tracked documents are selected only if `tracked_files_authorized` explicitly lists the final owner-sealed paths; the initial observation is not an acceptance of later edits.

| Category | Files | Bytes |
|---|---:|---:|
{cats}

`scope.json` is the explicit source of prefixes/files, with changing output folders excluded. `inventory-and-recovery.json` maps duplicate content to exact 37bb Git blobs or another selected path. {s['historical_exclusions']} historical untracked files retain exact Backup A/d1 recovery routes from archived proofs (old working-file hashes were not repeated on final inventory); none require another bulk copy and none is declared disposable. Restore aliases in a private destination by copying the selected bytes or obtaining the recorded committed blob, then apply the target row's mode and verify its SHA-256 and Git blob ID. Lossless-gzip mappings identify the committed gzip and exact raw length/SHA. Do not overwrite a differing file. Content aliases do not transfer test or visual acceptance.

All **{c['passed']}/{c['checked']} top-level receipt artifact-table entries** match locally. Receipt closures include byte checks for generated artifacts that may intentionally be excluded from new Git storage; the exclusion records remain explicit. Missing execution environments/caches are not inferred to be reconstructed merely because source files or control reports exist. Root's exact runtime stays 96d5; this backup is archive/docs/inactive authoring unless an owner separately records promotion.

`backup-A-verification/` preserves the original stage/commit/remote proof files and independently compares all 566 committed path/blob/mode/size rows (237,354,193 bytes) with37bb's Git tree and exact 96d5 parent. It verifies no active runtime/config/notice path changed. The retained remote result is the prior owner proof, not a new network query; original SHA-256 byte verification was not repeated as a 237 MB campaign. `cleanup-execution-reference.json` narrowly checks the r4 cleanup execution receipt against its committed map, exact 80 paths and 469,565,440 allocated bytes, current removed-path absence and retained ZIP sizes. No cleanup or repeated ZIP hashing was performed.

No new complete `/workspace` discovery was run for this interim checkpoint, as explicitly deferred by the parent. The previous complete discovery is retained in Backup A: one primary project monorepo and four third-party dependency/reference clones (Blender add-ons, ozz-animation, Godot demos, Material Maker). The four clones are not additional owned product repositories. The final metadata walk and cloud configuration remain a later step.

Current scope exclusions/ownership:

{limits}

All proposed backup metadata remains under `/workspace/scratch/yuga-backup-B-plan-after-37bb-r1`. Preserve the recovery map and this verification packet alongside selected payloads so original sealed paths can be restored in a future chat. Normal HEAD/index hashes stayed unchanged during inventory. Recheck source hashes/modes before root's eventual staging; use a new explicit extension for anything sealed later.
'''
(OUT/'README.md').write_text(readme)
names=['README.md','scope.json','allowlist.json','allowlist.paths','allowlist.paths0','summary.json','inventory-and-recovery.json','receipt-closure.json','inventory.py','finalize.py','git-before.json','git-after.json','root-docs-initial-observation.json','cleanup-execution-reference.json','verify_backup_A.py']
names += [str(p.relative_to(OUT))for p in (OUT/'backup-A-verification').iterdir()if p.is_file()]
art={}
for n in sorted(names):
 p=OUT/n;b=p.read_bytes();art[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
r={'schema':1,'status':'prepared_only_not_staged','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_head':s['head'],'selected_files':s['selected_files'],'selected_bytes':s['selected_bytes'],'receipt_entries_passed':c['passed'],'source_or_git_mutations':False,'engine_runs':0,'normal_head_index_unchanged':True,'artifacts':art};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'files':s['selected_files'],'bytes':s['selected_bytes'],'receipt_sha256':hashlib.sha256((OUT/'receipt.json').read_bytes()).hexdigest(),'allowlist_sha256':art['allowlist.json']['sha256'],'paths0_sha256':art['allowlist.paths0']['sha256']}))
