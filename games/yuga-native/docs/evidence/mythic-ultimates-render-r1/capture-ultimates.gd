extends SceneTree
## Actual rendered original VFX with scripted authority-shaped events. No gameplay damage.
const FX := preload("res://scripts/ultimate_effects.gd")
const FPS := 30
const REQUIRED_IMPORTS := ["res://assets/heroes/rama-production.glb"]
var capture_size := Vector2i(1280,720)
var output_path := ""
var sources := {}
var imports := {}
var frames: Array = []
var stills: Array = []
var variants: Array = []
var events: Array = []
var failure := ""
var started_ms := Time.get_ticks_msec()
var take_start_tick := 0
var take_ticks := 0
var studio: Node3D
var fx: Node3D
var hero: Node3D
var camera: Camera3D
var footer: Label
var rules: Dictionary = {}
var codex: Dictionary = {}
var next_id := 0
var outcomes := {"begin":false,"release":false,"contact":false,"expired":false,"persistent_zone_cancelled_for_take_end":false}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output_path = arg.trim_prefix("--output=")
		else:
			push_error("Unknown argument: "+arg)
			quit(1)
			return
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path) or FileAccess.file_exists(output_path):
		push_error("Choose a new absolute output directory")
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name() == "headless" or RenderingServer.get_current_rendering_method() != "forward_plus":
		_fail("Actual Forward+ display required")
		return
	if Engine.physics_ticks_per_second != 60 or not is_equal_approx(Engine.time_scale,1.0):
		_fail("Requires60Hz physics and time_scale1")
		return
	sources = _source_hashes()
	for path in REQUIRED_IMPORTS:
		if not _validate_import(path):
			_finish(false)
			return
	for rule in JSON.parse_string(FileAccess.get_file_as_string("res://assets/design/native-ultimate-rules.json")).rules:rules[rule.hero_id] = rule
	for entry in JSON.parse_string(FileAccess.get_file_as_string("res://assets/design/hero-codex.json")).heroes:codex[entry.id] = entry.abilities[2]
	root.size = capture_size
	root.content_scale_size = capture_size
	root.msaa_3d = Viewport.MSAA_2X
	root.title = "YUGA — Scripted Invocation VFX Studies"
	root.show()
	_make_studio()
	await _draw_frames(3)
	# Fourteen individually staged warning/motif studies, prior to the continuous take.
	for id in FX.HEROES:
		fx.reset()
		fx.set_process(false)
		fx.set_options({"reduced_effects":false,"reduced_motion":false})
		var event := _event(id,Vector3.ZERO)
		if not fx.consume_event(event):
			_fail("Fixture begin rejected: "+id)
			return
		var age: float = event.timing.windup_s*.85
		fx.step(age)
		var direction := Vector3(1.0,.85,-1.0).normalized()
		var target: Vector3 = event.geometry.center+Vector3.UP*.6
		var distance := 21.0
		if event.geometry.kind in ["sector","projectile_volley"]:
			target = Vector3(0,1,9)
			distance = 42 if event.geometry.kind == "sector" and event.geometry.range_m > 18 else 32
		if event.geometry.kind == "summon_pair":distance = 12
		camera.global_position = target+direction*distance
		camera.look_at(target)
		hero.position = Vector3.ZERO
		footer.text = "%s · %s\nLocked warning / original motif · scripted presentation through the Rama avatar"%[id.capitalize(),rules[id].name]
		await _draw_frames(2)
		stills.append({"hero_id":id,"effect_id":event.effect_id,"codex_shape":codex[id].native_demo.shape,"sample_age_s":age,"image":_save_image("still-"+id+".png"),"fx":_fx_summary()})
	for mode in ["low-effects","reduced-motion","four-overlap"]:
		fx.reset()
		fx.set_options({"reduced_effects":mode=="low-effects","reduced_motion":mode=="reduced-motion"})
		var heroes := ["sita"] if mode != "four-overlap" else ["sita","ravana","ulupi","karna"]
		for i in range(heroes.size()):
			var offset := Vector3((i%2)*10-5,0,(i/2)*10-5) if heroes.size()>1 else Vector3.ZERO
			fx.consume_event(_event(heroes[i],offset))
		fx.step(.6)
		camera.global_position = Vector3(22,22,-26) if heroes.size()>1 else Vector3(12,12,-15)
		camera.look_at(Vector3(0,1,0))
		footer.text = "Invocation visual stress · "+mode+"\nExact warnings retained · no gameplay cooldown bypass"
		await _draw_frames(2)
		variants.append({"id":mode,"image":_save_image("still-"+mode+".png"),"fx":_fx_summary()})
	fx.reset()
	fx.set_options({"reduced_effects":false,"reduced_motion":false})
	camera.global_position = Vector3(24,18,-30)
	camera.look_at(Vector3(0,1,6))
	hero.position = Vector3(-5,0,-7)
	footer.text = "Dawn Volley + Shelter of Mithila · scripted VFX sequence\nNo damage simulation / zone cancelled at take end / silent evidence video"
	await _draw_frames(2)
	var attack := _event("rama",Vector3(-5,0,-7))
	var zone := _event("sita",Vector3(6,0,1))
	var attack_sequence := 0
	var zone_sequence := 0
	var prior_tick := Engine.get_physics_frames()
	var prior_draw := Engine.get_frames_drawn()
	take_start_tick = prior_tick
	fx.set_process(true)
	for index in range(120):
		var time_s := index/float(FPS)
		if index==0:
			_emit(attack,"begin",attack_sequence,time_s)
			_emit(zone,"begin",zone_sequence,time_s)
			outcomes.begin = true
		if index==24:
			zone_sequence += 1
			_emit(zone,"release",zone_sequence,time_s)
			zone_sequence += 1
			_emit(zone,"impact",zone_sequence,time_s)
		if index==30:
			attack_sequence += 1
			_emit(attack,"release",attack_sequence,time_s)
			outcomes.release = true
		for projectile_index in range(3):
			if index==[36,38,40][projectile_index]:
				attack_sequence += 1
				var contact := attack.duplicate(true)
				contact.projectile_index = projectile_index
				var arrow: Dictionary = attack.geometry.projectiles[projectile_index]
				contact.contact_position = arrow.origin+arrow.forward*((time_s-1.0)*62.0)
				contact.reason = "scripted_study_contact"
				_emit(contact,"impact",attack_sequence,time_s)
				outcomes.contact = true
		if index==76:
			attack_sequence += 1
			_emit(attack,"end",attack_sequence,time_s)
			outcomes.expired = true
		if index==114:
			zone_sequence += 1
			_emit(zone,"cancel",zone_sequence,time_s)
			outcomes.persistent_zone_cancelled_for_take_end = true
		await _draw_frames(1)
		var tick := Engine.get_physics_frames()
		var draw := Engine.get_frames_drawn()
		var summary := _fx_summary()
		if tick-prior_tick != 2 or draw<=prior_draw or not summary.finite or not failure.is_empty():
			_fail("Sequential capture clocks/state failed at %d"%index)
			return
		var phases: Array = []
		for state in fx.report().casts:phases.append(state.phase)
		frames.append({"index":index,"presentation_seconds":time_s,"sample_end_simulation_seconds":float(tick-take_start_tick)/60.0,"physics_tick":tick,"physics_tick_delta":tick-prior_tick,"render_frame":draw,"finite":true,"effect_phases":phases,"image":_save_image("frame-%05d.png"%index),"fx":summary})
		prior_tick = tick
		prior_draw = draw
		if index%30==0:print("YUGA_ULTIMATE_CAPTURE ",index)
	take_ticks = Engine.get_physics_frames()-take_start_tick
	fx.set_process(false)
	if sources != _source_hashes():
		_fail("Runtime source set/hash changed during capture")
		return
	if fx.report().active != 0:
		_fail("Fixture failed to retire all presentations")
		return
	_finish(true)

