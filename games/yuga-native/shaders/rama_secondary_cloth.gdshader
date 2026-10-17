shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled, diffuse_burley, specular_schlick_ggx;

// Authored white vertex RGB + alpha are semantic motion weights, not opacity.
// No TIME, extra skeleton modifier, screen texture, transient light or particles.
// Forward+ supplies an already-skinned local vertex. Static authored alpha
// identifies the same vertices through every pose; offset is in hero local space.
uniform vec4 base_color : source_color = vec4(1.0);
uniform sampler2D base_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D rough_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D metal_texture : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool use_base_texture = false;
uniform bool use_rough_texture = false;
uniform bool use_metal_texture = false;
uniform bool use_normal_texture = false;
uniform float roughness_value : hint_range(0.0, 1.0) = 0.5;
uniform float metallic_value : hint_range(0.0, 1.0) = 0.0;
uniform float normal_strength : hint_range(-16.0, 16.0) = 1.0;
uniform float specular_value : hint_range(0.0, 1.0) = 0.5;
uniform vec4 rough_channel = vec4(1.0, 0.0, 0.0, 0.0);
uniform vec4 metal_channel = vec4(1.0, 0.0, 0.0, 0.0);
uniform vec3 secondary_offset = vec3(0.0);

void vertex() {
	// The same continuous field is authored on mantle and its metallic hem.
	// Fixed edges, chest, belt, fitted panels, scalp and brows have exactly zero.
	float weight = clamp(COLOR.a, 0.0, 1.0);
	VERTEX += secondary_offset * weight * weight;
}

void fragment() {
	vec4 texel = use_base_texture ? texture(base_texture, UV) : vec4(1.0);
	ALBEDO = base_color.rgb * texel.rgb;
	ROUGHNESS = clamp(roughness_value * (use_rough_texture ? dot(texture(rough_texture, UV), rough_channel) : 1.0), 0.0, 1.0);
	METALLIC = clamp(metallic_value * (use_metal_texture ? dot(texture(metal_texture, UV), metal_channel) : 1.0), 0.0, 1.0);
	SPECULAR = specular_value;
	if (use_normal_texture) {
		NORMAL_MAP = texture(normal_texture, UV).rgb;
		NORMAL_MAP_DEPTH = normal_strength;
	}
	// Opaque by design: COLOR.a is a mask, never surface transparency.
}
