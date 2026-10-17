extends Node3D
## Original continuous Rama ribbons and swept arrows, driven only by accepted events.
## No gameplay references, lights, particles, camera shake, screen read or audio.
const RibbonShader = preload("res://shaders/rama_ribbon.gdshader")
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const COLORS := {"kodanda":Color("e8c373"),"piercing_dawn":Color("8fdce7"),"measured_step":Color("77b8df"),"guardian_circle":Color("8de4c4"),"dawn_volley":Color("f4bf6a")}
const MAX_CASTS := 12
const MAX_IMPACTS := 18
const MAX_LIFETIME := 8.0
var _casts: Dictionary = {}
var _impacts: Array = []
var _impact_pool: Array = []
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
	if options.get("reduced_motion",false) is bool:_reduced_motion = options.get("reduced_motion",false)
	if options.get("reduced_effects",false) is bool:_reduced_effects = options.get("reduced_effects",false)
	for cast in _casts.values():
		cast.last_geometry_frame=-1
		_animate(cast)
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
			if event.has("contact_position") and cast.id!="measured_step":_impact(event.contact_position,COLORS[cast.id],event.get("reason","")=="unit")
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
		var t: float = impact.age/.42
		impact.root.scale=Vector3.ONE*(.65 if _reduced_motion else .3+(1-pow(1-t,3))*.9)
		impact.material.set_shader_parameter("opacity",(1-t)*.85)
		impact.material.set_shader_parameter("phase",impact.age)

func _material(color: Color, opacity := .8, flow := .7) -> ShaderMaterial:
	var material:=ShaderMaterial.new()
	material.shader=RibbonShader
	material.set_shader_parameter("tint",color)
	material.set_shader_parameter("opacity",opacity)
	material.set_shader_parameter("flow",flow)
	return material
func _ribbon(paths: Array, width: float, vertical := false, taper := false) -> ArrayMesh:
	var vertices:=PackedVector3Array()
	var uv:=PackedVector2Array()
	var colors:=PackedColorArray()
	var indices:=PackedInt32Array()
	for path in paths:
		if path.size()<2:continue
		var base:=vertices.size()
		for i in path.size():
			var tangent: Vector3 = path[mini(i+1,path.size()-1)]-path[maxi(i-1,0)]
			var side:=Vector3.UP if vertical else tangent.cross(Vector3.UP).normalized()
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
func _warning(g: Dictionary) -> Array:
	var paths: Array=[]
	if g.kind=="circle":
		# Continuous exact outer edge; decorative petals stay inside this boundary.
		paths.append(_arc(float(g.radius_m)-.055,.055))
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
	var main:=_material(COLORS[event.ability_id])
	var detail_color: Color={"kodanda":Color("74bde1"),"piercing_dawn":Color("eef5ec"),"measured_step":Color("b4dfef"),"guardian_circle":Color("c2e8b5"),"dawn_volley":Color("9cd9ea")}[event.ability_id]
	var detail:=_material(detail_color,.75,.25)
	var warning_material:=_material(Color("edc875"),.82,0.0)
	warning_material.set_shader_parameter("luminous",.1)
	var warning:=_part(root_,"ExactSweepBoundary",_warning(event.geometry),.11,warning_material)
	var motif:=_part(root_,"LivingRibbon",[],.1,main)
	var accent:=_part(root_,"FilamentContour",[],.07,detail)
	var recipients:=_part(root_,"AcceptedWardRecipients",[],.12,detail)
	var arrows: Array=[]
	for p in event.geometry.get("projectiles",[]):
		var group:=Node3D.new();root_.add_child(group)
		var shaft: Array=[Vector3(0,0,-.85),Vector3(0,0,.50)]
		var head: Array=[Vector3(-.16,0,.20),Vector3(0,0,.65),Vector3(.16,0,.20)]
		var shaft_node:=_part(group,"ArrowShaft",[shaft,head],.065,main,false)
		var feather:=_part(group,"SplitFeatherWake",[],.12,detail,true,true)
		arrows.append({"root":group,"shaft":shaft_node,"feather":feather})
	var cast:={"root":root_,"id":event.ability_id,"cast_id":event.cast_id,"geometry":event.geometry.duplicate(true),"timing":event.timing.duplicate(true),"duration":float(event.duration_s),"age":float(event.age_s),"authority_age":float(event.age_s),"released":false,"release_age_s":float(event.timing.windup_s),"contacts":{},"main":main,"detail":detail,"warning_material":warning_material,"warning":warning,"motif":motif,"accent":accent,"recipients":recipients,"attachments":[],"arrows":arrows,"last":event.duplicate(true),"last_geometry_frame":-1,"since_event":0.0}
	_animate(cast)
	return cast

