extends SceneTree
## Actual per-army status/arrow geometry ownership, not rendered performance.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
const MAP := "res://assets/world/confluence-map.json"
const ORACLE := "res://docs/evidence/desktop-finish/continuation-oct18/W4-army-resources-r1/baseline-lane_minion.gd.txt"
const ORACLE_SHA256 := "90fe2d84f5c408b4b99779b00c11e59e850c1bb4f88dafb42a8a5aba74cc119c"
var checks: Array[Dictionary] = []
var report_path := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, ok: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"details":details})
	print("PASS " if ok else "FAIL ",label)

func hash_value(value: Variant) -> String:
	var h:=HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(var_to_bytes(value))
	return h.finish().hex_encode()

func parts(unit: Node3D) -> Array:
	var result: Array = []
	if is_instance_valid(unit.health_fill):
		result.append(unit.health_fill.get_parent().get_child(0))
		result.append(unit.health_fill)
		result.append(unit.shield_fill)
	if is_instance_valid(unit.arrow): result.append(unit.arrow)
	return result

func geometry(part: MeshInstance3D) -> Dictionary:
	var surfaces: Array=[]
	for index in part.mesh.get_surface_count(): surfaces.append(hash_value(part.mesh.surface_get_arrays(index)))
	return {"class":part.mesh.get_class(),"aabb":part.mesh.get_aabb(),"arrays":surfaces}

func visual_state(unit: Node3D) -> Array:
	var rows: Array=[]
	for p in parts(unit):
		var m:=p.material_override as StandardMaterial3D
		rows.append({"geometry":geometry(p),"transform":p.transform,"visible":p.visible,"shadow":p.cast_shadow,
			"material":{"albedo":m.albedo_color,"shading":m.shading_mode,"roughness":m.roughness,"transparency":m.transparency},
			"bar_transform":p.get_parent().transform})
	return rows

func identities(units: Array, materials: bool = false) -> Dictionary:
	var ids: Dictionary={}
	for unit in units:
		for p in parts(unit): ids[(p.material_override if materials else p.mesh).get_instance_id()]=true
	return ids

func material_partition(units: Array) -> bool:
	# Bow shaft intentionally shares only its own unit's health material.
	return identities(units,true).size()==3*units.size()

func disjoint(a: Dictionary,b: Dictionary) -> bool:
	for id in a:
		if b.has(id):return false
	return true

func make_unit(script: GDScript, parent: Node3D, owner_army: Node3D, team: String, role: String, id: int):
	var unit=script.new()
	unit.setup(owner_army,id,team,role,1)
	parent.add_child(unit)
	unit.set_process(false)
	return unit

