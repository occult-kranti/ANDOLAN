shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

uniform sampler2D time_field : filter_nearest, repeat_disable;
uniform float clock_s = 0.0;
uniform float tile_count = 3.0;

varying vec2 ground_local;
varying vec2 ground_world;
varying vec4 tile_slot;
varying vec3 strand_color;

void vertex() {
	ground_local = VERTEX.xz;
	ground_world = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xz;
	tile_slot = INSTANCE_CUSTOM;
	strand_color = COLOR.rgb;
}

void fragment() {
	float radial = length(ground_local);
	float side_distance = ground_local.y - (2.0 * tile_slot.z - 1.0) * radial;
	bool sector = tile_slot.y > 0.5;
	if (radial >= 1.0 || (sector && side_distance < 0.0)) {
		discard;
	}

	// Stay inside the slot even at the left/right edge of a bounded quad.
	vec2 cell = clamp(ground_local * 0.5 + 0.5, vec2(0.0001), vec2(0.9999));
	vec2 stamp = texture(time_field, vec2(cell.x, (tile_slot.x + cell.y) / tile_count)).rg;
	float age = clock_s - stamp.x;
	if (stamp.y <= 0.0 || age < 0.0 || age >= stamp.y) {
		discard;
	}
	float time_fraction = age / stamp.y;
	float falloff = 1.0 - smoothstep(0.1, 1.0, time_fraction);
	float appear = smoothstep(0.0, sector ? 0.10 : 0.035, age);
	float edge = 1.0 - smoothstep(0.91, 1.0, radial);
	if (sector) {
		edge *= smoothstep(0.0, 0.08, side_distance);
	}
	// A newly reached cell retains a brighter edge before settling into
	// a muted wash. Irregular low contrast grain preserves the paving.
	float drift = sin(ground_world.x * 1.73 - ground_world.y * 3.08);
	float grain = 0.93 + 0.07 * sin(ground_world.x * 4.16 + ground_world.y * 2.47 + drift);
	float front = 1.0 - smoothstep(0.04, 0.25, abs(time_fraction - 0.13));
	vec3 cooler_body = strand_color * vec3(0.94, 0.74, 0.58);
	vec3 crest = mix(cooler_body, vec3(1.0, 0.73, 0.41), front * 0.65);
	ALBEDO = crest * grain;
	ALPHA = (sector ? 0.27 : 0.33) * appear * falloff * edge * grain * (0.47 + 0.53 * front);
}
