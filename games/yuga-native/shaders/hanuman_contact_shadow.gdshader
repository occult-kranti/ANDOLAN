shader_type spatial;
render_mode unshaded, shadows_disabled, depth_draw_never;

uniform float opacity : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec2 footprint = UV * 2.0 - vec2(1.0);
	float radius = length(footprint);
	float penumbra = 1.0 - smoothstep(0.12, 1.0, radius);
	ALBEDO = vec3(0.012, 0.011, 0.016);
	ALPHA = opacity * penumbra * penumbra;
}
