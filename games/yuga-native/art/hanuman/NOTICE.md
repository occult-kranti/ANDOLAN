# Hanuman asset provenance

This character design uses the user-supplied *Mythic 3D Hero Design Pipeline*,
page 12, as a design brief. The lower silhouette, gada, nonliteral armor motifs,
face mesh edits, cloth textures, effects staging and jewelry here were authored
for YUGA. No image from that PDF is packed into the model or texture set.

The existing browser YUGA Hanuman supplies the authoring path, original mace
poses, anatomy configuration and rig format. Reuse is through these repository
sources, with exact hashes recorded in [manifest.json](manifest.json):

- [CC0 MakeHuman donor manifest](../../../yuga/art/sources/makehuman/manifest.json)
- [CC0 asset license](../../../yuga/art/sources/makehuman/makehuman-assets-license.md)
- [Existing anatomy importer](../../../yuga/art/pipeline/anatomy.py)
- [Original pose and IK authoring](../../../yuga/art/pipeline/animations.py)
- [Geometry helpers](../../../yuga/art/pipeline/geometry.py)

The pin for MakeHuman data is `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.
Attribution: © 2020 Data Collection AB, Joel Palmius, Jonas Hauquier.
The anatomical mesh, target geometry, skeleton definitions and weights use
CC0 data. No MakeHuman application source, downloaded commercial asset,
unlicensed texture pack or captured motion is included. Open Image Denoise
was used only as a postprocessor and its executable is not redistributed.
