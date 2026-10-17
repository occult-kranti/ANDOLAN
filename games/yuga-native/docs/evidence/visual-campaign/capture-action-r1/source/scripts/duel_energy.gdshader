shader_type spatial;
render_mode unshaded, cull_disabled, blend_add, depth_draw_never;

// Original film VFX. No TIME: every visible property is sampled by the director.
uniform vec4 tint : source_color = vec4(1.0, 0.68, 0.24, 1.0);
uniform float opacity : hint_range(0.0, 1.0) = 0.8;
uniform float energy : hint_range(0.0, 3.0) = 1.1;
uniform int pattern : hint_range(0, 5) = 4;
uniform float progress : hint_range(0.0, 1.0) = 0.0;

void fragment() {
	vec2 q = UV * 2.0 - 1.0;
	float radius = length(q);
	float mask = 1.0;
	if (pattern == 0) {
		float outer = 1.0 - smoothstep(0.012, 0.042, abs(radius - 0.79));
		float inner = 1.0 - smoothstep(0.008, 0.028, abs(radius - 0.57));
		float angle = atan(q.y, q.x);
		float petals = 1.0 - smoothstep(0.015, 0.045, abs(radius - 0.38 - sin(angle * 6.0) * 0.08));
		mask = max(outer, max(inner * 0.5, petals * 0.42));
	} else if (pattern == 1) {
		float border = 1.0 - smoothstep(0.025, 0.075, abs(abs(q.x) - 0.87));
		float mark = abs(fract(UV.y * 4.0 - abs(q.x) * 0.28) - 0.5);
		float chevron = 1.0 - smoothstep(0.022, 0.052, mark);
		mask = max(border, chevron * 0.45) * smoothstep(0.0, 0.08, UV.y) * smoothstep(0.0, 0.08, 1.0 - UV.y);
	} else if (pattern == 2) {
		vec2 cell = abs(mod(q * 6.0, vec2(1.732, 3.0)) - vec2(0.866, 1.5));
		float hex = max(dot(cell, vec2(0.866, 0.5)), cell.y);
		float grid = 1.0 - smoothstep(0.025, 0.09, abs(hex - 0.84));
		float rim = 1.0 - smoothstep(0.018, 0.06, abs(radius - 0.87));
		mask = max(rim, 0.10 + grid * 0.28) * (1.0 - smoothstep(0.89, 0.96, radius));
	} else if (pattern == 3) {
		mask = pow(max(0.0, 1.0 - abs(q.x)), 1.8) * smoothstep(0.0, 0.16, UV.y) * smoothstep(0.0, 0.16, 1.0 - UV.y);
	} else if (pattern == 4) {
		float rim = pow(1.0 - abs(dot(normalize(NORMAL), normalize(VIEW))), 1.5);
		mask = 0.25 + rim * 0.75;
	} else if (pattern == 5) {
		mask = (1.0 - smoothstep(0.25, 1.0, radius)) * 0.35;
	}
	// Slow 8% breathing is contained within a cue. No white fullscreen flash.
	float breathing = 0.96 + sin(progress * 3.14159265) * 0.04;
	ALBEDO = tint.rgb * energy;
	ALPHA = clamp(mask * opacity * breathing, 0.0, 0.95);
}
