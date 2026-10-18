extends Node3D
## Original continuous Rama ribbons and swept arrows, driven only by accepted events.
## No gameplay references, lights, particles, camera shake, screen read or audio.
const RibbonShader = preload("res://shaders/rama_ribbon.gdshader")
const CalligraphyShader = preload("res://shaders/rama_ability_calligraphy.gdshader")
const BoundaryShader = preload("res://shaders/rama_ability_boundary.gdshader")
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const COLORS := {"kodanda":Color("e8c373"),"piercing_dawn":Color("f2c46e"),"measured_step":Color("77b8df"),"guardian_circle":Color("8de4c4"),"dawn_volley":Color("ffc271")}
const MAX_CASTS := 12
const MAX_IMPACTS := 18
const MAX_LIFETIME := 8.0
var _casts: Dictionary = {}
var _impacts: Array = []
var _impact_pool: Array = []
# These shapes have no per-cast state. Retain a bounded set across resets so
# repeated contacts and arrows reuse geometry while keeping independent clocks,
# colours and materials. Dynamic ribbons continue to follow their accepted cast.
var _impact_meshes: Dictionary = {}
var _arrow_meshes: Dictionary = {}
var _generation := -1
var _sequence := -1
var _high_cast := -1
var _suspended := false
var _reduced_motion := false
var _reduced_effects := false
var _counts := {"accepted":0,"invalid":0,"stale":0,"expired":0,"capacity":0}
var _peak := 0
var _retired: Dictionary = {}

func _ready() -> void:process_mode = Node.PROCESS_MODE_PAUSABLE
func _process(delta: float) -> void:step(delta)
func set_suspended(value: bool) -> void:_suspended = value
func set_options(options: Dictionary) -> void:
	var previous_effects := _reduced_effects
	if options.get("reduced_motion",false) is bool:_reduced_motion = options.get("reduced_motion",false)
	if options.get("reduced_effects",false) is bool:_reduced_effects = options.get("reduced_effects",false)
	for cast in _casts.values():
		cast.last_geometry_frame=-1
		_animate(cast)
	for impact in _impacts:
		if previous_effects != _reduced_effects:_refresh_impact(impact)
		_animate_impact(impact)
func _finite(value: Variant, depth := 0) -> bool:
	if depth > 8:return false
	if value is float:return is_finite(value)
	if value is Vector3:return value.is_finite() and value.length_squared() < 10000000
	if value is Dictionary:
		if value.size()>64:return false
		for item in value.values():
			if not _finite(item,depth+1):return false
	elif value is Array:
		if value.size()>80:return false
		for item in value:
			if not _finite(item,depth+1):return false
	elif value is String:return value.length()<=256
	elif not (value is int or value is bool or value==null):return false
	return true
func _number(value: Variant, lower: float, upper: float) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)>=lower and float(value)<=upper
func _valid(event: Dictionary) -> bool:
	if not _finite(event) or not event.get("schema") is int or event.get("schema")!=1 or not event.get("kind","") in ["begin","release","impact","tick","recovery","end","cancel","reset"]:return false
	for key in ["generation","cast_id","event_seq"]:
		if not event.get(key) is int or event[key]<0:return false
	if event.kind=="reset":return true
	if not IDS.has(event.get("ability_id")) or not _number(event.get("duration_s"),.01,MAX_LIFETIME) or not _number(event.get("age_s"),0,MAX_LIFETIME+.1) or not _number(event.get("time_s"),0,1e8):return false
	for key in ["origin","forward","target"]:
		if not event.get(key) is Vector3:return false
	if absf(event.forward.length()-1)> .002 or absf(event.forward.y)>.001:return false
	var timing = event.get("timing")
	if not timing is Dictionary:return false
	for key in ["windup_s","recovery_s","travel_s","active_s","movement_s"]:
		if not _number(timing.get(key),0,8):return false
	var g = event.get("geometry")
	if not g is Dictionary or not g.get("kind","") in ["projectiles","circle","step"]:return false
	for key in ["origin","center","forward"]:
		if not g.get(key) is Vector3:return false
	var required_kind: String="circle" if event.ability_id=="guardian_circle" else ("step" if event.ability_id=="measured_step" else "projectiles")
	if g.kind!=required_kind:return false
	if g.origin!=event.origin or g.forward!=event.forward:return false
	if g.kind in ["circle","step"] and g.center!=event.target:return false
	if not _number(g.get("range_m"),.1,45) or not _number(g.get("radius_m"),.05,6):return false
	var arrows = g.get("projectiles",[])
	if not arrows is Array or arrows.size()>3:return false
	if g.kind=="projectiles":
		if arrows.size()!=(3 if event.ability_id=="dawn_volley" else 1) or not _number(g.get("speed_mps"),1,80):return false
		for index in arrows.size():
			var p = arrows[index]
			if not p is Dictionary or not p.get("index") is int or p.get("index")!=index or not p.get("origin") is Vector3 or not p.get("forward") is Vector3 or absf(p.forward.length()-1)>.002 or not _number(p.get("delay_s"),0,.5):return false
	var receipts = event.get("receipts",[])
	if not receipts is Array or receipts.size()>73:return false
	for receipt in receipts:
		if not receipt is Dictionary or not receipt.get("unit_id") is int or receipt.unit_id<0 or not receipt.get("position") is Vector3 or receipt.get("kind","") not in ["damage","guardian"]:return false
	if event.has("projectile_index") and (not event.projectile_index is int or event.projectile_index<0 or event.projectile_index>=arrows.size()):return false
	if event.kind=="impact" and g.kind=="projectiles" and (not event.get("contact_position") is Vector3 or not event.get("projectile_index") is int or not event.get("terminal") is bool or event.get("reason","") not in ["unit","wall","range"]):return false
	if event.has("contact_position") and not event.contact_position is Vector3:return false
	return true
