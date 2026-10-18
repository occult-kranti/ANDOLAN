shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx, cull_disabled;

// Original world-metre mineral wash over the original imported UV textures.
// No mesh displacement, transparency, fake apertures or screen/depth reads.
uniform vec4 base_color : source_color = vec4(1.0);
uniform sampler2D albedo_texture : source_color, filter_linear_mipmap, repeat_enable;
uniform sampler2D normal_texture : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D roughness_texture : filter_linear_mipmap, repeat_enable;
uniform sampler2D metallic_texture : filter_linear_mipmap, repeat_enable;
uniform bool has_albedo = false;
uniform bool has_normal = false;
uniform bool has_roughness = false;
uniform bool has_metallic = false;
uniform vec4 roughness_channel = vec4(0.0, 1.0, 0.0, 0.0);
uniform vec4 metallic_channel = vec4(0.0, 0.0, 1.0, 0.0);
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform vec3 surface_tint = vec3(1.0);
uniform vec3 mineral_tint = vec3(0.72, 0.81, 0.75);
uniform float weather_amount : hint_range(0.0, 0.3) = 0.18;
uniform float carving_amount : hint_range(0.0, 1.0) = 0.0;
uniform float base_roughness = 0.8;
uniform float base_metallic = 0.0;
uniform float base_specular = 0.5;
uniform float normal_depth = 1.0;
uniform bool window_surface = false;
uniform float night_blend : hint_range(0.0, 1.0) = 0.0;
// G0 diagnostic only: original G2 bindings and texture channels retained.
// No world-coordinate wash, carving, derivative relief or vertex function.
void fragment() {
    vec2 uv = UV * uv_scale.xy + uv_offset.xy;
    vec3 original = base_color.rgb;
    if (has_albedo) { original *= texture(albedo_texture, uv).rgb; }
    ALBEDO = original * surface_tint;
    float roughness = base_roughness;
    if (has_roughness) { roughness *= dot(texture(roughness_texture, uv), roughness_channel); }
    ROUGHNESS = clamp(roughness, 0.22, 0.96);
    METALLIC = base_metallic;
    if (has_metallic) { METALLIC *= dot(texture(metallic_texture, uv), metallic_channel); }
    SPECULAR = base_specular;
    vec3 mapped_normal = vec3(0.5, 0.5, 1.0);
    if (has_normal) { mapped_normal = texture(normal_texture, uv).rgb; }
    NORMAL_MAP = mapped_normal;
    NORMAL_MAP_DEPTH = has_normal ? normal_depth : 1.0;
    if (window_surface) {
        EMISSION = original * vec3(1.0, 0.70, 0.36) * mix(0.03, 0.78, night_blend);
    }
}
