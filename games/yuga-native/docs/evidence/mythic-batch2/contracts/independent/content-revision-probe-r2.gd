extends SceneTree
const C = preload("res://scripts/native_contracts.gd")
const OUT = "/workspace/scratch/yuga-contracts-b2-independent/"
const OLD = "/workspace/scratch/yuga-bridge/native-practice-content1-descriptor.json"
const SCOPE = {"room":"QA","epoch":1,"identity":"hero"}
const EXPECTED = {"browser-p2-3v3":1,"native-offline-triad":2,"production-6v6":1}
var rows:Array=[]

func _initialize()->void:
 call_deferred("run")

func check(name_:String,passed:bool,details:Variant=null)->void:
 rows.append({"case":name_,"passed":passed,"details":details})

func rejected(name_:String,g:RefCounted,before:Dictionary,result:Dictionary,code_:String,field_:String="")->void:
 var same:bool=g.report()==before
 check(name_,not result.ok and result.code==code_ and same and (field_.is_empty() or result.details.get("field")==field_),{"result":result,"state_unchanged":same})

func input(seq_:int=0)->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"seq":seq_,"actor_id":"hero","move":[0,0],"yaw":0,"pitch":0,"buttons":0}

func event(seq_:int=0)->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"seq":seq_,"tick":seq_,"kind":"shot","actor_id":"hero","target_id":"","position":[0,0,0],"amount":0}

func snapshot(tick_:int=0)->Dictionary:
 return {"version":1,"room":"QA","epoch":1,"tick":tick_,"entities":[{"id":"hero","generation":1,"kind":"actor","team":"sun","position":[0,0,0],"yaw":0,"pitch":0,"discontinuity":0,"alive":true,"ack_input":tick_,"owner_id":""}]}

func replay_header(desc:Dictionary)->Dictionary:
 return {"format":1,"descriptor":desc,"room":"QA","epoch":1,"identity":"hero","seed":5,"record_count":3}

