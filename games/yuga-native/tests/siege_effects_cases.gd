extends SceneTree
## Headless real-node/mesh/audio lifecycle checks. No perceptual/render approval.
const EFFECTS := preload("res://scripts/siege_effects.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ", label)

func _event(identity: int, kind := "windup", role := "cannon_cart", team := "sun") -> Dictionary:
	return {"kind":kind,"id":identity,"role":role,"team":team,
		"origin":Vector3(0,1.3,0),"target":Vector3(0,0,18),
		"delay":(0.8 if role=="cannon_cart" else 0.55) if kind=="windup" else 0.0,
		"radius":3.0 if role=="cannon_cart" else 2.4,"damage":24.0 if role=="cannon_cart" else 22.0}

func _nodes(node: Node) -> int:
	var count := 1
	for child in node.get_children(): count += _nodes(child)
	return count

func _wait_real(seconds: float) -> void:
	var deadline := Time.get_ticks_usec() + int(seconds * 1000000.0)
	while Time.get_ticks_usec() < deadline: await process_frame

func _run() -> void:
	var source_hash := FileAccess.get_sha256("res://scripts/siege_effects.gd")
	var host := Node3D.new()
	host.position = Vector3(17,4,-11)
	root.add_child(host)
	var fx = EFFECTS.new()
	fx.configure(0.0)
	host.add_child(fx)
	await process_frame
	fx.set_process(false)
	_check("configure before ready is silent with six reusable voices",fx.report().muted and fx.report().voice_pool==6 and fx.report().playing_voices==0 and _nodes(fx)==7)
	var pcm_valid := true
	for cue: String in EFFECTS.CUE_NAMES:
		var stream: AudioStreamWAV = fx._streams[cue]
		pcm_valid = pcm_valid and stream!=null and stream.format==AudioStreamWAV.FORMAT_16_BITS and not stream.stereo and stream.mix_rate==24000
		if stream: pcm_valid = pcm_valid and stream.data==FileAccess.get_file_as_bytes(EFFECTS.AUDIO_BASE+cue+".wav").slice(44)
	_check("four imported cues retain exact verified mono PCM",pcm_valid)
	var event := _event(1)
	var unchanged := event.duplicate(true)
	fx.handle_event(event)
	_check("muted windup retains full radius visible ground ring",fx.report().windups==1 and fx.report().playing_voices==0 and fx._effects[0].ring.visible and is_equal_approx(fx.report().states[0].radius,3.0))
	_check("target world coordinates ignore transformed owner",fx._effects[0].node.global_position.is_equal_approx(event.target+Vector3.UP*.055))
	_check("presentation never mutates received damage event",event==unchanged)
	fx.handle_event(event)
	_check("duplicate windup cannot allocate another warning",fx.report().active_events==1 and fx.report().rejected==1)
	fx.handle_event(_event(2,"windup","royal_chariot","moon"))
	_check("Sun and Moon have distinct geometric marker grammar",fx.report().states[0].glyph_count==8 and fx.report().states[1].glyph_count==4 and fx._effects[0].glyph.mesh!=fx._effects[1].glyph.mesh)
	fx._process(.4)
	_check("arc appears only after committed preparation",fx.report().states[0].projectile_visible and fx.report().states[0].projectile_position.y>0.0 and fx.report().states[0].projectile_position.is_finite())
	var origin := Vector3(2,1.3,-4)
	var target := Vector3(-3,0,15)
	_check("arc has exact endpoints and finite raised midpoint",EFFECTS.arc_position(origin,target,0.0).is_equal_approx(origin) and EFFECTS.arc_position(origin,target,1.0).is_equal_approx(target) and EFFECTS.arc_position(origin,target,.5).y>maxf(origin.y,target.y))
	fx.clear()
	var quick := _event(3)
	quick.delay = .1
	fx.handle_event(quick)
	fx._process(.06)
	_check("short windup retains charge and omits misleading arc",fx.report().windups==1 and not fx.report().states[0].projectile_visible and fx._effects[0].charge.visible)
	fx.clear()
	fx.handle_event(_event(4))
	fx.handle_event(_event(4,"impact"))
	_check("impact atomically replaces matching windup",fx.report().windups==0 and fx.report().impacts==1 and fx.report().active_events==1)
	fx.handle_event(_event(4,"impact"))
	fx.handle_event(_event(4))
	_check("repeated impact and late windup are ignored",fx.report().active_events==1 and fx.report().history_size==1)
	fx._process(.49)
	_check("impact aftermath expires with no orphan nodes",fx.report().active_events==0 and _nodes(fx)==7)
	fx.handle_event(_event(5))
	fx._process(1.16)
	_check("missing terminal receipt has bounded fallback cleanup",fx.report().active_events==0 and _nodes(fx)==7)
	fx.clear()
	for identity in range(1,10001): fx.handle_event(_event(identity))
	_check("ten thousand windups cap at thirty-two live warnings",fx.report().active_events==32 and fx.report().peak_events==32 and fx.report().playing_voices==0 and _nodes(fx)==167,{"nodes":_nodes(fx),"active_events":fx.report().active_events})
	fx.handle_event(_event(1,"impact"))
	fx.handle_event(_event(10001))
	_check("capacity preserves danger before impact decoration",fx.report().active_events==32 and fx.report().windups==32 and fx.report().impacts==0)
	fx.clear()
	for identity in range(1,501): fx.handle_event(_event(identity,"impact"))
	_check("impact flood bounds visuals and duplicate history",fx.report().active_events<=32 and fx.report().history_size==64 and _nodes(fx)<=103)
	fx.clear()
	fx.clear()
	_check("double clear is immediate and idempotent",fx.report().active_events==0 and fx.report().history_size==0 and fx.report().playing_voices==0 and _nodes(fx)==7)
	var malformed := [
		["missing id","id",null],["float id","id",1.0],["negative id","id",-2],
		["unknown kind","kind","release"],["unknown role","role","../../other"],["unknown team","team","neutral"],
		["array origin","origin",[0,1,0]],["NaN origin","origin",Vector3(NAN,0,0)],["infinite target","target",Vector3(0,0,INF)],
		["huge position","origin",Vector3(20000,0,0)],["unagreed elevated target","target",Vector3(0,4,18)],
		["NaN delay","delay",NAN],["infinite radius","radius",INF],["negative damage","damage",-1.0],
		["zero radius","radius",0.0],["huge radius","radius",21.0],["zero delay","delay",0.0],
		["huge delay","delay",11.0],["bool damage","damage",true],["string delay","delay",".8"],
		["bad cancellation type","cancelled",1],["cancelled windup","cancelled",true],["unknown field","surprise",0]]
	var rejects: int = fx.report().rejected
	for fixture in malformed:
		var invalid := _event(1)
		invalid[fixture[1]] = fixture[2]
		fx.handle_event(invalid)
		_check("reject "+fixture[0],fx.report().active_events==0 and fx.report().rejected==rejects+1)
		rejects = fx.report().rejected
	var bad_impact := _event(1,"impact")
	bad_impact.delay = .3
	fx.handle_event(bad_impact)
	_check("impact cannot invent a second windup delay",fx.report().active_events==0 and fx.report().rejected==rejects+1)
	fx.handle_event(_event(1))
	var age: float = fx.report().states[0].age
	fx._process(NAN)
	fx._process(-1.0)
	_check("nonfinite and negative elapsed time cannot corrupt effect",fx.report().states[0].age==age)
	fx.handle_event({"kind":"reset","id":0,"radius":NAN})
	_check("malformed reset is rejected without destroying valid warning",fx.report().windups==1)
	fx.handle_event({"kind":"reset","id":0,"role":"","team":"","origin":Vector3.ZERO,"target":Vector3.ZERO,"delay":0.0,"radius":0.0,"damage":0.0})
	_check("full neutral army reset clears presentation",fx.report().active_events==0 and _nodes(fx)==7)
	fx.set_volume(.7)
	fx.handle_event(_event(1))
	_check("valid audible windup starts bounded original cue",fx.report().playing_voices==1 and fx.report().played_cues>0)
	var played: int = fx.report().played_cues
	var cancel := _event(1,"impact")
	cancel.cancelled = true
	cancel.damage = 0.0
	fx.handle_event(cancel)
	_check("cancellation removes warning and its voice without impact",fx.report().active_events==0 and fx.report().playing_voices==0 and fx.report().played_cues==played and fx.report().cancelled>0)
	fx.clear()
	fx.handle_event(_event(2,"windup","royal_chariot","moon"))
	fx.set_suspended(true)
	age = fx.report().states[0].age
	fx._process(.2)
	fx.handle_event(_event(3))
	_check("overview suspension freezes effects and pending voice start",fx.report().states[0].age==age and fx.report().active_events==1 and fx.report().paused_voices==1 and fx.report().playing_voices==0)
	fx.set_suspended(false)
	_check("overview resume releases owned paused voice",fx.report().paused_voices==0 and fx.report().playing_voices==1)
	paused = true
	await create_timer(.025,true).timeout
	fx._process(.2)
	fx.handle_event(_event(4))
	_check("scene pause freezes visual time and incoming events",fx.report().states[0].age==age and fx.report().active_events==1 and fx.report().tree_paused)
	_check("scene pause stops pending or active audio with retained position",fx.report().playing_voices==0 and fx.report().paused_voices==1)
	fx.set_volume(0.0)
	_check("mute while paused stops audio but retains warning",fx.report().playing_voices==0 and fx.report().windups==1)
	fx.set_volume(1.0)
	_check("unmute does not replay stale paused cue",fx.report().playing_voices==0 and fx.report().windups==1)
	fx.handle_event({"kind":"reset","id":0})
	_check("reset while paused clears all transient presentation",fx.report().active_events==0 and fx.report().playing_voices==0)
	paused = false
	fx.clear()
	for role in ["cannon_cart","royal_chariot"]:
		fx.handle_event(_event(1 if role=="cannon_cart" else 2,"windup",role))
		fx.handle_event(_event(1 if role=="cannon_cart" else 2,"impact",role))
	_check("both role impacts play distinct semantic cues",fx.report().playing_voices==2 and fx.report().impacts==2)
	var voice_peak: int = fx.report().playing_voices
	for cycle in range(4):
		await _wait_real(.06)
		for role in ["cannon_cart","royal_chariot"]:
			fx.handle_event(_event(10+cycle*2+(1 if role=="cannon_cart" else 0),"impact",role))
		voice_peak = maxi(voice_peak,fx.report().playing_voices)
	_check("voice overflow reuses pool without node accumulation",voice_peak<=6 and fx.report().voice_pool==6 and _nodes(fx)<=103,{"peak_voices":voice_peak})
	fx.set_volume(-1.0)
	_check("negative volume clamps to a complete mute",fx.report().muted and fx.report().playing_voices==0)
	fx.set_volume(NAN)
	_check("NaN volume uses finite modest default",is_equal_approx(fx.report().volume,.35))
	fx.set_volume(INF)
	_check("infinite volume uses finite modest default",is_equal_approx(fx.report().volume,.35))
	fx.set_volume(99.0)
	_check("high volume cannot exceed declared per-voice gain",fx.report().volume==1.0 and fx._voices[0].volume_db<=-12.0 and fx._voices[0].max_db<=-12.0)
	var stable_children := host.get_child_count()
	for repeat in range(20):
		fx.clear()
		fx.handle_event(_event(1))
		fx.handle_event({"kind":"reset","id":0})
	_check("twenty reset cycles leave no presentation accumulation",_nodes(fx)==7 and host.get_child_count()==stable_children)
	var released: WeakRef = weakref(fx)
	host.queue_free()
	await process_frame
	await process_frame
	await _wait_real(.09)
	_check("scene destruction releases all owned effects and players",not is_instance_valid(released.get_ref()))
	_check("runtime source remained unchanged during tests",FileAccess.get_sha256("res://scripts/siege_effects.gd")==source_hash)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"checks":checks,
		"sources":{"runtime":source_hash,"runner":FileAccess.get_sha256(get_script().resource_path),"audio_provenance":FileAccess.get_sha256("res://assets/audio/siege/provenance.json")},
		"scope":"Headless real Node3D/mesh/audio states, finite arcs, validated events, 10000-event flood, bounded resources, pause/mute/cancel/reset/disposal. No audible-quality, actual rendered readability, OS focus or hardware-performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	print("YUGA_SIEGE_EFFECTS_CASES ",JSON.stringify(report))
	quit(0 if passed else 1)
