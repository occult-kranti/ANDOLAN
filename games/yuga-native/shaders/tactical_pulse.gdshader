shader_type spatial;
render_mode unshaded, blend_add, cull_disabled, depth_draw_never;
uniform float age=0.0;
uniform float duration=0.65;
uniform vec4 tint:source_color=vec4(0.88,0.66,0.30,1.0);
void fragment(){
	float progress=clamp(age/max(duration,0.001),0.0,1.0);
	float envelope=(1.0-smoothstep(0.05,1.0,progress))*smoothstep(0.0,0.07,progress);
	ALBEDO=tint.rgb*0.32;
	ALPHA=envelope*0.32;
}
