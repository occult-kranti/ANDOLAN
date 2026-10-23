extends SceneTree
## One actual native view of the isolated existing element; no concept image.
const Loader=preload("res://map_loader.gd")
const PBR=preload("res://pbr_material.gd")
func _initialize()->void:call_deferred("run")
func run()->void:
	var output:=""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="):output=argument.trim_prefix("--output=")
	if output.is_empty():quit(2);return
	var loaded:Dictionary=Loader.load_element("res://assets/courtyard.glb")
	if not loaded.ok:print(JSON.stringify(loaded));quit(1);return
	root.add_child(loaded.root)
	var material:Dictionary=PBR.new().build(output)
	if not material.ok:print(JSON.stringify(material));quit(1);return
	loaded.visual.material_override=material.material
	var environment:=WorldEnvironment.new()
	environment.environment=Environment.new()
	environment.environment.background_mode=Environment.BG_COLOR
	environment.environment.background_color=Color("172934")
	environment.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color=Color("b9c6ce")
	environment.environment.ambient_light_energy=.7
	loaded.root.add_child(environment)
	var light:=DirectionalLight3D.new()
	light.rotation_degrees=Vector3(-48,-28,0)
	light.light_color=Color("ffe1b4")
	light.light_energy=1.8
	light.shadow_enabled=true
	loaded.root.add_child(light)
	var camera:=Camera3D.new()
	loaded.root.add_child(camera)
	camera.projection=Camera3D.PROJECTION_ORTHOGONAL
	camera.size=62
	camera.position=Vector3(48,35,50)
	camera.look_at(Vector3(0,3,-5))
	camera.current=true
	for unused in 8:await process_frame
	await RenderingServer.frame_post_draw
	var image:=root.get_texture().get_image()
	var status:=image.save_png(output.path_join("existing-courtyard-element.png"))
	var report:={"passed":status==OK,"source_sha256":loaded.source_sha256,"element":Loader.ELEMENT,"triangles":loaded.triangles,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Actual isolated native source-element preview; original CC0 map geometry plus existing PBR material adapter. Software render, no visual acceptance or hardware performance claim.","runtime_promoted":false}
	FileAccess.open(output.path_join("preview-report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify(report))
	quit(0 if status==OK else 1)
