shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
// Original bounded silk/energy ribbon. No screen texture, full-screen flash or TIME.
// Host updates phase only while simulation presentation is running, so pause freezes.
uniform vec4 tint : source_color = vec4(1.0,0.72,0.3,1.0);
uniform float opacity : hint_range(0.0,1.0) = 0.8;
uniform float phase = 0.0;
uniform float flow : hint_range(0.0,1.0) = 0.7;
uniform float luminous : hint_range(0.0,2.0) = 0.6;
uniform float core_strength : hint_range(0.0,1.0) = 0.0;
uniform bool reduced_motion = false;
void fragment() {
	float centre = max(0.0, 1.0 - abs(UV.y * 2.0 - 1.0));
	float edge = pow(centre, 0.55);
	float core = pow(centre, 8.0) * core_strength;
	float filament = 0.74 + 0.26 * sin(UV.x * 25.1327 - (reduced_motion ? 0.0 : phase * 5.0));
	float pulse = mix(1.0, filament, flow);
	// A fine ivory centre and coloured falloff preserve a crisp arrow at range.
	// No additive screen fill, texture reads, lights, random seed or global TIME.
	vec3 energy = mix(tint.rgb, vec3(1.0,0.95,0.80),core);
	ALBEDO = energy;
	EMISSION = energy * luminous * pulse;
	ALPHA = tint.a * opacity * edge * pulse * COLOR.a;
}
