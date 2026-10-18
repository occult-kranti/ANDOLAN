from pathlib import Path
import hashlib,json,difflib
out=Path(__file__).parent;base_path=Path('/workspace/scratch/yuga-next-W1-r1/harness/capture_water_baseline.gd');base=base_path.read_text();run=base[base.index('func run()'):base.index('func finish(')];finish=base[base.index('func finish('):]
run=run.replace('elif arg=="--preflight":preflight=true','elif arg=="--preflight":preflight=true\n\t\telif arg.begins_with("--water-role="):water_role=arg.trim_prefix("--water-role=")')
run=run.replace('\tif not output.is_absolute_path()', '\tif water_role not in ["baseline","candidate"]:finish("Explicit water role required");return\n\tif not output.is_absolute_path()',1)
run=run.replace('\tscene.player.rama_motion.modification_processed.connect(observe_final_pose);', '\tif not install_water_shader(scene):finish("Exact water shader/uniform installation failed");return\n\tscene.player.rama_motion.modification_processed.connect(observe_final_pose);',1)
run=run.replace('Vector3(-67,4.6,20),"target":Vector3(-83,-.15,-12)', 'Vector3(-94,4.6,-38),"target":Vector3(-80,-.15,-38)')
run=run.replace('"phase":0.0,"water":"coastal"}]','"phase":0.0,"water":"coastal"},{"id":"02-day-swamp","position":Vector3(-48,2.8,8),"target":Vector3(-61,1,0),"phase":0.0,"water":"shallow"}]')
finish=finish.replace('"two declared full-world water stills",shots.size()==2','"three declared full-world water observations",shots.size()==3')
finish=finish.replace('"Exact79e5 PCK full production world, fixed fixture camera/night phase and water animation_speed0 only; UI retained, original full hero/material/light/collision/clock collector. No temporal/HW FPS/finished-art acceptance."','"Exact79e5 PCK full production world; common fixed cameras/phases and water animation0. Candidate changes only the external exact thin-film shader on3water materials, with all original uniforms copied. Baseline night is a JSON observation for strict original-image reuse. No temporal/HW FPS/finished-art acceptance."')
finish=finish.replace('\tvar report:={','\tvar report:={"water_role":water_role,"candidate_path":CANDIDATE_PATH,"candidate_source_sha256":FileAccess.get_sha256(CANDIDATE_PATH),"override_proof":water_override_proof,')
finish=finish.replace('WATER_BASELINE_COMPLETE','WATER_PAIR_COMPLETE')
extra='''extends "/workspace/scratch/yuga-next-W1-r1/harness/capture_water_baseline.gd"
## One identical source-only pair helper; W1 owns native parse/transport/rendering.
## Same original 12-ready/12-per-view callback schedule and known mixer cleanup.
const CANDIDATE_PATH := "/workspace/scratch/yuga-next-W4-r1/thin-film-r1/world_water.gdshader"
const CANDIDATE_SHA256 := "3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e"
const ORIGINAL_SHADER_SHA256 := "add24973aab0d30ebeae2f2db7d096f74fd304bf22868afc4470e22506f86283"
const REUSED_NIGHT_PATH := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/W1-actual-r1/water-baseline-r1/raw/00-night-swamp.png"
const REUSED_NIGHT_SHA256 := "f169f43710434b3dc871ce792182e424578ceb90226d106b5e165962754b9bb7"
var water_role: String = ""
var water_override_proof: Array = []

func uniform_values(material: ShaderMaterial) -> Dictionary:
	var values: Dictionary = {}
	for entry in material.shader.get_shader_uniform_list():
		values[String(entry.name)] = material.get_shader_parameter(String(entry.name))
	return values

func install_water_shader(scene: Node3D) -> bool:
	if FileAccess.get_sha256(CANDIDATE_PATH) != CANDIDATE_SHA256:return false
	var candidate_shader: Shader
	if water_role == "candidate":
		candidate_shader = load(CANDIDATE_PATH) as Shader
		if candidate_shader == null or candidate_shader.code.sha256_text() != CANDIDATE_SHA256:return false
	water_override_proof.clear()
	for description in scene.manifest.waters:
		var node: MeshInstance3D = scene.world.get_node_or_null(String(description.id))
		if node == null:return false
		var original: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		if original == null or original.shader == null or node.material_override != original:return false
		var original_code_sha: String = original.shader.code.sha256_text()
		if original_code_sha != ORIGINAL_SHADER_SHA256:return false
		var before: Dictionary = uniform_values(original)
		var active: ShaderMaterial = original
		if water_role == "candidate":
			active = original.duplicate(false) as ShaderMaterial
			active.shader = candidate_shader
			for name in before:active.set_shader_parameter(name,before[name])
			node.material_override = active
		var after: Dictionary = uniform_values(active)
		if before != after:return false
		water_override_proof.append({"id":String(description.id),"applied":water_role=="candidate","original_shader_path":original.shader.resource_path,"original_code_sha256":original_code_sha,"active_shader_path":active.shader.resource_path,"active_code_sha256":active.shader.code.sha256_text(),"uniforms_before":encode_value(before),"uniforms_after_install":encode_value(after),"all_uniforms_copied_exact":before==after})
	check("three real water materials retain every original uniform",water_override_proof.size()==3 and water_override_proof.all(func(row):return row.all_uniforms_copied_exact))
	return water_override_proof.size()==3

func snapshot(id: String) -> Dictionary:
	var result: Dictionary = super.snapshot(id)
	result.water_shader_override = {"role":water_role,"candidate_path":CANDIDATE_PATH,"candidate_sha256":CANDIDATE_SHA256,"rows":water_override_proof.duplicate(true)}
	result.review_fixture.animation = "only water animation_speed frozen0; exact isolated external shader override declared separately"
	for row in result.water_shader_override.rows:
		var node: MeshInstance3D = current_scene.world.get_node(String(row.id))
		var material: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		row.uniforms_at_snapshot = encode_value(uniform_values(material))
	return result

func take(id: String) -> bool:
	if water_role != "baseline" or id != "00-night-swamp":return super.take(id)
	# Observe the complete same actual frame, but do not recapture its PNG.
	var state: Dictionary = snapshot(id)
	if not preflight:
		state.framebuffer_size = [root.get_texture().get_width(),root.get_texture().get_height()]
		state.reused_original = {"path":REUSED_NIGHT_PATH,"sha256":REUSED_NIGHT_SHA256,"strict_control_comparison_required":true}
	shots.append(state)
	write_json(output.path_join(id+".json"),state)
	checkpoint("shot:"+id)
	return true

'''
text=extra+run+finish;f=out/'capture_water_pair.gd';f.write_text(text);sha=lambda b:hashlib.sha256(b).hexdigest();m={'scope':'source-only common paired water helper; native parse/preflight unrun, W1 owns them','helper_sha256':sha(f.read_bytes()),'base_path':str(base_path),'base_sha256':sha(base.encode()),'candidate_path':'/workspace/scratch/yuga-next-W4-r1/thin-film-r1/world_water.gdshader','candidate_sha256':'3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e','inputs_untouched':'W1 controls.json not edited','clock_schedule':'original12ready+12each at night24/coast36/day-swamp48; original frames/observer inherited unchanged','baseline_images':2,'candidate_images':3,'baseline_night':'full snapshot only; reuse depends on W1 strict comparison to original','override':'3 actual ShaderMaterial copies; every shader uniform copied; no root ground relief','camera_check_receipt_sha256':'f11015d38691c11411833c311243aea202d4ab76954716526b523acdd99f7be3'};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');(out/'base-run-finish.diff').write_text(''.join(difflib.unified_diff((base[base.index('func run()'):]).splitlines(True),(run+finish).splitlines(True),fromfile=str(base_path)+'#run-finish',tofile=str(f)+'#run-finish')));print(json.dumps(m,indent=2))
