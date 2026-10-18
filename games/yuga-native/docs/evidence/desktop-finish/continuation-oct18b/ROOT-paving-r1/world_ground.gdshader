shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

#include "res://scripts/world_ground_common.gdshaderinc"

varying vec3 world_position;

void vertex() {
	world_position = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec3 stone_color;
	vec2 stone_slope;
	sample_world_paving(world_position.xz, stone_color, stone_slope);
	ALBEDO = stone_color;
	NORMAL = paving_lit_normal(NORMAL, INV_VIEW_MATRIX, VIEW_MATRIX, stone_slope);
	METALLIC = 0.0;
	ROUGHNESS = world_paving_roughness(world_position.xz);
	SPECULAR = 0.30;
}