func consume_event(event: Dictionary) -> bool:
	if not _valid(event):_counts.invalid+=1;return false
	if event.generation<_generation or (event.generation==_generation and event.event_seq<=_sequence):_counts.stale+=1;return false
	if _suspended and not event.kind in ["reset","cancel","end"]:_counts.stale+=1;return false
	if event.generation>_generation:
		if event.kind not in ["reset","begin"]:_counts.stale+=1;return false
		_clear();_generation=event.generation;_sequence=-1;_high_cast=-1;_retired.clear()
	if event.kind=="reset":_clear();_sequence=event.event_seq;_counts.accepted+=1;return true
	var id: int = event.cast_id
	if event.kind=="begin":
		if _casts.has(id) or _retired.has(id) or id<=_high_cast:_counts.stale+=1;return false
		_high_cast=id
		if _casts.size()>=MAX_CASTS:_counts.capacity+=1;return false
		_casts[id]=_build(event)
		_peak=maxi(_peak,_casts.size())
	elif event.kind in ["end","cancel"]:
		if not _casts.has(id):_counts.stale+=1;return false
		_retire(id)
		_retired[id]=true
		if _retired.size()>96:_retired.erase(_retired.keys()[0])
	elif _casts.has(id):
		var cast: Dictionary = _casts[id]
		# A cast releases once. A new sequence number must not restart the
		# accepted projectile clock or relocate already committed presentation.
		if event.kind == "release" and cast.released:
			_counts.stale += 1
			return false
		if event.kind == "impact" and not cast.released:
			_counts.stale += 1
			return false
		if event.ability_id!=cast.id or event.age_s+1e-6<cast.authority_age or not _same_geometry(cast,event):_counts.stale+=1;return false
		cast.authority_age=event.age_s
		cast.since_event=0.0
		cast.age=clampf(cast.age,float(event.age_s),float(event.age_s)+.05)
		cast.last=event.duplicate(true)
		if event.kind=="release":
			cast.released=true
			cast.release_age_s=float(event.age_s)
			cast.geometry=event.geometry.duplicate(true)
			cast.root.global_position=event.origin if cast.geometry.kind!="circle" else event.target
		if event.kind=="impact":
			if event.has("projectile_index") and event.get("terminal",true):cast.contacts[event.projectile_index]=event.contact_position
			if event.has("contact_position") and cast.id!="measured_step":_impact(event.contact_position,COLORS[cast.id],event.get("reason","")=="unit",cast.geometry.forward)
			for receipt in event.receipts:
				if receipt.kind=="guardian":continue
				if not event.has("contact_position"):_impact(receipt.position+Vector3.UP, COLORS[cast.id],true)
			if cast.id=="measured_step":cast.geometry.center=event.geometry.center
		cast.attachments=event.geometry.get("attachments",[]).duplicate(true)
		_animate(cast)
	else:_counts.stale+=1;return false
	_sequence=event.event_seq
	_counts.accepted+=1
	return true
