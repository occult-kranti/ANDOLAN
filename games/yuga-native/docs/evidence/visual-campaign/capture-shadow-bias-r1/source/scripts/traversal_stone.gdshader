shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Original stone facade, measured in local metres. No displacement, texture
// reads, alpha, time dependence or fragment loops. The top remains landable.
uniform float deck_height : hint_range(1.0, 16.0) = 8.0;
uniform float deck_width : hint_range(2.0, 16.0) = 8.0;
varying vec3 local_position;
varying vec3 local_normal;

void vertex() {
	local_position = VERTEX;
	local_normal = NORMAL;
}

float soft_line(float distance_to_line, float width, float aa) {
	return 1.0 - smoothstep(max(0.0, width - aa), width + aa, distance_to_line);
}

void fragment() {
	float along = abs(local_normal.x) > 0.5 ? local_position.z : local_position.x;
	float height = local_position.y + deck_height * 0.5;
	vec2 wall = vec2(along, height);
	float footprint = max(fwidth(wall.x), fwidth(wall.y));
	float aa = max(footprint * 0.75, 0.002);
	// Large running-bond stones; narrow joints fade before becoming distant noise.
	vec2 slab_size = vec2(2.0, 0.85);
	float row = floor(height / slab_size.y);
	vec2 tiled = wall / slab_size + vec2(mod(row, 2.0) * 0.5, 0.0);
	vec2 edge = min(fract(tiled), 1.0 - fract(tiled)) * slab_size;
	float joint = soft_line(min(edge.x, edge.y), 0.025, aa);
	joint *= 1.0 - smoothstep(0.15, 0.42, footprint);
	float mineral = (fract(sin(dot(floor(tiled), vec2(12.9898, 78.233))) * 43758.5453) - 0.5) * 0.024;
	vec3 stone = vec3(0.48, 0.425, 0.32) * (1.0 + mineral);
	stone = mix(stone, stone * 0.78, joint);
	// Closed, shallow arch reliefs. The infill retains masonry so these never
	// resemble open doors or imply an unimplemented entrance through a solid wall.
	float bay_width = deck_width / 3.0;
	float bay = mod(along + deck_width * 0.5, bay_width) - bay_width * 0.5;
	float arch_top = deck_height * 0.64 + sqrt(max(0.0, 1.0 - bay * bay));
	float panel = (1.0 - smoothstep(0.84 - aa, 0.84 + aa, abs(bay)))
		* smoothstep(1.6 - aa, 1.6 + aa, height)
		* (1.0 - smoothstep(arch_top - aa, arch_top + aa, height));
	stone *= 1.0 - panel * 0.09;
	float frame = max(soft_line(abs(abs(bay) - 0.84), 0.055, aa),
		max(soft_line(abs(height - 1.6), 0.055, aa), soft_line(abs(height - arch_top), 0.055, aa)));
	stone = mix(stone, vec3(0.55, 0.46, 0.30), frame * panel * 0.55);
	float plinth = 1.0 - smoothstep(0.92 - aa, 1.08 + aa, height);
	float rim = smoothstep(deck_height - 0.72 - aa, deck_height - 0.55 + aa, height);
	stone = mix(stone, vec3(0.28, 0.26, 0.215), plinth);
	stone = mix(stone, vec3(0.57, 0.45, 0.27), rim);
	// A quiet, lighter top communicates an actual landing surface.
	float top = step(0.5, local_normal.y);
	ALBEDO = mix(stone, vec3(0.56, 0.52, 0.42), top);
	METALLIC = 0.0;
	ROUGHNESS = 0.84;
	SPECULAR = 0.22;
}
