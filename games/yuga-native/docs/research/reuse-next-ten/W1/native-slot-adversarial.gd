extends "res://native_authority.gd"
## Persistent slot ownership across partial batches; no listener or physics run.
var checks := []
func _initialize() -> void: call_deferred("run_review")
func run_review() -> void:
	var output := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	contract=JSON.parse_string(FileAccess.get_file_as_string("res://bridge-contract.json"))
	for new_slot in [0,1]:
		world=Node3D.new();root.add_child(world)
		actors={"aaaaaaaaaaaaaaaa":null};slots={"aaaaaaaaaaaaaaaa":0};revision=1
		var before_rejected:=rejected_packets
		var packet:={"schema":1,"fixtureHash":FileAccess.get_sha256("res://physics-fixture-v1.json"),"contractHash":FileAccess.get_sha256("res://bridge-contract.json"),"revision":2,"actors":[{"id":"bbbbbbbbbbbbbbbb","slot":new_slot,"connected":false,"intent":null}]}
		accept_packet(packet)
		var expected_reject:bool=new_slot==0
		var rejected:bool=rejected_packets==before_rejected+1
		var passed:bool=(rejected and revision==1 and actors.size()==1 and world.get_child_count()==0) if expected_reject else (not rejected and revision==2 and actors.size()==2 and slots.get("bbbbbbbbbbbbbbbb")==1)
		checks.append({"new_slot":new_slot,"expected_rejected":expected_reject,"rejected":rejected,"actors":actors.size(),"slots":slots.duplicate(),"passed":passed})
		actors.clear();slots.clear();world.free()
	var report:={"scope":"Independent cumulative slot ownership through actual native accept_packet with one pre-existing identity; no TCP, movement, raster or public-client claim.","checks":checks,"passed":checks.all(func(row):return row.passed),"native_authority_sha256":FileAccess.get_sha256("res://native_authority.gd")}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if report.passed else 1)
