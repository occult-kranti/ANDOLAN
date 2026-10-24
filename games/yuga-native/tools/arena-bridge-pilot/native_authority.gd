extends SceneTree
## Native physics backend. Current Node arena transport owns public sessions/input schema.
const Actor=preload("res://authority_actor.gd")
var tcp:=TCPServer.new()
var peer:StreamPeerTCP
var pending:=""
var options:Dictionary={}
var fixture:Dictionary={}
var contract:Dictionary={}
var world:Node3D
var actors:Dictionary={}
var slots:Dictionary={}
var tick:=0
var elapsed:=0.0
var stage_index:=-1
var stage_elapsed:=0.0
var revision:=-1
var samples:Array[Dictionary]=[]
var step_times:Array[int]=[]
var rejected_packets:=0
var initialized:=false
var poll_frames:=0
var received_bytes:=0
var duration_seconds:=0.0

func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var pair:=argument.trim_prefix("--").split("=",true,1)
			options[pair[0]]=pair[1]
	call_deferred("setup")

func setup()->void:
	Engine.max_fps=120
	fixture=JSON.parse_string(FileAccess.get_file_as_string("res://physics-fixture-v1.json"))
	contract=JSON.parse_string(FileAccess.get_file_as_string("res://bridge-contract.json"))
	for stage in contract.stages:duration_seconds+=float(stage.seconds)
	Engine.physics_ticks_per_second=int(contract.physicsHz)
	world=Node3D.new();root.add_child(world)
	# Exact existing physics fixture construction from tests/physics_authority_cases.gd.
	for collider in fixture.colliders:
		if collider.visual_only:continue
		var body:=StaticBody3D.new()
		body.name=collider.id;body.set_meta("fixture_id",collider.id)
		body.collision_layer=int(collider.layer);body.collision_mask=0
		var holder:=CollisionShape3D.new()
		if collider.shape=="box":
			var shape:=BoxShape3D.new();shape.size=v(collider.size);holder.shape=shape;body.position=v(collider.center)
		else:
			var shape:=ConvexPolygonShape3D.new();var points:=PackedVector3Array()
			for point in collider.vertices:points.append(v(point))
			shape.points=points;holder.shape=shape
		body.add_child(holder);world.add_child(body)
	var error:=tcp.listen(int(options.port),"127.0.0.1")
	if error!=OK:push_error("authority TCP listen failed");quit(2);return
	FileAccess.open(options.ready,FileAccess.WRITE).store_string(JSON.stringify({"ready":true,"engine":Engine.get_version_info().string,"physicsEngine":ProjectSettings.get_setting("physics/3d/physics_engine","GodotPhysics3D"),"fixtureHash":FileAccess.get_sha256("res://physics-fixture-v1.json"),"contractHash":FileAccess.get_sha256("res://bridge-contract.json"),"authority":"native-3d-pilot-v1"})+"\n")
	await physics_frame;await physics_frame
	initialized=true
	physics_frame.connect(advance_authority)

func v(value:Array)->Vector3:return Vector3(value[0],value[1],value[2])
func number(value:Variant)->bool:return (value is int or value is float) and is_finite(value)
func valid_input(value:Variant)->bool:
	if not value is Dictionary or value.size()!=8:return false
	for key in ["type","seq","moveX","moveZ","yaw","pitch","fire","jump"]:
		if not value.has(key):return false
	if value.type!="input" or not number(value.seq) or value.seq<0 or value.seq!=floor(value.seq) or value.seq>9007199254740991:return false
	for key in ["moveX","moveZ","yaw","pitch"]:
		if not number(value[key]):return false
	return absf(value.moveX)<=1 and absf(value.moveZ)<=1 and absf(value.yaw)<=PI+.000001 and absf(value.pitch)<=1.35 and value.fire is bool and value.jump is bool

