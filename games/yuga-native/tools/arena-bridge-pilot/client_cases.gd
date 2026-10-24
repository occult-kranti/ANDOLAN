extends SceneTree
## Two real unchanged protocol-2 native clients observe the isolated native authority.
const Client=preload("res://scripts/arena_client.gd")
const Interpolator=preload("res://scripts/arena_interpolator.gd")
var client:Node
var sampler:RefCounted
var options:Dictionary={}
var contract:Dictionary={}
var recordings:Array[Dictionary]=[]
var checks:Array[Dictionary]=[]
var faults:Array[String]=[]
var peer_id:=""
var injected:=false
var stage_acks:Dictionary={}
var done:=false

func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var pair:=argument.trim_prefix("--").split("=",true,1);options[pair[0]]=pair[1]
	call_deferred("run")
func check(label:String,passed:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":passed,"detail":detail})
func on_snapshot(snapshot:Dictionary)->void:
	if not snapshot.has("bridge"):return
	recordings.append(snapshot)
	sampler.push_snapshot(snapshot)
	for actor in snapshot.actors:
		if actor.id!=client.identity:peer_id=actor.id
	if snapshot.bridge.done:done=true

func run()->void:
	Engine.max_fps=120
	contract=JSON.parse_string(FileAccess.get_file_as_string("res://bridge-contract.json"))
	client=Client.new();root.add_child(client);sampler=Interpolator.new()
	client.snapshot_received.connect(on_snapshot)
	client.protocol_fault.connect(func(code:String):faults.append(code))
	var room:=""
	if options.role=="guest":
		var deadline:=Time.get_ticks_msec()+6000
		while room.is_empty() and Time.get_ticks_msec()<deadline:
			if FileAccess.file_exists(options.coordination):
				var data:Variant=JSON.parse_string(FileAccess.get_file_as_string(options.coordination))
				if data is Dictionary:room=data.get("room","")
			await process_frame
	client.connect_arena(options.url,"rama","W6 "+String(options.role),room)
	var deadline:=Time.get_ticks_msec()+18000
	while not done and Time.get_ticks_msec()<deadline:
		if client.state=="playing":
			if options.role=="host" and not FileAccess.file_exists(options.coordination):FileAccess.open(options.coordination,FileAccess.WRITE).store_string(JSON.stringify({"room":client.room}))
			var snapshot:Dictionary=client.get_snapshot()
			if snapshot.has("bridge"):
				var slot:=0
				for actor in snapshot.actors:
					if actor.id==client.identity:slot=int(actor.get("bridgeSlot",0 if options.role=="host" else 1))
				for stage in contract.stages:
					if stage.id!=snapshot.bridge.stage:continue
					var intent:Dictionary=stage.inputs[slot]
					if not intent.has("stopSendingAfter") or snapshot.bridge.stageTime<float(intent.stopSendingAfter):
						client.send_input(Vector2(0,float(intent.get("moveZ",0))),0,float(intent.get("pitch",0)),intent.get("fire",false),snapshot.bridge.stageTime<float(intent.get("jumpUntil",0)))
				if not injected and snapshot.bridge.nativeTick>10:
					injected=true
					var basic:={"type":"input","seq":0,"moveX":0,"moveZ":0,"yaw":0,"pitch":0,"fire":false,"jump":false}
					client._send(basic) # old sequence must not roll acknowledgement back.
					if options.role=="host":
						for bad in [{"x":9999,"y":9999,"z":9999},{"elevation":9999},{"teleport":true}]:
							var packet:=basic.duplicate();packet.merge(bad);client._send(packet)
		await process_frame
	check("native stage sequence completed over real socket",done,{"snapshots":recordings.size(),"state":client.state})
	check("two unique peers observed",not peer_id.is_empty() and peer_id!=client.identity)
	check("client local nonfinite intent refused",not client.send_input(Vector2(NAN,0),0,0,false,false))
	var epoch:=-1;var tick:=-1;var monotonic:=true;var bounded:=true;var seen:={};var acknowledged:=false
	for snapshot in recordings:
		monotonic=monotonic and snapshot.tick>tick and int(snapshot.bridge.epoch)>=epoch
		tick=int(snapshot.tick);epoch=int(snapshot.bridge.epoch)
		seen[snapshot.bridge.stage]=true
		for actor in snapshot.actors:
			bounded=bounded and absf(actor.x)<100 and actor.y>-.1 and actor.y<10 and absf(actor.z)<40
			if actor.id==client.identity and actor.get("bridgeAckSeq",-1)>2:acknowledged=true
	check("ticks and server transition epochs monotonic",monotonic)
	check("all six shared input stages observed",seen.size()>=6,seen)
	check("server physics acknowledgement advances",acknowledged)
	check("forged position elevation teleport fields cannot escape fixture",bounded)
	if options.role=="host":check("existing public parser rejects all three position claims",faults.count("SERVER_REJECTED_REQUEST")>=3,faults)
	check("existing interpolator accepts received3D data",sampler.sample().actors.size()>0)
	var identity:String=client.identity
	client.disconnect_arena();await process_frame
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(options.report,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"role":options.role,"identity":identity,"peer":peer_id,"checks":checks,"faults":faults,"recordings":recordings,"scope":"Real loopback native transports; headless presentation only; no complete match or rendered client"},"  ")+"\n")
	print(JSON.stringify({"passed":passed,"role":options.role,"checks":checks.size(),"snapshots":recordings.size()}))
	quit(0 if passed else 1)
