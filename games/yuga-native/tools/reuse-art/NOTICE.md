# Third-party software and asset rights

This original, project-local offline adapter calls separately installed npm
packages. It does not embed their source in the runtime game, and it does not
assert a repository-wide license. The package is private/UNLICENSED for the
original adapter; upstream components retain the licenses below.

- **glTF-Transform core, extensions and functions 4.3.0:** MIT; Don McCurdy.
  Repository https://github.com/donmccurdy/glTF-Transform, release commit
  `3b3afffbd4d3a29790c9fb166fa4c6755687154d`. Inspected `LICENSE.md`,
  `packages/functions/src/weld.ts`, `reorder.ts`, `hash-table.ts` and
  `compact-primitive.ts`. `npm view @gltf-transform/core@4.3.0 gitHead`
  independently returned this commit. The annotated tag object itself is
  `517461f7f82019312323822f07d9ba6fbd8655b0`; it is not the source commit.
- **meshoptimizer 0.24.0:** MIT; Arseny Kapoulkine. Repository
  https://github.com/zeux/meshoptimizer, pinned source
  `7b2d4f4c817aea55d74dcd65d9763ac2ca608026`; inspected `LICENSE.md`,
  `js/meshopt_encoder.js`, `js/README.md` and `src/vcacheoptimizer.cpp`.
  This retains the version already used by YUGA's native LOD authoring work;
  the JS package is separately locked and hashed. Upstream 1.0 was read for
  comparison but was not adopted here.

`package-lock.json` records exact resolved packages and registry integrity.
Direct MIT licenses do not replace transitive dependency terms: the functions
package also installs image-processing dependencies, including sharp
(Apache-2.0) and a platform libvips package (LGPL-3.0-or-later, with its own
third-party notices). Those paths are not exercised by this geometry adapter.
Retain installed dependency license files when redistributing an installation;
this repository does not vendor or bundle them.

The test's synthetic plane is original project work. The measured courtyard
input is the project's CC0-1.0 generated geometry/textures, as dedicated in
`assets/environment/lanka_courtyard.metadata.json` and `art/README.md`.
Its generator's code licensing is separate. The tool license grants no rights
to an arbitrary input model. The report identifies the original GLB hash;
all provenance remains attached to the input and source research record.
No Blender/Rigify/Material Maker code or third-party character model is copied
into this adapter.

## glTF-Transform license

The MIT License (MIT)

Copyright (c) 2024 Don McCurdy

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## meshoptimizer license

MIT License

Copyright (c) 2016-2025 Arseny Kapoulkine

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
