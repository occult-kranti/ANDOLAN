extends SceneTree
const Lamp=preload("flame_lamp.gd")
const Effects=preload("res://scripts/rama_ability_effects.gd")
const Fixture=preload("event_fixture.gd")
const Source=preload("source_loader.gd")
var rows: Array=[]
func check(label: String, passed: bool, evidence: Variant=null) -> void:
    rows.append({"case":label,"passed":passed,"evidence":evidence})
func _initialize() -> void:call_deferred("run")
func run() -> void:
    var lamp=Lamp.new();root.add_child(lamp)
    var source=Source.load_diya()
    var empty:=PackedScene.new();var node:=Node3D.new();empty.pack(node);node.free()
    check("incompatible source rolls back all children",not lamp.configure(empty) and lamp.get_child_count()==0)
    check("exact imported source configures",lamp.configure(source),lamp.report())
    var count:=lamp.get_child_count()
    check("repeated configure does not duplicate mesh",not lamp.configure(source) and count==lamp.get_child_count())
    lamp.step(.125);var phase: float=lamp.phase
    for invalid in [NAN,INF,-.1,.5001]:lamp.step(invalid)
    check("invalid delta cannot advance flame",lamp.phase==phase)
    lamp.set_suspended(true);lamp.step(.25)
    check("pause freezes flame and light clock",lamp.phase==phase,lamp.report())
    lamp.set_suspended(false);lamp.step(.125)
    check("unpause continues bounded clock",is_equal_approx(lamp.phase,.25),lamp.report())
    paused=true;lamp.step(.25);paused=false
    check("tree pause also freezes clock",is_equal_approx(lamp.phase,.25),lamp.report())
    var full: float=lamp.light.light_energy
    lamp.set_options(true,true)
    check("reduced intensity preserves cue with less light",lamp.light.light_energy>0 and lamp.light.light_energy<full,lamp.report())
    check("motion toggle reaches both materials",lamp.materials.all(func(m):return m.get_shader_parameter("reduced_motion")==true))
    check("distance culling hides surfaces and zeroes light",lamp.set_viewer_distance(18.01) and not lamp.report().visible and lamp.light.light_energy==0,lamp.report())
    check("bad distance cannot restore culled cue",not lamp.set_viewer_distance(NAN) and not lamp.set_viewer_distance(-1) and lamp.report().culled)
    check("distance recovery restores bounded surfaces",lamp.set_viewer_distance(1) and lamp.report().visible and lamp.report().flame_triangles==4,lamp.report())
    var effects=Effects.new();root.add_child(effects);effects.set_process(false)
    check("staged begin accepted",effects.consume_event(Fixture.event("begin",1,1,0.0)),effects.report())
    effects.step(.1)
    check("no projectile before release",effects.report().live_arrows==0,effects.report())
    check("staged release accepted",effects.consume_event(Fixture.event("release",1,2,.25)))
    var before: Dictionary=effects.report()
    check("duplicate release rejected",not effects.consume_event(Fixture.event("release",1,3,.25)))
    effects.set_suspended(true);effects.step(.3)
    check("pause freezes cast",effects.report().casts==before.casts,effects.report())
    effects.set_suspended(false)
    check("impact accepted",effects.consume_event(Fixture.event("impact",1,4,.75)),effects.report())
    check("pooled contact created once",effects.report().impacts==1 and effects.report().allocated_impacts==1,effects.report())
    effects.step(.43)
    check("contact expires into hidden pool",effects.report().impacts==0 and effects.report().pooled_impacts==1,effects.report())
    check("end accepted",effects.consume_event(Fixture.event("end",1,5,1.2)))
    check("second cast starts",effects.consume_event(Fixture.event("begin",2,6,0.0)))
    check("second release accepted",effects.consume_event(Fixture.event("release",2,7,.25)))
    check("contact pool reused",effects.consume_event(Fixture.event("impact",2,8,.75)) and effects.report().allocated_impacts==1 and effects.report().pooled_impacts==0,effects.report())
    effects.set_options({"reduced_motion":true,"reduced_effects":true})
    check("reused effects retain reduced options",effects.report().reduced_motion and effects.report().reduced_effects and effects.report().finite,effects.report())
    effects.reset()
    check("reset destroys active and pooled presentation",effects.report().active==0 and effects.report().allocated_impacts==0,effects.report())
    check("bad forward rejected after reset",not effects.consume_event({"schema":1,"kind":"begin","generation":2,"event_seq":9,"cast_id":3,"forward":Vector3(NAN,0,0)}))
    effects.free();lamp.free()
    var passed:=true
    for row in rows:passed=passed and row.passed
    var report:={"passed":passed,"cases":rows.size(),"checks":rows,"scope":"Headless lifecycle and source-import data checks; not render performance or gameplay authority"}
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--report="):
            var file=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
            if file==null:push_error("report path must be writable");quit(2);return
            file.store_string(JSON.stringify(report,"  ")+"\n")
    print(JSON.stringify(report));quit(0 if passed else 1)
