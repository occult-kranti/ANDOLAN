// Original shared Confluence paving. All coordinates are world metres, X/Z.
// Ground and shallow-water borders use the exact same opaque surface function.
uniform float arrival_court_z = 69.0;
uniform int lane_count : hint_range(0, 8) = 0;
uniform vec4 lane_segments[8];
uniform int rotation_count : hint_range(0, 20) = 0;
uniform vec4 rotation_segments[20];
// The composed Sangam district selects this profile for both paving and the
// opaque dry edge of shallow water. Legacy scenes retain their exact palette.
uniform bool sangam_paving = false;

float segment_distance(vec2 p, vec4 segment) {
	vec2 a = segment.xy;
	vec2 v = segment.zw - a;
	float t = clamp(dot(p - a, v) / max(dot(v, v), 0.0001), 0.0, 1.0);
	return length(p - a - v * t);
}

float stone_random(vec2 cell) {
	return fract(sin(dot(cell, vec2(12.9898, 78.233))) * 43758.5453);
}

vec3 paving_stones(vec2 p, vec2 slab_size, vec3 tint) {
	float row = floor(p.y / slab_size.y);
	vec2 tiled = vec2(p.x / slab_size.x + mod(row, 2.0) * 0.5, p.y / slab_size.y);
	vec2 cell = floor(tiled);
	vec2 edge = min(fract(tiled), 1.0 - fract(tiled)) * slab_size;
	float screen_step = max(fwidth(p.x), fwidth(p.y));
	float aa = max(screen_step * 0.65, 0.001);
	float grout = 1.0 - smoothstep(0.008 - aa, 0.018 + aa, min(edge.x, edge.y));
	// The narrow joints disappear gradually in the distance instead of aliasing.
	grout *= 1.0 - smoothstep(0.18, 0.55, screen_step);
	// Screen-space footprint in slab units: preserve cells >=5 pixels wide,
	// then converge subpixel cell colour to its original endpoint mean.
	// Use continuous world coordinates; staggered row boundaries must not
	// themselves inflate the derivative footprint.
	vec2 cell_footprint = fwidth(p) / slab_size;
	float cell_detail = 1.0 - smoothstep(0.20, 0.65, max(cell_footprint.x, cell_footprint.y));
	float variation = (stone_random(cell) - 0.5) * 0.18 * cell_detail;
	float weathering = sin(p.x * 0.16 + p.y * 0.11) * sin(p.y * 0.21) * 0.065;
	// Broad mineral layers add age without a noisy repeating high-frequency texture.
	weathering += sin(p.x * 0.43 - p.y * 0.27 + sin(p.y * 0.12)) * 0.028;
	vec3 mineral = mix(vec3(0.88, 0.96, 1.0), vec3(1.05, 0.99, 0.88), stone_random(cell + vec2(19.0, 7.0)));
	mineral = mix((vec3(0.88, 0.96, 1.0) + vec3(1.05, 0.99, 0.88)) * 0.5, mineral, cell_detail);
	vec3 stone = tint * mineral * (1.0 + variation + weathering);
	// Shallow, darker joints describe slab scale without drawing a distant grid.
	return mix(stone, stone * 0.55, grout);
}

float world_paving_roughness(vec2 p) {
	// Broad dry wear, not wet mirror lanes. Shared by opaque pool borders.
	float wear = sin(p.x * 0.23 + sin(p.y * 0.09)) * sin(p.y * 0.31);
	return (sangam_paving ? 0.77 : 0.84) + wear * 0.055;
}

// Shallow stone bevels change shading only, never physical floor elevation.
// Derivative fading removes the fine normal response before it aliases.
float sangam_stone_height(vec2 p) {
	float row = floor(p.y / 0.72);
	vec2 uv = vec2(p.x / 1.12 + mod(row, 2.0) * 0.5, p.y / 0.72);
	vec2 edge = min(fract(uv), 1.0 - fract(uv)) * vec2(1.12, 0.72);
	return smoothstep(0.006, 0.035, min(edge.x, edge.y)) * 0.008;
}

vec3 sangam_paving_normal(vec2 p) {
	float detail = 1.0 - smoothstep(0.025, 0.13, max(fwidth(p.x), fwidth(p.y)));
	float dx = (sangam_stone_height(p + vec2(0.006, 0.0)) - sangam_stone_height(p - vec2(0.006, 0.0))) / 0.012;
	float dz = (sangam_stone_height(p + vec2(0.0, 0.006)) - sangam_stone_height(p - vec2(0.0, 0.006))) / 0.012;
	return normalize(vec3(-dx * detail, 1.0, -dz * detail));
}

vec3 world_paving(vec2 p) {
	float lane_distance = 10000.0;
	for (int i = 0; i < 8; i++) {
		if (i >= lane_count) { break; }
		lane_distance = min(lane_distance, segment_distance(p, lane_segments[i]));
	}
	float rotation_distance = 10000.0;
	for (int i = 0; i < 20; i++) {
		if (i >= rotation_count) { break; }
		rotation_distance = min(rotation_distance, segment_distance(p, rotation_segments[i]));
	}
	float aa = max(max(fwidth(p.x), fwidth(p.y)), 0.01);
	float lane = 1.0 - smoothstep(3.80 - aa, 3.90 + aa, lane_distance);
	float rotation = 1.0 - smoothstep(1.33 - aa, 1.45 + aa, rotation_distance);
	vec3 paving = paving_stones(p, vec2(1.65, 1.10), vec3(0.205, 0.221, 0.207));
	vec3 avenue = paving_stones(p, vec2(2.40, 1.20), vec3(0.133, 0.165, 0.166));
	if (sangam_paving) {
		// Human-scale warm sandstone gives the indigo hero and cool arcades a
		// stable background. Broad wear stays quiet beneath hostile telegraphs.
		paving = paving_stones(p, vec2(1.12, 0.72), vec3(0.285, 0.221, 0.155));
		avenue = paving_stones(p, vec2(1.12, 0.72), vec3(0.205, 0.175, 0.145));
		float seam = 1.0 - smoothstep(0.025 - aa, 0.055 + aa, abs(lane_distance - 3.85));
		seam *= 1.0 - smoothstep(0.12, 0.5, aa);
		paving = mix(paving, vec3(0.36, 0.32, 0.24), seam * 0.65);
	}
	// A single union mask resolves intersections without overlapping geometry.
	paving = mix(paving, avenue, max(lane, rotation * 0.55));
	// Quiet arrival-court inlays are descriptive scenery, never combat markers.
	float court_radius = min(length(p - vec2(0.0, arrival_court_z)), length(p - vec2(0.0, -arrival_court_z)));
	float court = 1.0 - smoothstep(7.0, 7.15, court_radius);
	vec3 court_stone = paving_stones(p, vec2(2.2, 2.2), vec3(0.265, 0.239, 0.185));
	paving = mix(paving, court_stone, court * 0.75);
	float ring_distance = min(abs(court_radius - 6.35), abs(court_radius - 4.8));
	float ring = 1.0 - smoothstep(0.018 - aa, 0.047 + aa, ring_distance);
	ring *= 1.0 - smoothstep(0.20, 0.65, aa);
	return mix(paving, vec3(0.32, 0.285, 0.19), ring * 0.4);
}