func run() -> void:
	var inputs: Array = [MAP,ORACLE,"res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/world_render_resources.gd",get_script().resource_path]
	var before: Dictionary={}
	for path in inputs:before[path]=FileAccess.get_sha256(path)
	var old:=GDScript.new()
	old.source_code=FileAccess.get_file_as_string(ORACLE)
	var oracle_ok: bool=FileAccess.get_sha256(ORACLE)==ORACLE_SHA256 and old.reload()==OK
	check("retained unit oracle is exact pinned pre-change source and parses",oracle_ok)
	if not oracle_ok:quit(1);return
	var data: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(MAP))
	var army=Army.new()
	var other=Army.new()
	root.add_child(army)
	root.add_child(other)
	army.set_physics_process(false)
	other.set_physics_process(false)
	check("two actual armies configure their initial mirrored thirty units",army.configure(data,null) and other.configure(data,null) and army.units.size()==30 and other.units.size()==30)
	for unit in army.units+other.units:unit.set_process(false)
	var bows: int=army.units.filter(func(u):return u.role=="bow_guard").size()
	check("initial 102 status and arrow instances reference exactly four meshes",bows==12 and identities(army.units).size()==4,{"units":army.units.size(),"bows":bows,"instances":3*army.units.size()+bows,"unique_meshes":identities(army.units).size()})
	check("all ninety initial mutable materials retain per-unit ownership",material_partition(army.units) and identities(army.units,true).size()==90)
	check("independent army geometry and materials have disjoint ownership",disjoint(identities(army.units),identities(other.units)) and disjoint(identities(army.units,true),identities(other.units,true)))
	var colliders: Dictionary={}
	for unit in army.units:colliders[unit.shape.shape.get_instance_id()]=true
	check("thirty unit capsule resources remain independent",colliders.size()==30)
	var fixture_root:=Node3D.new()
	root.add_child(fixture_root)
	var parity:=true
	var no_embedded:=true
	var role_count:=0
	for team in ["sun","moon"]:
		for role in Unit.STATS:
			var current=make_unit(Unit,fixture_root,army,team,role,1001)
			var original=make_unit(old,fixture_root,other,team,role,1001)
			parity=parity and visual_state(current)==visual_state(original) and current.shape.shape.get_class()==original.shape.shape.get_class() and current.shape.shape.radius==original.shape.shape.radius and current.shape.shape.height==original.shape.shape.height
			for p in parts(current):no_embedded=no_embedded and p.mesh.surface_get_material(0)==null
			# Same real damage/heal/shield APIs, thresholds, and visual transforms.
			for unit in [current,original]:
				unit.receive_damage(20,"army")
				unit.receive_heal(5)
				unit.apply_shield(30,2)
				unit._update_health_bar()
			parity=parity and visual_state(current)==visual_state(original) and current.health==original.health and current.shield==original.shield
			for unit in [current,original]:
				unit.step_statuses(2.1)
				unit._update_health_bar()
			parity=parity and visual_state(current)==visual_state(original) and current.shield==0 and original.shield==0
			current.free()
			original.free()
			role_count+=1
	check("all five roles and both teams match original full arrays materials bar state and capsule dimensions",parity and role_count==10,{"role_team_variants":role_count})
	check("shared geometry has no embedded material",no_embedded)
	var first=army.units[0]
	var peer=army.units[1]
	var peer_before:=visual_state(peer)
	var other_before:=visual_state(other.units[0])
	first.receive_damage(20,"army")
	first.apply_shield(40,2)
	first._update_health_bar()
	check("damage and shields mutate only targeted node transforms and visibility",visual_state(peer)==peer_before and visual_state(other.units[0])==other_before and first.health<first.max_health and first.shield_fill.visible)
	var material: StandardMaterial3D=first.health_fill.material_override
	var old_color:=material.albedo_color
	material.albedo_color=Color.MAGENTA
	check("material mutation cannot bleed to another unit or army",visual_state(peer)==peer_before and visual_state(other.units[0])==other_before)
	material.albedo_color=old_color
	var first_state:=visual_state(first)
	var old_mesh: Mesh=first.health_fill.mesh
	first.health_fill.mesh=old_mesh.duplicate()
	(first.health_fill.mesh as BoxMesh).size.x+=.01
	check("negative wrong bar dimensions are detected",visual_state(first)!=first_state)
	first.health_fill.mesh=old_mesh
	old_mesh=null
	var own_material: Material=peer.health_fill.material_override
	peer.health_fill.material_override=first.health_fill.material_override
	check("negative shared mutable unit material is detected",not material_partition(army.units))
	peer.health_fill.material_override=own_material
	own_material=null
	check("negative controls restore exact target and peer visual state",visual_state(first)==first_state and visual_state(peer)==peer_before and material_partition(army.units))
	var arrow_units: Array=army.units.filter(func(u):return u.role=="bow_guard")
	var arrow_a=arrow_units[0]
	var arrow_b=arrow_units[1]
	arrow_a.start_attack(arrow_a.position+Vector3(0,0,4))
	arrow_b.start_attack(arrow_b.position+Vector3(2,0,6))
	arrow_a.attack_time=.32
	arrow_b.attack_time=.18
	arrow_a.update_pose(.1,1)
	arrow_b.update_pose(.1,1)
	check("simultaneous bow arrows share geometry but keep independent poses",arrow_a.arrow.mesh==arrow_b.arrow.mesh and arrow_a.arrow.transform!=arrow_b.arrow.transform)
	# Replace actual wave without changing the army's authority or timers.
	var initial_ids:=identities(army.units)
	var initial_material_ids:=identities(army.units,true)
	army.reset()
	for unit in army.units:unit.set_process(false)
	check("actual wave reset retains only the same finite four-shape cache",army.units.size()==30 and identities(army.units)==initial_ids and material_partition(army.units) and disjoint(initial_material_ids,identities(army.units,true)))
	for unit in army.units:
		unit.progress+=20
		unit.position=army.route_sample(unit.lane_id,unit.progress,unit.team,unit.lateral).position
	army._spawn_wave()
	for unit in army.units:unit.set_process(false)
	check("later actual wave reuses the same four geometries across sixty units",army.units.size()==60 and identities(army.units)==initial_ids and material_partition(army.units))
	var before_count: int=army.units.size()
	for unit in army.units.duplicate():unit.receive_damage(1000,"army")
	for i in 25:army.step_simulation(.05)
	check("actual corpse teardown removes all dead unit nodes",before_count==60 and army.units.is_empty())
	army.reset()
	for unit in army.units:unit.set_process(false)
	check("replacement wave reuses exactly four geometry resources with fresh materials",army.units.size()==30 and identities(army.units)==initial_ids and material_partition(army.units))
	# Standalone path has no army/accessor and must still construct all visuals.
	var standalone=make_unit(Unit,fixture_root,null,"sun","bow_guard",3001)
	var standalone_peer=make_unit(Unit,fixture_root,null,"moon","bow_guard",3002)
	check("standalone units without an army retain valid independent fallback resources",parts(standalone).size()==4 and disjoint(identities([standalone]),identities([standalone_peer])) and disjoint(identities([standalone]),identities(army.units)))
	standalone.free()
	standalone_peer.free()
	var owned_mesh_weak: WeakRef=weakref(army.units[0].health_fill.mesh)
	var other_mesh_ids:=identities(other.units)
	# Erase fixture local references so the ownership test observes the army only.
	first=null
	peer=null
	material=null
	arrow_a=null
	arrow_b=null
	arrow_units=[]
	army.free()
	await process_frame
	check("destroying an army releases its finite pool and leaves the other army intact",owned_mesh_weak.get_ref()==null and identities(other.units)==other_mesh_ids and other.units.size()==30)
	other.free()
	fixture_root.free()
	await process_frame
	var after: Dictionary={}
	for path in inputs:after[path]=FileAccess.get_sha256(path)
	check("all tested sources and manifest remain unchanged",before==after)
	var passed: bool=checks.all(func(row):return row.passed)
	var report: Dictionary={"passed":passed,"count":checks.size(),"checks":checks,"source_before":before,"source_after":after,"scope":"Actual two-army initial30/reset/corpse/standalone lifecycle, fixed four status/arrow geometries and independent mutable materials, all5roles×2teams original-array/material/capsule parity, damage/heal/shield and negative controls. No imports/raster/FPS/art or online authority claim."}
	if not report_path.is_empty():FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if passed else 1)
