extends SceneTree
const C = preload("res://scripts/native_contracts.gd")
const PROFILE = "browser-p2-3v3"
const SCOPE = {"room":"QA","epoch":1,"identity":"hero"}
var rows:Array=[]
func input()->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"seq":0,"actor_id":"hero","move":[0,0],"yaw":0,"pitch":0,"buttons":0}
func event()->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"seq":0,"tick":0,"kind":"shot","actor_id":"hero","target_id":"","position":[0,0,0],"amount":0}
func entity()->Dictionary:
 return {"id":"hero","generation":1,"kind":"actor","team":"sun","position":[0,0,0],"yaw":0,"pitch":0,"discontinuity":0,"alive":true,"ack_input":-1,"owner_id":""}
func snapshot()->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"tick":0,"entities":[entity()]}
func guard()->RefCounted:
 var g=C.new()
 g.load_catalog()
 g.open_session(PROFILE,g.descriptor(PROFILE),SCOPE)
 return g
func _initialize()->void:
 call_deferred("run")
func record(name_:String,r:Variant,before:Dictionary,after:Dictionary,expected_ok:bool=false)->void:
 var shape:bool=r is Dictionary and r.get("ok") is bool and r.get("code") is String and r.get("details") is Dictionary
 rows.append({"case":name_,"passed":shape and r.ok==expected_ok and before==after,"result":r,"state_unchanged":before==after})
func run()->void:
 var source_before:String=FileAccess.get_sha256("res://scripts/native_contracts.gd")
 var g=guard()
 var before:Dictionary=g.report()
 var desc:Dictionary=g.descriptor(PROFILE)
 var valid_snapshot:Dictionary=snapshot();valid_snapshot.entities[0].ack_input=0
 var records:Array=[{"kind":"input","value":input()},{"kind":"snapshot","value":valid_snapshot},{"kind":"event","value":event()}]
 var header:Dictionary={"format":1,"descriptor":desc,"room":"QA","epoch":1,"identity":"hero","seed":5,"record_count":3}
 record("valid_replay_isolated",g.validate_replay(header,records),before,g.report(),true)
 record("valid_replay_repeated",g.validate_replay(header,records),before,g.report(),true)
 record("json_numeric_roundtrip",g.validate_replay(JSON.parse_string(JSON.stringify(header)),JSON.parse_string(JSON.stringify(records))),before,g.report(),true)
 var bad_types:Array=[[],{},true,null,"bad"]
 for field in ["format","epoch","seed","record_count"]:
  for bad in bad_types:
   var h:Dictionary=header.duplicate(true);h[field]=bad
   record("replay_header_"+field+"_"+type_string(typeof(bad)),g.validate_replay(h,records),before,g.report())
 for field in ["room","identity"]:
  for bad in [42,[],{},true,null]:
   var h:Dictionary=header.duplicate(true);h[field]=bad
   record("replay_header_"+field+"_"+type_string(typeof(bad)),g.validate_replay(h,records),before,g.report())
 for field in C.DESCRIPTOR_KEYS:
  for bad in [[],{},true,null,42]:
   var d:Dictionary=desc.duplicate(true);d[field]=bad
   record("descriptor_"+field+"_"+type_string(typeof(bad)),C.compatibility(desc,d),before,g.report())
 for field in C.VERSION_KEYS:
  for bad in bad_types:
   var d:Dictionary=desc.duplicate(true);d.versions[field]=bad
   record("descriptor_version_"+field+"_"+type_string(typeof(bad)),C.compatibility(desc,d),before,g.report())
 for field in ["kind","value"]:
  for bad in [42,[],{},true,null,"bad"]:
   var r:Array=records.duplicate(true);r[0][field]=bad
   record("replay_record_"+field+"_"+type_string(typeof(bad)),g.validate_replay(header,r),before,g.report())
 var rejected_epoch:Dictionary=header.duplicate(true);rejected_epoch.epoch=2
 record("foreign_epoch_records_rejected",g.validate_replay(rejected_epoch,records),before,g.report())
 var reordered:Array=records.duplicate(true);reordered.reverse()
 record("ack_before_input_rejected",g.validate_replay(header,reordered),before,g.report())
 var source_after:String=FileAccess.get_sha256("res://scripts/native_contracts.gd")
 var passed:bool=source_before==source_after
 for r in rows:passed=passed and r.passed
 var report:Dictionary={"passed":passed,"checks":rows.size(),"source_sha256":source_before,"source_unchanged":source_before==source_after,"rows":rows,"scope":"Independent pure-validator malformed header/descriptor/replay and transactional probes; no socket or authority re-simulation"}
 var f=FileAccess.open("/workspace/scratch/yuga-batch2-qa/contracts-r1/contracts-replay.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  ")+"\n")
 print(JSON.stringify({"passed":passed,"checks":rows.size()}))
 quit(0 if passed else 1)
