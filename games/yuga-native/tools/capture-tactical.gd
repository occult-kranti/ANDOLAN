extends SceneTree
## Staged native art/UI review; ordinary input and natural-match evidence are separate.
var output:=""
var shots:Array=[]
var bindings:Dictionary={}
var world:Node3D
func _initialize()->void:call_deferred("run")
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	for path in ["res://scripts","res://assets/tactical","res://scenes","res://shaders"]:_hash_files(path)
	bindings["res://project.godot"]=FileAccess.get_sha256("res://project.godot")
	root.size=Vector2i(1280,720);root.content_scale_size=root.size;root.show()
	var front:Control=load("res://scenes/tactical_frontend.tscn").instantiate();root.add_child(front);current_scene=front
	for page in ["home","casual","hero","settings","help"]:
		front.show_page(page);await frames(3);capture("menu-"+page)
	root.remove_child(front);front.queue_free();current_scene=null;await process_frame
	world=load("res://scenes/tactical_world.tscn").instantiate();root.add_child(world);current_scene=world;world.set_physics_process(false)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	await frames(30);capture("01-first-person-buy")
	world._shop_open=true;world._pause();await frames(3);capture("02-equipment-shop")
	world.request_resume();world._pause();world.ui.show_guide();await frames(3);capture("03-kit-guide")
	world.request_resume();world._pause();await frames(3);capture("04-pause")
	world.request_resume();world.map.set_buy_barriers(false);world.rules.phase="live";world.rules.time_left=89;world._hint_life=0
	world.player.reset_at(Vector3(-29,0,-20),PI,"carbine");world.player.weapon.step(.1)
	await frames(3);capture("05-a-approach")
	world.player.weapon.ads=true;world.player.weapon.step(.5);world.player.camera.fov=65
	await frames(3);capture("06-aim-down-sights")
	world.player.weapon.ads=false;world.player.weapon.fire();world.player.weapon.reload();world.player.weapon.step(.9)
	await frames(3);capture("06b-reload")
	world.player.weapon.step(2)
	world.player.weapon.ads=false;world.player.weapon.step(.5);world.player.camera.fov=90
	world.effects.ward(Vector3(-29,0,-8),0);world.effects.veil(Vector3(-29,0,8))
	world.effects.step(.5);await frames(20);capture("07-ward-and-veil")
	world.effects.clear();world.rules.phase="planted";world.rules.site="A";world.rules.time_left=31;world._step_relic(.1)
	world.player.reset_at(Vector3(-37,0,-1),PI,"carbine");world.player.yaw=-2.42;world.player.rotation.y=-2.42
	await frames(3);capture("08-astra-planted")
	world.ui.hide();var camera:=Camera3D.new();world.add_child(camera);camera.position=Vector3(-69,89,-94);camera.look_at(Vector3(0,0,0));camera.far=250;camera.fov=64;camera.make_current()
	await frames(3);capture("09-map-overview")
	camera.position=Vector3(34,2.6,-16);camera.look_at(Vector3(26,4,8));await frames(3);capture("10-b-site-architecture")
	world.player.camera.make_current();world.ui.show();Input.action_press("tac_score");await frames(3);capture("11-scoreboard");Input.action_release("tac_score")
	world.rules.phase="round_end";world.rules.winner="sun";world.rules.reason="Astra attuned";await frames(3);capture("12-round-result")
	world.rules.phase="match_end";world.rules.scores={"sun":13,"moon":9};world.rules.winner="sun";await frames(3);capture("13-match-result")
	var changed:Array=[]
	for path in bindings:
		if FileAccess.get_sha256(path)!=bindings[path]:changed.append(path)
	var report:={"kind":"staged-native-tactical-art-review","complete":changed.is_empty(),"changed_sources":changed,"source_sha256":bindings,"shots":shots,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Actual native rendered screens and geometry. Fixture authority states stage plant/results for art review; not natural gameplay/input or hardware performance proof."}
	var file:=FileAccess.open(output.path_join("review.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t")+"\n")
	world.queue_free();await frames(2);quit(0 if changed.is_empty() else 1)
func frames(count:int)->void:
	for i in count:await process_frame;await RenderingServer.frame_post_draw
func capture(id:String)->void:
	var path:=output.path_join(id+".png");root.get_texture().get_image().save_png(path)
	shots.append({"id":id,"sha256":FileAccess.get_sha256(path),"frames":Engine.get_frames_drawn()});print("TACTICAL_CAPTURE "+id)
func _hash_files(path:String)->void:
	for child in DirAccess.get_files_at(path):
		if child.ends_with(".uid") or child.ends_with(".import"):continue
		var file:=path.path_join(child);bindings[file]=FileAccess.get_sha256(file)
	for child in DirAccess.get_directories_at(path):_hash_files(path.path_join(child))
