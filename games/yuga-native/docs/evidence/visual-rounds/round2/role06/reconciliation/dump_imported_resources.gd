extends SceneTree
## Text serialization for exact property comparison; never changes source files.
func _initialize() -> void:
	var output_dir := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_dir = arg.trim_prefix("--output=")
	if not output_dir.is_absolute_path() or DirAccess.dir_exists_absolute(output_dir): quit(1); return
	DirAccess.make_dir_recursive_absolute(output_dir)
	for name in ["rama-hero","rama-hero-mid","rama-hero-far"]:
		var source: String = "res://assets/heroes/"+name+".glb"
		if ResourceSaver.save(load(source),output_dir.path_join(name+".tscn")) != OK: quit(1); return
	quit(0)
