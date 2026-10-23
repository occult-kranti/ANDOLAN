extends SceneTree
const Lamp=preload("flame_lamp.gd")
const Effects=preload("res://scripts/rama_ability_effects.gd")
const Fixture=preload("event_fixture.gd")
const Source=preload("source_loader.gd")
var output:=""
var sequence:=0
var samples: Array=[]
var cast:=-1
var released:=false
var impacted:=false
var ended:=false
var controls_only:=false
func _initialize() -> void:call_deferred("run")
func send(effects: Node, kind: String, age: float) -> bool:
    sequence+=1
    return effects.consume_event(Fixture.event(kind,cast,sequence,age))
func projected_box(camera: Camera3D, lamp: Node3D, low: Vector3, high: Vector3) -> Array:
    var rect:=Rect2(camera.unproject_position(lamp.to_global(low)),Vector2.ZERO)
    for x in [low.x,high.x]:
        for y in [low.y,high.y]:
            for z in [low.z,high.z]:rect=rect.expand(camera.unproject_position(lamp.to_global(Vector3(x,y,z))))
    return [floorf(rect.position.x)-3,floorf(rect.position.y)-3,ceilf(rect.size.x)+6,ceilf(rect.size.y)+6]
func effect_screen_bounds(effects: Node3D, camera: Camera3D) -> Dictionary:
    var pending: Array=[effects];var points: Array=[]
    while not pending.is_empty():
        var node: Node=pending.pop_back();pending.append_array(node.get_children())
        if not node is MeshInstance3D or not node.is_visible_in_tree() or node.mesh==null or node.mesh.get_surface_count()==0:continue
        var box: AABB=node.mesh.get_aabb()
        for i in 8:
            var point: Vector3=node.to_global(box.get_endpoint(i))
            if camera.is_position_behind(point):return {"fits":false,"behind_camera":true}
            points.append(camera.unproject_position(point))
    if points.is_empty():return {"fits":true,"visible_meshes":false}
    var rect:=Rect2(points[0],Vector2.ZERO)
    for point in points:rect=rect.expand(point)
    return {"fits":rect.position.x>=24 and rect.position.y>=100 and rect.end.x<=936 and rect.end.y<=575,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"visible_meshes":true}
