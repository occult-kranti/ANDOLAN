extends SceneTree
const Placement = preload("res://tools/map-reuse-placement/placement.gd")
func _initialize() -> void:
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	var rows := []
	for value in [null,false,{},"not an array"]:
		var selection := {"schema":1,"source_sha256":Placement.SOURCE_SHA,"placement_translation":[-40.0,0.0,-29.2],"selected":value}
		var result := Placement.build("res://assets/environment/lanka_courtyard.glb",selection)
		rows.append({"selected":value,"result":result,"passed":result.get("ok")==false and result.get("reason")=="selection_contract"})
	var result := {"scope":"Four pure selection-contract counterexamples; no native scene generation, renderer or full parser coverage.","checks":rows,"passed":rows.all(func(row):return row.passed),"placement_sha256":FileAccess.get_sha256("res://tools/map-reuse-placement/placement.gd")}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
