extends SceneTree
## Same-method runtime intake only; no graphical/pose/contact acceptance.
var checks:Array[Dictionary]=[]
func check(name_:String,pass_:bool,detail:Variant=null)->void:
	checks.append({"name":name_,"passed":pass_,"detail":detail})
func collect(node:Node,class_:String)->Array[Node]:
	var result:Array[Node]=[]
	if node.is_class(class_):result.append(node)
	for child in node.get_children():result.append_array(collect(child,class_))
	return result
func load_hero(path:String)->Node:
	var document:=GLTFDocument.new();var state:=GLTFState.new()
	var error:=document.append_from_file(path,state)
	check("runtime GLTF parse "+path.get_file(),error==OK,error)
	if error!=OK:return null
	return document.generate_scene(state)
func animations_signature(node:Node)->String:
	var rows:=[]
	for item in collect(node,"AnimationPlayer"):
		var player:AnimationPlayer=item
		for name_ in player.get_animation_list():
			var animation:Animation=player.get_animation(name_);var tracks:=[]
			for t in animation.get_track_count():
				var keys:=[]
				for k in animation.track_get_key_count(t):keys.append([animation.track_get_key_time(t,k),animation.track_get_key_value(t,k),animation.track_get_key_transition(t,k)])
				tracks.append([animation.track_get_type(t),str(animation.track_get_path(t)),keys])
			rows.append([name_,animation.length,animation.loop_mode,tracks])
	return var_to_bytes(rows).hex_encode().sha256_text()
func _initialize()->void:call_deferred("run")
func run()->void:
	var source:="";var candidate:="";var report_path:=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--source="):source=arg.trim_prefix("--source=")
		elif arg.begins_with("--candidate="):candidate=arg.trim_prefix("--candidate=")
		elif arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	if source.is_empty() or candidate.is_empty() or report_path.is_empty():push_error("source/candidate/report required");quit(2);return
	var original:=load_hero(source);var edited:=load_hero(candidate)
	if original==null or edited==null:quit(1);return
	root.add_child(original);root.add_child(edited)
	var first:=collect(original,"Skeleton3D");var second:=collect(edited,"Skeleton3D")
	check("one source-compatible skeleton",first.size()==1 and second.size()==1)
	if first.size()==1 and second.size()==1:
		var a:Skeleton3D=first[0];var b:Skeleton3D=second[0];var exact:=a.get_bone_count()==164 and b.get_bone_count()==164
		for i in mini(a.get_bone_count(),b.get_bone_count()):exact=exact and a.get_bone_name(i)==b.get_bone_name(i) and a.get_bone_parent(i)==b.get_bone_parent(i) and a.get_bone_rest(i)==b.get_bone_rest(i)
		check("all 164 bone names parents and REST matrices exact",exact)
	check("embedded animation names tracks key data exact",animations_signature(original)==animations_signature(edited))
	var left:=collect(original,"MeshInstance3D");var right:=collect(edited,"MeshInstance3D");check("same mesh node count",left.size()==right.size());var changed:=0;var nonhair_exact:=true;var arrays_exact:=true;var binds_exact:=true;var all_finite:=true;var max_move:=0.0;var surfaces:=0
	for index in mini(left.size(),right.size()):
		var a:MeshInstance3D=left[index];var b:MeshInstance3D=right[index]
		check("mesh surface count "+str(a.name),a.mesh.get_surface_count()==b.mesh.get_surface_count())
		if a.skin!=null and b.skin!=null:
			binds_exact=binds_exact and a.skin.get_bind_count()==b.skin.get_bind_count()
			for bind in mini(a.skin.get_bind_count(),b.skin.get_bind_count()):binds_exact=binds_exact and a.skin.get_bind_bone(bind)==b.skin.get_bind_bone(bind) and a.skin.get_bind_name(bind)==b.skin.get_bind_name(bind) and a.skin.get_bind_pose(bind)==b.skin.get_bind_pose(bind)
		else:binds_exact=binds_exact and (a.skin==null)==(b.skin==null)
		for s in mini(a.mesh.get_surface_count(),b.mesh.get_surface_count()):
			surfaces+=1;var aa:=a.mesh.surface_get_arrays(s);var bb:=b.mesh.surface_get_arrays(s);var material:Material=a.mesh.surface_get_material(s);var hair:=material!=null and material.resource_name=="Swept black hair"
			for slot in [Mesh.ARRAY_TEX_UV,Mesh.ARRAY_TEX_UV2,Mesh.ARRAY_COLOR,Mesh.ARRAY_BONES,Mesh.ARRAY_WEIGHTS,Mesh.ARRAY_INDEX]:arrays_exact=arrays_exact and var_to_bytes(aa[slot])==var_to_bytes(bb[slot])
			var av:PackedVector3Array=aa[Mesh.ARRAY_VERTEX];var bv:PackedVector3Array=bb[Mesh.ARRAY_VERTEX];check("same surface vertices "+str(a.name)+":"+str(s),av.size()==bv.size())
			for v in mini(av.size(),bv.size()):
				all_finite=all_finite and bv[v].is_finite();var distance:=av[v].distance_to(bv[v]);max_move=maxf(max_move,distance)
				if distance>0.000001:changed+=1;nonhair_exact=nonhair_exact and hair
	check("runtime UV colors bones weights and indices exact",arrays_exact)
	check("runtime skin bind resources exact",binds_exact)
	check("only named hair surface positions changed",nonhair_exact and changed>0,changed)
	check("runtime hair displacement bounded",max_move>0.01 and max_move<0.03,max_move)
	check("all runtime vertices finite",all_finite)
	var passed:=checks.all(func(item):return item.passed)
	var report:={"passed":passed,"checks":checks,"check_count":checks.size(),"source_sha256":FileAccess.get_sha256(source),"candidate_sha256":FileAccess.get_sha256(candidate),"changed_runtime_vertices":changed,"max_displacement":max_move,"surfaces_compared":surfaces,"same_import_method":"GLTFDocument.append_from_file/generate_scene for BOTH ancestors","scope":"Actual runtime source/candidate resource/skin/animation-rest intake. No rendered frame, dynamic hair-pose contact, native gameplay, LOD or hardware acceptance.","canonical_promoted":false}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n");print(JSON.stringify({"passed":passed,"checks":checks.size(),"changed":changed,"max_move":max_move}));original.queue_free();edited.queue_free();quit(0 if passed else 1)
