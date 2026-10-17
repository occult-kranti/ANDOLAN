# Rama facial performance sources

The small orbital partition and runtime eyelid performance code are original project work. The anatomy, skeleton and weights retain the attribution in [the Rama hero notice](../hero-rama/NOTICE.md).

The two source data files below are **CC0**, as explicitly recorded by `face-poseunits.json`:

> (c) 2020 Data Collection AB, Joel Palmius, Jonas Hauquier. Standard face pose units. Author: MakeHuman. License: CC0.

Pinned upstream revision: `makehumancommunity/makehuman@a8bc2d54ff0ac92e78ff71431b1023eda42bf482`.

| Local file | Upstream source | SHA-256 |
| --- | --- | --- |
| `sources/face-poseunits.json` | [Metadata](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/poseunits/face-poseunits.json) | `e7224f76e9610049b79e5f9e8ac2985d1e9a367333395c07537919258cb42cc3` |
| `sources/face-poseunits.bvh` | [Pose data](https://github.com/makehumancommunity/makehuman/blob/a8bc2d54ff0ac92e78ff71431b1023eda42bf482/makehuman/data/poseunits/face-poseunits.bvh) | `42a8e69692e30010371ee6993a6e5d3b468d35065559ec0953c936e31b8d903f` |

These are authoring data. Upper/lower eyelid poses are baked into a small native orbital mesh; the runtime does not import MakeHuman application code or add another skeleton controller. No commercial game character, texture or animation is included.
