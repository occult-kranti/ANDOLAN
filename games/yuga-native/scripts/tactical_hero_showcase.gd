extends Control
## Isolated character inspection. Reuses accepted skin, finish and authored idle.
## No player, collision, combat input, authority clock or animation release exists here.
const T = preload("res://scripts/tactical_theme.gd")
const Motion = preload("res://scripts/rama_motion.gd")
const Surface = preload("res://scripts/rama_surface_materials.gd")
const Secondary = preload("res://scripts/rama_secondary_motion.gd")
const Finish = preload("res://scripts/rama_surface_finish.gd")
const HERO_PATH := "res://assets/heroes/rama-hero.glb"
const WEAPON_PATH := "res://assets/tactical/surya-carbine.glb"
var viewport: SubViewport
var stage: Node3D
var turntable: Node3D
var visual: Node3D
var camera: Camera3D
var rig: Skeleton3D
var motion: SkeletonModifier3D
var socket: BoneAttachment3D
var weapon: Node3D
var feedback: Label
var drag_area: Control
var state := "loading"
var source_hero := HERO_PATH
var source_weapon := WEAPON_PATH
var yaw := .28
var distance := 4.2
var _dragging := false
var _materials := {}
var _wrist_error := {}
var _gear_filter := {}

func _ready() -> void:
	name="RamaShowcase"
	size_flags_horizontal=Control.SIZE_EXPAND_FILL
	size_flags_vertical=Control.SIZE_EXPAND_FILL
	custom_minimum_size=Vector2(260,220)
	var panel:=Panel.new();panel.add_theme_stylebox_override("panel",T.panel(Color("111c2a"),0,Color("344655")));panel.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(panel);panel.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var layout:=VBoxContainer.new();layout.add_theme_constant_override("separation",0);add_child(layout);layout.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var container:=SubViewportContainer.new();container.stretch=true;container.size_flags_horizontal=Control.SIZE_EXPAND_FILL;container.size_flags_vertical=Control.SIZE_EXPAND_FILL;container.mouse_filter=Control.MOUSE_FILTER_IGNORE;layout.add_child(container)
	viewport=SubViewport.new();viewport.name="CharacterViewport";viewport.own_world_3d=true;viewport.size=Vector2i(640,480);viewport.msaa_3d=Viewport.MSAA_2X;viewport.render_target_update_mode=SubViewport.UPDATE_WHEN_VISIBLE;container.add_child(viewport)
	stage=Node3D.new();viewport.add_child(stage)
	turntable=Node3D.new();turntable.name="InspectionTurntable";stage.add_child(turntable)
	camera=Camera3D.new();camera.fov=30;camera.near=.05;camera.far=30;stage.add_child(camera);camera.make_current()
	_environment()
	var margin:=MarginContainer.new();layout.add_child(margin)
	for side in ["left","right","top","bottom"]:margin.add_theme_constant_override("margin_"+side,12)
	var controls:=T.stack(6);margin.add_child(controls)
	var row:=T.row(8);controls.add_child(row)
	for entry in [["Front","front"],["Back","back"]]:
		var button:=T.button(entry[0],func():set_view(entry[1]));button.name="Inspect"+entry[0];button.size_flags_horizontal=Control.SIZE_EXPAND_FILL;T.quiet(button);row.add_child(button)
	feedback=T.prose("Preparing character…",12);feedback.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;controls.add_child(feedback)
	drag_area=Control.new();drag_area.name="RotateCharacter";drag_area.focus_mode=Control.FOCUS_ALL;drag_area.mouse_default_cursor_shape=Control.CURSOR_DRAG;container.add_child(drag_area);drag_area.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);drag_area.gui_input.connect(_inspect_input)
	resized.connect(_stop_drag)
	set_view("front")
	call_deferred("_load_character")

