# Pinned REA development CLI bootstrap

This manifest and lockfile reuse the exact previously reviewed `rea-agents`
**6.5.0** package tree. `setup-rea.sh` installs it into a fresh directory outside
the checkout. The existing `/workspace/tooling/rea-runtime` is preserved; the
script refuses every existing destination, including empty directories and
symlinks. Choose a new path when testing or restoring another installation.

From the repository root:

```sh
bash games/yuga-native/tools/native-analysis/setup-rea.sh \
  --destination /workspace/tooling/rea-runtime-NEW --dry-run
bash games/yuga-native/tools/native-analysis/setup-rea.sh \
  --destination /workspace/tooling/rea-runtime-NEW
```

The dry run validates source pins, destination and executable presence. It does
not run Node/npm, create the destination or contact the network. A real install
checks Node/npm versions before creating the destination. Requirements are
POSIX/Bash, Python 3.12, existing Node 22.19+, 24.11+, or 26+, npm, and the adjacent
repository `inspect-component.py` process helper. The helper supplies the tested
bounded-process-group cleanup; its exact hash is recorded in every receipt.
No `sudo`, persistent agent registration, Ghidra installation or network-policy
change occurs.

The install uses `npm ci --ignore-scripts --no-fund --no-audit --strict-ssl=true`
with the inherited proxy/CA/environment and an owned npm cache inside the new
destination. The source and copied lockfile must remain byte-identical. The
installed package name/version/bin entry, five compiled dispatcher/runtime
files, actual CLI version and help commands are checked before **READY** is
written to `setup-receipt.json`. Optional components that require lifecycle
builds, browser/native providers and analysis of a target have separate setup
and acceptance. The installed CLI path is printed on success.

The default deadline is 300 seconds per install/CLI process; `--timeout` accepts
1–600 seconds. Local Node/npm version probes use a 30-second deadline. On a
failed install, the script returns nonzero and retains **FAILED** plus partial
logs in its own newly created directory. It does not delete or replace an
existing installation. Review those logs and use a fresh destination for a
later attempt. Logs never intentionally print authentication values; credentials
are not written into these source files or receipts.

Pins:

- `package.json` SHA256: `04df3d8e8a559cd75824d810268a49519164930cf09386e76b56bc8e086836ed`
- `package-lock.json` SHA256: `73fa03d670870e8234e7823bca98e8cd846773fb661819ffe48a5bbb6728c7dd`
- Root package integrity: `sha512-C6BG7LyrAdR74mSjertM6PrxJkcNZ2bfQNOJornPo9erDEp2tyPRVYPnV5Yodr+1RqewCQla68WulXlVnveD+A==`

The lock contains 179 entries including the root and platform/optional packages;
the actual installed count depends on the host. npm enforces lockfile archive
integrity. This bootstrap does not rerun the earlier independent registry
signature audit or establish every dependency publisher's provenance. REA's
own code is MIT; its dependencies and separately obtained providers retain their
own terms. The current GitHub source checkpoint is not asserted identical to
this published npm package merely because both label themselves 6.5.0.

Actual guards, failed attempts and the fresh successful install are archived in
[`docs/evidence/open-art-wave/toolchain/`](../../../docs/evidence/open-art-wave/toolchain/).
The [REA source/reuse study](../../../docs/research/REA_REUSE_REFRESH.md) records
the separate real MikkTSpace component analysis. Successful CLI installation is
not a game, graphics, optional-provider or multiplayer acceptance result.
