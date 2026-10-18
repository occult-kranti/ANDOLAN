shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://scripts/world_ground_common.gdshaderinc"

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	ALBEDO = world_paving(world_position.xz);
	METALLIC = 0.0;
	ROUGHNESS = world_paving_roughness(world_position.xz);
	SPECULAR = 0.30;
}