func _environment() -> void:
	var world:=WorldEnvironment.new();var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color("111c2a");env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.68,.77,1);env.ambient_light_energy=.4;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC;env.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED;world.environment=env;stage.add_child(world)
	var key_light:=true
	for spec in [[Vector3(-36,-35,0),Color(1,.86,.68),2.0],[Vector3(-15,125,0),Color(.54,.7,1),.8],[Vector3(-55,170,0),Color(1,.84,.57),1.1]]:
		var light:=DirectionalLight3D.new();light.rotation_degrees=spec[0];light.light_color=spec[1];light.light_energy=spec[2];light.shadow_enabled=key_light
		if key_light:light.shadow_bias=.035;light.shadow_normal_bias=.5;light.directional_shadow_max_distance=10.0
		stage.add_child(light);key_light=false
	var floor:=MeshInstance3D.new();var cylinder:=CylinderMesh.new();cylinder.top_radius=.65;cylinder.bottom_radius=.65;cylinder.height=.04;cylinder.radial_segments=64;floor.mesh=cylinder;floor.position.y=-.023
	var material:=StandardMaterial3D.new();material.albedo_color=Color("263343");material.roughness=.72;floor.material_override=material;stage.add_child(floor)

func _load_character() -> void:
	if not is_inside_tree():return
	if not ResourceLoader.exists(source_hero):_fail("Character unavailable. Abilities and Casual remain available.");return
	var packed=load(source_hero)
	if not packed is PackedScene:_fail("Character unavailable. Abilities and Casual remain available.");return
	visual=packed.instantiate() as Node3D
	if visual==null:_fail("Character unavailable. Abilities and Casual remain available.");return
	turntable.add_child(visual)
	var animator:AnimationPlayer=_find(visual,"AnimationPlayer")
	motion=Motion.new()
	if not motion.configure(visual,animator):motion.free();motion=null;_fail("Character rig unavailable. Abilities and Casual remain available.");return
	# Borrow the validated rig/pose/arm-chain adapter, but disable all modifier work.
	motion.active=false
	rig=motion.rig
	var bow:Node3D=visual.find_child("RamaBow",true,false)
	if bow!=null:bow.hide()
	motion.nocked_arrow.hide()
	_remove_archery_gear()
	var idle:Dictionary=motion._sample("idle",.2)
	for index in rig.get_bone_count():
		rig.set_bone_pose_position(index,idle.positions[index]);rig.set_bone_pose_rotation(index,idle.rotations[index])
	for pair in [["calibration",Surface],["secondary",Secondary],["finish",Finish]]:
		var owner:Node=pair[1].new();visual.add_child(owner);_materials[pair[0]]=owner.configure(visual)
	if ResourceLoader.exists(source_weapon):_attach_weapon()
	state="ready"
	feedback.text="Drag to turn · scroll to zoom" if weapon!=null else "Character view · SURYA model unavailable"
	_apply_view()

# The original export merged quiver/shafts/fletching into RamaHero. Identify
# complete disconnected source components, never cut a triangle by position.
# Source: art/hero-rama/build_hero.py weapon(), base/top/radius and spine01 bind.
# Canonical assets remain untouched; only this instance receives an ArrayMesh.
func _component_root(parents:PackedInt32Array,index:int)->int:
	while parents[index]!=index:
		parents[index]=parents[parents[index]];index=parents[index]
	return index

