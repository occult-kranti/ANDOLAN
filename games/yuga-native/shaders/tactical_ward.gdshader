shader_type spatial;
render_mode cull_disabled, depth_draw_opaque;
uniform float age = 0.0;
varying vec3 local_point;
void vertex(){local_point=VERTEX;}
void fragment(){
 vec2 p=local_point.xy;
 vec2 cell=abs(fract(p*vec2(1.2,1.2))-.5);
 float diamond=abs(cell.x+cell.y-.34);
 float filigree=1.0-smoothstep(.006,.022,diamond);
 float sweep=pow(max(0.0,1.0-abs(fract(p.y*.28-age*.12)-.5)*2.0),12.0);
 vec3 ink=mix(vec3(.025,.14,.18),vec3(.13,.38,.41),p.y/2.8);
 ALBEDO=mix(ink,vec3(.64,.50,.24),filigree*.5);
 EMISSION=vec3(.17,.51,.55)*(.10+sweep*.35)+vec3(.92,.68,.30)*filigree*.4;
 METALLIC=.25;ROUGHNESS=.4;ALPHA=.87;
}
