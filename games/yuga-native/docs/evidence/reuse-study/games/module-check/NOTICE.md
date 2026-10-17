# Separate GPLv3 research fixture

`vendor/openmw/components/misc/objectpool.hpp` is an **unchanged** source file from the OpenMW project, maintained by the OpenMW contributors, at commit `fa732a1551a696f8cb52a65c9896b8b4b92eb3dd`:

https://github.com/OpenMW/openmw/blob/fa732a1551a696f8cb52a65c9896b8b4b92eb3dd/components/misc/objectpool.hpp

The pinned OpenMW README declares GPLv3. Its complete unchanged license text accompanies the header at `vendor/openmw/COPYING`. `input-manifest.json` records the original source bytes and hash. No OpenMW models, textures, sounds, NIF/KF data, commercial Morrowind files or other engine source are included.

`openmw-pool-check.cpp` is an original GPL-3.0-only research harness written for this audit. It compiles that header directly to test reuse, duplicate null/reset ownership, retained payload, missing capacity limit and destruction. The executable is generated in scratch and is not distributed with native YUGA. This directory is a separate research component; it is not an MIT-licensed game runtime dependency.

Reproduce with a local C++ compiler and sanitizers, without installation scripts or external packages:

```sh
taskset -c 0,1 python3 games/yuga-native/docs/evidence/reuse-study/games/module-check/check.py --output /tmp/NEW-openmw-pool-check
```

The pool owner must outlive and remain at a stable address relative to its borrowed objects. The test does not execute an invalid dangling-owner release or claim thread safety. It demonstrates no item growth only for the stated fixed-concurrency workload; the pool has no hard capacity guard or automatic payload reset.
