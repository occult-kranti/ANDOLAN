extends SceneTree
## Export the live canonical bodies and record queries through Godot's actual physics space.
const SCENE := "res://scenes/confluence_world.tscn"
const BUILD := "res://scripts/traversal_landmarks.gd"
const WORLD := "res://scripts/confluence_world.gd"
const MAP := "res://assets/world/confluence-map.json"
const PLAYER := "res://scripts/player.gd"
const LIFT := 0.02
var space: PhysicsDirectSpaceState3D
var shape: CapsuleShape3D
var origin: Vector3
var char_exclude: Array[RID] = []
var samples := []
var occupancy := []

func _initialize() -> void:
    call_deferred("run")

func fail(message: String) -> void:
    push_error(message)
    quit(1)

func vec(v: Vector3) -> Array:
    return [v.x,v.y,v.z]

func occupied(feet: Vector3) -> bool:
    var query := PhysicsShapeQueryParameters3D.new()
    query.collision_mask = 1
    query.exclude = char_exclude
    query.shape = shape
    query.transform = Transform3D(Basis.IDENTITY,feet+Vector3.UP*shape.height*.5)
    return not space.intersect_shape(query,1).is_empty()

func point_inside(at: Vector3) -> bool:
    var q := PhysicsPointQueryParameters3D.new()
    q.collision_mask=1
    q.exclude=char_exclude
    q.position=at
    return not space.intersect_point(q,1).is_empty()

func ray(at: Vector3, to: Vector3) -> Dictionary:
    var q:=PhysicsRayQueryParameters3D.create(at,to,1,char_exclude)
    return space.intersect_ray(q)

func surface(label_:String, local: Vector3, drop:float) -> void:
    var at:=origin+local
    var blocked:=point_inside(at)
    var down:=ray(at,at-Vector3.UP*drop) if not blocked else {}
    var above:=ray(at,at+Vector3.UP*16) if not blocked else {}
    var height:Variant=null
    var top:Variant=null
    var stand:=false
    if not down.is_empty() and down.normal.y>.99:
        height=down.position.y
        stand=not occupied(Vector3(at.x,float(height)+LIFT,at.z))
    if not above.is_empty() and above.normal.y<-.99:top=above.position.y
    samples.append({"name":label_,"origin":vec(at),"max_drop":drop,"start_blocked":blocked,
        "surface_y":height,"ceiling_y":top,"can_stand":stand})

func capsule_case(label_:String,local_feet: Vector3) -> void:
    var feet:=origin+local_feet
    occupancy.append({"name":label_,"feet":vec(feet),"blocked":occupied(feet)})

func run() -> void:
    var args:=OS.get_cmdline_user_args()
    if args.size()!=1:fail("Supply a new output file");return
    var scene:Node3D=load(SCENE).instantiate()
    root.add_child(scene)
    await process_frame
    if not scene.world_ready:fail("Canonical scene did not build");return
    scene.set_paused(false);scene.set_process(false);scene.set_physics_process(false)
    scene.player.active=false;scene.player.set_physics_process(false)
    scene.army.set_process(false);scene.army.set_physics_process(false)
    for child in scene.player.get_children():
        if child is CollisionShape3D and child.shape is CapsuleShape3D:shape=child.shape.duplicate()
    var target:Node3D=scene.world.get_node("TraversalRelics/sun-lift-west")
    var body:StaticBody3D=target.get_node("WindCourtDetailedCollision")
    if shape==null or not scene.landmark_report.wind_court_pilot.integrated_collision or body.get_child_count()!=36 or scene.world.has_node("sun-lift-west-deck"):
        fail("Expected canonical detailed collider and actual hero capsule");return
    origin=target.global_position
    char_exclude.append(scene.player.get_rid())
    await physics_frame
    await physics_frame
    space=scene.world.get_world_3d().direct_space_state
    var solids:=[]
    for parent in [body,scene.floor_body]:
        for c in parent.get_children():
            if not c is CollisionShape3D:continue
            if not c.shape is BoxShape3D or c.disabled or not c.global_basis.is_equal_approx(Basis.IDENTITY):
                fail("Expected enabled axis-aligned native box");return
            var half:Vector3=c.shape.size*.5
            solids.append({"name":str(c.name) if parent==body else str(parent.name),
                "min":vec(c.global_position-half),"max":vec(c.global_position+half)})
    for x in [-3.96,-1.5,0.,1.5,3.96]:
        for z in [-3.96,-1.5,0.,1.5,3.96]:
            surface("roof",Vector3(x,12,z),15)
    for z in [-4.85,-4.35,-4.05,-3.97,-3.90,-3.79,-3.63,-3.47,-3.25,-2.9,0.]:
        for y in [0.31,0.95,2.75,5.1,6.8,7.29,7.65,8.27]:
            surface("facade_slices",Vector3(1.05,y,z),12)
    surface("outside_ground",Vector3(1.05,1.,-4.85),2)
    surface("upper_plinth_tread",Vector3(1.05,3.,-3.73),4)
    surface("lower_plinth_tread",Vector3(1.05,3.,-3.92),4)
    surface("under_crown_rim",Vector3(1.05,4.,-3.91),5)
    surface("closed_core",Vector3(0,4.,0),5)
    surface("roof_landing",Vector3(0,12.,0),6)
    surface("outside_misses_short_drop",Vector3(1.05,5,-4.85),.5)
    capsule_case("recess_clear",Vector3(1.05,3.7-shape.height*.5,-4.02))
    capsule_case("closed_bay_blocked",Vector3(1.05,3.7-shape.height*.5,-3.55))
    capsule_case("open_below_crown",Vector3(1.05,4.8,-4.02))
    capsule_case("head_hits_crown",Vector3(1.05,6.25,-4.02))
    capsule_case("roof_clear",Vector3(0,8.03,0));capsule_case("roof_overlap",Vector3(0,7.94,0))
    for z in [-4.85,-4.42,-4.08,-3.94,-3.64,-3.25]:
        for y in [-.08,.03,.55,1.21,2.8,4.1,5.5,6.4,7.56,8.05]:
            capsule_case("facade_capsules",Vector3(1.05,y,z))
    var sources:={}
    for resource in [SCENE,BUILD,WORLD,MAP,PLAYER]:sources[resource.trim_prefix("res://")]=FileAccess.get_sha256(resource)
    var evidence:={"schema":1,"engine":Engine.get_version_info().string,"landmark":"sun-lift-west",
        "origin":vec(origin),"floor_lift":LIFT,"capsule_radius":shape.radius,"capsule_height":shape.height,
        "sources":sources,"solids":solids,"samples":samples,"occupancy":occupancy}
    var out:=FileAccess.open(args[0],FileAccess.WRITE)
    if not out:fail("Cannot write native geometry fixture");return
    out.store_string(JSON.stringify(evidence,"  ",true,true)+"\n");out.close()
    print("Canonical court: ",solids.size()," solids, ",samples.size()," bidirectional support probes, ",occupancy.size()," capsule overlaps")
    quit()
