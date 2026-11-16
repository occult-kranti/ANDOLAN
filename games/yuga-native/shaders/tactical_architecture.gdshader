shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;

// Original tactical civic material kit. World metres keep large procedural
// boxes and rescaled immutable modules at the same masonry scale. No vertex
// displacement, alpha cutout, collision or gameplay-dependent coloration.
#include "res://scripts/world_ground_common.gdshaderinc"

uniform sampler2D source_albedo : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D source_roughness : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 mineral_tint : source_color = vec4(0.66, 0.58, 0.46, 1.0);
uniform vec4 roughness_channel = vec4(1.0, 0.0, 0.0, 0.0);
uniform bool source_maps = false;
// sandstone, limestone, glazed indigo, paving, carved trim
uniform int surface_kind : hint_range(0, 4) = 0;
uniform float minimum_roughness : hint_range(0.0, 1.0) = 0.76;
uniform float block_width = 1.12;
uniform float block_height = 0.48;
uniform float joint_gain = 0.28;
uniform float variation_gain = 0.16;
varying vec3 world_position;
varying vec3 world_normal;

float civic_hash(vec2 p) {
	return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);
}

float civic_noise(vec2 p) {
	vec2 cell=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
	return mix(mix(civic_hash(cell),civic_hash(cell+vec2(1.0,0.0)),f.x),
		mix(civic_hash(cell+vec2(0.0,1.0)),civic_hash(cell+vec2(1.0)),f.x),f.y);
}

vec2 masonry_edge(vec2 p) {
	float row=floor(p.y/block_height);
	vec2 cell=vec2(p.x+mod(row,2.0)*block_width*.5,p.y);
	vec2 local=mod(cell,vec2(block_width,block_height));
	return min(local,vec2(block_width,block_height)-local);
}

float masonry_height(vec2 p) {
	vec2 edge=masonry_edge(p);
	return smoothstep(.007,.036,min(edge.x,edge.y))*.006;
}

void vertex() {
	world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;
	world_normal=normalize(MODEL_NORMAL_MATRIX*NORMAL);
}

void fragment() {
	if (surface_kind==3) {
		vec2 p=world_position.xz;
		// Broad cool/warm mineral movement breaks a uniform orange field while
		// leaving the aiming floor quiet and the unchanged site outlines clear.
		vec3 stone=world_paving(p);
		float mineral=civic_noise(p*.065);
		vec3 cast=mix(vec3(.86,.95,1.06),vec3(1.02,1.0,.93),mineral);
		ALBEDO=stone*cast;
		ROUGHNESS=world_paving_roughness(p);
		NORMAL=normalize((VIEW_MATRIX*vec4(sangam_paving_normal(p),0.0)).xyz);
		METALLIC=0.0; SPECULAR=.28;
	} else {
		vec3 n=normalize(world_normal);
		vec3 an=abs(n);
		vec3 axis_u=vec3(1.0,0.0,0.0);
		vec3 axis_v=vec3(0.0,1.0,0.0);
		if (an.y>.65) { axis_v=vec3(0.0,0.0,1.0); }
		else if (an.x>an.z) { axis_u=vec3(0.0,0.0,1.0); }
		vec2 p=vec2(dot(world_position,axis_u),dot(world_position,axis_v));
		float footprint=max(fwidth(p.x),fwidth(p.y));
		float detail=1.0-smoothstep(.025,.16,footprint);
		float aa=max(.001,footprint*.65);
		float row=floor(p.y/block_height);
		vec2 cell=floor(vec2(p.x+mod(row,2.0)*block_width*.5,p.y)/vec2(block_width,block_height));
		vec2 edge=masonry_edge(p);
		float joint=(1.0-smoothstep(.006-aa,.013+aa,min(edge.x,edge.y)))*detail;
		float cell_detail=1.0-smoothstep(.16,.55,footprint/min(block_width,block_height));
		float block=(civic_hash(cell)-.5)*variation_gain*cell_detail;
		float broad=(civic_noise(p*.31)-.5)*.09;
		float grain=(civic_noise(p*47.0)-.5)*.035*(1.0-smoothstep(.005,.04,footprint));
		float source_grain=0.0;
		float source_rough=minimum_roughness;
		if (source_maps) {
			source_grain=(dot(texture(source_albedo,UV).rgb,vec3(.2126,.7152,.0722))-.35)*.045;
			source_rough=dot(texture(source_roughness,UV),roughness_channel);
		}
		float age=(1.0-smoothstep(.16,1.05,world_position.y))*mix(.45,1.0,civic_noise(vec2(p.x*.75,p.y*.16)));
		vec3 mineral=mix(vec3(.92,.97,1.04),vec3(1.04,.99,.89),civic_noise(world_position.xz*.085));
		vec3 stone=mineral_tint.rgb*mineral*(1.0+block+broad+grain+source_grain);
		vec3 mortar=stone*vec3(.68,.72,.73);
		ALBEDO=mix(stone,mortar,joint*joint_gain);
		ALBEDO=mix(ALBEDO,ALBEDO*vec3(.70,.75,.72),age*.42);
		if (surface_kind==2) {
			// Glaze keeps a controlled low sheen; no gold or emissive gameplay cue.
			ROUGHNESS=clamp(minimum_roughness+(civic_noise(p*.7)-.5)*.14+joint*.12,.43,.9);
			SPECULAR=.45;
		} else {
			ROUGHNESS=clamp(max(minimum_roughness,source_rough*.9)+broad*.5+age*.08,.65,1.0);
			SPECULAR=.28;
		}
		float dx=(masonry_height(p+vec2(.006,0.0))-masonry_height(p-vec2(.006,0.0)))/.012;
		float dy=(masonry_height(p+vec2(0.0,.006))-masonry_height(p-vec2(0.0,.006)))/.012;
		float relief=surface_kind==4 ? .25 : .7;
		vec3 shaded=normalize(n-(axis_u*dx+axis_v*dy)*detail*relief);
		NORMAL=normalize((VIEW_MATRIX*vec4(shaded,0.0)).xyz);
		METALLIC=0.0;
	}
}