func _animate(cast: Dictionary) -> void:
	var age: float=cast.age
	var prepare:=clampf(age/maxf(.01,float(cast.timing.windup_s)),0,1)
	var after:=maxf(0,age-float(cast.release_age_s)) if cast.released else 0.0
	var fade:=clampf((cast.duration-age)/.30,0,1)
	var field_active: bool=not cast.released or after+.000001<float(cast.timing.active_s)
	if cast.id=="guardian_circle" and cast.released:
		# Decoration settles before the exact gameplay boundary expires.
		fade=minf(fade,smoothstep(0,.25,maxf(0,float(cast.timing.active_s)-after))) if field_active else 0.0
	cast.main.set_shader_parameter("opacity",(.62 if _reduced_effects else .88)*fade)
	cast.detail.set_shader_parameter("opacity",.70*fade)
	for material in [cast.main,cast.detail]:
		material.set_shader_parameter("phase",age)
		material.set_shader_parameter("reduced_motion",_reduced_motion)
	cast.warning.visible=not cast.released or (cast.id=="guardian_circle" and field_active)
	if cast.id=="kodanda":cast.warning.visible=false
	var geometry_frame:=int(age*30)
	if geometry_frame!=cast.last_geometry_frame:
		cast.last_geometry_frame=geometry_frame
		var shapes:=_shapes(cast,prepare,after)
		cast.motif.mesh=_ribbon(shapes.main,.14 if cast.id!="guardian_circle" else .18,false,true)
		cast.accent.mesh=_ribbon(shapes.detail,.065,true,true)
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
		var wake: Array=[]
		for sign_ in [-1,1]:
			var path: Array=[]
			for k in range(17):
				var t:=k/16.0
				var wave:=sin(t*PI*2.0-age*6.0)*.08 if not _reduced_motion else 0.0
				path.append(Vector3(sign_*(.08+t*.18)+wave,.03*sin(t*PI),-.3-t*(2.2 if cast.id=="piercing_dawn" else 1.4)))
			wake.append(path)
		arrow.feather.mesh=_ribbon(wake,.15,true,true)

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
		"piercing_dawn":
			if not cast.released:
				for sign_ in [-1,1]:
					var path: Array=[]
					for i in range(49):
						var t:=i/48.0
						var a: float=t*TAU+sign_*PI*.5+(age*2 if not _reduced_motion else 0.0)
						var r: float=(.38-.25*t)*prepare
						path.append(Vector3(cos(a)*r,1.25+sin(a)*r,.1+t*2.1))
					main.append(path)
					detail.append(_curve(Vector3(sign_*.4,.4,-.4),Vector3(sign_*1.15,1.5,0),Vector3(sign_*.35,1.7,1),Vector3(0,1.25,2.1)))
			elif after<.35:
				for sign_ in [-1,1]:main.append(_curve(Vector3(0,1.25,.4),Vector3(sign_*.5,1.5,1),Vector3(sign_*.7,.9,1.5),Vector3(sign_*.8,1.25,2)))
		"measured_step":
			var destination: Vector3=cast.root.global_basis.inverse()*(cast.geometry.center-cast.geometry.origin)
			var t:=clampf(after/maxf(.01,float(cast.timing.movement_s)),0,1) if cast.released else 0.0
			for sign_ in [-1,1]:
				var a:=Vector3(sign_*.26,.55,0)
				var d:=destination*t+Vector3(sign_*.26,.65,0)
				main.append(_curve(a,a+Vector3(sign_*.7,.5,0)+destination*.2*t,d+Vector3(-sign_*.25,.45,0)-destination*.25*t,d))
				if cast.released:detail.append(_curve(a+Vector3.UP*.5,a+destination*.3*t+Vector3.UP*.3,d-destination*.15*t+Vector3.UP*.7,d+Vector3.UP*.4))
		"guardian_circle":
			var radius: float=cast.geometry.radius_m
			var growth:=smoothstep(0,1,prepare)
			if not cast.released or after+.000001<float(cast.timing.active_s):
				for index in range(6):
					var a:=TAU*index/6.0
					var out:=Vector3(sin(a),0,cos(a))
					var right:=Vector3(cos(a),0,-sin(a))
					var base:=out*radius*.64
					var height:=1.0*growth
					if not _reduced_motion:height+=sin(age*1.8+index*.7)*.08
					main.append(_curve(base-right*.95+Vector3.UP*.12,base-right*.65+Vector3.UP*height,base+right*.65+Vector3.UP*height,base+right*.95+Vector3.UP*.12))
					if index%2==0:detail.append(_arc(radius*.78,.15+growth*.05,a-.35,a+.35,20))
				main.append(_arc(radius*.88,.10+growth*.02))
		"dawn_volley":
			var collapse:=1.0-smoothstep(0,.38,after) if cast.released else 1.0
			if collapse>0:
				# Three curved iris vanes gather toward the nock; no opaque solar disk.
				for index in range(3):
					var a:=TAU*index/3.0+(age*.35 if not _reduced_motion else 0.0)
					var path: Array=[]
					var inner: Array=[]
					for i in range(49):
						var t:=i/48.0
						var angle:=a+t*2.45
						var r: float=(.35+sin(t*PI)*.74)*(.4+.6*prepare)*collapse
						path.append(Vector3(cos(angle)*r,1.35+sin(angle)*r,.28+t*.48))
						inner.append(Vector3(cos(angle)*r*.84,1.35+sin(angle)*r*.84,.30+t*.48))
					main.append(path);detail.append(inner)
	return {"main":main,"detail":detail}
