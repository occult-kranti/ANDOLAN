extends SceneTree
func _initialize() -> void: call_deferred("run")
func frames(n:=5) -> void:
	for unused in n: await process_frame
func run() -> void:
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world;await frames()
	world.player.set_physics_process(false);world.army.set_physics_process(false)
	var rows:=[]
	for scale in [1.0,1.5,2.0]:
		root.content_scale_factor=scale;await frames()
		var camera:Camera3D=world.player.camera
		var torso:=Rect2();var first:=true
		for height in [.75,1.80]:
			for side in [-.32,.32]:
				var point:=camera.unproject_position(world.player.global_position+Vector3.UP*height+camera.global_basis.x*side)
				if first:torso=Rect2(point,Vector2.ZERO);first=false
				else:torso=torso.expand(point)
		var blocking:=[];var rects:={}
		for control in world.hud.get_children():
			if control is Control and control.is_visible_in_tree():
				rects[String(control.name)]=str(control.get_global_rect())
				if control.get_global_rect().intersects(torso):blocking.append(String(control.name))
		if world.rama_hud.get_global_rect().intersects(torso):blocking.append("RamaHeroHUD")
		rows.append({"scale":scale,"viewport":str(root.get_visible_rect()),"torso":str(torso),"blocking":blocking,"peers":rects})
	FileAccess.open("res://docs/evidence/desktop-finish/S5/W2/torso-projection.json",FileAccess.WRITE).store_string(JSON.stringify({"rows":rows,"world_sha256":FileAccess.get_sha256("res://scripts/confluence_world.gd"),"scope":"Existing neutral torso proxy .75..1.80m and ±.32m from rama_hud_layout_cases, headless projection; not actual rendered occlusion."},"  ")+"\n")
	current_scene=null;world.queue_free();await frames(8);quit()
