extends Control
## Isolated hero studio. Reuses accepted skin, finish and actual firearm art.
## No player, collision, combat input, authority clock or animation release exists here.
const T = preload("res://scripts/tactical_theme.gd")
const Motion = preload("res://scripts/rama_motion.gd")
const Surface = preload("res://scripts/rama_surface_materials.gd")
const Secondary = preload("res://scripts/rama_secondary_motion.gd")
const Finish = preload("res://scripts/rama_surface_finish.gd")
const Weapon = preload("res://scripts/tactical_weapon.gd")
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
var hero_pose: RefCounted
var first_person_weapon: Node3D
var first_person_camera: Camera3D
var _floor: MeshInstance3D
var _loading_cover: PanelContainer
var _mode_buttons := {}
var _turn_buttons: Array[Button] = []
var _pause_button: Button
var _view_mode := "hero"
var _selected_stance := "idle"
var _preview_paused := false
var _reduced_motion := false
var _render_ready := false
var _render_probe_clock := 0.0
var _base_firearm := Transform3D.IDENTITY

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
	var modes:=T.row(6);controls.add_child(modes)
	for entry in [["Hero","hero"],["First person","first_person"]]:
		var mode:=T.button(entry[0],func():set_view_mode(entry[1]));mode.name="StudioMode_"+entry[1];mode.custom_minimum_size.y=34;mode.size_flags_horizontal=Control.SIZE_EXPAND_FILL;mode.add_theme_font_size_override("font_size",14);modes.add_child(mode);_mode_buttons[entry[1]]=mode
	_pause_button=T.button("Pause",func():set_preview_paused(not _preview_paused));_pause_button.name="PausePreview";_pause_button.custom_minimum_size.y=34;_pause_button.add_theme_font_size_override("font_size",14);modes.add_child(_pause_button)
	var row:=T.row(8);controls.add_child(row)
	for entry in [["Front","front"],["Back","back"]]:
		var button:=T.button(entry[0],func():set_view(entry[1]));button.name="Inspect"+entry[0];button.size_flags_horizontal=Control.SIZE_EXPAND_FILL;T.quiet(button);row.add_child(button);_turn_buttons.append(button)
	feedback=T.prose("Preparing character…",12);feedback.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;controls.add_child(feedback)
	drag_area=Control.new();drag_area.name="RotateCharacter";drag_area.focus_mode=Control.FOCUS_ALL;drag_area.mouse_default_cursor_shape=Control.CURSOR_DRAG;container.add_child(drag_area);drag_area.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);drag_area.gui_input.connect(_inspect_input)
	_loading_cover=PanelContainer.new();_loading_cover.mouse_filter=Control.MOUSE_FILTER_IGNORE;_loading_cover.add_theme_stylebox_override("panel",T.panel(Color("111c2a"),16));container.add_child(_loading_cover);_loading_cover.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var preparing:=T.prose("Preparing Rama’s studio…",16,T.GOLD);preparing.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;preparing.vertical_alignment=VERTICAL_ALIGNMENT_CENTER;_loading_cover.add_child(preparing)
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
	var floor:=MeshInstance3D.new();_floor=floor;var cylinder:=CylinderMesh.new();cylinder.top_radius=.65;cylinder.bottom_radius=.65;cylinder.height=.04;cylinder.radial_segments=64;floor.mesh=cylinder;floor.position.y=-.023
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
	if is_instance_valid(weapon):
		var pose_script=load("res://scripts/tactical_hero_pose.gd")
		if pose_script!=null:
			hero_pose=pose_script.new()
			if not hero_pose.configure(rig,motion,socket,weapon,_base_firearm):hero_pose=null
	set_reduced_motion(_reduced_motion)
	state="ready"
	set_view_mode("hero")
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
	_base_firearm=firearm
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
	if is_instance_valid(_loading_cover):_loading_cover.hide()
	_pause_button.disabled=true
	for button in _mode_buttons.values():button.disabled=true

func set_reduced_motion(enabled:bool)->void:
	_reduced_motion=enabled
	if is_instance_valid(first_person_weapon):first_person_weapon.reduced_motion=enabled
	if hero_pose!=null and hero_pose.has_method("set_reduced_motion"):hero_pose.set_reduced_motion(enabled)

func set_preview(action:String)->bool:
	if state!="ready" or action not in ["idle","aim","q","e","c","x"] or hero_pose==null:return false
	var accepted:bool=hero_pose.set_stance(action) if action in ["idle","aim"] else hero_pose.play_ability(action)
	if not accepted:return false
	set_preview_paused(false)
	if action in ["idle","aim"]:_selected_stance=action
	if is_instance_valid(first_person_weapon):
		first_person_weapon.ads=_selected_stance=="aim"
		if action in ["idle","aim"]:first_person_weapon.reset_presentation()
		else:first_person_weapon.present_ability(action)
	return true

