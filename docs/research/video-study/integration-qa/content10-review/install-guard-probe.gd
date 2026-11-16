extends SceneTree
const District = preload("res://scripts/sangam_district.gd")
func _initialize() -> void:
	var host := Node3D.new()
	root.add_child(host)
	var result: Dictionary = District.build(host)
	var sources := {}
	for path in ["res://scripts/sangam_district.gd","res://assets/world/sangam-district.json","res://shaders/sangam_masonry.gdshader"]: sources[path] = FileAccess.get_sha256(path)
	var receipt := {"result":result,"sources":sources,"scope":"Direct current adapter guard probe in an identity host. Rejection before inherited-host lookup identifies the active specification gate; no render/import or successful installation claim."}
	FileAccess.open("/workspaces/ANDOLAN/docs/research/video-study/integration-qa/content10-review/install-guard-probe.json",FileAccess.WRITE).store_string(JSON.stringify(receipt,"  ")+"\n")
	print(JSON.stringify(receipt))
	host.free();quit(0)