func _same_geometry(cast: Dictionary, event: Dictionary) -> bool:
	if cast.timing != event.timing or absf(cast.duration-float(event.duration_s))>.00001:return false
	var before: Dictionary=cast.geometry.duplicate(true)
	var after: Dictionary=event.geometry.duplicate(true)
	before.erase("attachments");after.erase("attachments")
	if before.get("projectiles",[]).size()!=after.get("projectiles",[]).size():return false
	if cast.id=="kodanda" and event.kind=="release":
		if before.origin.distance_to(after.origin)>4.0001:return false
		before.origin=after.origin;before.center=after.center
	if before.kind=="projectiles" and event.kind=="release":
		for i in before.projectiles.size():
			if after.projectiles[i].origin.distance_to(after.origin)>3.0001:return false
			before.projectiles[i].origin=after.projectiles[i].origin
	if cast.id=="measured_step" and event.kind=="impact":
		if before.origin.distance_to(after.center)>float(before.range_m)+.01:return false
		before.center=after.center
	return before==after
func _clear() -> void:
	for cast in _casts.values():
		if is_instance_valid(cast.root):cast.root.free()
	_casts.clear()
	for impact in _impacts:
		if is_instance_valid(impact.root):impact.root.free()
	_impacts.clear()
	for impact in _impact_pool:
		if is_instance_valid(impact.root):impact.root.free()
	_impact_pool.clear()
func reset() -> void:_clear()
func _exit_tree() -> void:_clear()
func _retire(id: int) -> void:
	if not _casts.has(id):return
	_casts[id].root.free();_casts.erase(id);_retired[id]=true
	if _retired.size()>96:_retired.erase(_retired.keys()[0])
func step(delta: float) -> void:
	if not is_finite(delta) or delta<0 or delta>.5 or _suspended or (is_inside_tree() and get_tree().paused):return
	for id in _casts.keys():
		var cast: Dictionary = _casts[id]
		cast.age=minf(cast.age+delta,cast.authority_age+.05)
		cast.since_event+=delta
		# Waiting for an authoritative release never grows a phantom projectile.
		if cast.age>cast.duration+.35 or cast.since_event>MAX_LIFETIME:_counts.expired+=1;_retire(id)
		else:_animate(cast)
	for i in range(_impacts.size()-1,-1,-1):
		var impact: Dictionary = _impacts[i]
		impact.age+=delta
		if impact.age>.42:
			impact.root.visible=false
			_impact_pool.append(impact)
			_impacts.remove_at(i)
			continue
		_animate_impact(impact)

func _animate_impact(impact: Dictionary) -> void:
	var t: float = clampf(impact.age/.42,0.0,1.0)
	impact.root.scale=Vector3.ONE*(.65 if _reduced_motion else .3+(1-pow(1-t,3))*.9)
	impact.material.set_shader_parameter("opacity",(1-t)*(.52 if _reduced_effects else .85))
	impact.material.set_shader_parameter("phase",impact.age)
	impact.material.set_shader_parameter("reduced_motion",_reduced_motion)

func _material(color: Color, opacity := .8, flow := .7) -> ShaderMaterial:
	var material:=ShaderMaterial.new()
	material.shader=RibbonShader
	material.set_shader_parameter("tint",color)
	material.set_shader_parameter("opacity",opacity)
	material.set_shader_parameter("flow",flow)
	return material

func _calligraphy(color: Color, opacity := .8, flow := .7) -> ShaderMaterial:
	var material := _material(color,opacity,flow)
	material.shader=CalligraphyShader
	return material

# The indigo contour is a restrained silhouette against warm paving, not another
# gameplay outline. These authored paths are packed into the existing meshes.
func _solar_arc(radius: float, center: Vector3, start: float, end: float, count:=24) -> Array:
	var path: Array=[]
	for i in range(count+1):
		var a:=lerpf(start,end,float(i)/count)
		path.append(center+Vector3(cos(a)*radius,sin(a)*radius,0))
	return path
func _quill_paths(length: float, spread: float) -> Array:
	var paths: Array=[]
	for sign_ in [-1,1]:
		paths.append([Vector3(sign_*spread,0,.05),Vector3(0,0,.62),Vector3(sign_*spread*.35,0,.20)])
		paths.append([Vector3(0,-sign_*spread,.05),Vector3(0,0,.62)])
		# Split, swept vanes stay behind the actual projectile tip. All of the
		# sculpted arrow's lines share its one existing mesh and material.
		paths.append(_curve(Vector3(0,0,-length),Vector3(sign_*spread*.5,.025,-length*.72),Vector3(sign_*spread*1.5,.025,-length*.52),Vector3(0,0,-length*.20),12))
	paths.append([Vector3(0,0,-length),Vector3(0,0,.62)])
	return paths
