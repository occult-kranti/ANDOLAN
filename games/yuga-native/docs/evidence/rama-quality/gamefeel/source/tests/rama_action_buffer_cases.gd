extends SceneTree
## Counterexamples against the real 20 Hz kit. No renderer or human-feel claim.
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Buffer = preload("res://scripts/rama_action_buffer.gd")
var army
var kit
var buffer
var checks: Array = []
var events: Array = []
var requests: Array = []
var dispatches: Array = []
var sources: Dictionary = {}
var output := ""
var edge := 0
var eligible := true
var eligibility_reason := ""
var origin := Vector3.ZERO
var aim := Vector3(0, 0, 1)
var reenter_request := false
var reenter_sample := false
var reset_sample := false
var reset_begin := false
var reenter_feedback := false
var reenter_clear := false
var bad_request_result := false
var nested_result: Dictionary = {}

func _initialize() -> void: call_deferred("run")

func check(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label, "passed":passed, "evidence":evidence})
	if not passed: push_error("ACTION BUFFER FAILED: " + label)

func advance(seconds: float) -> void:
	var left := seconds
	while left > 1e-8:
		var delta := minf(.05, left)
		army.step_simulation(delta)
		left -= delta

func immediate(id: String) -> Dictionary:
	requests.append({"id":id, "time_s":kit.elapsed, "origin":origin, "forward":aim})
	if reenter_request:
		reenter_request = false
		edge += 1
		nested_result = buffer.push_input("piercing_dawn", edge)
	if bad_request_result: return {}
	return kit.request_ability(id, origin, aim, origin + aim * 4)

func state() -> Dictionary:
	if reenter_sample:
		reenter_sample = false
		edge += 1
		nested_result = buffer.push_input("piercing_dawn", edge)
	if reset_sample:
		reset_sample = false
		kit.reset("eligibility callback reset")
	return {"eligible":eligible, "reason":eligibility_reason}

func tap(id: String) -> Dictionary:
	edge += 1
	return buffer.push_input(id, edge)

func cast(id := "kodanda") -> Dictionary:
	return kit.request_ability(id, origin, aim, origin + aim * 4)

func count_begin(id: String) -> int:
	return events.filter(func(event): return event.kind == "begin" and event.ability_id == id).size()

func fresh() -> void:
	paused = false
	kit.set_suspended(false)
	army.reset()
	for unit in army.units.duplicate(): army.units.erase(unit); unit.free()
	army._rebuild_buckets()
	events.clear(); requests.clear(); dispatches.clear(); nested_result.clear()
	eligible = true; eligibility_reason = ""; origin = Vector3.ZERO; aim = Vector3(0, 0, 1)
	reenter_request = false; reenter_sample = false; reset_sample = false; reset_begin = false
	reenter_feedback = false; reenter_clear = false; bad_request_result = false

func queue_from_primary(id := "dawn_volley") -> Dictionary:
	cast(); advance(.30)
	return tap(id)

func on_event(event: Dictionary) -> void:
	events.append(event.duplicate(true))
	if reset_begin and event.kind == "begin" and event.ability_id == "dawn_volley":
		reset_begin = false
		kit.reset("begin listener reset")

func on_dispatch(result: Dictionary) -> void:
	dispatches.append(result.duplicate(true))
	if reenter_feedback:
		reenter_feedback = false
		edge += 1
		nested_result = buffer.push_input("piercing_dawn", edge)

