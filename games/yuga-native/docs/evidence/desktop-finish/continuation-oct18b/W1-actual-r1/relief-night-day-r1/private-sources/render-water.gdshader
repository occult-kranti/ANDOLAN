shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

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
	return 0.84 + wear * 0.055;
}


// Three-millimetre rounded stone bevels, expressed only as a lighting slope.
// Position, silhouette and physical support remain the original flat plane.
// Screen derivatives widen the transition and fade relief before it aliases.
vec2 paving_stone_slope(vec2 p, vec2 slab_size) {
	float row = floor(p.y / slab_size.y);
	vec2 tiled = vec2(p.x / slab_size.x + mod(row, 2.0) * 0.5, p.y / slab_size.y);
	vec2 inside = fract(tiled);
	vec2 edge = min(inside, 1.0 - inside) * slab_size;
	float footprint = max(fwidth(p.x), fwidth(p.y));
	float visibility = 1.0 - smoothstep(0.025, 0.10, footprint);
	float width = max(0.038, footprint * 1.5);
	vec2 t = clamp((edge - vec2(0.008)) / width, vec2(0.0), vec2(1.0));
	vec2 face = t * t * (3.0 - 2.0 * t);
	vec2 gradient = 6.0 * t * (1.0 - t) / width;
	// The product produces a rounded two-axis corner, with no min-edge cusp.
	vec2 sign_to_center = sign(vec2(0.5) - inside);
	return 0.003 * visibility * gradient * face.yx * sign_to_center;
}

vec3 paving_lit_normal(vec3 normal_in_view, mat4 inverse_view,
		mat4 view, vec2 slope) {
	vec3 world_normal = normalize((inverse_view * vec4(normal_in_view, 0.0)).xyz);
	float upper_surface = smoothstep(0.65, 0.95, world_normal.y);
	vec3 relieved = normalize(world_normal + vec3(-slope.x, 0.0, -slope.y) * upper_surface);
	return normalize((view * vec4(relieved, 0.0)).xyz);
}

void sample_world_paving(vec2 p, out vec3 color, out vec2 slope) {
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
	// A single union mask resolves intersections without overlapping geometry.
	float avenue_mix = max(lane, rotation * 0.55);
	paving = mix(paving, avenue, avenue_mix);
	slope = mix(paving_stone_slope(p, vec2(1.65, 1.10)),
		paving_stone_slope(p, vec2(2.40, 1.20)), avenue_mix);
	// Quiet arrival-court inlays are descriptive scenery, never combat markers.
	float court_radius = min(length(p - vec2(0.0, arrival_court_z)), length(p - vec2(0.0, -arrival_court_z)));
	float court = 1.0 - smoothstep(7.0, 7.15, court_radius);
	vec3 court_stone = paving_stones(p, vec2(2.2, 2.2), vec3(0.265, 0.239, 0.185));
	paving = mix(paving, court_stone, court * 0.75);
	slope = mix(slope, paving_stone_slope(p, vec2(2.2, 2.2)), court * 0.75);
	float ring_distance = min(abs(court_radius - 6.35), abs(court_radius - 4.8));
	float ring = 1.0 - smoothstep(0.018 - aa, 0.047 + aa, ring_distance);
	ring *= 1.0 - smoothstep(0.20, 0.65, aa);
	color = mix(paving, vec3(0.32, 0.285, 0.19), ring * 0.4);
}

// Callers needing color only retain the same function and exact color path.
vec3 world_paving(vec2 p) {
	vec3 color;
	vec2 unused_slope;
	sample_world_paving(p, color, unused_slope);
	return color;
}


