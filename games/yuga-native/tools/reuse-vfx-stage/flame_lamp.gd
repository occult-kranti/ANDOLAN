extends Node3D
## A small original integration around the reused original diya mesh.
const FlameShader=preload("flame.gdshader")
const MaskShader=preload("source_mask.gdshader")
var phase:=0.0
var reduced_motion:=false
var reduced_effects:=false
var suspended:=false
var culled:=false
var light: OmniLight3D
var flame_root: Node3D
var materials: Array[ShaderMaterial]=[]
var source_materials: Array[ShaderMaterial]=[]
var source_meshes:=0
var source_triangles:=0
var masked_triangles:=0
func configure(source: PackedScene) -> bool:
    if source==null or flame_root!=null:return false
    var asset: Node3D=source.instantiate()
    add_child(asset)
    var pending: Array=[asset]
    while not pending.is_empty():
        var n: Node=pending.pop_back();pending.append_array(n.get_children())
        if not n is MeshInstance3D:continue
        var mesh: Mesh=n.mesh
        for surface in mesh.get_surface_count():
            var old: Material=n.get_active_material(surface)
            if not old is StandardMaterial3D or old.albedo_texture==null:return _rollback(asset)
            var material:=ShaderMaterial.new();material.shader=MaskShader
            material.set_shader_parameter("base_texture",old.albedo_texture)
            material.set_shader_parameter("orm_texture",old.metallic_texture)
            n.set_surface_override_material(surface,material)
            source_materials.append(material)
            source_meshes+=1
            var arrays:=mesh.surface_get_arrays(surface)
            var indices: PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
            var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
            source_triangles+=indices.size()/3
            for i in range(0,indices.size(),3):
                var center: Vector3=(vertices[indices[i]]+vertices[indices[i+1]]+vertices[indices[i+2]])/3.0
                if center.x>0.005 and center.x<0.115 and center.y>0.135 and center.y<0.30 and absf(center.z)<0.065:masked_triangles+=1
    if source_meshes==0 or masked_triangles==0:return _rollback(asset)
    flame_root=Node3D.new();add_child(flame_root)
    flame_root.position=Vector3(0.058,0.142,0.006)
    for angle in [0.0,PI*0.5]:
        var plane:=MeshInstance3D.new();flame_root.add_child(plane)
        var mesh:=QuadMesh.new();mesh.size=Vector2(0.135,0.22);plane.mesh=mesh
        plane.position.y=0.105;plane.rotation.y=angle
        var material:=ShaderMaterial.new();material.shader=FlameShader
        plane.material_override=material;materials.append(material)
    light=OmniLight3D.new();light.light_color=Color("ffb858");light.omni_range=2.7
    light.position=Vector3(0.058,0.23,0.006);light.shadow_enabled=false;add_child(light)
    _apply()
    return source_meshes>0 and masked_triangles>0
func _rollback(asset: Node3D) -> bool:
    asset.free();source_materials.clear();source_meshes=0;source_triangles=0;masked_triangles=0
    return false
func set_source_mask_enabled(value: bool) -> void:
    for material in source_materials:material.set_shader_parameter("mask_active",value)
func set_options(motion: bool, effects: bool) -> void:
    reduced_motion=motion;reduced_effects=effects;_apply()
func set_suspended(value: bool) -> void:suspended=value
func set_viewer_distance(distance: float) -> bool:
    if not is_finite(distance) or distance<0:return false
    culled=distance>18.0;_apply();return true
func step(delta: float) -> void:
    if suspended or (is_inside_tree() and get_tree().paused) or not is_finite(delta) or delta<0 or delta>.5:return
    phase=fmod(phase+delta,TAU*100.0);_apply()
func _apply() -> void:
    if flame_root==null:return
    flame_root.visible=not culled
    for material in materials:
        material.set_shader_parameter("phase",phase)
        material.set_shader_parameter("reduced_motion",reduced_motion)
        material.set_shader_parameter("intensity",0.64 if reduced_effects else 1.0)
    light.light_energy=0.0 if culled else (0.26 if reduced_effects else 0.72)*(1.0 if reduced_motion else 0.94+0.06*sin(phase*8.2))
func report() -> Dictionary:
    return {"phase":phase,"visible":flame_root.visible if flame_root else false,"light_energy":light.light_energy if light else 0.0,"reduced_motion":reduced_motion,"reduced_effects":reduced_effects,"culled":culled,"source_meshes":source_meshes,"source_triangles":source_triangles,"mask_triangle_centers":masked_triangles,"flame_surfaces":2,"flame_triangles":4,"lights":1,"global_time_shader":false}
