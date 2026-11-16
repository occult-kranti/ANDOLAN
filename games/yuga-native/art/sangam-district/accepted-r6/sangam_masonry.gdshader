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

void fragment() {
	vec3 source = texture(source_albedo, UV).rgb;
	float luminance = dot(source, vec3(0.2126, 0.7152, 0.0722));
	float mineral_variation = clamp((luminance - 0.35) * 0.10, -0.035, 0.035);
	ALBEDO = mineral_tint.rgb * (1.0 + mineral_variation);
	ROUGHNESS = max(minimum_roughness, dot(texture(source_roughness, UV), roughness_channel));
	METALLIC = 0.0;
	SPECULAR = 0.35;
	NORMAL_MAP = texture(source_normal, UV).rgb;
	NORMAL_MAP_DEPTH = normal_strength;
}
