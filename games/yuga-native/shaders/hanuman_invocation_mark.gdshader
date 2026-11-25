shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

uniform sampler2D painted_masks : filter_linear, repeat_disable;
uniform vec2 atlas_cell = vec2(0.0);
uniform vec4 tone : source_color = vec4(1.0, 0.72, 0.38, 1.0);
uniform vec4 glint : source_color = vec4(1.0, 0.94, 0.76, 1.0);
uniform float opacity = 0.68;

varying vec2 mark_uv;

void vertex() {
	mark_uv = vec2(VERTEX.x * 0.5 + 0.5, 0.5 - VERTEX.z * 0.5);
}

void fragment() {
	vec2 cell_uv = clamp(mark_uv, vec2(0.004), vec2(0.996));
	vec3 paint = texture(painted_masks, (atlas_cell + cell_uv) / vec2(3.0, 5.0)).rgb;
	float outer_wash = paint.r * 0.32 + paint.b * 0.34;
	float line = paint.g * 0.86;
	vec3 dark_tone = tone.rgb * 0.43;
	ALBEDO = mix(dark_tone, mix(tone.rgb, glint.rgb, 0.34), paint.g);
	ALPHA = min(1.0, outer_wash + line) * opacity * tone.a;
}
