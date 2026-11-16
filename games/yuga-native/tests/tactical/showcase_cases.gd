extends SceneTree
const Showcase=preload("res://scripts/tactical_hero_showcase.gd")
const Frontend=preload("res://scripts/tactical_frontend.gd")
var checks:Array[Dictionary]=[]
var report_path:=""
func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):report_path=argument.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,passed:bool)->void:
	checks.append({"name":label,"passed":passed});print("PASS " if passed else "FAIL ",label)
func run()->void:
	root.content_scale_size=Vector2i(1280,720);root.size=Vector2i(1280,720)
	var front:=Frontend.new();root.add_child(front);await process_frame
	front.show_page("hero");await process_frame;await process_frame
	var view:Control=front.hero_showcase
	var initial:Dictionary=view.inspection_report()
	print(JSON.stringify(initial))
	check("Hero page mounts the accepted full-body model and 164-bone skin",initial.state=="ready" and initial.bones==164)
	check("SURYA is a right-wrist attachment without first-person arms",initial.weapon_attached and view.socket.bone_name=="wrist.R" and view.weapon.get_parent()==view.socket)
	check("Production material calibration, secondary and finish bind",initial.materials.values().all(func(value):return value))
	check("Bow and nocked arrow are hidden",not view.visual.find_child("RamaBow",true,false).visible and not view.motion.nocked_arrow.visible)
	check("Inspection has no collision/authority and no active motion modifier",initial.authority_nodes==0 and not initial.modifier_active and view.motion.release_count==0)
	check("Static hold reaches both wrists within 1cm",initial.wrist_error_m.values().all(func(value):return value<.01))
	var finite:=true
	for index in view.rig.get_bone_count():finite=finite and view.rig.get_bone_global_pose(index).is_finite()
	check("Every posed bone stays finite",finite)
	check("Only 40 complete authored quiver components are omitted",initial.gear_filter.get("applied",false) and initial.gear_filter.get("removed_triangles",0)==8100 and initial.gear_filter.get("complete_components",0)==40)
	check("Retained skin, vertex and material arrays stay unchanged",initial.gear_filter.get("retained_vertex_bone_material_arrays_unchanged",false))
	view.set_process(false)
	check("Studio provides all six real presentation actions",view.preview_report().ready and view.preview_report().supported_actions==["idle","aim","q","e","c","x"])
	check("First-person mode mounts the real isolated SURYA component",view.set_view_mode("first_person") and view.first_person_weapon.weapon_id=="carbine" and view.first_person_camera.current and not view.turntable.visible)
	check("Studio weapon starts with its own magazine and no world authority",view.first_person_weapon.ammo==24 and view.first_person_weapon.reserve==72 and view.find_children("*","CollisionObject3D",true,false).is_empty())
	check("Aim previews change both representations",view.set_preview("aim") and view.first_person_weapon.ads)
	for index in 10:view.advance_preview(.1)
	check("First-person ADS reaches a readable camera while preserving rounds",is_equal_approx(view.first_person_camera.fov,54.0) and view.first_person_weapon.ammo==24)
	check("Utility preview is accepted without a purchase or match",view.set_preview("q") and view.preview_report().busy and view.first_person_weapon.cast_motion.report().active)
	view.advance_preview(.1);view.set_preview_paused(true)
	var paused_report:Dictionary=view.preview_report();var paused_weapon:float=view.first_person_weapon.clock
	view.advance_preview(.2)
	check("Pause freezes both hero and first-person clocks",view.preview_report().pose.age_s==paused_report.pose.age_s and view.first_person_weapon.clock==paused_weapon)
	view.set_preview_paused(false)
	for index in 30:view.advance_preview(.1)
	check("Utility returns to the selected stance without spending ammunition",not view.preview_report().busy and view.preview_report().current_action=="aim" and view.first_person_weapon.ammo==24)
	view.set_reduced_motion(true)
	check("Saved reduced motion reaches both preview representations",view.preview_report().reduced_motion and view.first_person_weapon.reduced_motion and view.hero_pose.reduced_motion)
	check("Unsupported preview input leaves current state intact",not view.set_preview("unavailable") and not view.set_view_mode("invalid") and view.preview_report().current_action=="aim")
	view.set_preview("idle");view.set_view_mode("hero")
	check("Return to hero restores its camera and interaction",view.camera.current and view.turntable.visible and not view.first_person_weapon.visible)
	view.set_view("back");check("Back action turns the full character",is_equal_approx(view.yaw,PI+.28))
	var before:float=view.yaw
	var key:=InputEventKey.new();key.keycode=KEY_LEFT;key.pressed=true;view._inspect_input(key)
	check("Focused keyboard rotation changes inspection only",not is_equal_approx(before,view.yaw) and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE)
	view.zoom_by(-100);check("Zoom has a safe close bound",is_equal_approx(view.distance,3.2));view.zoom_by(100);check("Zoom has a safe far bound",is_equal_approx(view.distance,5.6))
	view.rotate_by(NAN);view.zoom_by(INF);check("Nonfinite control input is ignored",is_finite(view.yaw) and is_finite(view.distance))
	for size_ in [Vector2i(1280,720),Vector2i(960,540)]:
		root.content_scale_size=size_;root.size=size_;await process_frame;await process_frame
		check("Inspection stays within native viewport "+str(size_),Rect2(Vector2.ZERO,Vector2(size_)).encloses(view.get_global_rect()) and view.size.x>=260 and view.size.y>=220)
	var prior:WeakRef=weakref(view);front.show_page("home");await process_frame;await process_frame
	check("Leaving hero page frees viewport and releases original menu art",prior.get_ref()==null and front.hero_showcase==null and front._key_art.visible)
	front.show_page("hero");await process_frame;await process_frame
	check("Repeated hero entry has exactly one isolated world",front._content_row.find_children("RamaShowcase","Control",true,false).size()==1 and front.hero_showcase.state=="ready")
	front.show_page("settings");check("Settings flow remains available after inspection",front.settings_controls.size()==5)
	root.remove_child(front);front.free()
	var missing:=Showcase.new();missing.source_hero="res://tests/tactical/no-hero.glb";root.add_child(missing);await process_frame;await process_frame
	check("Missing model shows a truthful recoverable fallback",missing.state=="unavailable" and missing.feedback.text.contains("Abilities and Casual remain available"))
	root.remove_child(missing);missing.free()
	var passed:=checks.all(func(row):return row.passed)
	var sources:={}
	for path in ["res://scripts/tactical_frontend.gd","res://scripts/tactical_hero_showcase.gd","res://tests/tactical/showcase_cases.gd","res://assets/heroes/rama-hero.glb","res://assets/tactical/surya-carbine.glb"]:sources[path]=FileAccess.get_sha256(path)
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"inspection":initial,"sources":sources,"scope":"Headless native model/rig/material/pose binding, page lifecycle, controls and geometry bounds. Rendered art, finger contacts and ordinary pointer interaction need separate native capture."}
	if not report_path.is_empty():var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"))
	quit(0 if passed else 1)
