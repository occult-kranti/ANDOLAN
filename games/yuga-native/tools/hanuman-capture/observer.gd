extends "res://tools/ui-campaign/observer.gd"
## Observe the normal launcher and trial while a separate XTest driver plays.

const TRIAL := "res://scenes/hanuman_trial.tscn"
var trial_events: Array[Dictionary] = []
var pending_images: Array[String] = []
var connected_id := 0


func _process(delta: float) -> bool:
	if current_scene and current_scene.scene_file_path == TRIAL:
		var combat: Variant = current_scene.get("combat")
		if is_instance_valid(combat) and combat.get_instance_id() != connected_id:
			combat.ability_event.connect(_record_ability)
			connected_id = combat.get_instance_id()
		if not capturing and not pending_images.is_empty():
			_capture(pending_images.pop_front())
	return super._process(delta)


func _record_ability(event: Dictionary) -> void:
	if event.kind == "tick":
		return
	trial_events.append({
		"frame": Engine.get_process_frames(), "physics_frame": Engine.get_physics_frames(),
		"event": event.duplicate(true),
	})
	_write(output + "/abilities.json", {"events": trial_events})
	if event.kind == "impact" and not pending_images.has("ability-" + str(event.ability_id)):
		var name := "ability-" + str(event.ability_id)
		if not captured.has(name):
			pending_images.append(name)


func snapshot() -> Dictionary:
	var result := super.snapshot()
	if current_scene and current_scene.scene_file_path == TRIAL:
		result["trial_observed"] = connected_id > 0
		if current_scene.has_method("report"):
			result["trial"] = current_scene.report()
			var actor: Variant = current_scene.get("hero")
			if actor is CharacterBody3D:
				result["actor_z"] = actor.global_position.z
	return result
