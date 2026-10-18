from pathlib import Path
import hashlib,json,difflib
root=Path('/workspace/scratch/yuga-next-root-r1/ground-relief-r1');parent=Path('/workspace/scratch/yuga-next-W4-r1/water-temporal-helper-r2/capture_water_temporal.gd');old=parent.read_text();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(parent.read_bytes())=='8c51ca9decf0226c7d9dca860966903e2905bc8726f0d719be3030c4dc8d2eef';out=Path(__file__).parent
names=['world_ground.gdshader','world_ground_common.gdshaderinc','world_water.gdshader','render-ground.gdshader','render-water.gdshader','manifest.json','render-derivation.json','water-derivation.json'];pins={str(root/n):sha((root/n).read_bytes()) for n in names};constants='const COMBINED_PINS := '+json.dumps(pins,indent=2)+'\nconst COMBINED_WATER_PATH := '+json.dumps(str(root/'render-water.gdshader'))+'\nconst COMBINED_WATER_SHA := '+json.dumps(pins[str(root/'render-water.gdshader')])+'\nconst COMBINED_GROUND_PATH := '+json.dumps(str(root/'render-ground.gdshader'))+'\nconst COMBINED_GROUND_SHA := '+json.dumps(pins[str(root/'render-ground.gdshader')])+'\nconst ORIGINAL_GROUND_SHA := "7f687dbde3fe62bbcc38317d87229b4857c7340e1c7bfbb895c4c6911d765213"\nvar ground_override_proof: Dictionary = {}\n'
new=old.replace('const CAMERA_TRAVEL := Vector3.ZERO','const CAMERA_TRAVEL := Vector3(0.6,0,0)',1);new=new.replace('var declared_fixed_fps: String = ""',constants+'var declared_fixed_fps: String = ""',1)
new=new.replace('\tstate.water_animation_reset=animation_reset.duplicate(true)','\tstate.water_shader_override.candidate_path=COMBINED_WATER_PATH\n\tstate.water_shader_override.candidate_sha256=COMBINED_WATER_SHA\n\tstate.water_shader_override.baseline_shader_path=CANDIDATE_PATH\n\tstate.water_shader_override.baseline_shader_sha256=CANDIDATE_SHA256\n\tstate.ground_shader_override=ground_override_proof.duplicate(true)\n\tstate.combined_source_pins=COMBINED_PINS\n\tstate.water_animation_reset=animation_reset.duplicate(true)',1)
new=new.replace('"candidate_path":CANDIDATE_PATH,"candidate_sha256":CANDIDATE_SHA256,','"candidate_path":COMBINED_WATER_PATH,"candidate_sha256":COMBINED_WATER_SHA,"baseline_water_path":CANDIDATE_PATH,"baseline_water_sha256":CANDIDATE_SHA256,"combined_source_pins":COMBINED_PINS,"ground_override_proof":ground_override_proof,',1)
new=new.replace('32actual consecutive fixed30Hz night-swamp samples with real TIME and restored original water animation.','32actual consecutive fixed30Hz night-swamp samples with real TIME, restored original water animation and matched0.6m lateral translation; baseline thin-film versus combined root ground/water relief.',1)
extra='''
func install_water_shader(scene: Node3D) -> bool:
	# The only combined installation differences. Timeline/collection stays inherited.
	for path in COMBINED_PINS:
		if FileAccess.get_sha256(path)!=COMBINED_PINS[path]:return false
	if FileAccess.get_sha256(CANDIDATE_PATH)!=CANDIDATE_SHA256:return false
	var selected_path: String = CANDIDATE_PATH if water_role=="baseline" else COMBINED_WATER_PATH
	var expected_sha: String = CANDIDATE_SHA256 if water_role=="baseline" else COMBINED_WATER_SHA
	var selected_shader: Shader = load(selected_path) as Shader
	if selected_shader==null or selected_shader.code.sha256_text()!=expected_sha:return false
	water_override_proof.clear()
	for description in scene.manifest.waters:
		var node: MeshInstance3D = scene.world.get_node_or_null(String(description.id))
		if node==null:return false
		var original: ShaderMaterial = node.get_active_material(0) as ShaderMaterial
		if original==null or original.shader==null or node.material_override!=original:return false
		if original.shader.code.sha256_text()!=ORIGINAL_SHADER_SHA256:return false
		var before: Dictionary = uniform_values(original)
		var active: ShaderMaterial = original.duplicate(false) as ShaderMaterial
		active.shader=selected_shader
		for name in before:active.set_shader_parameter(name,before[name])
		node.material_override=active
		var after: Dictionary = uniform_values(active)
		if before!=after:return false
		water_override_proof.append({"id":String(description.id),"applied":true,"role":water_role,"original_shader_path":original.shader.resource_path,"original_code_sha256":original.shader.code.sha256_text(),"active_shader_path":active.shader.resource_path,"active_code_sha256":active.shader.code.sha256_text(),"expected_active_code_sha256":expected_sha,"uniforms_before":encode_value(before),"uniforms_after_install":encode_value(after),"all_uniforms_copied_exact":before==after})
	var floor_node: MeshInstance3D = scene.world.get_node_or_null("FlatCityPaving")
	if floor_node==null:return false
	var floor_original: ShaderMaterial = floor_node.get_active_material(0) as ShaderMaterial
	if floor_original==null or floor_original.shader==null or floor_node.material_override!=floor_original:return false
	if floor_original.shader.code.sha256_text()!=ORIGINAL_GROUND_SHA:return false
	var floor_before: Dictionary = uniform_values(floor_original)
	var floor_active: ShaderMaterial = floor_original
	if water_role=="candidate":
		var floor_shader: Shader = load(COMBINED_GROUND_PATH) as Shader
		if floor_shader==null or floor_shader.code.sha256_text()!=COMBINED_GROUND_SHA:return false
		floor_active=floor_original.duplicate(false) as ShaderMaterial
		floor_active.shader=floor_shader
		for name in floor_before:floor_active.set_shader_parameter(name,floor_before[name])
		floor_node.material_override=floor_active
	var floor_after: Dictionary = uniform_values(floor_active)
	if floor_before!=floor_after:return false
	ground_override_proof={"id":"FlatCityPaving","applied":water_role=="candidate","original_shader_path":floor_original.shader.resource_path,"original_code_sha256":floor_original.shader.code.sha256_text(),"active_shader_path":floor_active.shader.resource_path,"active_code_sha256":floor_active.shader.code.sha256_text(),"uniforms_before":encode_value(floor_before),"uniforms_after_install":encode_value(floor_after),"all_uniforms_copied_exact":floor_before==floor_after,"apron_untouched":true}
	check("combined exact4target materials retain every original uniform",water_override_proof.size()==3 and water_override_proof.all(func(row):return row.all_uniforms_copied_exact) and ground_override_proof.all_uniforms_copied_exact)
	return water_override_proof.size()==3
'''
new+=extra
f=out/'capture_water_relief.gd';f.write_text(new);(out/'change.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(parent),tofile=str(f))));m={'status':'source-only; native parse/preflight/render not run by W4','parent':str(parent),'parent_sha256':sha(parent.read_bytes()),'helper_sha256':sha(f.read_bytes()),'same_loop_proof':'run(),frames(),compact_state(),clock_state(),reset_animation() and cleanup bytes unchanged; only fixed camera travel, explicit source proof and installation differ','camera_travel':[.6,0,0],'roles':'baseline3f5a water+PCKground vs combined0e61water+45f984ground; all original uniforms copied','targets':['lanka-sea','west-reed-water','east-reed-water','FlatCityPaving'],'apron_untouched':True,'root_pins':pins,'required_userarg':'--capture-fixed-fps=30','canonical_mutation':False};(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
# Independent bounded text identity check for every timing/trace routine.
for name in ['run','frames','compact_state','clock_state','reset_animation','light_trace','save_full']:
 def body(text):
  start=text.index('func '+name+'(');end=text.find('\nfunc ',start+1);return text[start:] if end<0 else text[start:end]
 assert body(old)==body(new),name
print(json.dumps(m,indent=2))
