shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_disabled;

// Original world-metre mineral wash over the original imported UV textures.
// No mesh displacement, transparency, fake apertures or screen/depth reads.
uniform vec4 base_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_texture : filter_linear_mipmap, repeat_enable;
uniform sampler2D metallic_texture : filter_linear_mipmap, repeat_enable;
// Original linear data maps. Implicit texture LOD supplies distance filtering.
uniform sampler2D fine_mineral_signal : filter_linear_mipmap, repeat_enable;
uniform sampler2D frieze_height_gradient : filter_linear_mipmap, repeat_enable;
const float FRIEZE_PERIOD_M = 0.4487989505128276;
uniform bool has_albedo = false;
uniform bool has_normal = false;
uniform bool has_roughness = false;
uniform bool has_metallic = false;
uniform vec4 roughness_channel = vec4(0.0, 1.0, 0.0, 0.0);
uniform vec4 metallic_channel = vec4(0.0, 0.0, 1.0, 0.0);
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform vec3 surface_tint = vec3(1.0);
uniform vec3 mineral_tint = vec3(0.72, 0.81, 0.75);
uniform float weather_amount : hint_range(0.0, 0.3) = 0.18;
uniform float carving_amount : hint_range(0.0, 1.0) = 0.0;
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
	float fine = texture(fine_mineral_signal,vec2(fine_phase / 6.283185307179586,0.5)).r;
	float mineral = broad * 0.72 + fine * 0.28;
	float plinth = 1.0 - smoothstep(0.18, 2.0, p.y);
	float age = clamp((mineral * 0.70 + plinth * 0.30) * weather_amount, 0.0, 0.3);
	ALBEDO = original * surface_tint * mix(vec3(1.0), mineral_tint, age);
	float roughness = base_roughness;
	if (has_roughness) { roughness *= dot(texture(roughness_texture, uv), roughness_channel); }
	ROUGHNESS = clamp(roughness + age * 0.26, 0.22, 0.96);
	METALLIC = base_metallic;
	if (has_metallic) { METALLIC *= dot(texture(metallic_texture, uv), metallic_channel); }
	SPECULAR = base_specular;
	vec3 mapped_normal = vec3(0.5, 0.5, 1.0);
	if (has_normal) { mapped_normal = texture(normal_texture, uv).rgb; }
	if (carving_amount > 0.0) {
		// Same periodic double lines and motif, baked from original G2 equations.
		// RGB = height mask / world-X(Z) gradient / world-Y gradient; linear data.
		vec3 world_normal = normalize((INV_VIEW_MATRIX * vec4(NORMAL,0.0)).xyz);
		float vertical = 1.0 - smoothstep(0.35,0.70,abs(world_normal.y));
		vec3 baked = texture(frieze_height_gradient,
			vec2((p.x+p.z)/FRIEZE_PERIOD_M,(p.y+0.10)/3.0)).rgb;
		float strength = vertical * carving_amount;
		float cut = baked.r * strength;
		ALBEDO *= 1.0 - cut * 0.18;
		ROUGHNESS = clamp(ROUGHNESS + cut * 0.04,0.22,0.96);
		// Analytic world-space gradient was baked offline. No explicit screen
		// derivatives; unchanged maximum authored height is 1.2 mm, no displacement.
		vec2 baked_gradient = (baked.gb * 255.0 - vec2(128.0)) * (128.0/127.0);
		vec3 gradient_world = -vec3(baked_gradient.x,baked_gradient.y,baked_gradient.x) * (0.0012*strength);
		vec3 tangent_world = normalize((INV_VIEW_MATRIX * vec4(TANGENT,0.0)).xyz);
		vec3 binormal_world = normalize((INV_VIEW_MATRIX * vec4(BINORMAL,0.0)).xyz);
		vec2 slope = clamp(vec2(dot(gradient_world,tangent_world),dot(gradient_world,binormal_world)),vec2(-0.12),vec2(0.12));
		mapped_normal.xy = clamp(mapped_normal.xy - slope * 0.5,vec2(0.02),vec2(0.98));
	}
	NORMAL_MAP = mapped_normal;
	NORMAL_MAP_DEPTH = has_normal ? normal_depth : 1.0;
	if (window_surface) {
		// Sparse authored window surfaces, never whole-wall emission or new lamps.
		EMISSION = original * vec3(1.0, 0.70, 0.36) * mix(0.03, 0.78, night_blend);
	}
}
