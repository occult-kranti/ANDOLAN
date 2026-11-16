extends SceneTree
## Actual native studio capture. Explicit preview clock, no match authority.
var output:=""
var front:Control
var shots:Array=[]
var film:Array=[]
var sources:={}
func _initialize()->void:call_deferred("run")
func frames(count:int)->void:
	for i in count:await process_frame;await RenderingServer.frame_post_draw
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	for path in ["res://scripts/tactical_frontend.gd","res://scripts/tactical_hero_showcase.gd","res://scripts/tactical_hero_pose.gd","res://scripts/tactical_hero_dossier.gd","res://scripts/tactical_weapon.gd","res://scripts/tactical_cast_motion.gd","res://assets/heroes/rama-hero.glb","res://assets/tactical/surya-carbine.glb"]:sources[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(1280,720);root.content_scale_size=root.size;root.show()
	front=load("res://scenes/tactical_frontend.tscn").instantiate();root.add_child(front);current_scene=front;front.show_page("hero")
	await frames(20)
	var view:Control=front.hero_showcase
	view.set_preview_paused(true);await frames(4);capture("01-hero-ready")
	for spec in [["aim",.45],["q",.42],["c",.55],["e",.30],["x",.65]]:
		view.hero_pose.reset();view.set_preview("idle")
		if spec[0] in ["q","c","e","x"]:front.hero_dossier.select_ability(spec[0])
		front.hero_dossier.request_preview(spec[0]);view.set_preview_paused(true)
		for tick in ceili(spec[1]*60):view.hero_pose.step(1.0/60.0)
		await frames(4);capture("02-hero-"+spec[0])
	view.hero_pose.reset();view.set_view("back");await frames(4);capture("03-hero-back")
	view.set_view("front");view.set_view_mode("first_person");view.set_preview("idle");await frames(12);view.set_preview_paused(true);capture("04-first-person-ready")
	for spec in [["q",.33],["x",.5],["aim",.45]]:
		if spec[0] in ["q","x"]:front.hero_dossier.select_ability(spec[0])
		view.set_preview(spec[0]);view.set_preview_paused(true)
		for tick in ceili(spec[1]*60):view.first_person_weapon.step(1.0/60.0)
		if spec[0]=="aim":view.first_person_camera.fov=54
		await frames(4);capture("05-first-person-"+spec[0])
	view.set_view_mode("hero");view.hero_pose.reset();view.set_preview("idle");view.set_preview_paused(true)
	var actions:={15:"aim",30:"q",52:"c",77:"e",92:"x",123:"idle"}
	for index in 135:
		if actions.has(index):
			var action:String=actions[index]
			if action in ["q","c","e","x"]:front.hero_dossier.select_ability(action)
			view.set_preview(action);view.set_preview_paused(true)
		view.hero_pose.step(1.0/15.0)
		await frames(1)
		var name:="frame-%05d.png"%index
		root.get_texture().get_image().save_png(output.path_join(name))
		film.append({"frame":index,"file":name,"sha256":FileAccess.get_sha256(output.path_join(name)),"pose":view.preview_report().pose})
	root.size=Vector2i(960,540);root.content_scale_size=root.size;await frames(5);capture("06-studio-960")
	front._settings.ui_scale=1.5;front._apply_settings();front.show_page("hero");await frames(20);front.hero_dossier.select_ability("x");front.hero_showcase.set_preview_paused(true);await frames(4);capture("07-studio-960-large")
	var changed:Array=[]
	for path in sources:
		if sources[path]!=FileAccess.get_sha256(path):changed.append(path)
	var report:={"complete":changed.is_empty(),"shots":shots,"frames":film,"sources":sources,"changed_sources":changed,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Actual native hero studio, explicit presentation clock; no combat authority, new hero, native full-body gameplay or hardware FPS claim."}
	FileAccess.open(output.path_join("review.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	front.queue_free();await frames(2);quit(0 if changed.is_empty() else 1)
func capture(id:String)->void:
	var path:=output.path_join(id+".png");root.get_texture().get_image().save_png(path)
	shots.append({"id":id,"sha256":FileAccess.get_sha256(path)});print("STUDIO_CAPTURE "+id)