func _ribbon(paths: Array, width: float, vertical := false, taper := false, plane_normal := Vector3.ZERO) -> ArrayMesh:
	var vertices:=PackedVector3Array()
	var uv:=PackedVector2Array()
	var colors:=PackedColorArray()
	var indices:=PackedInt32Array()
	for path in paths:
		if path.size()<2:continue
		var base:=vertices.size()
		for i in path.size():
			var tangent: Vector3 = path[mini(i+1,path.size()-1)]-path[maxi(i-1,0)]
			var side:=tangent.cross(plane_normal).normalized() if plane_normal.length_squared()>.001 else (Vector3.UP if vertical else tangent.cross(Vector3.UP).normalized())
			if side.length_squared()<.001:side=Vector3.RIGHT
			var t:=float(i)/float(path.size()-1)
			var envelope:=maxf(.04,sin(t*PI)) if taper else 1.0
			vertices.append(path[i]-side*width*.5*envelope)
			vertices.append(path[i]+side*width*.5*envelope)
			uv.append(Vector2(t,0));uv.append(Vector2(t,1))
			colors.append(Color(1,1,1,1));colors.append(Color(1,1,1,1))
			if i>0:
				var n: int=base+i*2
				indices.append_array(PackedInt32Array([n-2,n-1,n,n,n-1,n+1]))
	var mesh:=ArrayMesh.new()
	if vertices.is_empty():return mesh
	var arrays:=[]
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_COLOR]=colors;arrays[Mesh.ARRAY_INDEX]=indices
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return mesh
func _part(parent: Node3D, label: String, paths: Array, width: float, material: Material, vertical:=false, taper:=false) -> MeshInstance3D:
	var node:=MeshInstance3D.new()
	node.name=label;node.mesh=_ribbon(paths,width,vertical,taper);node.material_override=material
	node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(node)
	return node
func _arc(radius: float, height: float, start:=0.0, end:=TAU, count:=64) -> Array:
	var path: Array=[]
	for i in range(count+1):
		var a:=lerpf(start,end,float(i)/count)
		path.append(Vector3(sin(a)*radius,height,cos(a)*radius))
	return path
func _curve(a: Vector3,b: Vector3,c: Vector3,d: Vector3,count:=32) -> Array:
	var path: Array=[]
	for i in range(count+1):
		var t:=float(i)/count
		path.append(a.bezier_interpolate(b,c,d,t))
	return path
func _basis(forward: Vector3) -> Basis:return Basis(Vector3(forward.z,0,-forward.x),Vector3.UP,forward)
func _warning_width(g: Dictionary) -> float:
	# The essential ward boundary has a dark inward stroke, not a filled field.
	# Scaling for tiny valid radii keeps the whole annulus inside its true edge.
	return minf(.22,float(g.radius_m)*.20) if g.kind=="circle" else .11
func _warning(g: Dictionary) -> Array:
	var paths: Array=[]
	if g.kind=="circle":
		# Continuous exact outer edge; decorative petals stay inside this boundary.
		paths.append(_arc(float(g.radius_m)-_warning_width(g)*.5,.055))
	elif g.kind=="step":
		var delta: Vector3=g.center-g.origin
		var inverse:=_basis(g.forward).inverse()
		var local: Vector3=inverse*delta
		paths.append([Vector3(0,.06,0),local+Vector3.UP*.06])
	else:
		for p in g.projectiles:
			var inverse:=_basis(g.forward).inverse()
			var direction: Vector3=inverse*p.forward
			var right:=Vector3(direction.z,0,-direction.x)
			for sign_ in [-1,1]:
				# The radius is the projectile sweep, unit hulls are separate receivers.
				paths.append([right*float(g.radius_m)*sign_+Vector3.UP*.055,direction*float(g.range_m)+right*float(g.radius_m)*sign_+Vector3.UP*.055])
	return paths
