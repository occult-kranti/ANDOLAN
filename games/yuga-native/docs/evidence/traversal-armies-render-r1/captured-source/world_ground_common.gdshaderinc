// Original shared Confluence paving. All coordinates are world metres, X/Z.
// Ground and shallow-water borders use the exact same opaque surface function.
uniform float arrival_court_z = 69.0;
uniform int lane_count : hint_range(0, 8) = 0;
uniform vec4 lane_segments[8];
uniform int rotation_count : hint_range(0, 20) = 0;
uniform vec4 rotation_segments[20];

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
	float variation = (stone_random(cell) - 0.5) * 0.045;
	float weathering = sin(p.x * 0.16 + p.y * 0.11) * sin(p.y * 0.21) * 0.008;
	vec3 stone = tint * (1.0 + variation + weathering);
	return mix(stone, stone * 0.78, grout);
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
	vec3 paving = paving_stones(p, vec2(1.65, 1.10), vec3(0.265, 0.280, 0.266));
	vec3 avenue = paving_stones(p, vec2(2.40, 1.20), vec3(0.218, 0.238, 0.229));
	// A single union mask resolves intersections without overlapping geometry.
	paving = mix(paving, avenue, max(lane, rotation * 0.55));
	// Quiet arrival-court inlays are descriptive scenery, never combat markers.
	float court_radius = min(length(p - vec2(0.0, arrival_court_z)), length(p - vec2(0.0, -arrival_court_z)));
	float court = 1.0 - smoothstep(7.0, 7.15, court_radius);
	vec3 court_stone = paving_stones(p, vec2(2.2, 2.2), vec3(0.285, 0.282, 0.252));
	paving = mix(paving, court_stone, court * 0.75);
	float ring_distance = min(abs(court_radius - 6.35), abs(court_radius - 4.8));
	float ring = 1.0 - smoothstep(0.018 - aa, 0.047 + aa, ring_distance);
	ring *= 1.0 - smoothstep(0.20, 0.65, aa);
	return mix(paving, vec3(0.32, 0.285, 0.19), ring * 0.4);
}
