shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

// Original two-tone bow-lane warning. Geometry owns the exact sweep and each
// lane's lifetime. Readiness comes from accepted simulation age, never TIME.
// Stable contrast survives reduced motion/effects and both bright/dark floors.
uniform vec4 tint : source_color = vec4(1.0,0.76,0.44,1.0);
uniform vec4 ink : source_color = vec4(0.045,0.065,0.11,1.0);
uniform float opacity : hint_range(0.0,1.0) = 0.95;
uniform float readiness : hint_range(0.0,1.0) = 0.0;

void fragment() {
	float aa = clamp(fwidth(UV.y),0.02,0.18);
	float edge = smoothstep(0.0,aa,UV.y) * (1.0-smoothstep(1.0-aa,1.0,UV.y));
	float core = smoothstep(0.22-aa,0.22+aa,UV.y) * (1.0-smoothstep(0.78-aa,0.78+aa,UV.y));
	// The complete committed lane is visible immediately. Readiness increases
	// the warm centre's emphasis; it never draws a false travelling projectile.
	vec3 prepared = mix(tint.rgb * 0.72,tint.rgb,readiness);
	ALBEDO = mix(ink.rgb,prepared,core);
	ALPHA = opacity * edge * COLOR.a;
}