func _build(event: Dictionary) -> Dictionary:
	var root_:=Node3D.new()
	root_.name="Rama_%s_%d"%[event.ability_id,event.cast_id]
	add_child(root_);root_.top_level=true
	root_.global_transform=Transform3D(_basis(event.forward),event.target if event.geometry.kind=="circle" else event.origin)
	var main:=_calligraphy(COLORS[event.ability_id])
	var detail_color: Color={"kodanda":Color("74bde1"),"piercing_dawn":Color("8490dd"),"measured_step":Color("b4dfef"),"guardian_circle":Color("c2e8b5"),"dawn_volley":Color("8d9bea")}[event.ability_id]
	var detail:=_calligraphy(detail_color,.75,.25)
	detail.set_shader_parameter("core_strength",.12)
	detail.set_shader_parameter("luminous",.24)
	if event.ability_id in ["piercing_dawn","dawn_volley"]:
		main.set_shader_parameter("core_strength",.62)
		main.set_shader_parameter("luminous",.65)
		detail.set_shader_parameter("core_strength",.18)
		detail.set_shader_parameter("luminous",.3)
	var warning_material:=_material(Color("edc875"),.82,0.0)
	warning_material.set_shader_parameter("luminous",.1)
	if event.geometry.kind=="circle":
		warning_material.shader=BoundaryShader
		warning_material.set_shader_parameter("opacity",.92)
		# Draw after other transparent decoration while retaining normal depth
		# testing, so opaque heroes, troops and cover still occlude the ring.
		warning_material.render_priority=2
	var warning:=_part(root_,"ExactSweepBoundary",_warning(event.geometry),_warning_width(event.geometry),warning_material)
	var motif:=_part(root_,"LivingRibbon",[],.1,main)
	var accent:=_part(root_,"FilamentContour",[],.07,detail)
	var recipients:=_part(root_,"AcceptedWardRecipients",[],.12,detail)
	var arrows: Array=[]
	for p in event.geometry.get("projectiles",[]):
		var group:=Node3D.new();root_.add_child(group)
		var long_arrow: bool=event.ability_id=="piercing_dawn"
		if not _arrow_meshes.has(long_arrow):
			_arrow_meshes[long_arrow]=_ribbon(_quill_paths(1.10 if long_arrow else .85,.17),.055)
		var shaft_node:=_part(group,"ArrowShaft",[],.055,main,false)
		shaft_node.mesh=_arrow_meshes[long_arrow]
		var feather:=_part(group,"SplitFeatherWake",[],.08,detail,true,true)
		arrows.append({"root":group,"shaft":shaft_node,"feather":feather})
	var cast:={"root":root_,"id":event.ability_id,"cast_id":event.cast_id,"geometry":event.geometry.duplicate(true),"timing":event.timing.duplicate(true),"duration":float(event.duration_s),"age":float(event.age_s),"authority_age":float(event.age_s),"released":false,"release_age_s":float(event.timing.windup_s),"contacts":{},"main":main,"detail":detail,"warning_material":warning_material,"warning":warning,"motif":motif,"accent":accent,"recipients":recipients,"attachments":[],"arrows":arrows,"last":event.duplicate(true),"last_geometry_frame":-1,"since_event":0.0}
	_animate(cast)
	return cast

