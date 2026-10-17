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
func run()->void:
 var values:Array=[42,[],{},true,null]
 for channel in ["input","event","snapshot"]:
  var fields:Array=["room","actor_id"] if channel=="input" else ["room","kind","actor_id","target_id"] if channel=="event" else ["room","owner_id"]
  for field in fields:
   for bad in values:
    var v:Dictionary=input() if channel=="input" else event() if channel=="event" else snapshot()
    if field=="owner_id":v.entities[0].owner_id=bad
    else:v[field]=bad
    var g=guard()
    var before:Dictionary=g.report()
    print("PROBE ",channel,".",field," type ",type_string(typeof(bad)))
    var r:Variant=g.call("accept_"+channel,v)
    rows.append({"case":channel+"."+field,"bad_type":type_string(typeof(bad)),"returned_dictionary":r is Dictionary,"result":r,"state_unchanged":g.report()==before})
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(C.CATALOG_PATH))
 for field in ["buttons_mask","simulation_hz","authority"]:
  var changed:Dictionary=catalog.duplicate(true)
  changed.profiles[0][field]=511 if field=="buttons_mask" else 120 if field=="simulation_hz" else "different_authority"
  var admitted:Variant=C.validate_catalog(changed)
  var original=guard()
  var other=C.new()
  other._catalog=changed
  var opened:Variant=other.open_session(PROFILE,original.descriptor(PROFILE),SCOPE)
  var flight=input();flight.buttons=16
  rows.append({"case":"catalogue_tamper_"+field,"validation":admitted,"compatibility":C.compatibility(original.descriptor(PROFILE),other.descriptor(PROFILE)),"opened":opened,"flight_result":other.accept_input(flight)})
 var f=FileAccess.open("/workspace/scratch/yuga-batch1-independent/contracts-probe-r2.json",FileAccess.WRITE)
 f.store_string(JSON.stringify({"source_sha256":FileAccess.get_sha256("res://scripts/native_contracts.gd"),"rows":rows},"  ")+"\n")
 quit()
