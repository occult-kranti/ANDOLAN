extends SceneTree
## External script: run against a real exported PCK, never as source-only proof.
var checks:Array[Dictionary]=[]
var output:=""
var expected_pack:=""
func _initialize()->void:call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--expected-pack="):expected_pack=arg.trim_prefix("--expected-pack=")
	if not output.is_absolute_path() or FileAccess.file_exists(output):push_error("Fresh absolute package probe report required");quit(1);return
	# Engine-consumed --main-pack is absent from OS.get_cmdline_args().
	# expected_pack labels the launcher receipt; it does not prove the mount.
	check("launcher expected pack file exists for report identity",expected_pack.is_absolute_path() and FileAccess.file_exists(expected_pack))
	var mounted_binary:=FileAccess.file_exists("res://project.binary")
	check("mounted resources contain actual exported project.binary",mounted_binary)
	if expected_pack.is_empty() or not mounted_binary:push_error("Exported mounted project.binary and --expected-pack required; source-only invocation refused");quit(1);return
	var helper:Script=load("res://scripts/lanka_lane_gate.gd")
	check("exported production helper resolves",helper!=null)
	if helper==null:quit(1);return
	check("exported native scene FileAccess resolves exact qualified bytes",FileAccess.file_exists(helper.ASSET) and FileAccess.get_sha256(helper.ASSET)==helper.ASSET_SHA,FileAccess.get_sha256(helper.ASSET))
	var first:=Node3D.new();var peer:=Node3D.new();root.add_child(first);root.add_child(peer)
	var a:Dictionary=helper.build(first);var b:Dictionary=helper.build(peer)
	check("actual packaged native scene builds through production helper",a.get("enabled",false) and b.get("enabled",false),a.get("report",{}))
	if a.get("enabled",false) and b.get("enabled",false):
		check("packaged instance geometry and resource budgets exact",a.report.triangles==17862 and a.report.opaque_surfaces==11 and a.report.material_resources==6 and a.report.collision_triangles==6706)
		check("packaged native scene remains self-contained",ResourceLoader.get_dependencies(helper.ASSET).is_empty())
		check("packaged cached scene shares resources and unique owned collision",helper.cache_report().entries==1 and a.root.get_child(0).mesh==b.root.get_child(0).mesh and a.body!=b.body and a.shape!=b.shape)
		check("packaged duplicate call refused",not helper.build(first).enabled and first.get_child_count()==1)
		await physics_frame;await physics_frame
		var space:=root.world_3d.direct_space_state
		check("packaged opening remains real unblocked LOS",space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-40,1.6,-70),Vector3(-40,1.6,-38),1)).is_empty())
		check("packaged side pier remains real cover",not space.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-49,1.6,-70),Vector3(-49,1.6,-38),1)).is_empty())
		var original:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
		var prepared:Dictionary=helper.prepare_army_manifest(original,a.root)
		check("packaged original ground metadata prepares isolated army copy",prepared.get("ok",false) and prepared.get("boxes",[]).size()==10 and original.traversal.native_collision_boxes.size()==8)
		if prepared.get("ok",false):
			var army:Node3D=load("res://scripts/lane_army.gd").new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
			check("packaged unchanged army configure respects pier cover and open aperture",army.configure(prepared.manifest,null) and not army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)) and army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)))
			army.free()
	first.free();peer.free();helper.clear_cache()
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"engine":Engine.get_version_info(),"expected_pack":expected_pack,"expected_pack_sha256":FileAccess.get_sha256(expected_pack),"mounted_project_binary_sha256":FileAccess.get_sha256("res://project.binary"),"compiled_helper_remap_present":FileAccess.file_exists("res://scripts/lanka_lane_gate.gd.remap"),"engine_executable_sha256":FileAccess.get_sha256(OS.get_executable_path()),"scope":"Actual exported PCK resource/FileAccess/hash and production helper instance/physics/cache probe. Must be launched outside checkout with --main-pack actual.pck and this external script; parent launcher separately records actual argv/pack SHA. Expected-pack user argument is report identity only; mounted project.binary plus actual resource/hash/physics checks establish exported resource execution. No source-only or hardware/render claim."},"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
