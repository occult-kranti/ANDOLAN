shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Original Sangam finish. Existing credited maps remain the material inputs;
// quiet mineral variation preserves architectural scale without a cloth-like
// macro albedo pattern. No vertex displacement or gameplay-dependent effect.
uniform sampler2D source_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D source_normal : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D source_roughness : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 mineral_tint : source_color = vec4(0.73, 0.53, 0.35, 1.0);
uniform vec4 roughness_channel = vec4(1.0, 0.0, 0.0, 0.0);
uniform float minimum_roughness : hint_range(0.0, 1.0) = 0.78;
uniform float normal_strength : hint_range(0.0, 1.0) = 0.18;

float mineral_hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float mineral_noise(vec2 p) {
	vec2 cell = floor(p);
	vec2 local = fract(p);
	vec2 blend = local * local * (3.0 - 2.0 * local);
	return mix(mix(mineral_hash(cell), mineral_hash(cell + vec2(1.0, 0.0)), blend.x),
		mix(mineral_hash(cell + vec2(0.0, 1.0)), mineral_hash(cell + vec2(1.0, 1.0)), blend.x), blend.y);
}

void fragment() {
	vec3 source = texture(source_albedo, UV).rgb;
	float luminance = dot(source, vec3(0.2126, 0.7152, 0.0722));
	float mineral_variation = clamp((luminance - 0.35) * 0.10, -0.035, 0.035);
	// Authored UVs are projected in world metres divided by 2.4, with vertical
	// wall height on V. These quiet courses therefore retain a human scale.
	vec2 metres = UV * 2.4;
	vec2 block_size = vec2(1.2, 0.52);
	float row = floor(metres.y / block_size.y);
	vec2 staggered = vec2(metres.x + mod(row, 2.0) * 0.6, metres.y);
	vec2 block = floor(staggered / block_size);
	vec2 local = mod(staggered, block_size);
	vec2 edge = min(local, block_size - local);
	float pixel_metres = max(fwidth(metres.x), fwidth(metres.y));
	float detail_visibility = 1.0 - smoothstep(0.035, 0.13, pixel_metres);
	float antialias = max(0.001, pixel_metres * 0.65);
	float mortar = (1.0 - smoothstep(0.006 - antialias, 0.006 + antialias, min(edge.x, edge.y))) * detail_visibility;
	float block_variation = (mineral_hash(block) - 0.5) * 0.07;
	float grain_visibility = 1.0 - smoothstep(0.4, 1.5, pixel_metres * 110.0);
	float grain = (mineral_noise(metres * 110.0) - 0.5) * 0.035 * grain_visibility;
	ALBEDO = mineral_tint.rgb * (1.0 + mineral_variation + block_variation + grain) * (1.0 - mortar * 0.20);
	ROUGHNESS = max(minimum_roughness, dot(texture(source_roughness, UV), roughness_channel));
	METALLIC = 0.0;
	SPECULAR = 0.35;
	vec2 toward_edge = mix(vec2(1.0), vec2(-1.0), step(block_size * 0.5, local));
	vec2 bevel = -toward_edge * (vec2(1.0) - smoothstep(vec2(0.006), vec2(0.024), edge)) * 0.12 * detail_visibility;
	vec2 source_slope = (texture(source_normal, UV).rg * 2.0 - 1.0) * normal_strength;
	NORMAL_MAP = normalize(vec3(source_slope + bevel, 1.0)) * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
}
