extends SceneTree
## Independent data/lifecycle checks against the frozen isolated VFX project.
const Lamp=preload("res://flame_lamp.gd")
const Source=preload("res://source_loader.gd")
const Effects=preload("res://scripts/rama_ability_effects.gd")
const Fixture=preload("res://event_fixture.gd")
var rows: Array=[]
func _initialize()->void:call_deferred("run")
func check(label: String, passed: bool, evidence: Variant=null)->void:
	rows.append({"name":label,"passed":passed,"detail":evidence})
func run()->void:
	var lamp=Lamp.new();root.add_child(lamp)
	check("frozen exact source configures",lamp.configure(Source.load_diya()),lamp.report())
	lamp.set_viewer_distance(18.0)
	check("exact culling boundary keeps flame and bounded light",lamp.report().visible and lamp.report().light_energy>0)
	lamp.set_suspended(true);lamp.set_viewer_distance(18.0001)
	var original_phase: float=lamp.phase
	for delta in [NAN,INF,-INF,-.0001,0.0,.5,.50001]:lamp.step(delta)
	check("culling plus pause and invalid deltas never restore light or advance phase",not lamp.report().visible and lamp.report().light_energy==0 and lamp.phase==original_phase)
	lamp.set_options(true,true);lamp.set_viewer_distance(0.0)
	check("paused culling recovery keeps reduced options and fixed phase",lamp.report().visible and lamp.report().light_energy<=.260001 and lamp.phase==original_phase and lamp.materials.all(func(m):return m.get_shader_parameter("reduced_motion")==true))
	lamp.set_suspended(false)
	lamp.phase=TAU*100.0-.01
	var expected_phase: float=lamp.phase+.02
	lamp.step(.02)
	check("bounded phase wrap remains continuous for both shader frequencies",lamp.phase<.02 and absf(sin(expected_phase*4.2)-sin(lamp.phase*4.2))<.00001 and absf(sin(expected_phase*8.2)-sin(lamp.phase*8.2))<.00001)
	paused=true;var paused_phase: float=lamp.phase;lamp.step(.5);paused=false
	check("explicit stepping cannot bypass actual tree pause",lamp.phase==paused_phase)
	lamp.set_source_mask_enabled(false)
	check("source mask toggle reaches every retained source material",lamp.source_materials.all(func(m):return m.get_shader_parameter("mask_active")==false))
	var effects=Effects.new();root.add_child(effects);effects.set_process(false)
	var accepted:=0
	for id in range(1,33):
		if effects.consume_event(Fixture.event("begin",id,id,0.0)):accepted+=1
	var pressure: Dictionary=effects.report()
	check("cast pressure is capped at twelve without invalid resources",accepted==12 and pressure.active==12 and pressure.counts.capacity==20 and pressure.finite,pressure)
	effects.set_suspended(true)
	for i in range(20):effects.step(.5)
	check("suspended pressure cannot expire or advance presentation",effects.report().casts==pressure.casts)
	effects.set_suspended(false)
	for i in range(100):effects.step(.5)
	check("missing authority eventually expires all capped casts",effects.report().active==0 and effects.report().finite,effects.report())
	var new_event: Dictionary=Fixture.event("begin",1,1,0.0);new_event.generation=2
	var old_event: Dictionary=Fixture.event("begin",99,100,0.0)
	check("new generation can reset presentation but old-generation replay cannot resurrect it",effects.consume_event(new_event) and not effects.consume_event(old_event) and effects.report().active==1 and effects.report().generation==2)
	effects.reset()
	check("reset after pressure leaves zero active, pooled and allocated effects",effects.report().active==0 and effects.report().allocated_impacts==0 and effects.report().meshes==0)
	var passed:=rows.all(func(r):return r.passed)
	var report:={"passed":passed,"cases":rows.size(),"checks":rows,"lamp_sha256":FileAccess.get_sha256("res://flame_lamp.gd"),"manifest_sha256":FileAccess.get_sha256("res://source-manifest.json"),"scope":"Independent headless lifecycle/clock/capacity counterexamples against the frozen isolated VFX preview. No image, temporal-render, gameplay authority or physical-GPU acceptance."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	effects.free();lamp.free()
	print(JSON.stringify({"passed":passed,"cases":rows.size()}));quit(0 if passed else 1)
