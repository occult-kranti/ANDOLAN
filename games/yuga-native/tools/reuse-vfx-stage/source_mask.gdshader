shader_type spatial;
render_mode cull_back;
uniform sampler2D base_texture : source_color, filter_linear_mipmap;
uniform sampler2D orm_texture : filter_linear_mipmap;
uniform bool mask_active = true;
varying vec3 source_position;
void vertex() { source_position=VERTEX; }
void fragment() {
    // Deliberately bounded center flame region, in the immutable source GLB coordinates.
    // The metal bowl/finial remain unchanged; only the baked white flame is hidden.
    if(mask_active && source_position.x > 0.005 && source_position.x < 0.115 && source_position.y > 0.135 && source_position.y < 0.30 && abs(source_position.z)<0.065) discard;
    vec4 albedo=texture(base_texture,UV);
    vec3 orm=texture(orm_texture,UV).rgb;
    ALBEDO=albedo.rgb;
    ROUGHNESS=orm.g;
    METALLIC=orm.b;
}