func on_intent_changed() -> void:
	if reenter_clear:
		reenter_clear = false
		edge += 1
		nested_result = buffer.push_input("piercing_dawn", edge)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	for path in ["res://scripts/rama_action_buffer.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/lane_army.gd", "res://assets/design/rama-ability-kit.json", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	army = Army.new(); army.visual_enabled = false; root.add_child(army); army.set_physics_process(false)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	check("Actual lane authority configures", army.configure(manifest, null))
	kit = Kit.new(); root.add_child(kit); kit.ability_event.connect(on_event)
	check("Actual Rama kit configures", kit.configure(army))
	buffer = Buffer.new(); root.add_child(buffer)
	check("Invalid source cannot configure a buffer", not buffer.configure(null, immediate, state))
	check("Buffer configures once around the existing immediate API", buffer.configure(kit, immediate, state) and not buffer.configure(kit, immediate, state))
	buffer.dispatch_finished.connect(on_dispatch)
	buffer.intent_changed.connect(on_intent_changed)
	check("Scope is one 120 ms Q/X intent", buffer.WINDOW_S == .12 and buffer.ABILITIES == ["piercing_dawn", "dawn_volley"] and buffer.report().pending.is_empty())

	fresh()
	var result := tap("piercing_dawn")
	check("Ready Q takes the ordinary immediate path", result.accepted and not result.queued and not result.from_buffer and requests.size() == 1 and count_begin("piercing_dawn") == 1)
	check("A direct kit request remains immediately busy-rejected", not cast("dawn_volley").accepted and kit.report().rejected_casts == 1 and buffer.report().pending.is_empty())
	result = tap("dawn_volley")
	check("A windup press is rejected instead of silently armed", not result.accepted and not result.queued and buffer.report().pending.is_empty() and requests.size() == 1)
	advance(.70)
	result = tap("dawn_volley")
	check("Recovery outside the 120 ms window is rejected", not result.accepted and not result.queued and buffer.report().pending.is_empty())
	advance(.15)
	var before_accepted: int = kit.accepted_casts
	var before_rejected: int = kit.rejected_casts
	result = tap("dawn_volley")
	check("Final 100 ms admits one explicit queued intent", not result.accepted and result.queued and buffer.report().pending.ability_id == "dawn_volley", {"authority_s":kit.elapsed, "pending":buffer.report().pending})
	check("Queuing emits no fake begin and spends no cooldown", kit.accepted_casts == before_accepted and kit.rejected_casts == before_rejected and kit.report().cooldowns.dawn_volley == 0 and count_begin("dawn_volley") == 0 and requests.size() == 1)
	var queued_at: float = buffer.report().pending.queued_at
	var expires_at: float = buffer.report().pending.expires_at
	check("Held and autorepeat edges cannot refresh a pending intent", not buffer.push_input("dawn_volley", edge, false).queued and not buffer.push_input("dawn_volley", edge + 100, true).queued and buffer.report().pending.queued_at == queued_at and buffer.report().pending.expires_at == expires_at)
	advance(.05)
	check("An intent cannot dispatch before actual recovery", requests.size() == 1 and count_begin("dawn_volley") == 0 and kit.report().action_locked)
	origin = Vector3(.5, 0, 0); aim = Vector3.RIGHT
	advance(.05)
	check("Recovery dispatches exactly one normal request at the army tick", requests.size() == 2 and count_begin("dawn_volley") == 1 and dispatches.size() == 2 and dispatches[-1].accepted and dispatches[-1].from_buffer and is_equal_approx(requests[-1].time_s, .95) and buffer.report().pending.is_empty(), {"request":requests[-1], "result":dispatches[-1]})
	check("Buffered execution samples current position and aim", requests[-1].origin == origin and requests[-1].forward == aim and events[-1].kind == "tick")
	advance(.10)
	check("A queued tap never repeats on following ticks", requests.size() == 2 and count_begin("dawn_volley") == 1)

	fresh()
	queue_from_primary()
	result = tap("piercing_dawn")
	check("A newer eligible deliberate press replaces the single intent", result.queued and buffer.report().pending.ability_id == "piercing_dawn")
	advance(.10)
	check("Only the newest intent executes", requests.size() == 1 and requests[0].id == "piercing_dawn" and count_begin("dawn_volley") == 0 and count_begin("piercing_dawn") == 1)

	fresh()
	queue_from_primary()
	check("E and C are never buffered without shared geometry preflight", not tap("measured_step").queued and not tap("guardian_circle").queued and buffer.report().pending.ability_id == "dawn_volley")
	advance(.10)
	check("Excluded E/C input does not silently replace an admitted Q/X tap", requests.size() == 1 and requests[0].id == "dawn_volley")

	fresh()
	cast("piercing_dawn"); advance(.95)
	cast(); advance(.30)
	result = tap("piercing_dawn")
	check("Cooldown rejection never becomes a queued intent", not result.accepted and not result.queued and buffer.report().pending.is_empty() and requests.is_empty())
	advance(.10)
	check("A cooldown-blocked tap is not retried after recovery", requests.is_empty())

	for reason in ["Not grounded", "Aim must be finite", "Reloading", "Legacy invocation preparing", "Actor inactive", "Actor defeated", "Gameplay modal visible"]:
		fresh(); cast(); advance(.30)
		eligible = false; eligibility_reason = reason
		result = tap("dawn_volley")
		check("Current eligibility rejects: " + reason, not result.accepted and not result.queued and result.reason == reason and buffer.report().pending.is_empty())

	for reason in ["Pause", "Gameplay modal", "Window focus lost", "Defeated", "Hit reaction", "Teleport", "Explicit player reset"]:
		fresh(); queue_from_primary()
		buffer.cancel_pending(reason)
		advance(.10)
		check("Explicit lifecycle clear prevents execution after: " + reason, requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); queue_from_primary()
	paused = true
	check("Tree pause itself clears pending input", buffer.report().pending.is_empty())
	paused = false; advance(.10)
	check("Resume cannot replay a pre-pause tap", requests.is_empty())

	fresh(); queue_from_primary()
	eligible = false; eligibility_reason = "Actor died before recovery"
	advance(.10); eligible = true; advance(.10)
	check("Eligibility is sampled again at dispatch and is never retried", requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); queue_from_primary()
	kit.set_suspended(true)
	check("Suspended source rejects new input", not tap("piercing_dawn").queued)
	buffer.cancel_pending("Runtime suspended")
	kit.set_suspended(false); advance(.10)
	check("Suspension does not replay an old tap on resume", requests.is_empty())

	fresh(); queue_from_primary()
	army.reset(); advance(.50)
	check("Actual army reset discards the previous generation", requests.is_empty() and buffer.report().pending.is_empty() and kit.generation > 0)

	fresh(); queue_from_primary()
	kit.cancel_active("hit interrupt"); advance(.50)
	check("Actual cancellation cannot shortcut recovery into a new cast", requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); queue_from_primary()
	kit.ability_event.disconnect(buffer._on_event)
	advance(.20)
	kit.ability_event.connect(buffer._on_event)
	advance(.05)
	check("A missed recovery callback cannot cause a late cast", requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); cast()
	var stale_begin: Dictionary = events[0].duplicate(true)
	army.reset(); events.clear()
	queue_from_primary()
	stale_begin.kind = "recovery"
	kit.ability_event.emit(stale_begin)
	check("Stale generation recovery cannot dispatch or erase current intent", requests.is_empty() and not buffer.report().pending.is_empty())
	stale_begin.kind = "reset"
	kit.ability_event.emit(stale_begin)
	check("A stale reset event cannot erase a current-generation intent", requests.is_empty() and not buffer.report().pending.is_empty())
	advance(.10)
	check("A current genuine recovery still dispatches after stale input", requests.size() == 1)

	fresh(); queue_from_primary()
	reenter_request = true
	advance(.10)
	check("Request callback cannot reenter and create a second cast", not nested_result.get("accepted", true) and not nested_result.get("queued", true) and requests.size() == 1 and count_begin("dawn_volley") == 1 and count_begin("piercing_dawn") == 0)

	fresh(); queue_from_primary()
	reenter_feedback = true
	advance(.10)
	check("Dispatch feedback cannot reenter and create another intent", not nested_result.get("accepted", true) and not nested_result.get("queued", true) and requests.size() == 1 and buffer.report().pending.is_empty())

	fresh(); cast(); advance(.30)
	reenter_sample = true
	result = tap("dawn_volley")
	check("Eligibility callback cannot recursively enqueue another edge", result.queued and not nested_result.get("queued", true) and buffer.report().pending.ability_id == "dawn_volley")
	buffer.cancel_pending("test close")

	fresh(); queue_from_primary()
	reenter_clear = true
	buffer.cancel_pending("Modal opened")
	check("Clear feedback cannot reenter with a new intent", not nested_result.get("accepted", true) and not nested_result.get("queued", true) and requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); cast(); advance(.30)
	reset_sample = true
	result = tap("dawn_volley")
	check("Reset during eligibility invalidates the whole input request", not result.accepted and not result.queued and requests.is_empty() and buffer.report().pending.is_empty())

	fresh(); queue_from_primary()
	reset_begin = true
	advance(.10)
	check("Reset inside a genuine begin cannot leave a pending replay", requests.size() == 1 and dispatches.size() == 1 and not dispatches[0].accepted and buffer.report().pending.is_empty() and not kit.report().action_locked)
	advance(.50)
	check("A reentrant reset never retries the consumed input", requests.size() == 1 and kit.report().casts.is_empty())

	fresh(); queue_from_primary()
	bad_request_result = true
	advance(.10)
	check("An invalid request result does not fabricate acceptance", requests.size() == 1 and not dispatches[0].get("accepted", false) and buffer.report().pending.is_empty() and count_begin("dawn_volley") == 0)

	fresh()
	check("Zero, negative and older edge tokens never dispatch", not buffer.push_input("dawn_volley", 0).accepted and not buffer.push_input("dawn_volley", -1).accepted and not buffer.push_input("dawn_volley", edge - 1).accepted and requests.is_empty())
	var unchanged := true
	for path in sources: unchanged = unchanged and FileAccess.get_sha256(path) == sources[path]
	check("Authority and buffer sources remained unchanged during this fixture", unchanged)
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed":passed, "checks":checks, "sources":sources, "buffer":buffer.report(), "scope":"Real 20 Hz lane army and unchanged Rama kit, isolated explicit edge/eligibility callbacks. No renderer, OS input, human feel, audio, network or hardware performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report, "\t") + "\n")
		else: passed = false
	army.queue_free(); kit.queue_free(); buffer.queue_free()
	for unused in 4: await process_frame
	quit(0 if passed else 1)
