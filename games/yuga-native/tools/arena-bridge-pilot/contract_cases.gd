extends "res://native_authority.gd"
## Cheap independent-of-world validation probes; no TCP listener or moving body.
var checks:Array[Dictionary]=[]
func check(label:String,passed:bool)->void:checks.append({"name":label,"passed":passed})
func _initialize()->void:
	var input:Dictionary=JSON.parse_string('{"type":"input","seq":1,"moveX":0,"moveZ":1,"yaw":0,"pitch":0,"fire":false,"jump":false}')
	check("JSON float integer input accepted",valid_input(input))
	for edit in [{"x":900},{"y":900},{"teleport":true},{"pitch":4},{"yaw":100},{"seq":-1},{"seq":1.5},{"seq":9007199254740992},{"seq":false},{"moveX":NAN},{"moveZ":1e308},{"jump":1}]:
		var bad:=input.duplicate(true);bad.merge(edit,true);check("bad intent "+str(checks.size()),not valid_input(bad))
	var packet:={"schema":1,"fixtureHash":FileAccess.get_sha256("res://physics-fixture-v1.json"),"contractHash":FileAccess.get_sha256("res://bridge-contract.json"),"revision":1,"actors":[]}
	accept_packet(packet);check("empty bootstrap revision positive control",revision==1 and actors.is_empty())
	var a:={"id":"aaaaaaaaaaaaaaaa","slot":0,"connected":true,"intent":null}
	var b:={"id":"bbbbbbbbbbbbbbbb","slot":1,"connected":true,"intent":null}
	for rows in [[a,a],[a,{"id":"bbbbbbbbbbbbbbbb","slot":0,"connected":true,"intent":null}],[a,{"id":"bbbbbbbbbbbbbbbb","slot":1.5,"connected":true,"intent":null}],[a,{"id":"----------------","slot":1,"connected":true,"intent":null}]]:
		var bad:=packet.duplicate(true);bad.revision=2;bad.actors=rows;var before:=rejected_packets
		accept_packet(bad);check("malformed actor batch atomic "+str(checks.size()),rejected_packets==before+1 and revision==1 and actors.is_empty())
	actors={a.id:null};slots={a.id:0}
	var occupied:=packet.duplicate(true);occupied.revision=2;occupied.actors=[{"id":b.id,"slot":0,"connected":true,"intent":null}]
	var before:=rejected_packets;accept_packet(occupied)
	check("later partial packet cannot steal an occupied slot",rejected_packets==before+1 and actors.size()==1 and revision==1)
	actors={a.id:null,b.id:null};slots={a.id:0,b.id:1}
	var expanded:=packet.duplicate(true);expanded.revision=2;expanded.actors=[{"id":"cccccccccccccccc","slot":0,"connected":true,"intent":null},{"id":"dddddddddddddddd","slot":1,"connected":true,"intent":null}]
	before=rejected_packets;accept_packet(expanded)
	check("cumulative registry remains exactly two known identities",rejected_packets==before+1 and actors.size()==2 and revision==1)
	var switched:=packet.duplicate(true);switched.revision=2;switched.actors=[{"id":a.id,"slot":1,"connected":true,"intent":null}]
	before=rejected_packets;accept_packet(switched);check("existing actor slot immutable",rejected_packets==before+1 and slots[a.id]==0 and revision==1)
	var passed:=checks.all(func(row):return row.passed)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):FileAccess.open(argument.trim_prefix("--report="),FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"checks":checks},"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
