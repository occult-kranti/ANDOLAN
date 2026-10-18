shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://scripts/world_ground_common.gdshaderinc"

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
		vec3 paving = world_paving(p);
		// Desaturated moss water, with a damp stone transition instead of a
		// hard green carpet. Every opaque border fragment matches the floor.
		vec3 wet_stone = paving * vec3(0.68, 0.76, 0.68);
		vec3 pool_color = mix(wet_stone, ALBEDO * 0.78, smoothstep(0.18, 0.85, pool));
		ALBEDO = mix(paving, pool_color, pool);
		SPECULAR = mix(0.30, 0.25, pool);
		ROUGHNESS = mix(world_paving_roughness(p), ROUGHNESS, pool);
	}
}
