extends SceneTree

const Selector = preload("res://scripts/rama_visual_lod.gd")
var checks: Array[Dictionary] = []

func expect(label: String, value: bool) -> void:
	checks.append({"name": label, "passed": value})

func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var lod = Selector.new()
	expect("Near first valid sample", lod.choose_pixels(600.0, 0.016) == 0)
	for i in range(60):
		lod.choose_pixels(419.0 if i % 2 == 0 else 421.0, 0.016)
	expect("Near threshold jitter does not oscillate", lod.level == 0)
	expect("Crossed exit enters mid", lod.choose_pixels(350.0, 0.2) == 1)
	expect("Minimum hold prevents immediate return", lod.choose_pixels(700.0, 0.016) == 1)
	expect("Mid holds inside near hysteresis", lod.choose_pixels(470.0, 0.2) == 1)
	expect("Mid crosses near reentry", lod.choose_pixels(490.0, 0.2) == 0)
	expect("Fast zoom-out changes at most one level", lod.choose_pixels(1.0, 0.2) == 1)
	expect("Second held sample reaches far", lod.choose_pixels(1.0, 0.2) == 2)
	for i in range(60):
		lod.choose_pixels(159.0 if i % 2 == 0 else 161.0, 0.016)
	expect("Far threshold jitter does not oscillate", lod.level == 2)
	expect("Far reentry boundary remains held", lod.choose_pixels(180.0, 0.2) == 2)
	expect("Far crosses mid reentry", lod.choose_pixels(190.0, 0.2) == 1)
	expect("NaN height falls back to near", lod.choose_pixels(NAN, 0.2) == 0)
	expect("Fresh valid far initializes directly", lod.choose_pixels(30.0, 0.016) == 2)
	expect("Negative delta invalidates history", lod.choose_pixels(30.0, -1.0) == 0)
	expect("Infinite delta falls back near", lod.choose_pixels(30.0, INF) == 0)
	expect("Zero height falls back near", lod.choose_pixels(0.0, 0.1) == 0)
	expect("Null camera falls back near", lod.choose_camera(null, Vector3.ZERO, 1.9, 0.1) == 0)
	var camera := Camera3D.new()
	expect("Detached camera falls back near", lod.choose_camera(camera, Vector3.ZERO, 1.9, 0.1) == 0)
	root.add_child(camera)
	root.size = Vector2i(1280, 720)
	await process_frame
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	camera.fov = 30.0
	lod.reset()
	expect("Narrow FOV selects near at same distance", lod.choose_camera(camera, Vector3(0, 0, -3), 1.9, 0.1) == 0)
	camera.fov = 120.0
	lod.reset()
	expect("Wide FOV selects far at same distance", lod.choose_camera(camera, Vector3(0, 0, -3), 1.9, 0.1) == 2)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 20.0
	lod.reset()
	expect("Orthographic screen size selects far", lod.choose_camera(camera, Vector3(0, 0, -3), 1.9, 0.1) == 2)
	camera.size = 2.0
	lod.reset()
	expect("Orthographic zoom selects near", lod.choose_camera(camera, Vector3(0, 0, -3), 1.9, 0.1) == 0)
	expect("Behind camera falls back near", lod.choose_camera(camera, Vector3(0, 0, 1), 1.9, 0.1) == 0)
	expect("Invalid center falls back near", lod.choose_camera(camera, Vector3(NAN, 0, -10), 1.9, 0.1) == 0)
	expect("Negative dimensions fall back near", lod.choose_camera(camera, Vector3(0, 0, -10), -1.9, 0.1) == 0)
	lod.choose_pixels(20.0, 0.1)
	lod.reset()
	expect("Death/reset hook clears selection and hysteresis", lod.level == 0 and not lod._initialized and lod._held_seconds == 0.0)
	camera.queue_free()
	await process_frame
	expect("Freed camera falls back near", lod.choose_camera(camera, Vector3(0, 0, -10), 1.9, 0.1) == 0)
	var passed := true
	for c in checks:
		passed = passed and c.passed
	var report := {"passed": passed, "total": checks.size(), "checks": checks, "limits": ["Selector-only tests; runtime mesh binding, same-camera visual transitions and hardware cost remain separate gates."]}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report, "\t") + "\n")
	print(JSON.stringify(report))
	quit(0 if passed else 1)
