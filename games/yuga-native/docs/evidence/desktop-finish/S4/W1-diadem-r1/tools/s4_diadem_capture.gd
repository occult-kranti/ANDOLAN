extends "res://tools/visual-rounds/capture_groom.gd"
## Review-only matched source comparison. No runtime geometry or material writes.
## Both branches use this exact helper; admission differs only in three GLBs.
const SOURCE_PINS := {
	"baseline": [
		"8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c",
		"d95a061e2243477afc0227bf52564252fbcb20cb039d303ad10292ea5d85beed",
		"ee2e35278ce49efdda6751850fddbb8f1b4de99ad019e6992c10e7702dc6317c"],
	"candidate": [
		"bda22a046d44079769ac60ca15db2b82be1a34eea72efc962547cfc7bd4b40f0",
		"ab2e0bacd9804c4af05f0ecfcbdfedfdeec6b3c40d8a7d86f2271613a94ddc82",
		"33019438b13e895181ef0d010e3abfef116f4048ebc0b3b19ad5d0201839d9d7"]}
const RAW_PATHS := ["res://assets/heroes/rama-hero.glb", "res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]
const REQUIRED_MOTION := "8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8"
const REQUIRED_FINISH := "6eb51ce8f34a3d5a33deb142ca92aaa20505516b0ee8fff3ca445bcab603078a"
var branch := ""

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output=arg.trim_prefix("--output=")
		elif arg.begins_with("--mode="): mode=arg.trim_prefix("--mode=")
		elif arg=="--preflight": preflight=true
		else: finish("Unknown argument "+arg); return
	expected=4
	if mode!="groom-stills": finish("Use --mode=groom-stills"); return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output): finish("Fresh absolute output required"); return
	DirAccess.make_dir_recursive_absolute(output)
	branch=OS.get_environment("YUGA_DIADEM_REVIEW")
	if not SOURCE_PINS.has(branch): finish("Explicit YUGA_DIADEM_REVIEW=baseline/candidate required"); return
	for index in RAW_PATHS.size():
		if FileAccess.get_sha256(RAW_PATHS[index])!=SOURCE_PINS[branch][index]: finish("Unexpected raw hero "+RAW_PATHS[index]); return
	if FileAccess.get_sha256("res://scripts/rama_motion.gd")!=REQUIRED_MOTION or FileAccess.get_sha256("res://scripts/rama_surface_finish.gd")!=REQUIRED_FINISH:
		finish("Motion/finish source differs from reviewed component inputs"); return
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):
		finish("X11 Forward+ required"); return
	seed(741031); root.size=SIZE; root.content_scale_size=SIZE; root.msaa_3d=Viewport.MSAA_2X
	if not preflight: root.show()
	sources=source_hashes()
	contract={"stills":[
		{"id":"rest-front","player_position_m":[19,.4400999976158142,-15],"visual_yaw_degrees":-90,"camera_position_m":[17.4,1.5000999976158143,-15],"look_at_m":[19,2.0000999976158145,-15],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"head"},
		{"id":"rest-profile","player_position_m":[19,.4400999976158142,-1],"visual_yaw_degrees":0,"camera_position_m":[17.4,1.5000999976158143,-1],"look_at_m":[19,2.0000999976158145,-1],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"head"},
		{"id":"rest-rear","player_position_m":[19,.4400999976158142,-1],"visual_yaw_degrees":90,"camera_position_m":[17.4,1.5000999976158143,-1],"look_at_m":[19,2.0000999976158145,-1],"fov_degrees":38,"near_m":.05,"night":false,"required_bounds":"head"}]}
	scene=load("res://scenes/courtyard.tscn").instantiate(); root.add_child(scene); current_scene=scene
	await draw(6); player=scene.player
	if not player.model_ready or not scene.environment_ready: finish("Actual hero/world missing"); return
	for forbidden in ["FourTaperedTempleWisps","SevenSweptUpperHairLayers","OptionalArrowFletching"]:
		if player.visual.find_child(forbidden,true,false)!=null: finish("Unreviewed optional helper present: "+forbidden); return
	review_camera=Camera3D.new(); scene.add_child(review_camera); review_camera.near=.05; review_camera.far=180
	player.rama_motion.modification_processed.connect(observe_final_pose)
	scene.start_training(); scene.title_light.hide(); await draw(8)
	paused=true; Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.ui.hide(); freeze_background_time(); set_light(false); cache_geometry()
	sequence_controls.append({"kind":"diadem_source_comparison","branch":branch,"default_activation":false,"added_geometry":false,"optional_helpers":false,"rest_contract":contract})
	await groom_stills()
	if not done: await actual_cast_view()
	if not done: finish("")