func _remove_archery_gear()->void:
	var body:MeshInstance3D=visual.find_child("RamaHero",true,false)
	if body==null or not body.mesh is ArrayMesh or body.mesh.get_blend_shape_count()!=0 or body.skin==null:return
	var source:ArrayMesh=body.mesh
	var expected:={"Ivory silk":[14,1806,2856],"Worked warm gold":[24,2590,4096],"Cobalt handwoven silk":[2,612,1148]}
	var spine_bind:=-1
	for index in body.skin.get_bind_count():
		if body.skin.get_bind_name(index)==&"spine01" or body.skin.get_bind_bone(index)==rig.find_bone("spine01"):spine_bind=index;break
	if spine_bind<0:return
	var candidate:=ArrayMesh.new();candidate.resource_name="Rama inspection / quiver omitted"
	var report:={};var unchanged:=true
	# Preserve encoded vertex/normal/UV/skin buffers exactly; decoding and
	# re-encoding normals would otherwise introduce a quantization round trip.
	var raw_surfaces:Array=source.get("_surfaces")
	var base:=Vector3(-.145,1.15,-.145);var axis:=Vector3(-.07,.49,-.015).normalized()
	for surface in source.get_surface_count():
		var arrays:=source.surface_get_arrays(surface)
		var material:=source.surface_get_material(surface)
		var label:=material.resource_name if material!=null else ""
		if expected.has(label):
			var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var bones:PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights:PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
			var parents:=PackedInt32Array();parents.resize(vertices.size())
			var eligible:=PackedByteArray();eligible.resize(vertices.size())
			for index in vertices.size():
				parents[index]=index
				var offset:=vertices[index]-base;var along:=offset.dot(axis)
				var rigid_weight:=0.0
				for influence in 4:
					if bones[index*4+influence]==spine_bind:rigid_weight+=weights[index*4+influence]
				eligible[index]=int(along>=-.015 and along<=.72 and (offset-axis*along).length()<.057 and rigid_weight>.999)
			for index in range(0,indices.size(),3):
				var first:=_component_root(parents,indices[index])
				parents[_component_root(parents,indices[index+1])]=first
				parents[_component_root(parents,indices[index+2])]=first
			var whole:={}
			for index in vertices.size():
				var component:=_component_root(parents,index)
				whole[component]=bool(whole.get(component,true)) and eligible[index]==1
			var kept:=PackedInt32Array();var removed_vertices:=0;var removed_triangles:=0
			for index in vertices.size():
				if whole[_component_root(parents,index)]:removed_vertices+=1
			for index in range(0,indices.size(),3):
				if whole[_component_root(parents,indices[index])]:removed_triangles+=1
				else:kept.append(indices[index]);kept.append(indices[index+1]);kept.append(indices[index+2])
			var counts:=[whole.values().count(true),removed_vertices,removed_triangles]
			if counts!=expected[label]:_gear_filter={"applied":false,"reason":"source component inventory changed","material":label,"actual":counts};return
			report[label]={"components":counts[0],"unused_vertices":counts[1],"removed_triangles":counts[2]}
			var stride:int=raw_surfaces[surface].index_data.size()/indices.size()
			if stride not in [2,4]:return
			var bytes:=PackedByteArray();bytes.resize(kept.size()*stride)
			for index in kept.size():
				if stride==2:bytes.encode_u16(index*stride,kept[index])
				else:bytes.encode_u32(index*stride,kept[index])
			raw_surfaces[surface].index_data=bytes;raw_surfaces[surface].index_count=kept.size()
			# Generated old LODs still include removed equipment. This close-up
			# inspection intentionally retains the finest topology for these slots.
			raw_surfaces[surface].erase("lods")
	candidate.set("_surfaces",raw_surfaces)
	for surface in source.get_surface_count():
		var copied:=candidate.surface_get_arrays(surface);var original:=source.surface_get_arrays(surface)
		for slot in Mesh.ARRAY_MAX:
			if slot!=Mesh.ARRAY_INDEX:unchanged=unchanged and copied[slot]==original[slot]
		unchanged=unchanged and candidate.surface_get_material(surface)==source.surface_get_material(surface)
	if report.size()!=3 or not unchanged:_gear_filter={"applied":false,"reason":"retained source arrays changed"};return
	body.mesh=candidate
	_gear_filter={"applied":true,"removed_triangles":8100,"complete_components":40,"retained_vertex_bone_material_arrays_unchanged":unchanged,"surfaces":report}

