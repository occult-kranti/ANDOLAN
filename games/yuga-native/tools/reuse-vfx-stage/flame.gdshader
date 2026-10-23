shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never, blend_mix;
// Reuses the original Rama ribbon's explicit paused-clock/unshaded alpha model.
// Original teardrop profile; no global TIME, screen reads, texture download or noise asset.
uniform float phase = 0.0;
uniform float intensity : hint_range(0.0,1.0) = 1.0;
uniform bool reduced_motion = false;
void vertex() {
    float t = 1.0-UV.y;
    float sway = reduced_motion ? 0.0 : sin(phase * 4.2 + t * 2.0) * 0.006;
    VERTEX.x += sway * t * t;
}
void fragment() {
    float t = clamp(1.0-UV.y,0.0,1.0);
    float half_width = max(0.005,pow(max(sin(t*3.14159265),0.0),0.72)*(1.0-t*0.58)*0.47);
    float shift = reduced_motion ? 0.0 : sin(phase*4.2+t*2.0)*0.025*t;
    float radial = abs(UV.x-0.5-shift)/half_width;
    float contour = 1.0-smoothstep(0.78,1.0,radial);
    float cap = smoothstep(0.0,0.05,t)*(1.0-smoothstep(0.94,1.0,t));
    float core = pow(max(0.0,1.0-radial),2.5)*(1.0-t*0.65);
    vec3 edge = mix(vec3(0.12,0.28,0.95),vec3(1.0,0.19,0.025),smoothstep(0.0,0.18,t));
    vec3 color = mix(edge,vec3(1.0,0.92,0.53),core);
    float pulse = reduced_motion ? 1.0 : 0.93+0.07*sin(phase*8.2+t*6.0);
    ALBEDO=color;
    EMISSION=color*(1.15+core*1.4)*pulse*intensity;
    ALPHA=contour*cap*0.90*intensity;
}