func set_preview_paused(paused:bool)->void:
	_preview_paused=paused
	if is_instance_valid(_pause_button):_pause_button.text="Play" if paused else "Pause"

func set_view_mode(mode:String)->bool:
	if mode not in ["hero","first_person"] or state!="ready":return false
	_stop_drag()
	if mode=="first_person" and not is_instance_valid(first_person_weapon):
		first_person_camera=Camera3D.new();first_person_camera.name="FirstPersonStudioCamera";first_person_camera.position=Vector3(20,0,0);first_person_camera.near=.03;first_person_camera.far=8;first_person_camera.fov=75;stage.add_child(first_person_camera)
		first_person_weapon=Weapon.new();first_person_weapon.name="StudioSurya";first_person_camera.add_child(first_person_weapon);first_person_weapon.equip("carbine");first_person_weapon.reduced_motion=_reduced_motion;first_person_weapon.ads=_selected_stance=="aim";first_person_weapon.step(1.0)
	_view_mode=mode
	turntable.visible=mode=="hero";_floor.visible=mode=="hero"
	if is_instance_valid(first_person_weapon):first_person_weapon.visible=mode=="first_person"
	if mode=="hero":camera.make_current()
	else:first_person_camera.make_current()
	for id in _mode_buttons:T.quiet(_mode_buttons[id],id==mode)
	for button in _turn_buttons:button.disabled=mode!="hero"
	drag_area.mouse_default_cursor_shape=Control.CURSOR_DRAG if mode=="hero" else Control.CURSOR_ARROW
	feedback.text="Drag to turn · scroll to zoom" if mode=="hero" else "SURYA · first-person motion preview"
	# A new camera can need new shaders. Keep the studio covered until it draws.
	_render_ready=false;_render_probe_clock=0
	if is_instance_valid(_loading_cover):_loading_cover.show()
	return true

func advance_preview(delta:float)->void:
	if state!="ready" or _preview_paused or not is_finite(delta) or delta<=0:return
	var advance:=minf(delta,.25)
	if hero_pose!=null:hero_pose.step(advance)
	if is_instance_valid(first_person_weapon):
		first_person_weapon.step(advance)
		first_person_camera.fov=lerpf(first_person_camera.fov,54.0 if first_person_weapon.ads else 75.0,minf(1.0,advance*13.0))

func _process(delta:float)->void:
	if not is_visible_in_tree():return
	advance_preview(delta)
	if state!="ready" or _render_ready or DisplayServer.get_name()=="headless":return
	_render_probe_clock+=delta
	if _render_probe_clock<.3:return
	_render_probe_clock=0
	var rendered:Image=viewport.get_texture().get_image()
	if rendered==null or rendered.is_empty():return
	# The previous packaged run exposed a black uncompiled SubViewport. Inspect
	# actual rendered pixels instead of reporting a fabricated percentage/timer.
	for sample in [Vector2(.25,.25),Vector2(.5,.5),Vector2(.75,.75)]:
		var color:=rendered.get_pixel(clampi(int(rendered.get_width()*sample.x),0,rendered.get_width()-1),clampi(int(rendered.get_height()*sample.y),0,rendered.get_height()-1))
		if maxf(color.r,maxf(color.g,color.b))>.035:
			_render_ready=true;_loading_cover.hide();break

func preview_report()->Dictionary:
	var pose:Dictionary=hero_pose.report() if hero_pose!=null else {}
	var active:String=pose.get("active_slot","")
	return {"ready":state=="ready" and hero_pose!=null,"supported_actions":["idle","aim","q","e","c","x"],"current_action":active if not active.is_empty() else _selected_stance,"busy":not active.is_empty(),"paused":_preview_paused,"reduced_motion":_reduced_motion,"view_mode":_view_mode,"render_ready":_render_ready,"pose":pose,"authority":"none; presentation-only studio"}

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
	if _view_mode!="hero":return
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
	return {"state":state,"hero_path":source_hero,"weapon_path":source_weapon,"bones":rig.get_bone_count() if is_instance_valid(rig) else 0,"weapon_attached":is_instance_valid(weapon),"materials":_materials.duplicate(),"wrist_error_m":_wrist_error.duplicate(),"gear_filter":_gear_filter.duplicate(true),"modifier_active":motion.active if is_instance_valid(motion) else false,"yaw":yaw,"distance":distance,"authority_nodes":find_children("*","CollisionObject3D",true,false).size(),"preview":preview_report(),"scope":"Existing skinned Rama/SURYA with tactical pose and first-person previews. Isolated from match state; no new hero or full-body gameplay controller claim."}
