extends SceneTree
## Independent geometry diagnosis of a FAILED conservative-AABB render gate.
## This does not rewrite the capture report or claim the unoccluded bounds fit.
const Effects=preload("res://scripts/rama_ability_effects.gd")
const Fixture=preload("event_fixture.gd")
var sequence:=0
var cast:=-1
var accepted:=true
func _initialize() -> void:call_deferred("run")
func send(effects: Node, kind: String, age: float) -> void:
    sequence+=1;accepted=effects.consume_event(Fixture.event(kind,cast,sequence,age)) and accepted
func clipped_at_floor(vertices: Array) -> Array:
    var out: Array=[]
    for i in vertices.size():
        var a: Vector3=vertices[i];var b: Vector3=vertices[(i+1)%vertices.size()]
        var a_in:=a.y>=0;var b_in:=b.y>=0
        if a_in:out.append(a)
        if a_in!=b_in:out.append(a.lerp(b,-a.y/(b.y-a.y)))
    return out
func bounds(points: Array) -> Dictionary:
    if points.is_empty():return {"empty":true,"fits":true}
    var rect:=Rect2(points[0],Vector2.ZERO)
    for point in points:rect=rect.expand(point)
    return {"empty":false,"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"fits":rect.position.x>=24 and rect.position.y>=100 and rect.end.x<=936 and rect.end.y<=575}
func analyze(effects: Node3D, camera: Camera3D) -> Dictionary:
    var full: Array=[];var clipped: Array=[];var pending: Array=[effects]
    var total:=0;var below:=0;var crossing:=0;var lowest:=INF
    while not pending.is_empty():
        var node: Node=pending.pop_back();pending.append_array(node.get_children())
        if not node is MeshInstance3D or not node.is_visible_in_tree() or node.mesh==null:continue
        for surface in node.mesh.get_surface_count():
            var arrays: Array=node.mesh.surface_get_arrays(surface)
            var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
            var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
            for i in range(0,indices.size(),3):
                var triangle: Array=[];total+=1
                for j in 3:
                    var world: Vector3=node.to_global(vertices[indices[i+j]])
                    lowest=minf(lowest,world.y);triangle.append(world);full.append(camera.unproject_position(world))
                var polygon:=clipped_at_floor(triangle)
                if polygon.is_empty():below+=1
                elif polygon!=triangle:crossing+=1
                for world in polygon:clipped.append(camera.unproject_position(world))
    return {"triangles":total,"fully_below_floor":below,"cross_floor":crossing,"minimum_world_y":lowest if is_finite(lowest) else null,"all_vertices":bounds(full),"above_floor_triangles":bounds(clipped)}
func run() -> void:
    var capture_path:="";var report_path:=""
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--capture="):capture_path=arg.trim_prefix("--capture=")
        if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
    if capture_path.is_empty() or report_path.is_empty():push_error("--capture and --report required");quit(2);return
    var capture=JSON.parse_string(FileAccess.get_file_as_string(capture_path))
    if not capture is Dictionary or capture.get("frames")!=72:quit(2);return
    root.size=Vector2i(960,640);root.content_scale_size=Vector2i(960,640);root.content_scale_mode=Window.CONTENT_SCALE_MODE_DISABLED
    var stage:=Node3D.new();root.add_child(stage)
    var camera:=Camera3D.new();stage.add_child(camera);camera.position=Vector3(3.2,2.4,4.3);camera.look_at(Vector3(.25,1.10,0));camera.fov=40;camera.current=true
    var effects=Effects.new();stage.add_child(effects);effects.set_process(false)
    await process_frame
    var released:=false;var impacted:=false;var ended:=false;var rows: Array=[];var state_match:=true
    for frame in 72:
        var t:=float(frame)/12.0;var reduced:=frame>=60
        effects.set_options({"reduced_motion":reduced,"reduced_effects":reduced})
        var next_cast:=int(floor((t-.25)/2.0))+1 if t>=.25 else -1
        var age:=t-(.25+float(next_cast-1)*2.0)
        if next_cast>cast:cast=next_cast;released=false;impacted=false;ended=false;send(effects,"begin",0.0)
        if cast>=1 and age>=.25 and not released:send(effects,"release",.25);released=true
        if cast>=1 and age>=.75 and not impacted:send(effects,"impact",.75);impacted=true
        if cast>=1 and age>=1.2 and not ended:send(effects,"end",1.2);ended=true
        elif cast>=1 and not ended:send(effects,"tick",maxf(age,0))
        effects.step(1.0/12.0)
        var state: Dictionary=effects.report();var original: Dictionary=capture.samples[frame].effects
        for key in ["active","impacts","pooled_impacts","meshes","total_triangles","live_arrows"]:state_match=state_match and state[key]==original[key]
        var geometry:=analyze(effects,camera)
        rows.append({"frame":frame,"original_conservative_aabb":capture.samples[frame].effect_screen_bounds,"geometry":geometry})
    var failed: Array=rows.filter(func(row):return not row.original_conservative_aabb.fits)
    var clipped_fit: bool=rows.all(func(row):return row.geometry.above_floor_triangles.fits)
    var full_fit: bool=rows.all(func(row):return row.geometry.all_vertices.fits)
    var result:={"diagnosis_passed":accepted and state_match and full_fit and clipped_fit,"original_conservative_gate_still_failed":not capture.framing_passed,"original_capture_passed":capture.passed,"same_replayed_effect_state_counts":state_match,"all_full_indexed_geometry_fits":full_fit,"all_above_floor_indexed_geometry_fits":clipped_fit,"diagnosis":"Projected enclosing AABB corners include empty volume beyond actual indexed geometry. Actual full indexed geometry fits already; floor clipping further reduces the visible envelope. Conservative AABB gate remains false.","viewport":[root.size.x,root.size.y],"floor":{"world_y":0.0,"opaque":true,"extent":200.0,"source":"preview.gd PlaneMesh"},"sources":{"effects":FileAccess.get_sha256("res://scripts/rama_ability_effects.gd"),"fixture":FileAccess.get_sha256("res://tools/reuse-vfx-stage/event_fixture.gd"),"analysis":FileAccess.get_sha256(get_script().resource_path),"capture":FileAccess.get_sha256(capture_path)},"failed_aabb_frames":failed,"all_frames":rows,"scope":"Headless exact indexed-triangle replay and clipping against the existing opaque floor plane; projection/occlusion diagnosis only. Does not rewrite failed conservative gate or establish whole-ability/game acceptance."}
    var file=FileAccess.open(report_path,FileAccess.WRITE)
    if file==null:quit(2);return
    file.store_string(JSON.stringify(result,"  ")+"\n")
    print(JSON.stringify({"diagnosis_passed":result.diagnosis_passed,"original_gate_failed":result.original_conservative_gate_still_failed,"state_match":state_match,"above_floor_fits":clipped_fit,"failed_frames":failed.size()}));quit(0 if result.diagnosis_passed else 1)
