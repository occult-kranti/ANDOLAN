shader_type spatial;
render_mode cull_disabled;
uniform float age = 0.0;
varying vec3 local_point;
float hash(vec3 p) { return fract(sin(dot(p, vec3(127.1,311.7,74.7)))*43758.5453); }
float noise3(vec3 p) {
 vec3 i=floor(p), f=fract(p);f=f*f*(3.0-2.0*f);
 return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
void vertex(){local_point=VERTEX;}
void fragment(){
 float settle=1.0-exp(-age*5.0);
 float turn=(1.0-settle)*.45;
 vec3 point=vec3(local_point.x*cos(turn)-local_point.z*sin(turn),local_point.y,local_point.x*sin(turn)+local_point.z*cos(turn));
 vec3 p=point*(.85+(1.0-settle)*.35)+vec3(age*.09,age*-.11,0.0);
 float cloud=noise3(p)*.6+noise3(p*2.1)*.28+noise3(p*4.3)*.12;
 ALBEDO=mix(vec3(.14,.24,.28),vec3(.57,.65,.61),smoothstep(.2,.85,cloud));
 ROUGHNESS=1.0;SPECULAR=.12;
 // The full opaque authority boundary remains visible from onset; light and
 // cloud density settle inside it instead of scaling a deceptively small shell.
 float crest=pow(max(0.0,1.0-abs(local_point.y-(age*13.0-4.2))*.8),3.0)*(1.0-smoothstep(.25,.65,age));
 EMISSION=vec3(.045,.063,.059)*cloud+vec3(.22,.15,.065)*crest;
}
