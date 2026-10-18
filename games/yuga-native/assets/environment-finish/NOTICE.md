# Original Confluence and courtyard surface finish

The G1 masonry shader and world-space mineral treatment are original project
work created for YUGA. They use only the project's existing imported Confluence
architecture textures; no external texture, model or commercial game asset is
included. The shader does not modify those source maps or mesh buffers.

`scripts/environment_surface_finish.gd` binds a bounded set of explicitly named
opaque architecture materials below `CityArt` or `AuthoredLankaCourtyard`. It
preserves source UV transforms, albedo and normal maps and transports the
courtyard's linear roughness/metallic maps using their declared channel masks.
Original mineral color/roughness variation, shallow double-line/frieze shading
on selected vertical stone and a warm-window day/night emission treatment are
procedural. The frieze is a bounded tangent-normal addition over the existing
normal map; it creates no displaced silhouette or opening. Shared source
materials are not mutated. Other material features that the finish cannot
transport are refused. No geometry, collider, gameplay marker or light is added.

Actual day/night material and combat-visibility review is required before visual
acceptance. Software-renderer resource checks do not establish GPU performance.
