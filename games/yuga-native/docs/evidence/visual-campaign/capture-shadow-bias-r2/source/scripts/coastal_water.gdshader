shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

uniform vec4 deep_color : source_color = vec4(0.025, 0.18, 0.20, 1.0);
uniform vec4 crest_color : source_color = vec4(0.10, 0.31, 0.32, 1.0);
varying vec3 water_position;

void vertex() {
	float phase_x = VERTEX.x * 0.36 + TIME * 0.46;
	float phase_z = VERTEX.z * 0.29 - TIME * 0.33;
	VERTEX.y += sin(phase_x) * 0.035 + sin(phase_z) * 0.04;
	NORMAL = normalize(vec3(-cos(phase_x) * 0.0126, 1.0, -cos(phase_z) * 0.0116));
	water_position = VERTEX;
}

void fragment() {
	float ripples = sin(water_position.x * 1.6 + water_position.z * 0.7 + TIME * 0.5);
	ripples *= sin(water_position.z * 1.2 - TIME * 0.35);
	ALBEDO = mix(deep_color.rgb, crest_color.rgb, ripples * 0.18 + 0.32);
	METALLIC = 0.35;
	ROUGHNESS = 0.23 + ripples * 0.04;
	SPECULAR = 0.65;
}