func _animate(cast: Dictionary) -> void:
	var age: float=cast.age
	var prepare:=clampf(age/maxf(.01,float(cast.timing.windup_s)),0,1)
	var after:=maxf(0,age-float(cast.release_age_s)) if cast.released else 0.0
	var fade:=clampf((cast.duration-age)/.30,0,1)
	var authority_after:=maxf(0,float(cast.authority_age)-float(cast.release_age_s)) if cast.released else 0.0
	var field_active: bool=not cast.released or authority_after+.000001<float(cast.timing.active_s)
	if cast.id=="guardian_circle" and cast.warning.visible!=field_active:
		# An authoritative expiry must clear recipients even when interpolation
		# has already reached this geometry frame and is waiting for the next tick.
		cast.last_geometry_frame=-1
	if cast.id=="guardian_circle" and cast.released:
		# Decoration settles before the exact gameplay boundary expires.
		fade=minf(fade,smoothstep(0,.25,maxf(0,float(cast.timing.active_s)-after))) if field_active else 0.0
	var charge:=lerpf(.26,1.0,smoothstep(0,.82,prepare)) if not cast.released and cast.id in ["piercing_dawn","dawn_volley"] else 1.0
	cast.main.set_shader_parameter("opacity",(.62 if _reduced_effects else .88)*fade*charge)
	cast.detail.set_shader_parameter("opacity",.70*fade)
	for material in [cast.main,cast.detail]:
		material.set_shader_parameter("phase",age)
		material.set_shader_parameter("reduced_motion",_reduced_motion)
	cast.warning.visible=not cast.released or (cast.id=="guardian_circle" and field_active)
	if cast.id=="kodanda":cast.warning.visible=false
	var geometry_frame:=int(age*30)
	var geometry_changed: bool=geometry_frame!=cast.last_geometry_frame
	if geometry_changed:
		cast.last_geometry_frame=geometry_frame
		var shapes:=_shapes(cast,prepare,after)
		var solar: bool=cast.id in ["piercing_dawn","dawn_volley"]
		var facing := Vector3.BACK if solar or cast.id=="kodanda" else Vector3.ZERO
		cast.motif.mesh=_ribbon(shapes.main,.085 if solar else (.15 if cast.id=="guardian_circle" else .12),false,true,facing)
		cast.accent.mesh=_ribbon(shapes.detail if not _reduced_effects else [],.040 if solar else .055,true,true,facing)
		var recipients: Array=[]
		var inverse: Transform3D=cast.root.global_transform.affine_inverse()
		var attachments: Array=cast.attachments if cast.id!="guardian_circle" or field_active else []
		for a in attachments:
			if not a is Dictionary or not a.get("position") is Vector3:continue
			var p: Vector3=inverse*a.position
			var path:=_arc(.65,1.1,-1.1,1.1,16)
			for i in path.size():path[i]+=p
			recipients.append(path)
		cast.recipients.mesh=_ribbon(recipients,.10,true)
	cast.accent.visible=not _reduced_effects
	for index in cast.arrows.size():
		var arrow: Dictionary=cast.arrows[index]
		var p: Dictionary=cast.geometry.projectiles[index]
		var travel:=after-float(p.delay_s)
		arrow.root.visible=cast.released and travel>=0 and not cast.contacts.has(index)
		var distance:=minf(float(cast.geometry.range_m),maxf(0,travel)*float(cast.geometry.speed_mps))
		var point: Vector3=p.origin+p.forward*distance
		arrow.root.global_transform=Transform3D(_basis(p.forward),point)
		arrow.feather.visible=not _reduced_effects
		if geometry_changed:
			var wake: Array=[]
			for sign_ in ([] if _reduced_effects else [-1,1]):
				var path: Array=[]
				for k in range(17):
					var t:=k/16.0
					var wave:=sin(t*PI*2.0-age*5.0)*.028*sin(t*PI) if not _reduced_motion else 0.0
					path.append(Vector3(sign_*(.045+sin(t*PI)*.16)+wave,.035*sin(t*PI),-.15-t*(2.0 if cast.id=="piercing_dawn" else 1.35)))
				wake.append(path)
			arrow.feather.mesh=_ribbon(wake,.065,true,true)

