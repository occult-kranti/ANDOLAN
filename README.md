# YUGA Hanuman native package recovery

This distribution branch holds the exact Linux and Windows ZIP payloads for the Hanuman ability update. The package and part sizes and SHA-256 values are recorded in [manifest.json](manifest.json). [SHA256SUMS.txt](SHA256SUMS.txt) contains the final package hashes. The release source and version are maintained separately on the [Hanuman Trial branch](https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-hanuman-trial).

To download and rebuild both verified ZIPs, use Git and Python 3.8 or newer.

```sh
git clone --depth 1 --single-branch --branch distribution/hanuman-abilities-2026-11-25 https://github.com/occult-kranti/ANDOLAN.git hanuman-packages
cd hanuman-packages
python3 rebuild-packages.py assembled
```

The rebuilt ZIPs are written to `assembled/`. Python checks every part and each rebuilt ZIP before returning its final name.
