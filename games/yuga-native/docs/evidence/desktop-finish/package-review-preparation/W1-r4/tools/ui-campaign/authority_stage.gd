extends RefCounted
## Explicit capture fixture. Never assigns winners or presentation labels.
const HOLD_META := "ui_campaign_authority_hold"

func perform(scene: Node, action: String) -> Dictionary:
	if not is_instance_valid(scene) or scene.scene_file_path != "res://scenes/confluence_world.tscn" or not scene.world_ready:
		return {"passed":false,"error":"Authority staging requires the ready actual Confluence scene."}
	var before := _state(scene)
	var receipt := {"passed":false,"action":action,"before":before,"signals":[],"scope":"STAGED authority inputs and explicit simulation hold; no native-playthrough claim."}
	if action == "release":
		_release(scene)
		receipt.passed = not scene.has_meta(HOLD_META)
	elif action in ["lane","relay-held","relay-contested","defeat","respawn"] or action.begins_with("outcome-"):
		_hold(scene)
		if action == "lane":
			scene.set_paused(false)
			scene.player.position = Vector3(0,.05,-60)
			receipt.presentation_refresh = _refresh_position(scene)
			receipt.passed = scene.lane_label.text.contains(scene.manifest.lanes[1].name) and scene.objective_label.text.contains("Escort Sun troops")
			receipt.manifest_lane_id = scene.manifest.lanes[1].id
		elif action in ["relay-held","relay-contested"]:
			scene.set_paused(false)
			scene.player.position = Vector3(0,.05,0)
			scene.relays.control.reset()
			var actors := [{"id":"ui-stage-sun","team":"sun","position":Vector3.ZERO,"alive":true}]
			for unused in range(37): scene.relays.control.step(.25,actors)
			if action == "relay-contested":
				actors.append({"id":"ui-stage-moon","team":"moon","position":Vector3.ZERO,"alive":true})
				scene.relays.control.step(.1,actors)
			receipt.presentation_refresh = _refresh_position(scene)
			var site: Dictionary = scene.relays.sites()[1]
			receipt.rule_inputs = {"actors":actors,"held_steps":37,"held_delta":.25,"contested_delta":.1 if action == "relay-contested" else 0.0}
			receipt.passed = site.owner == "sun" and (site.contested if action == "relay-contested" else scene.relay_hint.text.contains("next supply"))
		elif action.begins_with("outcome-"):
			var wanted := action.trim_prefix("outcome-")
			if wanted not in ["sun","moon","draw"]: return {"passed":false,"error":"Unknown terminal fixture"}
			scene.army.reset()
			scene.set_paused(false)
			var emissions: Array = []
			var listener := func(team: String): emissions.append(team)
			scene.army.outcome.connect(listener)
			scene.army.cores = {"sun":0.0 if wanted in ["moon","draw"] else 100.0,"moon":0.0 if wanted in ["sun","draw"] else 100.0}
			receipt.rule_inputs = {"cores":scene.army.cores.duplicate(),"delta":.05}
			scene.army.step_simulation(.05)
			scene.army.outcome.disconnect(listener)
			scene._update_practice_hud()
			var terminal: Dictionary = scene.army.report()
			scene._update_practice_hud()
			receipt.signals = emissions
			receipt.presentation_preserves_authority = scene.army.report() == terminal
			receipt.passed = scene.army.winner == wanted and emissions == [wanted] and scene.paused and scene.get_tree().paused and scene.outcome_summary.is_visible_in_tree() and scene.objective_label.text.contains(scene.outcome_summary.heading.text) and scene.relay_hint.text.contains("stopped") and receipt.presentation_preserves_authority
		elif action == "defeat":
			scene.set_paused(false)
			var vitals: Node = scene.rama_runtime.vitals
			receipt.damage = vitals.receive_damage(1000,"ui_capture_defeat",vitals.generation,1)
			scene.rama_hud._refresh()
			receipt.passed = receipt.damage.accepted and not vitals.alive and scene.rama_hud.note.text == "RETURNING IN 3.0s"
		elif action == "respawn":
			scene.set_paused(false)
			for unused in range(60): scene.army.step_simulation(.05)
			scene.rama_hud._refresh()
			receipt.rule_inputs = {"steps":60,"delta":.05}
			receipt.passed = scene.rama_runtime.vitals.alive and scene.player.active
	else:
		return {"passed":false,"error":"Unknown capture stage"}
	if action in ["defeat","respawn"] or action.begins_with("outcome-"):
		receipt.presentation_refresh = _refresh_position(scene)
	if receipt.has("presentation_refresh"):
		receipt.passed = receipt.passed and receipt.presentation_refresh.army_unchanged and receipt.presentation_refresh.relays_unchanged and receipt.presentation_refresh.atlas_matches_player and receipt.presentation_refresh.location_matches_player
	receipt.after = _state(scene)
	return receipt

func _refresh_position(scene: Node) -> Dictionary:
	var army_before: Dictionary = scene.army.report()
	var relay_before: Dictionary = scene.relays.control.report()
	var clock_before: float = scene.ui_clock
	# The normal presentation callback updates location and the atlas together.
	# It advances its declared presentation clock only; simulation remains held.
	scene._process(.13)
	return {"delta":.13,"ui_clock_before":clock_before,"ui_clock_after":scene.ui_clock,"army_unchanged":scene.army.report()==army_before,"relays_unchanged":scene.relays.control.report()==relay_before,"atlas_matches_player":scene.map_control.hero_position==scene.player.position,"location_matches_player":scene.location_label.text==scene.district_at(scene.player.position),"location":scene.location_label.text}

func _hold(scene: Node) -> void:
	if scene.has_meta(HOLD_META): return
	var records: Array[Dictionary] = []
	for node in [scene,scene.player,scene.army]:
		records.append({"node":weakref(node),"process":node.is_processing(),"physics":node.is_physics_processing()})
		node.set_process(false)
		node.set_physics_process(false)
	scene.set_meta(HOLD_META,records)

func _release(scene: Node) -> void:
	if not scene.has_meta(HOLD_META): return
	for record in scene.get_meta(HOLD_META):
		var node: Node = record.node.get_ref()
		if is_instance_valid(node):
			node.set_process(record.process)
			node.set_physics_process(record.physics)
	scene.remove_meta(HOLD_META)

func _state(scene: Node) -> Dictionary:
	var processing := {}
	for node in [scene,scene.player,scene.army]: processing[str(node.get_path())] = {"process":node.is_processing(),"physics":node.is_physics_processing()}
	return {"army":scene.army.report(),"relays":scene.relays.control.report(),"vitals":scene.rama_runtime.vitals.report(),"tree_paused":scene.get_tree().paused,"world_paused":scene.paused,"player_position":scene.player.position,"player_active":scene.player.active,"lane":scene.lane_label.text,"objective":scene.objective_label.text,"relay_hint":scene.relay_hint.text,"outcome_heading":scene.outcome_summary.heading.text,"outcome_detail":scene.outcome_summary.detail.text,"outcome_visible":scene.outcome_summary.is_visible_in_tree(),"hud_notice":scene.rama_hud.note.text,"simulation_hold":scene.has_meta(HOLD_META),"processing":processing}
