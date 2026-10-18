from pathlib import Path
p=Path(__file__).parent/'capture_frontage.gd';s=p.read_text()
s=s.replace('var route_checks: Dictionary = {}','''var route_checks: Dictionary = {}
var final_pose: Dictionary = {}
var final_pose_signals := 0

func observe_final_pose() -> void:
\t# Observe while completed RamaMotion transforms exist, before Skeleton3D restores them.
\tvar scene: Node3D = current_scene
\tvar rig: Skeleton3D = scene.player.rama_motion.rig
\tvar names: Array = []
\tvar poses: Array = []
\tfor index in rig.get_bone_count():
\t\tnames.append(String(rig.get_bone_name(index)))
\t\tposes.append(transform_values(rig.get_bone_global_pose(index)))
\tvar active_modifiers: Array = []
\tfor child in rig.get_children():
\t\tif child is SkeletonModifier3D and child.active and child.influence>0.0: active_modifiers.append(String(child.name))
\tfinal_pose_signals += 1
\tfinal_pose = {"bone_names":names,"bone_global_poses":poses,"rig_transform":transform_values(rig.global_transform),"hero_transform":transform_values(scene.player.global_transform),"active_modifiers":active_modifiers,"observer_modifier":String(scene.player.rama_motion.name),"signals":final_pose_signals,"process_frame":Engine.get_process_frames(),"physics_frame":Engine.get_physics_frames(),"drawn_frame":Engine.get_frames_drawn()}
''')
s=s.replace('var faces: PackedVector3Array = shape.get_faces()','''if not shape is ConcavePolygonShape3D:
\t\t\tserialization_errors.append("candidate shape is not ConcavePolygonShape3D")
\t\t\treturn result
\t\tvar concave := shape as ConcavePolygonShape3D
\t\tvar faces: PackedVector3Array = concave.get_faces()''')
s=s.replace('encode_value(shape.get_debug_mesh().get_aabb())','encode_value(concave.get_debug_mesh().get_aabb())').replace('"backface_collision":shape.backface_collision}\n\t\tresult.material','"backface_collision":concave.backface_collision}\n\t\tresult.material')
a=s.index('\tstate.hero_skeleton = {');b=s.index('\tstate.hero_global_transform',a)
s=s[:a]+'''\tstate.hero_skeleton = final_pose.duplicate(true)
\t# Raw counters remain available; comparator excludes ONLY these named absolute counters.
\tstate.pose_signal_counters = {}
\tfor name in ["process_frame","physics_frame","drawn_frame"]:
\t\tstate.pose_signal_counters[name] = state.hero_skeleton.get(name,-1)
\t\tstate.hero_skeleton.erase(name)
\tstate.pose_correlation = {"source":"RamaMotion.modification_processed","preflight_no_draw":preflight,"process_age":Engine.get_process_frames()-int(final_pose.get("process_frame",-1)),"physics_age":Engine.get_physics_frames()-int(final_pose.get("physics_frame",-1)),"draw_age":Engine.get_frames_drawn()-int(final_pose.get("drawn_frame",-1))}
'''+s[b:]
s=s.replace('check(id+" full164poses and finite supported controls",item.hero_skeleton.bone_names.size()==164 and item.hero_skeleton.bone_global_poses.size()==164 and item.serialization_errors.is_empty())','''check(id+" full164final-modifier poses and finite supported controls",item.hero_skeleton.get("bone_names",[]).size()==164 and item.hero_skeleton.get("bone_global_poses",[]).size()==164 and item.hero_skeleton.get("signals",0)>0 and item.serialization_errors.is_empty())
\tvar mods: Array = item.hero_skeleton.get("active_modifiers",[])
\tcheck(id+" observed modifier is last active skeleton modifier",not mods.is_empty() and mods.back()==item.hero_skeleton.get("observer_modifier",""))
\tcheck(id+" final-modifier sample belongs to captured frame",item.pose_correlation.process_age==0 and item.pose_correlation.physics_age==0 and (item.pose_correlation.draw_age==0 if preflight else item.pose_correlation.draw_age==1))''')
s=s.replace('var original_manifest := JSON.stringify(scene.manifest).sha256_text()','''var original_manifest := JSON.stringify(scene.manifest).sha256_text()
\tscene.player.rama_motion.modification_processed.connect(observe_final_pose)''')
p.write_text(s)
