extends Node3D
## Isolated authoring setup. Appearance remains Rama; gameplay is never enabled.
@export var hero_id := "arjuna"
const MANIFEST := "res://docs/research/hero-family-reuse-oct23/rama-family-manifest.json"
const Motion = preload("res://scripts/rama_motion.gd")
const Lod = preload("res://scripts/rama_lod_binding.gd")
const Surface = preload("res://scripts/rama_surface_materials.gd")
const Secondary = preload("res://scripts/rama_secondary_motion.gd")
const Finish = preload("res://scripts/rama_surface_finish.gd")
const Face = preload("res://scripts/rama_facial_performance.gd")
var motion: SkeletonModifier3D
var lod: Node
var surface: Node
var secondary: Node
var finish: Node
var face: Node
var errors: Array[String] = []
var configured := false
var _setup_attempted := false

func _ready() -> void:
	setup()

func _find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := _find(child,kind)
		if found: return found
	return null

func setup() -> bool:
	if configured: return true
	# A failed authoring instance must be discarded and reopened. Retrying a
	# partially configured instance could duplicate skeleton modifiers/materials.
	if _setup_attempted: return false
	_setup_attempted = true
	var manifest = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	if not manifest is Dictionary:
		errors.append("missing source-pinned manifest"); return false
	var eligible := false
	for hero in manifest.roster:
		if hero.hero_id == hero_id: eligible = hero.reuse_class == "archer_template"
	if not eligible:
		errors.append("hero needs unique anatomy/weapon authoring"); return false
	for reference in manifest.source_pins:
		if FileAccess.get_sha256(reference.res_path) != reference.sha256:
			errors.append("source pin mismatch: " + reference.path); return false
	var visual := get_node_or_null("SharedRamaDonor")
	if visual == null:
		errors.append("missing shared donor instance"); return false
	var animator := _find(visual,"AnimationPlayer") as AnimationPlayer
	motion = Motion.new()
	if not motion.configure(visual,animator):
		motion.free(); motion = null
		errors.append("runtime rig/rest/library mismatch"); return false
	# Same ordering as current player.gd; no mesh, library or script is copied.
	lod = Lod.new(); visual.add_child(lod)
	if not lod.configure(visual,motion.rig,manifest.lod.paths.map(func(path):return "res://"+path)):
		errors.append("LOD binding failed")
	surface = Surface.new(); visual.add_child(surface)
	if not surface.configure(visual): errors.append("surface calibration failed")
	secondary = Secondary.new(); visual.add_child(secondary)
	if not secondary.configure(visual): errors.append("secondary mask binding failed")
	finish = Finish.new(); visual.add_child(finish)
	if not finish.configure(visual): errors.append("surface finish failed")
	face = Face.new(); visual.add_child(face)
	if not face.configure(visual): errors.append("facial binding failed")
	configured = errors.is_empty()
	return configured

func socket_checked(socket_name: String) -> Dictionary:
	if socket_name not in ["bow_grip","string_nock","draw_hand","arrow_muzzle","head"]:
		return {"ok":false,"error":"UNKNOWN_SOCKET","name":socket_name}
	if not configured: return {"ok":false,"error":"TEMPLATE_NOT_CONFIGURED"}
	var result: Transform3D = motion.socket_global(socket_name)
	return {"ok":result.origin.is_finite() and result.basis.is_finite(),"name":socket_name,"position":[result.origin.x,result.origin.y,result.origin.z]}

func report() -> Dictionary:
	return {"configured":configured,"setup_attempted":_setup_attempted,"failure_retry_policy":"discard and reopen instance","hero_id":hero_id,"status":"authoring_template_only","appearance":"unchanged Rama donor reference","finished_hero":false,"gameplay_enabled":false,"runtime_promoted":false,"errors":errors.duplicate(),"motion":motion.diagnostics() if is_instance_valid(motion) else {},"lod":lod.report() if is_instance_valid(lod) else {},"surface":surface.diagnostics() if is_instance_valid(surface) else {},"secondary":secondary.report() if is_instance_valid(secondary) else {},"finish":finish.report() if is_instance_valid(finish) else {},"face":face.report() if is_instance_valid(face) else {}}