func _event(id: String, origin: Vector3) -> Dictionary:
	next_id += 1
	var rule: Dictionary = rules[id].duplicate(true)
	var g: Dictionary = rule.geometry
	g.origin = origin
	g.center = origin+Vector3(0,0,6) if g.anchor=="ground_target" else origin
	g.forward = Vector3(0,0,1)
	if g.kind == "projectile_volley":
		g.projectiles = []
		for i in range(g.yaw_offsets_rad.size()):g.projectiles.append({"index":i,"origin":origin,"forward":g.forward.rotated(Vector3.UP,g.yaw_offsets_rad[i])})
	if g.kind == "summon_pair":g.placements = [origin+Vector3(-1.3,0,0),origin+Vector3(1.3,0,0)]
	return {"schema":1,"kind":"begin","epoch":1,"cast_id":next_id,"event_seq":0,"hero_id":id,"effect_id":rule.effect_id,"team":"sun","time_s":0.0,"origin":origin,"forward":g.forward,"target":g.center,"timing":rule.timing,"geometry":g,"receipts":[],"reason":"scripted_visual_fixture"}

func _emit(base: Dictionary, kind: String, seq: int, at: float) -> void:
	var event := base.duplicate(true)
	event.kind = kind
	event.event_seq = seq
	event.time_s = at
	if not fx.consume_event(event):failure = "Scripted event rejected: "+str([base.hero_id,kind,seq,at])
	events.append({"hero_id":event.hero_id,"kind":kind,"time_s":at,"cast_id":event.cast_id,"event_seq":seq,"projectile_index":event.get("projectile_index",-1),"reason":event.reason})