func _impact(point: Vector3, color: Color, hit: bool) -> void:
	var recycled: Dictionary={}
	if not _impact_pool.is_empty():recycled=_impact_pool.pop_back()
	elif _impacts.size()>=MAX_IMPACTS:recycled=_impacts.pop_front()
	var root_: Node3D=recycled.get("root",null)
	var material: ShaderMaterial=recycled.get("material",null)
	if not is_instance_valid(root_):
		root_=Node3D.new();add_child(root_);root_.top_level=true
		material=_material(color,.85,.15)
	root_.global_position=point;root_.scale=Vector3.ONE*.3;root_.visible=true
	material.set_shader_parameter("tint",color);material.set_shader_parameter("opacity",.85)
	var paths: Array=[]
	for i in range(7 if hit else 4):
		var angle:=TAU*i/(7.0 if hit else 4.0)
		var direction:=Vector3(cos(angle),sin(angle),.12)
		paths.append(_curve(direction*.12,direction*.30+Vector3(0,.12,0),direction*.6+Vector3(0,.08,0),direction*.85,12))
	if root_.get_child_count()==0:_part(root_,"AcceptedContactBloom",paths,.09,material,true,true)
	else:root_.get_child(0).mesh=_ribbon(paths,.09,true,true)
	_impacts.append({"root":root_,"material":material,"age":0.0})
func report() -> Dictionary:
	var meshes:=0
	var triangles:=0
	var finite:=true
	var live_arrows:=0
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
	return {"active":_casts.size(),"peak_active":_peak,"max_casts":MAX_CASTS,"impacts":_impacts.size(),"pooled_impacts":_impact_pool.size(),"allocated_impacts":_impacts.size()+_impact_pool.size(),"max_impacts":MAX_IMPACTS,"generation":_generation,"meshes":meshes,"triangles":triangles,"live_arrows":live_arrows,"finite":finite,"reduced_motion":_reduced_motion,"reduced_effects":_reduced_effects,"counts":_counts.duplicate(),"casts":states,"particles":0,"lights":0,"scope":"Original event-driven Rama presentation; no gameplay authority"}
