extends "res://tools/ui-campaign/observer.gd"
## Read-only extension of the existing native input observer.
## All locomotion, aiming, combat and menus are driven by external XTest events.
var trace: FileAccess
var event_trace: FileAccess
var observed_kit: int = 0
var latest_gate: Dictionary = {}

func _initialize() -> void:
	super._initialize()
	trace = FileAccess.open(output + "/physics.jsonl", FileAccess.WRITE)
	event_trace = FileAccess.open(output + "/ability-events.jsonl", FileAccess.WRITE)

func _process(delta: float) -> bool:
	var result := super._process(delta)
	if not capturing and current_scene and current_scene.has_method("friendly_camera_visibility_report"):
		var visibility: Dictionary = current_scene.friendly_camera_visibility_report(false)
		# Observe one naturally occurring ally obstruction. No actor is moved,
		# authority held or transparency assigned by this observer.
		if visibility.get("blocked_units",0) > 0 and visibility.get("maximum_fade",0.0) >= .7 and not "auto-friendly-occlusion" in captured:
			_capture("auto-friendly-occlusion")
	return result

func _physics_process(_delta: float) -> bool:
	if not current_scene or current_scene.scene_file_path != "res://scenes/confluence_world.tscn": return false
	if not "player" in current_scene or not is_instance_valid(current_scene.player): return false
	var actor: CharacterBody3D = current_scene.player
	var slides: Array = []
	for i in actor.get_slide_collision_count():
		var hit := actor.get_slide_collision(i)
		var body := hit.get_collider()
		slides.append({"body":str(body.get_path()) if body is Node else str(body),"normal":_vec(hit.get_normal()),"position":_vec(hit.get_position())})
	var ray_start := actor.global_position + Vector3.UP * 1.5
	var target := Vector3(-40,1.5,-44 if actor.global_position.z < -54 else -64)
	var query := PhysicsRayQueryParameters3D.create(ray_start,target,1,[actor.get_rid()])
	var hit := actor.get_world_3d().direct_space_state.intersect_ray(query)
	latest_gate = {"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames(),"time_usec":Time.get_ticks_usec(),"position":_vec(actor.global_position),"velocity":_vec(actor.velocity),"yaw":actor.yaw,"pitch":actor.pitch,"sensitivity":actor.sensitivity,"grounded":actor.is_on_floor(),"active":actor.active,"paused":paused,"overview":current_scene.overview,"mouse_mode":Input.mouse_mode,"spring_length":actor.spring.spring_length,"spring_hit_length":actor.spring.get_hit_length(),"camera_position":_vec(actor.camera.global_position),"camera_forward":_vec(-actor.camera.global_basis.z),"shots_fired":actor.shots_fired,"ammo":actor.ammo,"slides":slides,"gate_ray":{"start":_vec(ray_start),"target":_vec(target),"clear":hit.is_empty(),"hit_position":_vec(hit.position) if not hit.is_empty() else [],"body":str(hit.collider.get_path()) if not hit.is_empty() and hit.collider is Node else ""},"input":{"forward":Input.is_action_pressed("move_forward"),"back":Input.is_action_pressed("move_back"),"left":Input.is_action_pressed("move_left"),"right":Input.is_action_pressed("move_right"),"fire":Input.is_action_pressed("fire")}}
	if is_instance_valid(current_scene.rama_runtime):
		latest_gate["vitals"] = current_scene.rama_runtime.vitals.report()
		var kit: Node = current_scene.rama_runtime.kit
		if is_instance_valid(kit) and kit.get_instance_id() != observed_kit:
			observed_kit = kit.get_instance_id()
			kit.ability_event.connect(_ability_event)
	if current_scene.has_method("friendly_camera_visibility_report"):
		latest_gate["friendly_camera"] = current_scene.friendly_camera_visibility_report(false)
	trace.store_line(JSON.stringify(latest_gate))
	trace.flush()
	return false

func _ability_event(event: Dictionary) -> void:
	if event.get("kind","") == "tick": return
	var row := {"physics_frame":Engine.get_physics_frames(),"time_usec":Time.get_ticks_usec(),"event":event}
	event_trace.store_line(JSON.stringify(row))
	event_trace.flush()

func snapshot() -> Dictionary:
	var result := super.snapshot()
	result["gate_input"] = latest_gate if current_scene and current_scene.scene_file_path == "res://scenes/confluence_world.tscn" else {}
	result["navigation_keys_pressed"] = {"Tab":Input.is_physical_key_pressed(KEY_TAB),"Return":Input.is_physical_key_pressed(KEY_ENTER),"Escape":Input.is_physical_key_pressed(KEY_ESCAPE)}
	result["friendly_camera"] = current_scene.friendly_camera_visibility_report(capturing) if current_scene and current_scene.has_method("friendly_camera_visibility_report") else {"available":false}
	return result

func _vec(v: Vector3) -> Array:
	return [v.x,v.y,v.z]