// Original Confluence water, developed from this project's production_water.
// Opaque dielectric: no alpha sorting, refraction, screen/depth reads or physics
// displacement. World-space waves stay continuous across adjacent flat meshes.
uniform vec4 deep_color : source_color = vec4(0.075, 0.294, 0.376, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.235, 0.549, 0.576, 1.0);
uniform float ripple_strength : hint_range(0.0, 0.10) = 0.055;
uniform float base_roughness : hint_range(0.1, 0.7) = 0.23;
uniform float animation_speed : hint_range(0.0, 1.0) = 0.8;
uniform bool swamp_overlay = false;
uniform vec2 overlay_size = vec2(12.0, 12.0);
uniform vec2 overlay_center = vec2(0.0, 0.0);
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world_position.xz;
	float clock = TIME * animation_speed;
	float a = dot(p, vec2(0.72, 0.38)) - clock * 0.36;
	float b = dot(p, vec2(-1.55, 1.12)) + clock * 0.57;
	float c = dot(p, vec2(3.10, 2.34)) - clock * 0.71;
	// Suppress fine wave slope where it becomes smaller than screen pixels.
	float detail = 1.0 - smoothstep(0.5, 1.8, fwidth(c));
	vec2 slope = cos(a) * vec2(0.72, 0.38) * 0.035;
	slope += cos(b) * vec2(-1.55, 1.12) * 0.014;
	slope += cos(c) * vec2(3.10, 2.34) * 0.004 * detail;
	vec3 wave_normal = normalize(vec3(-slope.x, 1.0, -slope.y));
	vec3 base_world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	vec3 paving_color = vec3(0.0);
	if (swamp_overlay) {
		vec2 paving_slope;
		sample_world_paving(p, paving_color, paving_slope);
		// The dry border is the exact same stone lighting surface as the ground.
		vec3 stone_normal = paving_lit_normal(NORMAL, INV_VIEW_MATRIX, VIEW_MATRIX, paving_slope);
		base_world_normal = normalize((INV_VIEW_MATRIX * vec4(stone_normal, 0.0)).xyz);
	}
	float upper_surface = smoothstep(0.65, 0.95, base_world_normal.y);
	float pool = 1.0;
	if (swamp_overlay) {
		vec2 local = (p - overlay_center) / max(overlay_size * 0.5, vec2(0.001));
		// Elliptical, softly irregular wet ground; the rectangular mesh border
		// becomes identical paving. This never changes collision or water depth.
		float outline = length(local * vec2(1.0, 1.08));
		outline += sin(p.x * 0.85 + p.y * 0.37) * 0.045;
		outline += sin(p.y * 1.15 - p.x * 0.22) * 0.035;
		pool = 1.0 - smoothstep(0.64, 0.88, outline);
		// A dry walking strip preserves the shared cross-mid route's legibility.
		pool *= smoothstep(1.1, 2.25, abs(p.y));
	}
	vec3 blended_normal = normalize(mix(base_world_normal, wave_normal,
		upper_surface * clamp(ripple_strength / 0.055, 0.0, 1.8) * pool));
	NORMAL = normalize((VIEW_MATRIX * vec4(blended_normal, 0.0)).xyz);
	float current = sin(a * 0.38 + sin(b * 0.16)) * 0.5 + 0.5;
	// Long mineral-green currents break the single-color water sheet. They are
	// reflectance only: no false foam obstacle, shoreline depth or collision.
	float stream = sin(dot(p, vec2(0.09, 0.14)) + sin(dot(p, vec2(0.17, -0.08)))) * 0.5 + 0.5;
	ALBEDO = mix(deep_color.rgb, shallow_color.rgb, 0.10 + current * 0.27 + stream * 0.16);
	METALLIC = 0.0;
	SPECULAR = 0.25;
	ROUGHNESS = clamp(base_roughness + current * 0.05, 0.1, 0.8);
	if (swamp_overlay) {
		vec3 paving = paving_color;
		// A shallow wet film retains the paving bed instead of filling its
		// centre with opaque moss paint. Keep at least 82% of the damp-stone
		// colour signal; the original pool mask and dry border stay identical.
		vec3 wet_stone = paving * vec3(0.68, 0.76, 0.68);
		vec3 pool_color = mix(wet_stone, ALBEDO * 0.78, smoothstep(0.18, 0.85, pool) * 0.18);
		ALBEDO = mix(paving, pool_color, pool);
		SPECULAR = mix(0.30, 0.25, pool);
		ROUGHNESS = mix(world_paving_roughness(p), ROUGHNESS, pool);
	}
}
