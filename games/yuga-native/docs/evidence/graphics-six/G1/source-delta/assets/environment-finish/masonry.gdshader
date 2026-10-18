shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_disabled;

// Original world-metre mineral wash over the original imported UV textures.
// No mesh displacement, transparency, fake apertures or screen/depth reads.
uniform vec4 base_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform bool has_albedo = false;
uniform bool has_normal = false;
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform vec3 surface_tint = vec3(1.0);
uniform vec3 mineral_tint = vec3(0.72, 0.81, 0.75);
uniform float weather_amount : hint_range(0.0, 0.3) = 0.18;
uniform float base_roughness = 0.8;
uniform float base_metallic = 0.0;
uniform float base_specular = 0.5;
uniform float normal_depth = 1.0;
uniform bool window_surface = false;
uniform float night_blend : hint_range(0.0, 1.0) = 0.0;
varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 uv = UV * uv_scale.xy + uv_offset.xy;
	vec3 original = base_color.rgb;
	if (has_albedo) { original *= texture(albedo_texture, uv).rgb; }
	vec3 p = world_position;
	// Broad forms survive ordinary play distance. A second mineral layer is
	// deliberately filtered away before it can turn into crawling pixel noise.
	float broad = sin(dot(p, vec3(0.39, 0.23, 0.31)) + sin(p.y * 0.7)) * 0.5 + 0.5;
	float fine_phase = dot(p, vec3(3.1, 5.7, 2.9));
	float detail = 1.0 - smoothstep(0.35, 1.2, fwidth(fine_phase));
	float mineral = broad * 0.72 + (sin(fine_phase) * 0.5 + 0.5) * 0.28 * detail;
	float plinth = 1.0 - smoothstep(0.18, 2.0, p.y);
	float age = clamp((mineral * 0.70 + plinth * 0.30) * weather_amount, 0.0, 0.3);
	ALBEDO = original * surface_tint * mix(vec3(1.0), mineral_tint, age);
	ROUGHNESS = clamp(base_roughness + age * 0.26, 0.22, 0.96);
	METALLIC = base_metallic;
	SPECULAR = base_specular;
	if (has_normal) {
		NORMAL_MAP = texture(normal_texture, uv).rgb;
		NORMAL_MAP_DEPTH = normal_depth;
	}
	if (window_surface) {
		// Sparse authored window surfaces, never whole-wall emission or new lamps.
		EMISSION = original * vec3(1.0, 0.70, 0.36) * mix(0.03, 0.78, night_blend);
	}
}
