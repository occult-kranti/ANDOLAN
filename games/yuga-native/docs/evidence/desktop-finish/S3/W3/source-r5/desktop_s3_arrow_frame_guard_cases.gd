extends SceneTree
const Fletching = preload("res://scripts/rama_arrow_fletching.gd")

func _initialize() -> void:
	var helper:=Fletching.new()
	var cases:={
		"unit identity admitted":[Transform3D.IDENTITY,true],
		"unit rotated basis admitted":[Transform3D(Basis(Vector3.UP,.71),Vector3(2,3,4)),true],
		"balanced anisotropic scale rejected":[Transform3D(Basis.from_scale(Vector3(2,.5,1)),Vector3.ZERO),false],
		"determinant-one shear rejected":[Transform3D(Basis(Vector3(1,0,0),Vector3(.25,1,0),Vector3(0,0,1)),Vector3.ZERO),false],
		"reflection rejected":[Transform3D(Basis.from_scale(Vector3(-1,1,1)),Vector3.ZERO),false],
		"nonfinite origin rejected":[Transform3D(Basis.IDENTITY,Vector3(INF,0,0)),false]}
	var checks:=[]
	for label in cases:
		var actual: bool=helper._finite_transform(cases[label][0])
		checks.append({"name":label,"passed":actual==cases[label][1],"actual":actual,"expected":cases[label][1]})
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,
		"helper_sha256":FileAccess.get_sha256("res://scripts/rama_arrow_fletching.gd"),
		"fixture_sha256":FileAccess.get_sha256(get_script().resource_path),
		"scope":"Pure helper frame admission counterexamples; no scene, pose, import or render execution."}
	print(JSON.stringify(result))
	helper.free()
	quit(0 if result.passed else 1)
