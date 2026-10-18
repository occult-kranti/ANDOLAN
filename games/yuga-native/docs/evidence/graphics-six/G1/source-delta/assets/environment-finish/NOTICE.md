# Original Confluence surface finish

The G1 masonry shader and world-space mineral treatment are original project
work created for YUGA. They use only the project's existing imported Confluence
architecture textures; no external texture, model or commercial game asset is
included. The shader does not modify those source maps or mesh buffers.

`scripts/environment_surface_finish.gd` binds a bounded set of explicitly named
opaque architecture materials below `CityArt`. It preserves source UV transforms,
albedo and normal maps, roughness, metalness and specular settings. Small original
mineral color/roughness variation and a warm-window day/night emission treatment
are procedural. Shared source materials are not mutated. Other material features
that the finish cannot transport are refused. No geometry, collider, gameplay
marker or light is added.

Actual day/night material and combat-visibility review is required before visual
acceptance. Software-renderer resource checks do not establish GPU performance.
