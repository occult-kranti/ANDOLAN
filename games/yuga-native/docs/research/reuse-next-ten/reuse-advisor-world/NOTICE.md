# Source notices

The isolated Python playback-window inspector adapts the half-open event-window,
loop-wrap, restart and terminal-update rules from Source 2 Viewer:

- `ValveResourceFormat/ValveResourceFormat`, commit
  `a2d07483864d380940f61abf52ddfcb905a00633`.
- `Renderer/Animation/SampledAnimationEvents.cs`, SHA-256
  `0529e7eb646c9dace4b0bd7ad6f28a1d6c33a7d206e1de0bce1a7a00504ceed6`.
- Copyright (c) 2015 ValveResourceFormat Contributors. MIT License.
- The complete permission and warranty text is retained unchanged in
  [the source licence](sources/ValveResourceFormat--ValveResourceFormat/LICENSE.txt).

The exact selected upstream source and third-party notices are retained under
`sources/`. OWLib references are MIT, Copyright (c) 2016-2024 overtools;
its complete [licence](sources/overtools--OWLib/LICENSE.txt) is retained.
No OWLib parser is ported or executed here. Its effect timing/attachment model
informs the proposed dependency metadata, rather than supplying any game art.

No upstream `Tests/Files` content, Overwatch data, Source 2 resources, client
builds, maps, audio, character models or extracted commercial files are included.
The executable experiment uses this repository's existing original Rama combat
fixture and original synthetic boundary values. It does not execute the upstream
tests, whose own fixtures are not admitted as our assets.

Local adaptation adds finite/type/range admission checks, explicit paused-final
behavior, validation of the non-loop `finished` contract, and exact represented
duration-multiple normalization. The last change addresses Python's
`(3 * .4) / .4 == 3.0000000000000004` loop-boundary case without a time epsilon.
The capture, report CLI and local checker are original project code. They use
original Rama events and synthetic edge values; the upstream C# tests were read
as source only. Modification details and accepted hashes are in
[provenance.json](provenance.json) and the accepted run receipt.
