extends SceneTree
const Bridge = preload("res://scripts/entity_bridge.gd")
var checks: Array[Dictionary] = []
func _initialize():
 call_deferred("run")
func run():
 var bridge = Bridge.new()
 root.add_child(bridge)
 for kind in ["actor", "minion", "neutral", "projectile"]:
  for yaw in [-PI, -1.7, 0.0, 1.2, PI]:
   for pitch in [-1.35, -0.65, 0.0, 0.45, 1.35]:
    var e={"id":"probe","generation":1,"kind":kind,"team":"sun","position":[0,0,0],"yaw":yaw,"pitch":pitch,"discontinuity":0,"alive":true,"ack_input":-1,"owner_id":""}
    bridge._clear_views()
    bridge._sync_entities({"probe":e})
    var node:Node3D=bridge.entity_node("probe")
    var actual:Vector3=node.get_node("Body").global_basis.y if kind=="projectile" else node.get_node("Aim").global_basis.z
    var expected:=Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))
    checks.append({"kind":kind,"yaw":yaw,"pitch":pitch,"distance":actual.distance_to(expected),"passed":actual.distance_to(expected)<0.000001})
 var invalid=Bridge.aim_direction(NAN,0)==Vector3.ZERO and Bridge.aim_direction(0,INF)==Vector3.ZERO
 checks.append({"id":"nonfinite aim rejects","passed":invalid})
 var collision_count=0
 for n in bridge.find_children("*","CollisionObject3D",true,false):collision_count+=1
 checks.append({"id":"presentation remains collision-free","passed":collision_count==0})
 var failed=checks.filter(func(c):return not c.passed).size()
 var report={"source_sha256":FileAccess.get_sha256("res://scripts/entity_bridge.gd"),"probe_sha256":FileAccess.get_sha256(get_script().resource_path),"passed":failed==0,"failed":failed,"checks":checks,"scope":"Independent headless actual node basis review via direct presentation adapter; no server transport or rasterized art claim"}
 var file=FileAccess.open("/workspace/scratch/yuga-physics-authority/bridge-axis-review.json",FileAccess.WRITE)
 file.store_string(JSON.stringify(report,"  ")+"\n")
 print(JSON.stringify({"checks":checks.size(),"failed":failed}))
 bridge.free()
 quit(1 if failed else 0)
