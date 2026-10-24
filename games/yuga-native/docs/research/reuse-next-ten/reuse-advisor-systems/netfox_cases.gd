extends SceneTree
const Upstream = preload("res://interpolators.gd")
const Existing = preload("res://arena_interpolator.gd")
var checks: Array = []
func check(name: String, ok: bool, detail: Variant = null) -> void:
	checks.append({"name":name,"passed":ok,"detail":detail})
func _initialize() -> void:
	var point: Vector3 = Upstream.interpolate(Vector3(0,3,0),Vector3(2,5,4),0.5)
	check("exact upstream Vector3 interpolation retains elevation",point.is_equal_approx(Vector3(1,4,2)),str(point))
	var a := Quaternion(Vector3.UP,deg_to_rad(179.0))
	var b := Quaternion(Vector3.UP,deg_to_rad(-179.0))
	var q: Quaternion = Upstream.interpolate(a,b,0.5)
	check("upstream quaternion takes short angular path",absf(q.dot(Quaternion(Vector3.UP,PI)))>0.9999,str(q))
	var yaw: float = Upstream.interpolate(deg_to_rad(179.0),deg_to_rad(-179.0),0.5)
	check("counterexample generic float interpolation loses yaw wrap",absf(yaw)<0.0001,yaw)
	var fallback: Callable = Upstream.find_for({"x":0})
	check("counterexample unsupported dictionary fallback is invalid on this engine",not fallback.is_valid(),{"callable_valid":fallback.is_valid()})
	var extrapolated: Vector3 = Upstream.interpolate(Vector3.ZERO,Vector3.ONE,2.0)
	check("counterexample upstream fraction is not bounded",extrapolated.is_equal_approx(Vector3.ONE*2),str(extrapolated))
	var original := Existing.new()
	var old := {"x":0.0,"y":0.0,"z":0.0,"health":100.0,"respawn":0.0}
	var next := old.duplicate();next.x=20.0
	var guard: String = original._discontinuity(old,next,0.1)
	var midpoint: Vector3 = Upstream.interpolate(Vector3.ZERO,Vector3(20,0,0),0.5)
	check("existing guard must precede upstream helper",guard=="teleport" and midpoint.x==10.0,{"existing":guard,"unguarded_midpoint":str(midpoint)})
	var passed := checks.all(func(row): return row.passed)
	FileAccess.open("res://result.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"checks":checks,"engine":Engine.get_version_info().string,"scope":"Exact small MIT upstream helper executed on synthetic poses; current local guard queried; no plugin installation, networking, animation asset or visual acceptance."},"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
