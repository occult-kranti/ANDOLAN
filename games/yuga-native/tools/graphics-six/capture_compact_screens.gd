extends SceneTree
## Authored evidence only: actual boot/title, product transition, live scaled world.
## No layout/camera/pose/light/clock/health overrides. Preflight writes no images.
var output := ""
var manifest := "res://.graphics-six-snapshot.json"
var preflight := false
var source_start := {}
var shots: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var checkpoints: Array[Dictionary] = []
var done := false
const SCALES := [1.0,1.25,1.5,2.0]
const SETTLE_FRAMES := 12
const TIMEOUT_MS := 120000

func _initialize() -> void:
	call_deferred("run")

func write_json(path: String, data: Dictionary) -> void:
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(data,"  ")+"\n")

func check(label: String, passed: bool) -> void:
	checks.append({"name":label,"passed":passed})

func checkpoint(stage: String) -> void:
	var row := {"stage":stage,"wall_ms":Time.get_ticks_msec(),"process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),"drawn_frame":Engine.get_frames_drawn()}
	checkpoints.append(row)
	print("COMPACT_SCREEN_STAGE ",JSON.stringify(row))

func frames(count: int) -> void:
	for unused in count:
		await process_frame
		if not preflight: await RenderingServer.frame_post_draw

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await frames(2)

func hashes() -> Dictionary:
	var seal: Variant=JSON.parse_string(FileAccess.get_file_as_string(manifest))
	if not seal is Dictionary or not seal.get("files") is Dictionary: return {}
	var result := {}
	for name in seal.files: result[name]=FileAccess.get_sha256("res://"+name)
	result[manifest]=FileAccess.get_sha256(manifest)
	result[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	return result

func wait_scene(path: String) -> bool:
	var start := Time.get_ticks_msec()
	while Time.get_ticks_msec()-start<TIMEOUT_MS:
		await frames(1)
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path: return true
	return false

func vector(v: Vector3) -> Array:
	return [v.x,v.y,v.z]

func camera_state(camera: Camera3D) -> Dictionary:
	return {"path":str(camera.get_path()),"fov":camera.fov,"near":camera.near,"far":camera.far,"transform":[vector(camera.global_basis.x),vector(camera.global_basis.y),vector(camera.global_basis.z),vector(camera.global_position)]}

func snapshot(id: String) -> Dictionary:
	var scene: Node=current_scene
	var focus := root.gui_get_focus_owner()
	var state := {"id":id,"scene_path":scene.scene_file_path,"physical_size":[root.size.x,root.size.y],"base_canvas":[root.content_scale_size.x,root.content_scale_size.y],"content_scale_factor":root.content_scale_factor,"logical_viewport":str(root.get_visible_rect()),"paused":paused,"scene_processing":scene.is_processing(),"scene_physics_processing":scene.is_physics_processing(),"mouse_mode":Input.mouse_mode,"window_focused":DisplayServer.window_is_focused(),"focus":str(focus.get_path()) if focus else "","process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),"drawn_frame":Engine.get_frames_drawn(),"camera":camera_state(root.get_camera_3d()),"visible_panels":{}}
	for field in ["main_panel","pause_panel","settings_panel","help_panel","hero_panel","rama_panel","atlas_guide","compact_world_card"]:
		if field in scene and is_instance_valid(scene.get(field)):
			var panel: Control=scene.get(field)
			state.visible_panels[field]={"visible":panel.is_visible_in_tree(),"rect":str(panel.get_global_rect())}
	var player: Node3D=scene.player
	state.hero={"model_ready":player.model_ready,"active":player.active,"position":vector(player.global_position),"presentation_suspended":player.presentation_suspended}
	if "rama_hud" in scene:
		var hud: Control=scene.rama_hud
		state.hud={"visible":hud.is_visible_in_tree(),"rect":str(hud.get_global_rect()),"notice":hud.note.text,"health":hud.life_text.text,"slots":hud.slots.map(func(item):return {"text":item.text,"rect":str(item.get_global_rect())})}
	if "world_ready" in scene:
		state.world_ready=scene.world_ready
		state.lane_label_visible=scene.lane_label.visible
		state.lane_label_effectively_visible=scene.lane_label.is_visible_in_tree()
		state.overview=scene.overview
		state.army_elapsed=scene.army.elapsed
		state.kit_elapsed=scene.rama_runtime.kit.elapsed
		state.runtime_suspended=scene.rama_runtime.suspended
		state.visible_hud_peers={}
		for child in scene.hud.get_children():
			if child is Control and child.is_visible_in_tree(): state.visible_hud_peers[String(child.name)]=str(child.get_global_rect())
		state.torso_proxy={"scope":"Existing neutral .75..1.80m and +/- .32m projection proxy; not every pose/aim angle.","rect":str(torso_proxy(player))}
		if scene.atlas_guide.visible: state.overview_scroll={"offset":scene.atlas_guide_scroll.scroll_vertical,"page":scene.atlas_guide_scroll.get_v_scroll_bar().page,"max":scene.atlas_guide_scroll.get_v_scroll_bar().max_value}
		if scene.rama_panel.visible:
			var guide: Control=scene.rama_panel
			state.guide={"selection":guide.selected_id,"card":str(guide.card.get_global_rect()),"back":str(guide.close_button.get_global_rect()),"details":str(guide.details_scroll.get_global_rect()),"details_offset":guide.details_scroll.scroll_vertical,"list_offset":guide.abilities_scroll.scroll_vertical,"effects_available":not guide.reduced_effects_button.disabled}
	else:
		state.environment_ready=scene.environment_ready
		state.started=scene.started
	return state

func torso_proxy(player: Node3D) -> Rect2:
	var camera: Camera3D=player.camera
	var result := Rect2()
	var first := true
	for height in [.75,1.80]:
		for side in [-.32,.32]:
			var point := camera.unproject_position(player.global_position+Vector3.UP*height+camera.global_basis.x*side)
			if first: result=Rect2(point,Vector2.ZERO);first=false
			else: result=result.expand(point)
	return result

func take(id: String) -> bool:
	var state := snapshot(id)
	if not preflight:
		var original := root.get_texture().get_image()
		state.framebuffer_size=[original.get_width(),original.get_height()]
		state.file=id+".png"
		if original.save_png(output.path_join(state.file))!=OK: finish("PNG write failed: "+id);return false
		state.sha256=FileAccess.get_sha256(output.path_join(state.file))
	shots.append(state)
	write_json(output.path_join(id+".json"),state)
	checkpoint("shot:"+id)
	return true

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--manifest="):manifest=arg.trim_prefix("--manifest=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown argument: "+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh absolute output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not FileAccess.file_exists(manifest):finish("Immutable source manifest missing");return
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		finish("Actual capture requires X11 Forward+");return
	source_start=hashes()
	if source_start.is_empty():finish("Expected manifest.files dictionary");return
	root.size=Vector2i(960,540)
	root.content_scale_size=Vector2i(1280,720)
	root.content_scale_factor=1.0
	root.title="YUGA actual compact screen qualification"
	if not preflight:root.show()
	checkpoint("actual_boot_main_scene")
	if change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))!=OK:finish("Main scene failed");return
	if not await wait_scene("res://scenes/courtyard.tscn"):finish("Boot did not reach courtyard within120s");return
	await frames(SETTLE_FRAMES)
	var court: Node3D=current_scene
	if not court.environment_ready or not court.player.model_ready or court.started:finish("Ordinary title not ready");return
	for index in SCALES.size():
		root.content_scale_factor=SCALES[index]
		await frames(SETTLE_FRAMES)
		check("title ordinary camera "+str(SCALES[index]),root.get_camera_3d()==court.title_camera and court.main_panel.visible and not court.player.active)
		if not take("0%d-title-%d" % [index,int(SCALES[index]*100)]):return
	# Activate the real primary Button via viewport key dispatch; no direct world load.
	root.content_scale_factor=1.0
	await frames(SETTLE_FRAMES)
	court.main_panel.primary_button.grab_focus()
	await key(KEY_ENTER)
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("Primary action did not reach Confluence within120s");return
	await frames(SETTLE_FRAMES)
	var world: Node3D=current_scene
	if not world.world_ready or not world.player.model_ready:finish("Actual world/hero not ready");return
	for index in SCALES.size():
		root.content_scale_factor=SCALES[index]
		await frames(SETTLE_FRAMES)
		check("world ordinary live camera "+str(SCALES[index]),world.is_processing() and world.is_physics_processing() and world.player.active and not world.overview and not paused and root.get_camera_3d()==world.player.camera)
		if not take("0%d-world-%d" % [index+SCALES.size(),int(SCALES[index]*100)]):return
	var clocks_progress := true
	for index in range(SCALES.size()+1,SCALES.size()*2):
		clocks_progress = clocks_progress and shots[index].army_elapsed>shots[index-1].army_elapsed
	check("actual world clocks progress across live observations",clocks_progress)
	await key(KEY_F1)
	var held_army: float=world.army.elapsed
	var held_kit: float=world.rama_runtime.kit.elapsed
	await frames(SETTLE_FRAMES)
	check("overview is suspended product view with keyboard owner",world.overview and not paused and world.atlas_guide.visible and root.gui_get_focus_owner()==world.atlas_guide_scroll and world.army.elapsed==held_army and world.rama_runtime.kit.elapsed==held_kit)
	if not take("08-overview-200"):return
	await key(KEY_F1)
	await key(KEY_ESCAPE)
	var opener := root.gui_get_focus_owner()
	await key(KEY_F3)
	await frames(SETTLE_FRAMES)
	check("guide opens through real pause shortcut",paused and world.paused and world.rama_panel.visible and not world.player.active and world.rama_runtime.suspended and is_instance_valid(opener))
	if not take("09-guide-200"):return
	await key(KEY_ESCAPE)
	await frames(SETTLE_FRAMES)
	check("guide returns exact usable pause opener",paused and world.pause_panel.visible and not world.rama_panel.visible and root.gui_get_focus_owner()==opener)
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after := hashes() if not source_start.is_empty() else {}
	check("ten actual ordinary screen observations",shots.size()==10)
	check("source unchanged",not source_start.is_empty() and source_start==after)
	var passed := failure.is_empty() and checks.all(func(item):return item.passed)
	var report := {"schema":1,"case":"compact-screens-125","complete":passed,"failure":failure,"preflight":preflight,"manifest":manifest,"manifest_sha256":FileAccess.get_sha256(manifest) if FileAccess.file_exists(manifest) else "","source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"shots":shots,"checks":checks,"checkpoints":checkpoints,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Actual boot→title→native viewport Enter primary→world; normal running100/125/150/200% content scale, native F1 overview and F3 guide from pause. No manual layout/camera/light/pose/health/clock override, no matched-tint comparison, no OS-input or perceptual/hardware quality claim. Fresh XDG settings/cache conditions belong to invocation receipt. Preflight produces no images."}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("COMPACT_SCREEN_COMPLETE ",passed," ",failure)
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	quit(0 if passed else 1)
