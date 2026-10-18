extends "/tmp/yuga-desktop-package-warm-r1/observer.gd"
## Explicit authority fixture for labeled U5 stage steps; base observer stays read-only.

var stage_history: Array[Dictionary] = []
var stage_ids: Dictionary = {}

func _process(delta: float) -> bool:
	var request_path := output + "/stage-request.json"
	if not output.is_empty() and FileAccess.file_exists(request_path):
		var request = JSON.parse_string(FileAccess.get_file_as_string(request_path))
		if request is Dictionary and not str(request.get("id", "")).is_empty() and not stage_ids.has(request.id):
			stage_ids[request.id] = true
			var before: Dictionary = snapshot()
			var authority = load("/tmp/yuga-desktop-package-warm-r1/authority_stage.gd").new()
			var receipt: Dictionary = authority.perform(current_scene, str(request.get("action", "")))
			receipt.merge({"id":request.id,"action":request.get("action", ""),"scope":"STAGED AUTHORITY: fixture inputs through actual game rules; not a native playthrough outcome.","frame":Engine.get_process_frames(),"before_snapshot":before,"after_snapshot":snapshot(),"fixture_sha256":FileAccess.get_sha256("/tmp/yuga-desktop-package-warm-r1/authority_stage.gd")},true)
			stage_history.append(receipt)
			_write(output + "/stage-history.json", {"stages":stage_history})
			_write(output + "/stage-result.json", receipt)
	return super._process(delta)

func snapshot() -> Dictionary:
	var result: Dictionary = super.snapshot()
	result.authority_staging = {"enabled":true,"completed_steps":stage_history.size(),"last_action":stage_history[-1].action if not stage_history.is_empty() else "","simulation_hold":is_instance_valid(current_scene) and current_scene.has_meta("ui_campaign_authority_hold")}
	return result
