extends SceneTree
var output := ""
var frozen := ""
var old_path := ""
var checks: Array = []
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		if arg.begins_with("--catalog="): frozen = arg.trim_prefix("--catalog=")
		if arg.begins_with("--old9="): old_path = arg.trim_prefix("--old9=")
	call_deferred("run")
func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func run() -> void:
	var script = load("res://scripts/native_contracts.gd")
	check("Actual PCK compiled contract resource loads",script is GDScript)
	if not script is GDScript: finish({});return
	var guard = script.new()
	check("Actual packed catalog loads through compiled validator",guard.load_catalog().ok)
	var expected: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(frozen))
	var profile: Dictionary = expected.profiles[1]
	var descriptor: Dictionary = guard.descriptor("native-offline-triad")
	check("Actual packed catalog bytes equal frozen source catalog",FileAccess.get_sha256("res://assets/contracts/native-contracts-v1.json")==FileAccess.get_sha256(frozen))
	check("Compiled native content revision and actual content/map identities match frozen10",descriptor.versions.content==10 and descriptor.content_sha256==profile.content_sha256 and descriptor.map_sha256==profile.map_sha256 and descriptor.map_id==profile.map_id,{"descriptor":descriptor})
	check("Browser and proposal remain content1 with original protocol/state",guard.descriptor("browser-p2-3v3").versions.content==1 and guard.profile("browser-p2-3v3").protocol==2 and guard.descriptor("production-6v6").versions.content==1 and guard.profile("production-6v6").state=="proposed")
	var old: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(old_path))
	var before: Dictionary = guard.report()
	var scope := {"room":"AUDIT","epoch":1,"identity":"hero"}
	var rejected: Dictionary = guard.open_session("native-offline-triad",old,scope)
	check("Actual compiled PCK rejects old9 admission transactionally",not rejected.ok and rejected.code=="MISMATCH_VERSIONS" and rejected.details.field=="content" and guard.report()==before)
	check("Actual compiled PCK opens only a current matching validator session",guard.open_session("native-offline-triad",descriptor,scope).ok and guard.report().network_connected==false)
	before = guard.report()
	var replay := {"format":1,"descriptor":old,"room":"AUDIT","epoch":1,"identity":"hero","seed":1,"record_count":0}
	check("Actual compiled PCK rejects old9 replay without touching live guard",not guard.validate_replay(replay,[]).ok and guard.report()==before)
	var forged: Dictionary = descriptor.duplicate(true);forged.content_sha256=old.content_sha256
	check("Actual compiled PCK rejects stale source digest at content10",not guard.resume_session(forged,scope).ok and guard.report()==before)
	finish(descriptor)
func finish(descriptor: Dictionary) -> void:
	var passed := checks.all(func(row):return row.passed)
	var result := {"passed":passed,"checks":checks,"descriptor":descriptor,"engine":Engine.get_version_info(),"executable":OS.get_executable_path(),"packed_catalog_sha256":FileAccess.get_sha256("res://assets/contracts/native-contracts-v1.json"),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Actual compiled contract/catalog loaded from supplied main PCK with headless Godot; pure RefCounted admission/replay validation only. No scenes, imports, rendering, online connection or Windows execution."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if passed else 1)