func actual_cast_view() -> void:
	paused=false
	scene.reset_training(); scene.start_training(); scene.ui.hide(); scene.title_light.hide()
	for action in ["move_left","move_right","move_forward","move_back","fire"]: Input.action_release(action)
	player.global_position=Vector3(-.65,.0001,0); player.velocity=Vector3.ZERO
	player.yaw=0; player.pitch=0; player._update_camera(); player.visual.rotation.y=PI
	player.reset_physics_interpolation(); player.visual.reset_physics_interpolation()
	set_light(false); player.camera.make_current(); await draw(8)
	if not player.is_on_floor(): finish("Actor lacks actual floor contact"); return
	var origin: Vector3=player.camera.project_ray_origin(Vector2(SIZE)*.5)
	var direction: Vector3=player.camera.project_ray_normal(Vector2(SIZE)*.5)
	var hit: Dictionary=scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(origin,origin+direction*80,1|4,[player.get_rid()]))
	if hit.is_empty() or String(hit.collider.name)!="Target03": finish("Actual player aim misses Target03"); return
	scene.rama_runtime.combat_event.connect(record_event)
	var cast: Dictionary=scene.rama_runtime.cast_ability("piercing_dawn")
	if not cast.get("accepted",false): finish("Actual Piercing Dawn refused"); return
	var begin_time: float=scene.rama_runtime.kit.elapsed
	var age:=0.0; var frames:=0
	while age+.000001<.30 and frames<30:
		await draw(1); frames+=1; age=scene.rama_runtime.kit.elapsed-begin_time
	paused=true
	if age>.325 or player.rama_motion.action_stage!="windup" or not player.rama_motion.nocked_arrow.visible:
		finish("Required live nocked windup missing"); return
	var rig: Skeleton3D=player.rama_motion.rig
	var head: int=rig.find_bone("head")
	if head!=104 or posed_globals.size()!=164: finish("Final imported head pose missing"); return
	var center: Vector3=rig.global_transform*posed_globals[head].origin+Vector3.UP*.06
	var offset:=Basis(Vector3.UP,player.visual.global_rotation.y-PI)*Vector3(-.96,.12,-1.02)
	review_camera.global_position=center+offset; review_camera.look_at(center); review_camera.fov=38
	review_camera.make_current(); review_camera.reset_physics_interpolation()
	player.rama_lod.reset("S4 actual cast crown review"); player.rama_lod.update(review_camera,1.0/30)
	await draw(4)
	sequence_controls.append({"kind":"real_public_cast","cast":normal(cast),"authority_age_s":age,"advanced_render_frames":frames,"aim_hit":normal(hit.position),"collider":String(hit.collider.name),"captured_motion_stage":player.rama_motion.action_stage})
	groom_frame("cast-three-quarter","head")

func groom_frame(id: String, required: String) -> void:
	super.groom_frame(id,required)
	if done: return
	shots[-1]["diadem_branch"]=branch
	shots[-1]["rendered_pose_globals"]=normal(posed_globals)
	shots[-1]["rendered_pose_pin"]=JSON.stringify(normal(posed_globals),"",true,true).sha256_text()
	shots[-1]["scope"]="S4 original diadem rail source comparison. Rest stations are staged; cast uses the actual public ability and final modifier pose. Head projection is not visibility, collision or general motion acceptance."

func source_hashes() -> Dictionary:
	var result:=super.source_hashes()
	result.erase("res://tools/visual-rounds/groom_contract.json")
	var helper_path: String=get_script().resource_path
	result[helper_path]=FileAccess.get_sha256(helper_path)
	return result