func _fx_summary() -> Dictionary:
	var full: Dictionary = fx.report()
	var result := {}
	for key in ["active","finite","nodes","triangles","lights","particles","voices","reduced_effects","reduced_motion"]:result[key] = full[key]
	return result

func _make_studio() -> void:
	studio = Node3D.new()
	root.add_child(studio)
	current_scene = studio
	var environment := WorldEnvironment.new()
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("172b3b")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("b8c6db")
	env.ambient_light_energy = .65
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.glow_enabled = false
	environment.environment = env
	studio.add_child(environment)
	var key := DirectionalLight3D.new()
	key.rotation_degrees = Vector3(-55,-35,0)
	key.light_color = Color("ffe8c5")
	key.light_energy = 1.4
	key.shadow_enabled = true
	studio.add_child(key)
	var floor_ := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(90,90)
	floor_.mesh = plane
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("344953")
	mat.roughness = .95
	floor_.material_override = mat
	studio.add_child(floor_)
	hero = load(REQUIRED_IMPORTS[0]).instantiate()
	studio.add_child(hero)
	var animation := _find_animation(hero)
	if animation:
		for name_ in animation.get_animation_list():
			if str(name_).get_file().to_lower()=="idle":
				animation.play(name_)
				animation.seek(.2,true)
				animation.pause()
	camera = Camera3D.new()
	camera.fov = 52
	camera.far = 160
	studio.add_child(camera)
	camera.make_current()
	fx = FX.new()
	studio.add_child(fx)
	fx.set_process(false)
	var ui := CanvasLayer.new()
	studio.add_child(ui)
	var title := Label.new()
	title.position = Vector2(24,20)
	title.text = "YUGA  /  ORIGINAL INVOCATION STUDIES"
	title.add_theme_font_size_override("font_size",24)
	ui.add_child(title)
	footer = Label.new()
	footer.position = Vector2(24,646)
	footer.add_theme_font_size_override("font_size",19)
	footer.add_theme_color_override("font_outline_color",Color("07131e"))
	footer.add_theme_constant_override("outline_size",5)
	ui.add_child(footer)

func _find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:return node
	for child in node.get_children():
		var found := _find_animation(child)
		if found:return found
	return null

func _draw_frames(count: int) -> void:
	for index in count:
		await process_frame
		await RenderingServer.frame_post_draw

