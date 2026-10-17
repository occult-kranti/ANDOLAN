extends RefCounted
## Original reversible look-development layer for the Rama courtyard.
## Apply after ProductionLighting.apply() and MythicEnvironment.set_phase().
## The existing scene owns every light, sky and gameplay object. This controller
## adds no nodes, mesh draw calls, particles or per-frame callbacks. Existing
## engine SSAO/glow settings still have GPU cost and need hardware profiling.
## "neutral" is the captured production baseline, not a white studio relight.

const MODES := ["day", "night", "neutral"]
const ENVIRONMENT_PROPERTIES := [
	"ambient_light_color", "ambient_light_energy", "tonemap_exposure",
	"fog_light_color", "fog_light_energy", "fog_density", "fog_sky_affect",
	"fog_sun_scatter", "glow_enabled", "glow_intensity", "glow_strength",
	"glow_bloom", "glow_hdr_threshold", "ssao_enabled", "ssao_radius",
	"ssao_intensity", "ssao_power", "ssao_detail", "ssao_light_affect",
]
const SUN_PROPERTIES := ["transform", "light_color", "light_energy", "light_specular"]
const SKY_PROPERTIES := ["sky_top_color", "sky_horizon_color", "ground_bottom_color",
	"ground_horizon_color", "sky_energy_multiplier", "ground_energy_multiplier"]
const FILL_PROPERTIES := ["light_color", "light_energy", "light_specular"]

var _world: Node3D
var _environment: Environment
var _sun: DirectionalLight3D
var _sky: ProceduralSkyMaterial
var _records: Array[Dictionary] = []
var _mode := "unbound"
var _configure_count := 0
var _last_error := ""

func configure(world: Node3D, environment: Environment, sun: DirectionalLight3D,
		night: bool = false) -> bool:
	# An explicit configure is a new upstream settings boundary. Refresh only
	# externally changed properties, so repeated identical configure calls keep
	# the original neutral comparison instead of capturing our own overlay.
	if not is_instance_valid(world) or environment == null or not is_instance_valid(sun):
		return _fail("invalid_scene")
	if not world.is_ancestor_of(sun):
		return _fail("sun_outside_world")
	if not _records.is_empty():
		if world != _world or environment != _environment or sun != _sun:
			return _fail("restore_before_rebind")
		if not _same_resources():
			return _fail("scene_resources_changed")
		_refresh_baseline()
	else:
		_world = world
		_environment = environment
		_sun = sun
		_capture(environment, ENVIRONMENT_PROPERTIES, "environment")
		_capture(sun, SUN_PROPERTIES, "sun")
		if environment.sky != null:
			_sky = environment.sky.sky_material as ProceduralSkyMaterial
		if _sky != null:
			_capture(_sky, SKY_PROPERTIES, "sky")
		var fill := world.get_node_or_null("CoolSkyFill") as DirectionalLight3D
		if fill != null: _capture(fill, FILL_PROPERTIES, "fill")
		var portrait := world.get_node_or_null("HeroPortraitFill") as OmniLight3D
		if portrait != null: _capture(portrait, FILL_PROPERTIES, "portrait")
	_configure_count += 1
	_apply("night" if night else "day")
	return true

func set_mode(mode: String) -> bool:
	if mode not in MODES: return _fail("unknown_mode")
	if _records.is_empty(): return _fail("not_configured")
	if not _same_resources(): return _fail("scene_resources_changed")
	# Photo comparisons cannot silently overwrite an upstream settings change.
	# Let the caller reconfigure after its production settings writer instead.
	for record in _records:
		var target: Object = record.object
		for property in record.written:
			if target.get(property) != record.written[property]:
				return _fail("external_property_change:" + record.label + ":" + property)
	_apply(mode)
	return true

func restore() -> Dictionary:
	# Restore each property only while its last value is still ours. A caller's
	# newer values survive teardown; the conflict is explicit in the receipt.
	var restored := 0
	var conflicts: Array[String] = []
	for record in _records:
		if not is_instance_valid(record.object):
			conflicts.append(record.label + ":freed")
			continue
		var target: Object = record.object
		for property in record.written:
			if target.get(property) == record.written[property]:
				target.set(property, record.baseline[property])
				restored += 1
			else:
				conflicts.append(record.label + ":" + property)
	_records.clear()
	_world = null
	_environment = null
	_sun = null
	_sky = null
	_mode = "unbound"
	_last_error = ""
	return {"restored_properties": restored, "conflicts": conflicts,
		"passed": conflicts.is_empty()}

func diagnostics() -> Dictionary:
	return {"mode": _mode, "bound": not _records.is_empty(),
		"configure_count": _configure_count, "resource_count": _records.size(),
		"last_error": _last_error, "added_lights": 0, "added_meshes": 0,
		"added_particles": 0, "per_frame_updates": 0,
		"neutral_policy": "captured production baseline",
		"scope": "courtyard presentation; rendered readability and GPU cost require review"}

