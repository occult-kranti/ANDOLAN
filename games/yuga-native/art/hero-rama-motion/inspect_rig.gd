extends SceneTree
func find_node(n: Node, kind: String) -> Node:
	if n.is_class(kind): return n
	for c in n.get_children():
		var r = find_node(c,kind)
		if r: return r
	return null
func _initialize():
	call_deferred("run")
func run():
	var hero=load("res://assets/heroes/rama-production.glb").instantiate()
	root.add_child(hero)
	var s: Skeleton3D=find_node(hero,"Skeleton3D")
	var a: AnimationPlayer=find_node(hero,"AnimationPlayer")
	var out={"skeleton_path":str(s.get_path()),"animations":{},"bones":{}}
	for clip in a.get_animation_list():
		var anim=a.get_animation(clip)
		out.animations[str(clip)]={"length":anim.length,"tracks":anim.get_track_count()}
	for name_ in ["root","spine05","spine03","spine01","head","upperarm01.R","upperarm02.R","lowerarm01.R","lowerarm02.R","wrist.R","upperarm01.L","upperarm02.L","lowerarm01.L","lowerarm02.L","wrist.L","bowstring","upperleg01.L","upperleg02.L","lowerleg01.L","lowerleg02.L","foot.L","toe1-1.L"]:
		var b=s.find_bone(name_)
		if b>=0:
			var tr=s.get_bone_global_rest(b)
			out.bones[name_]={"index":b,"parent":s.get_bone_name(s.get_bone_parent(b)) if s.get_bone_parent(b)>=0 else "", "position":[tr.origin.x,tr.origin.y,tr.origin.z],"local_rest":str(s.get_bone_rest(b)), "global_rest":str(tr)}
	print(JSON.stringify(out,"  "))
	quit()