func _shapes(cast: Dictionary, prepare: float, after: float) -> Dictionary:
	var main: Array=[]
	var detail: Array=[]
	var age: float=cast.age
	match cast.id:
		"kodanda":
			if not cast.released:
				var path: Array=[]
				for i in range(25):
					var a:=lerpf(-1.2,1.2,i/24.0)
					path.append(Vector3(sin(a)*(.16+.12*prepare),1.27+cos(a)*.24,.5))
				main.append(path)
				# Paired fine strings gather toward the nock; the centre remains
				# open so the reticle and opponent silhouette remain legible.
				for sign_ in [-1,1]:
					detail.append(_curve(Vector3(sign_*.24,1.13,.48),Vector3(sign_*.16,1.02,.54),Vector3(sign_*.08,1.30,.64),Vector3(0,1.30,.72),12))
		"piercing_dawn":
			if not cast.released:
				# An incomplete solar seal gathers toward the arrow point. Open
				# gaps and an empty centre preserve the aim/receiver silhouette.
				var r:=lerpf(.16,.57,smoothstep(0,1,prepare))
				var turn:=age*.32 if not _reduced_motion else 0.0
				for index in range(3):
					var a:=TAU*index/3.0+turn
					main.append(_solar_arc(r,Vector3(0,1.30,.70),a,a+1.18,24))
					detail.append(_solar_arc(r*1.12,Vector3(0,1.30,.72),a+.08,a+.92,18))
				for sign_ in [-1,1]:
					main.append(_curve(Vector3(sign_*.44,.94,.12),Vector3(sign_*.62,1.08,.55),Vector3(sign_*.22,1.48,1.0),Vector3(0,1.30,1.48),24))
					detail.append(_curve(Vector3(sign_*.25,1.58,.16),Vector3(sign_*.46,1.73,.6),Vector3(sign_*.13,1.40,1.10),Vector3(0,1.30,1.48),20))
			elif after<.24:
				var settle:=1.0-smoothstep(0,.24,after)
				for index in range(3):
					var a:=TAU*index/3.0
					main.append(_solar_arc(.57+after*.8,Vector3(0,1.30,.70+after),a,a+1.18*settle,18))
		"measured_step":
			var destination: Vector3=cast.root.global_basis.inverse()*(cast.geometry.center-cast.geometry.origin)
			var t:=clampf(after/maxf(.01,float(cast.timing.movement_s)),0,1) if cast.released else 0.0
			for sign_ in [-1,1]:
				var a:=Vector3(sign_*.26,.55,0)
				var d:=destination*t+Vector3(sign_*.26,.65,0)
				main.append(_curve(a,a+Vector3(sign_*.7,.5,0)+destination*.2*t,d+Vector3(-sign_*.25,.45,0)-destination*.25*t,d))
				if cast.released:detail.append(_curve(a+Vector3.UP*.5,a+destination*.3*t+Vector3.UP*.3,d-destination*.15*t+Vector3.UP*.7,d+Vector3.UP*.4))
			# Stationary, open drape echoes mark positions already traversed.
			# They never run ahead of movement or imply another living hero.
			if cast.released and not _reduced_motion and not _reduced_effects:
				for station in [.20,.48,.76]:
					if t<=station:continue
					var p: Vector3=destination*station
					var strength: float=clampf((t-station)*4.0,0.0,1.0)
					for sign_ in [-1,1]:
						detail.append(_curve(p+Vector3(sign_*.30,.28,0),p+Vector3(sign_*.18,.78,-.16)*strength,p+Vector3(sign_*.43,1.26,-.08),p+Vector3(sign_*.12,1.43,.02),16))
		"guardian_circle":
			var radius: float=cast.geometry.radius_m
			var growth:=smoothstep(0,1,prepare)
			if not cast.released or after+.000001<float(cast.timing.active_s):
				for index in range(8):
					var a:=TAU*index/8.0
					var out:=Vector3(sin(a),0,cos(a))
					var right:=Vector3(cos(a),0,-sin(a))
					var inner:=out*radius*.30+Vector3.UP*.10
					var tip:=out*radius*.84+Vector3.UP*.12
					var height:=minf(1.18,radius*.25)*growth
					if not _reduced_motion:height+=sin(age*1.4+index*.7)*minf(.055,radius*.01)
					var shoulder:=out*radius*.60+Vector3.UP*height
					main.append(_curve(inner,shoulder+right*radius*.19,tip+right*radius*.12,tip,24))
					main.append(_curve(tip,tip-right*radius*.12,shoulder-right*radius*.19,inner,24))
					if not _reduced_effects:
						# Detached inner veins imply a lotus rather than a second
						# protection boundary. Every petal stays inside the edge.
						detail.append(_curve(inner+out*radius*.08,shoulder+right*radius*.07,tip-out*radius*.12,tip-out*radius*.06,18))
						detail.append(_arc(radius*.49,.085,a-.12,a+.12,8))
		"dawn_volley":
			var collapse:=1.0-smoothstep(0,.30,after) if cast.released else 1.0
			if collapse>0:
				# Three distinct open sun-blades fold into one nock. Each blade
				# has a short engraved indigo echo, not a second broad ribbon.
				var growth:=lerpf(.32,1.0,smoothstep(0,1,prepare))
				for index in range(3):
					var a:=TAU*index/3.0+(age*.24 if not _reduced_motion else 0.0)
					var path: Array=[]
					var inner: Array=[]
					for i in range(33):
						var t:=i/32.0
						var angle:=a+t*1.62
						var r: float=(.23+sin(t*PI)*.59)*growth*collapse
						path.append(Vector3(cos(angle)*r,1.35+sin(angle)*r,.48+t*.62))
						inner.append(Vector3(cos(angle)*r*.84,1.35+sin(angle)*r*.84,.51+t*.62))
					main.append(path);detail.append(inner)
					if not _reduced_effects:
						# Three small notches count the actual unreleased arrows;
						# their removal uses the accepted projectile delay.
						if not cast.released or after<float(cast.geometry.projectiles[index].delay_s):
							var notch:=Vector3(cos(a+.72),sin(a+.72),0)*growth*collapse
							detail.append(_solar_arc(.075,Vector3(0,1.35,.60)+notch*.95,a+.1,a+2.2,12))
					var out:=Vector3(cos(a+.7),sin(a+.7),0)
					# Fine detached rays stay behind the forward muzzle and do not
					# impersonate the three unreleased gameplay arrows.
					if not _reduced_effects:
						for ray in range(2):
							var center:=Vector3(0,1.35,.62)+out*(.94+ray*.13)*growth*collapse
							detail.append([center-out*.045,center+out*.045])
	return {"main":main,"detail":detail}