func _save_image(filename: String) -> Dictionary:
	var rendered := root.get_texture().get_image()
	if rendered.is_empty() or rendered.get_size() != capture_size:
		failure = "Renderer did not produce the requested %dx%d image" % [capture_size.x, capture_size.y]
		return {}
	var path := output_path.path_join(filename)
	if FileAccess.file_exists(path) or rendered.save_png(path) != OK:
		failure = "Image save refused or failed: " + filename
		return {}
	return {"file":filename,"sha256":FileAccess.get_sha256(path),"width":capture_size.x,"height":capture_size.y,
		"render_frame":Engine.get_frames_drawn(),
		"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
		"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)}

func _source_hashes() -> Dictionary:
	var paths: Array[String] = ["res://project.godot","res://tools/capture-ultimates.gd","res://tools/run-ultimate-capture.py","res://tools/run-traversal-capture.py","res://art/world/confluence-map.json"]
	for directory in ["res://scripts","res://scenes","res://assets","res://shaders"]:
		_collect(directory,paths)
	paths.sort()
	var result := {}
	for path in paths:
		result[path] = FileAccess.get_sha256(path) if FileAccess.file_exists(path) else "MISSING"
	return result

func _collect(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path): paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path): _collect(path.path_join(name),paths)

func _validate_import(path: String) -> bool:
	var config := ConfigFile.new()
	if config.load(path + ".import") != OK:
		failure = "Missing import metadata: " + path
		return false
	var imported: String = config.get_value("remap","path","")
	var checksum := imported.get_basename() + ".md5"
	if not FileAccess.file_exists(imported) or not FileAccess.file_exists(checksum):
		failure = "Missing imported resource: " + path
		return false
	var pattern := RegEx.new()
	var stamp := FileAccess.get_file_as_string(checksum)
	for item in [["source_md5",path],["dest_md5",imported]]:
		pattern.compile(String(item[0]) + '="([a-f0-9]+)"')
		var match_ := pattern.search(stamp)
		if not match_ or match_.get_string(1) != FileAccess.get_md5(item[1]):
			failure = "Stale imported resource: " + path
			return false
	imports[path] = {"fresh":true,"imported":imported,"sha256":FileAccess.get_sha256(imported)}
	return true

func _normal(value):
	if value is Vector3: return [value.x,value.y,value.z]
	if value is Vector2: return [value.x,value.y]
	if value is Dictionary:
		var result := {}
		for key in value: result[key] = _normal(value[key])
		return result
	if value is Array:
		var result := []
		for item in value: result.append(_normal(item))
		return result
	return value


func _fail(message: String) -> void:
	failure = message
	_finish(false)

func _finish(success: bool) -> void:
	var report := {"schema":1,"kind":"actual-staged-native-ultimate-vfx","gameplay_applied":false,"complete":success,"failure":failure,"fps":FPS,"expected_frames":120,"width":capture_size.x,"height":capture_size.y,"physics_hz":Engine.physics_ticks_per_second,"time_scale":Engine.time_scale,"take_physics_ticks":take_ticks,"take_start_tick":take_start_tick,"source_sha256":sources,"imports":imports,"frames":frames,"stills":stills,"variants":variants,"events":events,"outcomes":outcomes,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"godot":Engine.get_version_info(),"wall_elapsed_ms":Time.get_ticks_msec()-started_ms,"scope":"Actual software-rendered original VFX responding to scripted geometry/events. No gameplay damage or authority outcomes. Fourteen static warning motifs; representative Rama full lifecycle and Sita onset/sustain, explicitly cancelled at take end before its normal six-second expiry. All fourteen full lifecycles are headless-only tests. Silent video; not realtime performance, online play or final commercial-quality acceptance."}
	var file := FileAccess.open(output_path.path_join("ultimate-render-review.json"),FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(report,"  ")+"\n")
	if not success:push_error(failure)
	quit(0 if success else 1)