func run() -> void:
    if DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus":
        push_error("Actual Forward+ display required for rendered proof");quit(2);return
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
        if arg=="--controls-only":controls_only=true
    if output.is_empty():push_error("--output required");quit(2);return
    DirAccess.make_dir_recursive_absolute(output)
    var stage:=Node3D.new();root.add_child(stage)
    var environment:=WorldEnvironment.new();stage.add_child(environment)
    var env:=Environment.new();environment.environment=env
    env.background_mode=Environment.BG_COLOR;env.background_color=Color("11162a")
    env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("7282aa");env.ambient_light_energy=.45
    env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
    var floor_node:=MeshInstance3D.new();stage.add_child(floor_node)
    var floor_mesh:=PlaneMesh.new();floor_mesh.size=Vector2(200,200);floor_node.mesh=floor_mesh
    var paving:=StandardMaterial3D.new();paving.albedo_color=Color("202a36");paving.roughness=.82;floor_node.material_override=paving
    var lamp=Lamp.new();stage.add_child(lamp);lamp.position=Vector3(-.90,.52,0)
    if not lamp.configure(Source.load_diya()):push_error("source model incompatible");quit(3);return
    var effects=Effects.new();stage.add_child(effects);effects.set_process(false)
    var sun:=DirectionalLight3D.new();stage.add_child(sun);sun.rotation_degrees=Vector3(-45,-30,0);sun.light_color=Color("ffe9d2");sun.light_energy=.35;sun.shadow_enabled=true
    var camera:=Camera3D.new();stage.add_child(camera);camera.position=Vector3(3.2,2.4,4.3);camera.look_at(Vector3(.25,1.10,0));camera.fov=40;camera.current=true
    var layer:=CanvasLayer.new();root.add_child(layer)
    var caption:=ColorRect.new();layer.add_child(caption);caption.color=Color(.025,.04,.07,.96);caption.size=Vector2(960,88)
    var footer:=ColorRect.new();layer.add_child(footer);footer.color=Color(.025,.04,.07,.96);footer.position.y=580;footer.size=Vector2(960,60)
    var title:=Label.new();layer.add_child(title);title.position=Vector2(28,22);title.add_theme_font_size_override("font_size",23);title.text="YUGA / reused-source effects study"
    var subtitle:=Label.new();layer.add_child(subtitle);subtitle.position=Vector2(30,54);subtitle.add_theme_font_size_override("font_size",15)
    var note:=Label.new();layer.add_child(note);note.position=Vector2(30,595);note.add_theme_font_size_override("font_size",14);note.text="Exact original diya GLB · masked baked flame · animated replacement · original event-driven bow cue"
    var sequence_flame_roi:=projected_box(camera,lamp,Vector3(-.02,.125,-.08),Vector3(.14,.38,.08))
    await process_frame
    var accepted:=true
    if controls_only:
        # Match the original control phase without claiming these held frames
        # establish motion. The original72 advancing frames remain separate.
        for i in 12:lamp.step(.5)
    for frame in (0 if controls_only else 72):
        var t:=float(frame)/12.0
        var day:=frame>=36 and frame<60
        var reduced:=frame>=60
        env.background_color=Color("a0b8ce") if day else Color("11162a")
        env.ambient_light_energy=.75 if day else .45
        sun.light_energy=1.6 if day else .35
        lamp.set_options(reduced,reduced);effects.set_options({"reduced_motion":reduced,"reduced_effects":reduced})
        var next_cast:=int(floor((t-.25)/2.0))+1 if t>=.25 else -1
        var age:=t-(.25+float(next_cast-1)*2.0)
        if next_cast>cast:
            cast=next_cast;released=false;impacted=false;ended=false
            accepted=send(effects,"begin",0.0) and accepted
        if cast>=1 and age>=.25 and not released:
            accepted=send(effects,"release",.25) and accepted;released=true
        if cast>=1 and age>=.75 and not impacted:
            accepted=send(effects,"impact",.75) and accepted;impacted=true
        if cast>=1 and age>=1.2 and not ended:
            accepted=send(effects,"end",1.2) and accepted;ended=true
        elif cast>=1 and not ended:
            accepted=send(effects,"tick",maxf(age,0)) and accepted
        lamp.step(1.0/12.0);effects.step(1.0/12.0)
        subtitle.text=("DAY" if day else "NIGHT")+ (" / REDUCED MOTION + INTENSITY" if reduced else " / FULL CUES")+"    ·    t = %.2f s" % t
        await process_frame
        await RenderingServer.frame_post_draw
        var image:=root.get_texture().get_image()
        var path:=output.path_join("frame_%03d.png" % frame)
        if image.save_png(path)!=OK:push_error("frame write failed");quit(4);return
        samples.append({"frame":frame,"simulation_s":t,"day":day,"reduced":reduced,"lamp":lamp.report(),"effects":effects.report(),"effect_screen_bounds":effect_screen_bounds(effects,camera),"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),"file":path.get_file()})
    var final_effects: Dictionary=effects.report();effects.reset()
    # Matched camera / source / exposure. Disable local light in every control so
    # the changed fragment region is attributable to the mask, not lighting.
    env.background_color=Color("11162a");env.ambient_light_energy=.60;sun.light_energy=.70
    sun.shadow_enabled=false
    camera.position=Vector3(.65,1.35,2.0);camera.look_at(Vector3(-.84,.68,0));camera.fov=35
    lamp.set_options(true,false);lamp.set_suspended(true);lamp.light.light_energy=0.0
    var control_flame_roi:=projected_box(camera,lamp,Vector3(.005,.135,-.065),Vector3(.115,.30,.065))
    var controls: Array=[]
    for variant in ["source-mask-off","source-mask-on-no-flame","source-mask-on-replacement"]:
        lamp.set_source_mask_enabled(variant!="source-mask-off")
        lamp.flame_root.visible=variant=="source-mask-on-replacement"
        subtitle.text="MATCHED CONTROL / "+variant+" · light off, fixed clock"
        await process_frame;await RenderingServer.frame_post_draw
        var control_path:=output.path_join(variant+".png")
        if root.get_texture().get_image().save_png(control_path)!=OK:quit(4);return
        controls.append({"file":control_path.get_file(),"lamp_phase":lamp.phase,"local_light_energy":lamp.light.light_energy,"directional_shadows":sun.shadow_enabled,"source_mask_active":variant!="source-mask-off","replacement_visible":lamp.flame_root.visible})
    var framing_passed: bool=samples.all(func(sample):return sample.effect_screen_bounds.fits)
    var report:={"schema_version":1,"kind":"held-shadow-disabled-controls" if controls_only else "reframed-advancing-sequence-with-shadow-disabled-controls","passed":accepted and framing_passed and samples.size()==(0 if controls_only else 72),"framing_passed":framing_passed,"sequence_directional_shadows":true,"frames":samples.size(),"simulation_fps":12,"simulation_duration_s":0 if controls_only else 6,"real_time_fps_measured":false,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"samples":samples,"sequence_flame_roi":sequence_flame_roi,"control_flame_roi":control_flame_roi,"controls":controls,"final_before_reset":final_effects,"after_reset":effects.report(),"scope":"Three fixed-clock geometry controls only; directional shadows disabled equally in every control. No advancing motion or corrected original footage claimed." if controls_only else "Actual deterministic rendered presentation with widened full-cast framing and backed captions; real shadows retained in sequence, disabled equally only in matched geometry controls. Staged events, no gameplay/network/hero-body-animation authority"}
    var file=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
    if file==null:push_error("capture report is not writable");quit(4);return
    file.store_string(JSON.stringify(report,"  ")+"\n")
    print(JSON.stringify({"passed":report.passed,"frames":samples.size(),"output":output,"renderer":report.renderer,"adapter":report.adapter}));quit(0 if report.passed else 5)
