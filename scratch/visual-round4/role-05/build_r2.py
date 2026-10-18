from pathlib import Path
p=Path('scratch/visual-round4/role-05')
s=(p/'rama_motion.release-r1.gd').read_text()
s=s.replace('if foot_locks[side]:\n\t\t\tvar local_anchor: Vector3=inverse*foot_targets[side]', 'if support:\n\t\t\tvar prospective:=foot_targets[side] if foot_locks[side] else Vector3(current.x,ground_height,current.z)\n\t\t\tvar local_anchor: Vector3=inverse*prospective')
s=s.replace('pelvis_compression=move_toward(pelvis_compression,clampf(requested_compression,0,MAX_PELVIS_COMPRESSION_M),.9*dt)','pelvis_compression=maxf(clampf(requested_compression,0,MAX_PELVIS_COMPRESSION_M),move_toward(pelvis_compression,0,.9*dt))')
s=s.replace('>length-.018:', '>length:')
s=s.replace('if support and not state.blocked and absf(state.point.y-ground_height)<.008:\n\t\t\t\tvar anchor:=Vector3(state.point.x,ground_height,state.point.z)\n\t\t\t\tif hip.distance_to(inverse*anchor)<length-.025:', 'if support and not state.blocked:\n\t\t\t\tvar anchor:=Vector3(desired.x,ground_height,desired.z)\n\t\t\t\tif hip.distance_to(inverse*anchor)<=length:')
(p/'rama_motion.release-r2.gd').write_text(s)
