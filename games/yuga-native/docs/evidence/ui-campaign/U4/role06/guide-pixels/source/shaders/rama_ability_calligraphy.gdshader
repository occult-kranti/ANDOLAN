shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

// Original woven-light strokes. Only the effect owner's paused simulation clock
// drives the fine travelling strand; no TIME, scene reads, particles or lights.
// The warning boundary uses the separate, unchanged rama_ribbon shader.
uniform vec4 tint : source_color = vec4(1.0,0.72,0.3,1.0);
uniform float opacity : hint_range(0.0,1.0) = 0.8;
uniform float phase = 0.0;
uniform float flow : hint_range(0.0,1.0) = 0.7;
uniform float luminous : hint_range(0.0,2.0) = 0.45;
uniform float core_strength : hint_range(0.0,1.0) = 0.36;
uniform bool reduced_motion = false;

void fragment() {
	float across = abs(UV.y * 2.0 - 1.0);
	float aa = max(fwidth(across),0.018);
	float body = 1.0 - smoothstep(0.46,1.0,across);
	float core = 1.0 - smoothstep(0.08-aa,0.17+aa,across);
	float hairline = 1.0 - smoothstep(0.035,0.035+aa,abs(across-0.68));
	float head = smoothstep(0.0,0.04,UV.x) * (1.0-smoothstep(0.90,1.0,UV.x));
	float clock = reduced_motion ? 0.0 : phase * 0.40;
	float travelling = 0.83 + 0.17 * cos((UV.x-clock)*18.84956);
	float pulse = mix(1.0,travelling,flow);
	float profile = max(body,hairline*0.28);
	// Saturated edges and a narrow warm core keep bloom from filling the stroke.
	vec3 ink = mix(tint.rgb*0.80,vec3(1.0,0.94,0.78),core*core_strength);
	ALBEDO = ink;
	EMISSION = ink * luminous * pulse * mix(0.40,1.0,core);
	ALPHA = tint.a * opacity * profile * head * pulse * COLOR.a;
}
