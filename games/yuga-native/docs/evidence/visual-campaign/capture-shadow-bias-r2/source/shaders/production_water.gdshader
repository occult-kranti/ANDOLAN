shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Opaque, dielectric coastal water. No scene/depth buffer reads or alpha sorting.
// The existing joined GLB water is sparsely tessellated, so all small waves are
// fragment normals. Vertex displacement would tilt a whole channel like a plank.
uniform vec4 deep_color : source_color = vec4(0.018, 0.105, 0.125, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.055, 0.19, 0.19, 1.0);
uniform float ripple_strength : hint_range(0.0, 0.15) = 0.055;
uniform float animation_speed : hint_range(0.0, 1.0) = 0.65;
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
	vec2 slope = cos(a) * vec2(0.72, 0.38) * 0.035;
	slope += cos(b) * vec2(-1.55, 1.12) * 0.014;
	// Fade subpixel ripples instead of producing a sparkling horizon.
	float detail = 1.0 - smoothstep(0.5, 1.8, fwidth(c));
	slope += cos(c) * vec2(3.10, 2.34) * 0.004 * detail;
	vec3 wave_normal = normalize(vec3(-slope.x, 1.0, -slope.y));
	// Preserve imported normals on the channel's vertical sides.
	vec3 base_world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	float upper_surface = smoothstep(0.65, 0.95, base_world_normal.y);
	vec3 blended_normal = normalize(mix(base_world_normal, wave_normal,
		upper_surface * clamp(ripple_strength / 0.055, 0.0, 1.8)));
	NORMAL = normalize((VIEW_MATRIX * vec4(blended_normal, 0.0)).xyz);
	float current = sin(a * 0.38 + sin(b * 0.16)) * 0.5 + 0.5;
	ALBEDO = mix(deep_color.rgb, shallow_color.rgb, current * 0.22);
	METALLIC = 0.0;
	// Godot's specular 0.25 gives approximately water's 2% normal reflectance.
	SPECULAR = 0.25;
	ROUGHNESS = 0.24 + current * 0.06;
}
