shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;

// A narrow two-tone annulus gives the exact Guardian edge contrast on both
// pale stone and dark ground. Its mesh extends only inward from the true radius.
// No emission, depth-test bypass, screen read or autonomous animation.
uniform vec4 tint : source_color = vec4(0.93,0.78,0.46,1.0);
uniform vec4 ink : source_color = vec4(0.055,0.095,0.13,1.0);
uniform float opacity : hint_range(0.0,1.0) = 0.92;

void fragment() {
	float aa = clamp(fwidth(UV.y),0.015,0.18);
	float coverage = smoothstep(0.0,aa,UV.y) * (1.0-smoothstep(1.0-aa,1.0,UV.y));
	// UV.y grows radially outward. The warm outer line identifies the true
	// edge; the dark inner stroke prevents its loss against bright paving.
	float edge = smoothstep(0.57-aa*0.5,0.64+aa*0.5,UV.y);
	ALBEDO = mix(ink.rgb,tint.rgb,edge);
	ALPHA = opacity * coverage * mix(ink.a,tint.a,edge) * COLOR.a;
}
