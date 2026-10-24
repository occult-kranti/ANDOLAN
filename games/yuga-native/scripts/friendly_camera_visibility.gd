extends RefCounted
## Presentation-only Forward+ camera readability. Existing per-instance
## transparency preserves shared mesh/material resources and all unit authority.

const MAX_UNITS := 96 # Existing LaneArmy total cap, including corpses.
const MAX_MESHES_PER_UNIT := 128
const MAX_CAMERA_DISTANCE := 6.0
const UNIT_BROAD_RADIUS := 5.0
const HERO_FOCUS_HEIGHT := 1.25
const MAX_FADE := .82
const ENTER_SPEED := 6.0
const RESTORE_SPEED := 4.0
const ENTER_PADDING := .025
const EXIT_PADDING := .12

var _entries: Dictionary = {}
var rejected_updates := 0
var _checked_meshes := 0

func _collect(unit: Node3D) -> Array:
	var result: Array = []
	var pending: Array[Node] = [unit]
	var visual: Node3D = unit.get("visual") as Node3D
	while not pending.is_empty() and result.size() < MAX_MESHES_PER_UNIT:
		var node: Node = pending.pop_back()
		if node is GeometryInstance3D:
			result.append({"node":weakref(node),"initial":node.transparency,
				"body":is_instance_valid(visual) and (node == visual or visual.is_ancestor_of(node))})
		for child in node.get_children(): pending.append(child)
	return result

func _restore(entry: Dictionary) -> void:
	for item in entry.meshes:
		var mesh: GeometryInstance3D = item.node.get_ref() as GeometryInstance3D
		if is_instance_valid(mesh): mesh.transparency = float(item.initial)

func reset() -> void:
	for entry in _entries.values(): _restore(entry)
	_entries.clear()
	_checked_meshes = 0

func _blocks(entry: Dictionary, start: Vector3, finish: Vector3) -> bool:
	var padding: float = EXIT_PADDING if entry.blocked else ENTER_PADDING
	for item in entry.meshes:
		var mesh: GeometryInstance3D = item.node.get_ref() as GeometryInstance3D
		if not is_instance_valid(mesh) or not item.body or float(item.initial) >= .99 or not mesh.is_visible_in_tree(): continue
		var transform := mesh.global_transform
		if not transform.is_finite() or absf(transform.basis.determinant()) < .000001: continue
		_checked_meshes += 1
		var inverse := transform.affine_inverse()
		# Test the actual articulated part's existing local AABB, not the friendly
		# collider (which intentionally has collision_layer 0).
		if mesh.get_aabb().grow(padding).intersects_segment(inverse*start,inverse*finish) != null: return true
	return false

func update(camera: Camera3D, hero: Node3D, units: Array, delta: float, enabled := true) -> void:
	if not is_finite(delta) or delta < 0.0:
		rejected_updates += 1
		return
	if not enabled or not is_instance_valid(camera) or not is_instance_valid(hero) or not camera.is_inside_tree() or not hero.is_inside_tree() or not camera.current:
		reset()
		return
	var start := camera.global_position
	var finish := hero.global_position + Vector3.UP*HERO_FOCUS_HEIGHT
	if not start.is_finite() or not finish.is_finite() or start.distance_to(finish) > MAX_CAMERA_DISTANCE or start.distance_squared_to(finish) < .0001:
		reset()
		return
	var dt := minf(delta,.1)
	var seen: Dictionary = {}
	_checked_meshes = 0
	for index in range(mini(units.size(),MAX_UNITS)):
		var unit = units[index]
		if not is_instance_valid(unit) or not unit is Node3D or not unit.is_inside_tree() or not unit.is_in_group("lane_ally") or unit.get("team") != "sun": continue
		var identity: int = unit.get_instance_id()
		seen[identity] = true
		if not _entries.has(identity):
			_entries[identity] = {"unit":weakref(unit),"meshes":_collect(unit),"fade":0.0,"blocked":false}
		var entry: Dictionary = _entries[identity]
		var nearby: bool = unit.global_position.is_finite() and unit.global_position.distance_to(start) <= MAX_CAMERA_DISTANCE+UNIT_BROAD_RADIUS
		entry.blocked = nearby and _blocks(entry,start,finish)
		var target: float = MAX_FADE if entry.blocked else 0.0
		entry.fade = move_toward(float(entry.fade),target,dt*(ENTER_SPEED if entry.blocked else RESTORE_SPEED))
		for item in entry.meshes:
			var mesh: GeometryInstance3D = item.node.get_ref() as GeometryInstance3D
			if is_instance_valid(mesh):
				mesh.transparency = 1.0-(1.0-float(item.initial))*(1.0-float(entry.fade))
	for identity in _entries.keys():
		if not seen.has(identity):
			_restore(_entries[identity])
			_entries.erase(identity)

func report(detailed := false) -> Dictionary:
	var active := 0
	var blocked := 0
	var maximum := 0.0
	var units: Array = []
	for entry in _entries.values():
		if float(entry.fade) > .000001: active += 1
		if entry.blocked: blocked += 1
		maximum = maxf(maximum,float(entry.fade))
		if detailed and float(entry.fade) > .000001:
			var unit: Node3D = entry.unit.get_ref() as Node3D
			if not is_instance_valid(unit): continue
			var minimum := 1.0
			var peak := 0.0
			var count := 0
			for item in entry.meshes:
				var mesh: GeometryInstance3D = item.node.get_ref() as GeometryInstance3D
				if not is_instance_valid(mesh): continue
				minimum = minf(minimum,mesh.transparency); peak = maxf(peak,mesh.transparency); count += 1
			units.append({"unit_id":unit.get("unit_id"),"path":str(unit.get_path()),"team":unit.get("team"),
				"position":[unit.global_position.x,unit.global_position.y,unit.global_position.z],"fade":entry.fade,
				"mesh_count":count,"mesh_transparency_min":minimum,"mesh_transparency_max":peak})
	return {"cached_units":_entries.size(),"faded_units":active,"blocked_units":blocked,
		"checked_meshes":_checked_meshes,"maximum_fade":maximum,"rejected_updates":rejected_updates,
		"details":units,
		"scope":"Forward+ friendly presentation only; no visibility, material, transform, aim or authority writes"}