func run()->void:
 var source_before:String=FileAccess.get_sha256("res://scripts/native_contracts.gd")
 var catalog_before:String=FileAccess.get_sha256(C.CATALOG_PATH)
 var catalog:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(C.CATALOG_PATH))
 var g=C.new()
 check("catalog_load",g.load_catalog().ok)
 check("catalog_current_valid",C.validate_catalog(catalog).ok)
 for index in catalog.profiles.size():
  var profile_id:String=catalog.profiles[index].id
  var desc:Dictionary=g.descriptor(profile_id)
  var expected_versions:Dictionary=catalog.envelope_versions.duplicate(true)
  expected_versions.content=EXPECTED[profile_id]
  check("descriptor_"+profile_id+"_only_content_override",desc.versions==expected_versions,desc.versions)
  check("descriptor_"+profile_id+"_wire_versions_stay_1",desc.versions.input==1 and desc.versions.event==1 and desc.versions.entity==1 and desc.versions.replay==1)
  check("descriptor_"+profile_id+"_json_roundtrip",C.compatibility(desc,JSON.parse_string(JSON.stringify(desc))).ok)
  var bad_cases:Array=[{"name":"missing"},{"name":"String","value":str(EXPECTED[profile_id])},{"name":"Array","value":[]},{"name":"Dictionary","value":{}},{"name":"true","value":true},{"name":"false","value":false},{"name":"null","value":null},{"name":"fraction","value":1.5},{"name":"zero","value":0},{"name":"negative","value":-1},{"name":"large","value":65536},{"name":"wrong_known_revision","value":1 if EXPECTED[profile_id]==2 else 2}]
  for entry in bad_cases:
   var bad:Dictionary=catalog.duplicate(true)
   if entry.name=="missing":bad.profiles[index].erase("content_revision")
   else:bad.profiles[index].content_revision=entry.value
   var result:Dictionary=C.validate_catalog(bad)
   check("catalog_"+profile_id+"_"+entry.name,not result.ok and result.code=="CATALOG_CONTENT_REVISION",result)
   var path:String=OUT+"catalog-r2-"+profile_id+"-"+entry.name+".json"
   var f=FileAccess.open(path,FileAccess.WRITE)
   f.store_string(JSON.stringify(bad,"",true,true))
   f.close()
   var before:Dictionary=g.report()
   var prior_descriptor:Dictionary=g.descriptor(profile_id)
   var loaded:Dictionary=g.load_catalog(path)
   check("load_"+profile_id+"_"+entry.name+"_transactional",not loaded.ok and loaded.code=="CATALOG_CONTENT_REVISION" and g.report()==before and g.descriptor(profile_id)==prior_descriptor,loaded)
  for nonfinite in [INF,-INF,NAN]:
   var invalid:Dictionary=catalog.duplicate(true)
   invalid.profiles[index].content_revision=nonfinite
   var result:Dictionary=C.validate_catalog(invalid)
   check("catalog_"+profile_id+"_nonfinite_"+str(nonfinite),not result.ok and result.code=="CATALOG_CONTENT_REVISION",result)
 check("global_envelope_versions_not_mutated",catalog.envelope_versions==g._catalog.envelope_versions and catalog.envelope_versions.values().all(func(v):return v==1))
 var old_desc:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OLD))
 var current:Dictionary=g.descriptor("native-offline-triad")
 check("preserved_content1_descriptor_structurally_valid",C.validate_descriptor(old_desc).ok and old_desc.versions.content==1)
 var old_revision_only:Dictionary=current.duplicate(true)
 old_revision_only.versions.content=1
 for entry in [{"name":"preserved_content1","descriptor":old_desc},{"name":"revision_only_content1","descriptor":old_revision_only}]:
  var desc:Dictionary=entry.descriptor
  var compatible:Dictionary=C.compatibility(current,desc)
  check(entry.name+"_compatibility",not compatible.ok and compatible.code=="MISMATCH_VERSIONS" and compatible.details.get("field")=="content",compatible)
  var reverse:Dictionary=C.compatibility(desc,current)
  check(entry.name+"_compatibility_reverse",not reverse.ok and reverse.code=="MISMATCH_VERSIONS" and reverse.details.get("field")=="content",reverse)
  var empty_before:Dictionary=g.report()
  rejected(entry.name+"_open_transactional",g,empty_before,g.open_session("native-offline-triad",desc,SCOPE),"MISMATCH_VERSIONS","content")
 check("current_content2_open",g.open_session("native-offline-triad",current,SCOPE).ok)
 check("native_input_envelope1_accepted",g.accept_input(input()).ok)
 check("native_event_envelope1_accepted",g.accept_event(event()).ok)
 check("native_entity_envelope1_accepted",g.accept_snapshot(snapshot()).ok)
 var active_before:Dictionary=g.report()
 var records:Array=[{"kind":"input","value":input()},{"kind":"event","value":event()},{"kind":"snapshot","value":snapshot()}]
 for entry in [{"name":"preserved_content1","descriptor":old_desc},{"name":"revision_only_content1","descriptor":old_revision_only}]:
  var desc:Dictionary=entry.descriptor
  rejected(entry.name+"_resume_transactional",g,active_before,g.resume_session(desc,SCOPE),"MISMATCH_VERSIONS","content")
  rejected(entry.name+"_migrate_transactional",g,active_before,g.migrate_session("native-offline-triad",desc,{"room":"QA","epoch":2,"identity":"hero"}),"MISMATCH_VERSIONS","content")
  rejected(entry.name+"_replay_transactional",g,active_before,g.validate_replay(replay_header(desc),records),"MISMATCH_VERSIONS","content")
 for channel in ["input","event","snapshot"]:
  var packet:Dictionary=input(1) if channel=="input" else event(1) if channel=="event" else snapshot(1)
  packet.version=2
  rejected("content2_does_not_change_"+channel+"_envelope",g,active_before,g.call("accept_"+channel,packet),"MESSAGE_VERSION")
 var valid_replay:Dictionary=g.validate_replay(replay_header(current),records)
 check("current_replay_format1_accepted_and_isolated",valid_replay.ok and valid_replay.code=="REPLAY_VALIDATED" and valid_replay.details.records==3 and g.report()==active_before,valid_replay)
 var resume:Dictionary=g.resume_session(current,SCOPE)
 check("current_resume_retains_state",resume.ok and resume.code=="RESUMED" and g.report()==active_before,resume)
 var migration:Dictionary=g.migrate_session("native-offline-triad",current,{"room":"QA","epoch":2,"identity":"hero"})
 var migrated:Dictionary=g.report()
 check("current_migrate_new_epoch_resets_state",migration.ok and migrated.session.scope.epoch==2 and migrated.last_input_seq==-1 and migrated.last_event_seq==-1 and migrated.last_snapshot_tick==-1 and migrated.entities.is_empty() and migrated.entity_history.is_empty(),migration)
 check("sources_unchanged",source_before==FileAccess.get_sha256("res://scripts/native_contracts.gd") and catalog_before==FileAccess.get_sha256(C.CATALOG_PATH))
 var passed:bool=true
 for row in rows:passed=passed and row.passed
 var report:Dictionary={"passed":passed,"checks":rows.size(),"source_sha256":source_before,"catalog_sha256":catalog_before,"old_descriptor_sha256":FileAccess.get_sha256(OLD),"rows":rows,"scope":"Pure native contracts; malformed content revisions, descriptor-only content override, preserved content1 rejection, transactional state and compatible format1 wire controls. No transport, render or authority simulation."}
 var f=FileAccess.open(OUT+"content-revision-r2.json",FileAccess.WRITE)
 f.store_string(JSON.stringify(report,"  ")+"\n")
 f.close()
 print(JSON.stringify({"passed":passed,"checks":rows.size()}))
 quit(0 if passed else 1)
