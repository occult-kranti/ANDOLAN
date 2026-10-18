"""Private, reversible paving bevel proposal; never edits the runtime files."""
from pathlib import Path
import hashlib
import json

SOURCE = Path('/workspace/ANDOLAN/games/yuga-native/scripts')
OUT = Path(__file__).resolve().parent

def sha(data):
    return hashlib.sha256(data).hexdigest()

common_bytes = (SOURCE / 'world_ground_common.gdshaderinc').read_bytes()
ground_bytes = (SOURCE / 'world_ground.gdshader').read_bytes()
common = common_bytes.decode()
helper = '''
// Three-millimetre rounded stone bevels, expressed only as a lighting slope.
// Position, silhouette and physical support remain the original flat plane.
// Screen derivatives widen the transition and fade relief before it aliases.
vec2 paving_stone_slope(vec2 p, vec2 slab_size) {
	float row = floor(p.y / slab_size.y);
	vec2 tiled = vec2(p.x / slab_size.x + mod(row, 2.0) * 0.5, p.y / slab_size.y);
	vec2 inside = fract(tiled);
	vec2 edge = min(inside, 1.0 - inside) * slab_size;
	float footprint = max(fwidth(p.x), fwidth(p.y));
	float visibility = 1.0 - smoothstep(0.025, 0.10, footprint);
	float width = max(0.038, footprint * 1.5);
	vec2 t = clamp((edge - vec2(0.008)) / width, vec2(0.0), vec2(1.0));
	vec2 face = t * t * (3.0 - 2.0 * t);
	vec2 gradient = 6.0 * t * (1.0 - t) / width;
	// The product produces a rounded two-axis corner, with no min-edge cusp.
	vec2 sign_to_center = sign(vec2(0.5) - inside);
	return 0.003 * visibility * gradient * face.yx * sign_to_center;
}

vec3 paving_lit_normal(vec3 normal_in_view, mat4 inverse_view,
		mat4 view, vec2 slope) {
	vec3 world_normal = normalize((inverse_view * vec4(normal_in_view, 0.0)).xyz);
	float upper_surface = smoothstep(0.65, 0.95, world_normal.y);
	vec3 relieved = normalize(world_normal + vec3(-slope.x, 0.0, -slope.y) * upper_surface);
	return normalize((view * vec4(relieved, 0.0)).xyz);
}

'''
assert common.count('vec3 world_paving(vec2 p) {') == 1
common = common.replace('vec3 world_paving(vec2 p) {', helper + 'void sample_world_paving(vec2 p, out vec3 color, out vec2 slope) {')
old = '\tpaving = mix(paving, avenue, max(lane, rotation * 0.55));'
new = '''	float avenue_mix = max(lane, rotation * 0.55);
	paving = mix(paving, avenue, avenue_mix);
	slope = mix(paving_stone_slope(p, vec2(1.65, 1.10)),
		paving_stone_slope(p, vec2(2.40, 1.20)), avenue_mix);'''
assert old in common
common = common.replace(old, new)
old = '\tpaving = mix(paving, court_stone, court * 0.75);'
new = old + '\n\tslope = mix(slope, paving_stone_slope(p, vec2(2.2, 2.2)), court * 0.75);'
assert old in common
common = common.replace(old, new)
old = '\treturn mix(paving, vec3(0.32, 0.285, 0.19), ring * 0.4);\n}'
new = '''	color = mix(paving, vec3(0.32, 0.285, 0.19), ring * 0.4);
}

// Callers needing color only retain the same function and exact color path.
vec3 world_paving(vec2 p) {
	vec3 color;
	vec2 unused_slope;
	sample_world_paving(p, color, unused_slope);
	return color;
}'''
assert old in common
common = common.replace(old, new)
ground = ground_bytes.decode()
old = '\tALBEDO = world_paving(world_position.xz);'
new = '''	vec3 stone_color;
	vec2 stone_slope;
	sample_world_paving(world_position.xz, stone_color, stone_slope);
	ALBEDO = stone_color;
	NORMAL = paving_lit_normal(NORMAL, INV_VIEW_MATRIX, VIEW_MATRIX, stone_slope);'''
assert old in ground
ground = ground.replace(old, new)
files = {'world_ground_common.gdshaderinc': common, 'world_ground.gdshader': ground}
for name, text in files.items():
    p = OUT / name
    if p.exists():
        assert p.read_text() == text, 'Never overwrite a changed private candidate'
    else:
        p.write_text(text)
manifest = {'status': 'private_unreviewed_candidate', 'source_baseline': {
    'world_ground_common.gdshaderinc': sha(common_bytes), 'world_ground.gdshader': sha(ground_bytes)},
    'candidate': {n: sha(t.encode()) for n,t in files.items()},
    'scope': 'Original derivative-filtered stone bevel normals; same color, roughness, coordinates, geometry and physics. Water dry-border normal matching is required before integration.',
    'actual_review': 'pending; shader compilation, matched near/distant and wet-border temporal views required'}
(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