func _capture(target: Object, properties: Array, label: String) -> void:
	var baseline := {}
	for property in properties: baseline[property] = target.get(property)
	_records.append({"object": target, "label": label,
		"baseline": baseline, "written": {}})

func _same_resources() -> bool:
	if not is_instance_valid(_world) or not is_instance_valid(_sun): return false
	if _environment == null: return false
	var actual_sky: ProceduralSkyMaterial = null
	if _environment.sky != null:
		actual_sky = _environment.sky.sky_material as ProceduralSkyMaterial
	if actual_sky != _sky: return false
	for record in _records:
		if not is_instance_valid(record.object): return false
		if record.label == "fill" and _world.get_node_or_null("CoolSkyFill") != record.object:
			return false
		if record.label == "portrait" and _world.get_node_or_null("HeroPortraitFill") != record.object:
			return false
	return true

func _refresh_baseline() -> void:
	for record in _records:
		var target: Object = record.object
		for property in record.baseline:
			var current: Variant = target.get(property)
			if property not in record.written or current != record.written[property]:
				record.baseline[property] = current

func _write(label: String, values: Dictionary) -> void:
	for record in _records:
		if record.label != label: continue
		var target: Object = record.object
		for property in values:
			target.set(property, values[property])
			# Capture the getter, since Godot clamps/canonicalizes some properties.
			record.written[property] = target.get(property)

func _apply(mode: String) -> void:
	if mode == "neutral":
		for record in _records: _write(record.label, record.baseline)
	else:
		var night := mode == "night"
		var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
		_write("environment", {
			# Preserve the established night visibility floor. Key/fill separation,
			# not a lower ambient floor, gives the face and costume their shape.
			"ambient_light_color": Color("b6c6dc") if night else Color("c7cbd1"),
			"ambient_light_energy": 0.32 if night else 0.30,
			"tonemap_exposure": 1.0,
			"fog_light_color": Color("4b6585") if night else Color("a3b0ba"),
			"fog_light_energy": 0.40 if night else 0.32,
			"fog_density": 0.00135 if night else 0.0009,
			"fog_sky_affect": 0.08, "fog_sun_scatter": 0.04,
			# Keep broad cloth/skin sheen below the glow trigger. Practical flame
			# accents can bloom locally; there is no full-frame bloom pedestal.
			"glow_enabled": forward_plus, "glow_intensity": 0.10,
			"glow_strength": 0.40, "glow_bloom": 0.0, "glow_hdr_threshold": 2.1,
			# Small-radius AO grounds the silhouette without dirtying the whole
			# face or turning cloth folds into black painted creases.
			"ssao_enabled": forward_plus, "ssao_radius": 0.28,
			"ssao_intensity": 0.68, "ssao_power": 1.08,
			"ssao_detail": 0.40, "ssao_light_affect": 0.10,
		})
		var angles := Vector3(-34, -52, 0) if night else Vector3(-30, -52, 0)
		var sun_transform := Transform3D(Basis.from_euler(angles * (PI / 180.0)), _sun.position)
		_write("sun", {"transform": sun_transform,
			"light_color": Color("bbceeb") if night else Color("ffe5c8"),
			"light_energy": 0.50 if night else 1.30, "light_specular": 0.82})
		_write("sky", {"sky_top_color": Color("1c2c46") if night else Color("415c78"),
			"sky_horizon_color": Color("63768e") if night else Color("a4afb7"),
			"ground_bottom_color": Color("142131") if night else Color("263641"),
			"ground_horizon_color": Color("63768e") if night else Color("a4afb7"),
			# ProceduralSky multiplies upper/lower hemispheres separately. Equal
			# horizon colors still leave a hard seam when their energy differs.
			# Match radiance at the join; retain the darker lower pole gradient.
			"sky_energy_multiplier": 0.68 if night else 0.86,
			"ground_energy_multiplier": 0.68 if night else 0.86})
		# Training hides the portrait light. The existing opposing sky fill must
		# therefore carry facial readability in gameplay as well as the title.
		_write("fill", {"light_color": Color("bacbe0"),
			"light_energy": 0.36 if night else 0.42, "light_specular": 0.30})
		# Existing production fill was brighter than every practical and could
		# flatten the nose/cheek. Keep its reach/transform and shadow policy.
		_write("portrait", {"light_color": Color("dce6f1"),
			"light_energy": 1.8 if night else 1.65, "light_specular": 0.30})
	_mode = mode
	_last_error = ""

func _fail(reason: String) -> bool:
	_last_error = reason
	return false
