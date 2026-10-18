# Single motion JSON recovery preparation

Only `/workspace/scratch/yuga-next-W1-r1/motion-candidate-actual-r1/capture.json` is proposed for removal. W1 explicitly releases this raw JSON and has no current/future dependency. All PNGs, other raw reports, source, PCK/extraction/runtime and caches remain protected. No deletion occurred during preparation.

Exact decoded bytes: 16703321; SHA256 `0488631d617417af6fad269410f49dd007ccf6b1e87a280bd7628c23df546ae2`. Allocated reclaim: **16703488 bytes**. Retained gzip `/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/motion-candidate-r1/capture.json.gz` is 6301308 bytes with SHA256 `40f1c1ea5dac2374a59b0f7df19f5429752d520938a05121081bb1e2aa1b57f8`. Immutable motion owner receipt SHA256 `bc8d344e78b2b048c25f425da155adf158ed7f258efd51ed4b2de1bdb2528fee` explicitly binds the raw path/bytes/hash and lossless gzip. Existing historical retention wording is not rewritten; a later removal receipt records the transition.

Preparation verified regular paths, no symlink ancestors, no hardlinks, exact inode/mode/size/hash/timestamps, streamed byte-for-byte gzip decompression including EOF/CRC, and accessible process files/maps (inspection limits remain in dry-run.json). Synthetic controls passed27/27; no real target unlink, engine or network in those checks. No whole-project scan.

Root must back up **all10 exact paths in recovery-map.json backup_required_paths**: eight direct files here plus the existing retained capture.json.gz and immutable owner receipt. The map and helper are part of that backup. Proposed ref `refs/heads/backup/yuga-desktop-motion-json-2026-10-18b`. A local commit alone is insufficient: root must push, verify full remotecommit and authorize the single removal.

Frozen map SHA `f5a3b6de728cfdddd895547ca8bad3476d234ef7a86b81c9b8fa15a70f8c425b`; guard SHA `af9fa4f5d6db31b913e0266f231573c38379dd61186e7c6701ca5ae673a9b804`. After backup and explicit root authorization, run:

```bash
python -B /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/motion-json-recovery-r1/motion-json.py --map-sha256 f5a3b6de728cfdddd895547ca8bad3476d234ef7a86b81c9b8fa15a70f8c425b --backup-ref refs/heads/backup/yuga-desktop-motion-json-2026-10-18b --backup-commit FULL_REMOTE_VERIFIED_COMMIT --remove --receipt /workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W6-integration-r1/motion-json-recovery-r1/execution.json
```

The guard verifies ls-remote and exact blobs for all10 required paths, then repeats recovery/ownership/process checks and checks final inode/metadata before unlinking ONLY the target. It records actual removed logical/allocated bytes and retained gzip/owner hashes. No broad cleanup is available.

Recovery is lossless decompression to a fresh exclusive0600 temporary sibling, enforcing decoded size/hash and gzip EOF/CRC, fsyncing then atomically installing only while target is absent. Preserve any newly existing target. A restored file has a new inode/time and requires a fresh map before any future cleanup. Check free space before restoring16.7MB.
