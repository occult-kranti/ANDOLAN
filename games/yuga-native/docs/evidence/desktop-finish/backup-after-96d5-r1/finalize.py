"""Seal the prepared backup proposal, without altering source or Git."""
from pathlib import Path
import collections,datetime,hashlib,json
OUT=Path(__file__).resolve().parent
summary=json.loads((OUT/'summary.json').read_text());inv=json.loads((OUT/'inventory-and-recovery.json').read_text());scope=json.loads((OUT/'scope.json').read_text());closure=json.loads((OUT/'receipt-closure.json').read_text());dep=json.loads((OUT/'dependency-recovery.json').read_text());allow=json.loads((OUT/'allowlist.json').read_text());before=json.loads((OUT/'git-before.json').read_text());after=json.loads((OUT/'git-after.json').read_text());assert before==after
category='\n'.join('| '+k+' | '+str(v['files'])+' | '+f"{v['bytes']:,}"+' |' for k,v in summary['categories'].items())
excluded='\n'.join('- `'+x['prefix']+'`: '+x['reason']+'.' for x in scope['active_exclusions'])
ignored=sum(x['ignored_but_explicit_frozen_artifact']for x in allow['files'])
text=f'''Prepared backup inventory at exact production HEAD `{summary['head']}`. **No staging, Git objects, refs, source mutations, deletion, engine, import or build was performed.** The parent retains staging/commit ownership. This proposal preserves authored work and evidence; it does not accept rejected hair or inactive environment geometry.

The exact candidate list is `allowlist.json` with NUL-delimited `allowlist.paths0` and readable `allowlist.paths`: **{summary['selected_files']} unique new files, {summary['selected_bytes']:,} logical bytes**. No selected file is over 95 MiB. Each row records SHA-256, Git blob SHA-1, byte count, physical mode and Git mode. {ignored} selected files are ignored by normal Git rules but explicitly belong to sealed evidence; any later staging must use the exact list and account for those files deliberately.

| Category | Files | Bytes |
|---|---:|---:|
{category}

`scope.json` gives every allowed prefix and explicit file. Frontage uses its exact 56-artifact native receipt plus receipt/index, avoiding native user directories. Transport source and execution are included only through the specified closed files. Generic `.uid`, `__pycache__`, ambient XDG/`.godot`, compiled candidate-import-cache tars and unrelated `.design`/scratch are omitted. The two W1 r4 isolated-user tar files are an explicit parent-approved exception: sealed controlled experiment evidence. `controlled-user-archive-review.json` records their metadata census; no bulk extraction occurred, and the single373B controlled settings payload matches its already-preserved report SHA. This exception does not admit ambient user state.

`inventory-and-recovery.json` describes all {summary['scope_files']} scoped files. {summary['recovery_kinds'].get('already_in_head',0)} already have their exact path and content in HEAD; {summary['recovery_kinds'].get('recover_from_head_blob',0)} duplicate another exact HEAD blob; {summary['recovery_kinds'].get('recover_from_selected_file',0)} duplicate a selected new file. An additional {summary['historical_exclusions']} untracked historical R4/R5/shoulder files are resolved by the existing d1 backup lineage or its exact-byte gzip maps; none require new content copies. These are content-recovery aliases, not transferred test or art acceptance.

To reconstruct a missing duplicate in a separate destination, obtain the recorded Git blob from the pinned commit/source or copy its selected source, write its exact bytes, apply the destination row's mode, and verify both SHA-256 and Git blob ID. For `historical_lossless_gzip_mapping`, decompress the recorded committed gzip and require the declared raw byte count/SHA. Do not overwrite a differing existing file. Restore path aliases before running receipts that use original filenames. The four clay external artifacts are now byte-exact repository payloads, verified against the unchanged9656d5a1 receipt and c805b7ea recovery map (`clay-recovery-checks.json`). The archive payloads and original PNGs remain exact; no image processing or recompression occurred.

Receipt closure: **{closure['passed']}/{closure['checked']} top-level artifact-table entries** match current exact bytes (including explicitly excluded generated artifacts still present locally); there are no unresolved in-repository paths in those checked tables. **{dep['passed']}/{dep['total']} R6 source dependencies** also match and have recovery paths; the retained draw gzip was decompressed read-only and matches its raw tape SHA. The first naïve checker treated the historical transport template's `generate.py` pin as the final generator and failed. That raw failure is retained; the corrected resolver maps only this explicitly documented historical entry to byte-identical `generate-pending-source.py`. No sealed receipt was rewritten. A second bookkeeping correction distinguishes ignored sealed logs from tracked working changes.

This is not a self-contained environment image. `dependency-recovery.json` preserves the R6 recipe's external immutable baseline/store and Godot/Mesa seed identities, plus exact official importer/unmodified renderer pins. Those generated execution aids are not copied. Source dependencies, semantic arrays and actual originals are preserved; recreating an execution environment requires the pinned tools/import process. `external-package-outputs.json` names the exact ZIP/PCK output dependencies and five source-pinned release assets. The146,132,535B Windows ZIP is external, not a proposed Git blob. Parent-owned public download verification supplies publication proof separately.

Current exclusion/ownership boundaries:

{excluded}

All output from this inventory remains under `/workspace/scratch/yuga-backup-plan-after-96d5-r1`. Normal HEAD and index SHA match before/after; no index lock was created. Revalidate row hashes/modes before eventual staging, and add any later sealed packet through a new explicit extension rather than broad directory staging.

`WORKSPACE_DISCOVERY.md` and `workspace-discovery.json` provide the complete dated `/workspace` repository/manifest classification: five Git roots, one primary monorepo plus four third-party reference checkouts, no followed symlinks and no traversal errors. Existing snapshot/tool manifests are distinguished from active product sources. This metadata census does not establish environment/test readiness or license permission.
'''
(OUT/'README.md').write_text(text)
files=['README.md','WORKSPACE_DISCOVERY.md','scope.json','allowlist.json','allowlist.paths','allowlist.paths0','inventory-and-recovery.json','summary.json','receipt-closure.json','receipt-closure-first-failure.json','dependency-recovery.json','external-package-outputs.json','controlled-user-archive-review.json','clay-recovery-checks.json','workspace-discovery-initial.json','workspace-discovery-delta.json','workspace-discovery.json','discover_workspace.py','inventory.py','inventory-r1.py','verify_dependencies.py','finalize.py','git-before.json','git-after.json']
artifacts={}
for n in files:
 p=OUT/n;b=p.read_bytes();artifacts[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
receipt={'schema':1,'status':'prepared_only_not_staged','sealed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_head':summary['head'],'selected_files':summary['selected_files'],'selected_bytes':summary['selected_bytes'],'over_95_MiB':summary['over_95_MiB'],'receipt_entries_passed':closure['passed'],'source_dependencies_passed':dep['passed'],'normal_head_index_unchanged':before==after,'source_mutations':False,'git_writes':False,'engine_runs':0,'artifacts':artifacts}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'files':summary['selected_files'],'bytes':summary['selected_bytes'],'receipt_sha256':hashlib.sha256((OUT/'receipt.json').read_bytes()).hexdigest(),'allowlist_sha256':artifacts['allowlist.json']['sha256'],'paths0_sha256':artifacts['allowlist.paths0']['sha256']}))