func _impact(point: Vector3, color: Color, hit: bool, forward := Vector3.BACK) -> void:
	var recycled: Dictionary={}
	if not _impact_pool.is_empty():recycled=_impact_pool.pop_back()
	elif _impacts.size()>=MAX_IMPACTS:recycled=_impacts.pop_front()
	var root_: Node3D=recycled.get("root",null)
	var material: ShaderMaterial=recycled.get("material",null)
	if not is_instance_valid(root_):
		root_=Node3D.new();add_child(root_);root_.top_level=true
		material=_calligraphy(color,.85,.15)
		material.set_shader_parameter("core_strength",.42)
		material.set_shader_parameter("luminous",.32)
	root_.global_transform=Transform3D(_basis(forward),point);root_.visible=true
	material.set_shader_parameter("tint",color);material.set_shader_parameter("opacity",.85)
	var impact:={"root":root_,"material":material,"age":0.0,"hit":hit}
	_refresh_impact(impact)
	_animate_impact(impact)
	_impacts.append(impact)

func _refresh_impact(impact: Dictionary) -> void:
	var key: int=(2 if impact.hit else 0)+(1 if _reduced_effects else 0)
	var root_: Node3D=impact.root
	if root_.get_child_count()==0:_part(root_,"AcceptedContactBloom",[],.055,impact.material,true,true)
	if _impact_meshes.has(key):
		root_.get_child(0).mesh=_impact_meshes[key]
		return
	var paths: Array=[]
	var spokes:=8 if impact.hit and not _reduced_effects else 4
	for i in range(spokes):
		var angle:=TAU*i/float(spokes)
		var direction:=Vector3(cos(angle),sin(angle),.20*sin(angle*2))
		var reach:=.88 if i%2==0 else .62
		paths.append(_curve(direction*.20,direction*.36+Vector3(0,.07,0),direction*reach, direction*(reach+.08),10))
		if impact.hit and not _reduced_effects and i%2==0:
			var right:=Vector3(-sin(angle),cos(angle),0)
			# Tiny open feather barbs echo the bow's swept quills, with no
			# opaque contact disk or screen-filling additive flash.
			paths.append(_curve(direction*.32,direction*.44+right*.16,direction*.62+right*.12,direction*.76,10))
	if not _reduced_effects:
		paths.append(_solar_arc(.24,Vector3.ZERO,-.35,2.1,18))
		paths.append(_solar_arc(.24,Vector3.ZERO,2.8,5.25,18))
	var mesh:=_ribbon(paths,.045,true,true,Vector3.BACK)
	_impact_meshes[key]=mesh
	root_.get_child(0).mesh=mesh
func report() -> Dictionary:
	var meshes:=0
	var triangles:=0
	var finite:=true
	var live_arrows:=0
	var impact_triangles:=0
	var states: Array=[]
	for cast in _casts.values():
		finite=finite and cast.root.global_transform.is_finite()
		var pending: Array=[cast.root]
		while not pending.is_empty():
			var node: Node=pending.pop_back()
			pending.append_array(node.get_children())
			if node is MeshInstance3D:
				meshes+=1
				if node.mesh and node.mesh.get_surface_count()>0:triangles+=node.mesh.surface_get_array_index_len(0)/3
		for arrow in cast.arrows:
			if arrow.root.visible:live_arrows+=1
		states.append({"cast_id":cast.cast_id,"ability_id":cast.id,"age_s":cast.age,"released":cast.released,"warning_visible":cast.warning.visible})
	for impact in _impacts:
		finite=finite and impact.root.global_transform.is_finite()
		var mesh: Mesh=impact.root.get_child(0).mesh
		if mesh and mesh.get_surface_count()>0:impact_triangles+=mesh.surface_get_array_index_len(0)/3
	return {"active":_casts.size(),"peak_active":_peak,"max_casts":MAX_CASTS,"impacts":_impacts.size(),"pooled_impacts":_impact_pool.size(),"allocated_impacts":_impacts.size()+_impact_pool.size(),"max_impacts":MAX_IMPACTS,"generation":_generation,"meshes":meshes,"triangles":triangles,"impact_triangles":impact_triangles,"total_triangles":triangles+impact_triangles,"live_arrows":live_arrows,"finite":finite,"reduced_motion":_reduced_motion,"reduced_effects":_reduced_effects,"counts":_counts.duplicate(),"casts":states,"particles":0,"lights":0,"scope":"Original event-driven Rama presentation; no gameplay authority"}