func _attach_weapon() -> void:
	var packed=load(source_weapon)
	if not packed is PackedScene:return
	# A fixed, authored low-ready pose. The existing skin retains its rest lengths.
	var firearm:=Transform3D(Basis(Vector3.UP,PI+.60),Vector3(-.16,1.31,.10))
	var right_basis:=Basis(Vector3(1,0,0),Vector3(0,-1,0),Vector3(0,0,-1))
	var right_grip:=firearm*Vector3(0,-.125,.008)
	var right_target:=right_grip-right_basis*Motion.GRIP_CENTER
	var left_basis:=Basis(Vector3(0,0,-1),Vector3(0,1,0),Vector3(1,0,0))
	var left_grip:=firearm*Vector3(0,-.045,-.28)
	var left_target:=left_grip-left_basis*Vector3(0,.105,.025)
	for entry in [["R",right_target,Vector3(-.65,1.1,.08),right_basis],["L",left_target,Vector3(.55,1.05,.18),left_basis]]:
		motion._solve_reaction_arm(entry[0],entry[1],entry[2])
		var index:=rig.find_bone("wrist."+entry[0]);motion._global_rotate(index,entry[3].get_rotation_quaternion())
		_wrist_error[entry[0]]=rig.get_bone_global_pose(index).origin.distance_to(entry[1])
	# Keep the accepted grip-finger closure; no mesh vertices or imported skin change.
	var grip:Dictionary=motion._sample("ready_draw",.75)
	for index in rig.get_bone_count():
		if String(rig.get_bone_name(index)).begins_with("finger"):rig.set_bone_pose_rotation(index,grip.rotations[index])
	socket=BoneAttachment3D.new();socket.name="SuryaRightHand";rig.add_child(socket);socket.bone_name="wrist.R"
	weapon=packed.instantiate() as Node3D
	if weapon==null:return
	socket.add_child(weapon)
	weapon.transform=rig.get_bone_global_pose(rig.find_bone("wrist.R")).affine_inverse()*firearm

func _find(node:Node,kind:String)->Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=_find(child,kind)
		if found!=null:return found
	return null

func _fail(message:String)->void:
	state="unavailable";feedback.text=message
	if is_instance_valid(visual):visual.hide()

func set_view(view:String)->void:
	yaw=PI+.28 if view=="back" else .28
	distance=4.2;_dragging=false;_apply_view()

func rotate_by(radians:float)->void:
	if not is_finite(radians):return
	yaw=wrapf(yaw+radians,-PI,PI);_apply_view()

func zoom_by(amount:float)->void:
	if not is_finite(amount):return
	distance=clampf(distance+amount,3.2,5.6);_apply_view()

func _apply_view()->void:
	if is_instance_valid(turntable):turntable.rotation.y=yaw
	if is_instance_valid(camera):camera.position=Vector3(0,1.0,distance);camera.look_at(Vector3(0,1.0,0))

func _stop_drag()->void:_dragging=false

func _inspect_input(event:InputEvent)->void:
	if event is InputEventMouseButton:
		if event.button_index==MOUSE_BUTTON_LEFT:_dragging=event.pressed;drag_area.grab_focus();accept_event()
		elif event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:zoom_by(-.2 if event.button_index==MOUSE_BUTTON_WHEEL_UP else .2);accept_event()
	elif event is InputEventMouseMotion and _dragging:
		if event.button_mask&MOUSE_BUTTON_MASK_LEFT:rotate_by(event.relative.x*.008)
		else:_dragging=false
		accept_event()
	elif event is InputEventKey and event.pressed:
		if event.keycode in [KEY_LEFT,KEY_RIGHT]:rotate_by(-.15 if event.keycode==KEY_LEFT else .15);accept_event()
		elif event.keycode==KEY_HOME:set_view("front");accept_event()

func inspection_report()->Dictionary:
	return {"state":state,"hero_path":source_hero,"weapon_path":source_weapon,"bones":rig.get_bone_count() if is_instance_valid(rig) else 0,"weapon_attached":is_instance_valid(weapon),"materials":_materials.duplicate(),"wrist_error_m":_wrist_error.duplicate(),"gear_filter":_gear_filter.duplicate(true),"modifier_active":motion.active if is_instance_valid(motion) else false,"yaw":yaw,"distance":distance,"authority_nodes":find_children("*","CollisionObject3D",true,false).size(),"scope":"Existing skinned Rama and SURYA with a static inspection hold. No new rig or combat animation claim."}