func accept_packet(value:Variant)->void:
	if not value is Dictionary or value.size()!=5 or value.get("schema")!=1 or value.get("fixtureHash")!=FileAccess.get_sha256("res://physics-fixture-v1.json") or value.get("contractHash")!=FileAccess.get_sha256("res://bridge-contract.json") or not value.get("actors") is Array or value.actors.size()>2:
		rejected_packets+=1;return
	if not number(value.get("revision")) or value.revision!=floor(value.revision) or value.revision<=revision or value.revision>9007199254740991:
		rejected_packets+=1;return
	var seen:=[];var seen_slots:=[];var new_ids:=0
	var identifier:=RegEx.create_from_string("^[a-f0-9]{16}$")
	for row in value.actors:
		if not row is Dictionary or row.size()!=4 or not row.get("id") is String or identifier.search(row.id)==null or row.id in seen or not number(row.get("slot")) or row.slot!=floor(row.slot) or row.slot<0 or row.slot>1 or not row.get("connected") is bool or (row.get("intent")!=null and not valid_input(row.intent)):
			rejected_packets+=1;return
		if int(row.slot) in seen_slots or (slots.has(row.id) and int(slots[row.id])!=int(row.slot)):
			rejected_packets+=1;return
		for known_id in slots:
			if known_id!=row.id and int(slots[known_id])==int(row.slot):
				rejected_packets+=1;return
		if not actors.has(row.id):new_ids+=1
		seen_slots.append(int(row.slot))
		seen.append(row.id)
	if actors.size()+new_ids>2:
		rejected_packets+=1;return
	# All packet fields are validated before any actor/intent mutation.
	revision=int(value.revision)
	for row in value.actors:
		if not actors.has(row.id):
			var body:=Actor.new();body.configure(contract);world.add_child(body)
			actors[row.id]=body;slots[row.id]=int(row.slot)
			var initial:Array=contract.stages[maxi(0,stage_index)].spawn[int(row.slot)]
			body.server_reset(v(initial),maxi(0,stage_index))
		if row.connected and row.intent!=null:actors[row.id].receive_input(row.intent,tick)
		else:actors[row.id].intent={}

func advance_authority()->void:
	if not initialized:return
	var delta:=1.0/float(contract.physicsHz)
	poll_frames+=1
	var started:=Time.get_ticks_usec()
	if peer==null and tcp.is_connection_available():peer=tcp.take_connection()
	if peer!=null:
		peer.poll()
		if peer.get_status()==StreamPeerTCP.STATUS_CONNECTED:
			var available:=peer.get_available_bytes()
			if available>0:
				received_bytes+=available
				pending+=peer.get_utf8_string(available)
				if pending.length()>65536:rejected_packets+=1;peer.disconnect_from_host();pending=""
				while "\n" in pending:
					var split:=pending.find("\n");var line:=pending.substr(0,split);pending=pending.substr(split+1)
					accept_packet(JSON.parse_string(line))
	if poll_frames%60==0:
		FileAccess.open(options.report+".progress.json",FileAccess.WRITE).store_string(JSON.stringify({"frames":poll_frames,"peerConnected":peer!=null and peer.get_status()==StreamPeerTCP.STATUS_CONNECTED,"receivedBytes":received_bytes,"revision":revision,"actors":actors.size(),"rejectedPackets":rejected_packets})+"\n")
	if actors.size()<2:return
	elapsed+=delta;tick+=1
	var previous:=stage_index
	var total:=0.0;stage_index=contract.stages.size()-1;stage_elapsed=float(contract.stages[-1].seconds)
	for index in contract.stages.size():
		var duration:float=contract.stages[index].seconds
		if elapsed<total+duration:
			stage_index=index;stage_elapsed=elapsed-total;break
		total+=duration
	if stage_index!=previous:
		for id in actors:actors[id].server_reset(v(contract.stages[stage_index].spawn[int(slots[id])]),stage_index)
	for id in actors:actors[id].authority_step(delta,tick)
	var rows:=[]
	for id in actors:
		var row:Dictionary=actors[id].wire(tick);row.id=id;row.bridgeSlot=slots[id];rows.append(row)
	var finished:=elapsed>=duration_seconds
	var state:={"schema":1,"fixtureHash":FileAccess.get_sha256("res://physics-fixture-v1.json"),"contractHash":FileAccess.get_sha256("res://bridge-contract.json"),"nativeTick":tick,"nativeTime":elapsed,"stage":String(contract.stages[stage_index].id),"stageTime":stage_elapsed,"epoch":stage_index,"done":finished,"revision":revision,"actors":rows,"rejectedPackets":rejected_packets}
	if tick%3==0 and peer!=null and peer.get_status()==StreamPeerTCP.STATUS_CONNECTED:
		peer.put_data((JSON.stringify(state)+"\n").to_utf8_buffer())
		samples.append(state)
	step_times.append(Time.get_ticks_usec()-started)
	if finished and not options.has("saved"):
		options.saved=true
		step_times.sort()
		FileAccess.open(options.report,FileAccess.WRITE).store_string(JSON.stringify({"scope":"Native CharacterBody3D authoritative fixture; no rendered game, full match or physical GPU","engine":Engine.get_version_info().string,"samples":samples,"stepMicroseconds":{"p50":step_times[step_times.size()/2],"p95":step_times[int(step_times.size()*.95)],"max":step_times[-1]},"source_fixture":fixture.fixture_id,"rejectedPackets":rejected_packets},"  ")+"\n")
