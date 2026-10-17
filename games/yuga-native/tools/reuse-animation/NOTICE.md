# ValveResourceFormat algorithm attribution

The hemisphere-alignment and Ramer–Douglas–Peucker key-selection portions of
`audit.py` adapt [Source 2 Viewer / ValveResourceFormat](https://github.com/ValveResourceFormat/ValveResourceFormat):

- Commit: `b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1`.
- File: `ValveResourceFormat/IO/Gltf/GltfModelExporter.Anim.cs`, lines 686–845.
- File SHA-256: `47122fb3effe5f7a0eb4a89922002a804d753729eaefb5e03095c045fb2ac803`.
- Upstream LICENSE SHA-256: `19549e9b3203eaf3938f35f98e63fc6b166a16af29936affa3df6ec7e2ae7f8d`.

YUGA's adaptation retains both existing endpoints, uses a conservative half
selection budget, restores source keys when dense interpolation checks fail,
and refuses unsupported channels. Its extraction, admission, numeric audit and
external JSON reporting are project additions. No Source 2 game asset,
Esoterica animation-graph code, viewer binary or dependency is included.

The MIT License (MIT)

Copyright (c) 2015 ValveResourceFormat Contributors

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
