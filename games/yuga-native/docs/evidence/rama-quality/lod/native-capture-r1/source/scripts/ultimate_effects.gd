extends Node3D
## Original bounded invocation studies. Pure event consumer; never owns gameplay.
## +Z is local forward. Ground warnings come only from validated authority geometry.

const HEROES := ["rama","ravana","arjuna","duryodhana","hanuman","karna","bhima","meghnad","sita","draupadi","subhadra","hidimbi","chitrangada","ulupi"]
const MAX_CASTS := 4
const MAX_LIFETIME := 12.0
const COLORS := [Color("efc66e"),Color("bd83d9"),Color("b9e5ef"),Color("cf985f"),Color("cbd590"),Color("efbb5d"),Color("b3b5a5"),Color("9fafe2"),Color("aedbb9"),Color("d895bc"),Color("e1b177"),Color("91be87"),Color("afcfdf"),Color("7bcfc8")]
var _casts: Dictionary = {}
var _epoch := -1
var _high_cast := -1
var _retired: Dictionary = {}
var _suspended := false
var _reduced_effects := false
var _reduced_motion := false
var _counts := {"accepted":0,"invalid":0,"stale":0,"duplicate":0,"capacity":0,"expired":0}
var _elapsed := 0.0
var _peak_casts := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func _process(delta: float) -> void:
	step(delta)

func _number(value: Variant, low := 0.0, high := 1000000.0) -> bool:
	return (value is float or value is int) and is_finite(float(value)) and float(value) >= low and float(value) <= high

func _vector(value: Variant, bound := 1000.0) -> bool:
	return value is Vector3 and value.is_finite() and value.abs().max_axis_index() >= 0 and absf(value.x) <= bound and absf(value.y) <= bound and absf(value.z) <= bound

func _valid_geometry(g: Variant) -> bool:
	if not g is Dictionary or not g.get("kind","") in ["disk","zone_disk","sector","projectile_volley","summon_pair"]:return false
	for key in ["origin","center","forward"]:
		if not _vector(g.get(key)):return false
	var f: Vector3 = g.forward
	if absf(f.y) > .001 or absf(f.length()-1.0) > .002:return false
	if not _number(g.get("height_m"),.01,10):return false
	match g.kind:
		"disk","zone_disk":
			if not _number(g.get("radius_m"),.1,30):return false
		"sector":
			if not _number(g.get("range_m"),.1,40) or not _number(g.get("half_angle_cos"),.01,.999):return false
		"projectile_volley":
			if not _number(g.get("range_m"),.1,40) or not _number(g.get("radius_m"),.05,2) or not _number(g.get("speed_mps"),1,120):return false
			var arrows: Variant = g.get("projectiles")
			if not arrows is Array or arrows.size() < 1 or arrows.size() > 3:return false
			var ids := {}
			for p in arrows:
				if not p is Dictionary or not p.get("index") is int or p.index < 0 or p.index >= arrows.size() or ids.has(p.index):return false
				if not _vector(p.get("origin")) or not _vector(p.get("forward")) or absf(p.forward.length()-1.0) > .002 or absf(p.forward.y) > .001:return false
				ids[p.index] = true
		"summon_pair":
			var places: Variant = g.get("placements")
			if not places is Array or places.size() != 2:return false
			for p in places:
				if not _vector(p):return false
	var attachments: Variant = g.get("attachments",[])
	if not attachments is Array or attachments.size() > 72:return false
	var attached := {}
	for a in attachments:
		if not a is Dictionary or not a.get("unit_id") is int or a.unit_id < 0 or attached.has(a.unit_id) or not a.get("kind","") in ["shield","summon"] or not _vector(a.get("position")):return false
		if not _number(a.get("remaining_s"),0,12) or not _number(a.get("shield"),0,10000):return false
		attached[a.unit_id] = true
	return true

func _finite_data(value: Variant, depth := 0) -> bool:
	if depth > 8:return false
	if value is float:return is_finite(value)
	if value is Vector3:return _vector(value)
	if value is Dictionary:
		if value.size() > 64:return false
		for item in value.values():
			if not _finite_data(item,depth+1):return false
	elif value is Array:
		if value.size() > 72:return false
		for item in value:
			if not _finite_data(item,depth+1):return false
	elif value is String:
		return value.length() <= 256
	elif not (value is int or value is bool or value == null):return false
	return true

func _valid_event(e: Dictionary) -> bool:
	if not _finite_data(e):return false
	if not e.get("schema") is int or e.schema != 1 or not e.get("kind","") in ["begin","release","impact","tick","end","cancel","reset"]:return false
	for key in ["epoch","cast_id","event_seq"]:
		if not e.get(key) is int or e[key] < 0:return false
	if e.kind == "reset":return true
	if not HEROES.has(e.get("hero_id")) or e.get("effect_id") != str(e.hero_id)+".r.v1" or e.get("team") != "sun":return false
	if not _number(e.get("time_s")):return false
	for key in ["origin","forward","target"]:
		if not _vector(e.get(key)):return false
	var timing: Variant = e.get("timing")
	if not timing is Dictionary:return false
	var lifetime := 0.0
	for key in ["windup_s","travel_s","active_s","recovery_s"]:
		if not _number(timing.get(key),0,10):return false
		lifetime += float(timing[key])
	if lifetime <= 0 or lifetime > MAX_LIFETIME:return false
	if not _valid_geometry(e.get("geometry")):return false
	var receipts: Variant = e.get("receipts",[])
	if not receipts is Array or receipts.size() > 72:return false
	for receipt in receipts:
		if not receipt is Dictionary or not receipt.get("unit_id") is int or receipt.unit_id < 0:return false
	if e.has("projectile_index"):
		if not e.projectile_index is int or e.projectile_index < 0 or e.projectile_index > 2 or not _vector(e.get("contact_position")):return false
	return true

func consume_event(event: Dictionary) -> bool:
	if not _valid_event(event):
		_counts.invalid += 1
		return false
	if _suspended and not event.kind in ["reset","cancel","end"]:
		_counts.stale += 1
		return false
	var epoch: int = event.epoch
	var id: int = event.cast_id
	if epoch < _epoch:
		_counts.stale += 1
		return false
	if event.kind == "reset":
		if epoch == _epoch:
			_counts.duplicate += 1
			return false
		_clear_casts()
		_epoch = epoch
		_high_cast = -1
		_retired.clear()
		_counts.accepted += 1
		return true
	if epoch > _epoch:
		if event.kind != "begin":
			_counts.stale += 1
			return false
		_clear_casts()
		_epoch = epoch
		_high_cast = -1
		_retired.clear()
	if event.kind == "begin":
		if _casts.has(id) or _retired.has(id) or id <= _high_cast:
			_counts.duplicate += 1
			return false
		if _suspended or _casts.size() >= MAX_CASTS:
			_counts.capacity += 1
			return false
		var cast := _build(event)
		_casts[id] = cast
		_high_cast = id
		_peak_casts = maxi(_peak_casts,_casts.size())
	else:
		if not _casts.has(id):
			_counts.stale += 1
			return false
		var cast: Dictionary = _casts[id]
		if int(event.event_seq) <= int(cast.seq):
			_counts.duplicate += 1
			return false
		if event.hero_id != cast.hero or event.time_s < cast.last_time or not _same_locked_geometry(cast.geometry,event.geometry):
			_counts.invalid += 1
			return false
		cast.seq = event.event_seq
		cast.last_time = event.time_s
		cast.age = maxf(cast.age,float(event.time_s)-float(cast.start_time))
		cast.phase = event.kind
		if event.kind in ["cancel","end"]:
			_retire(id)
		else:
			if event.kind == "release":cast.released = true
			if event.kind == "impact":
				cast.impacted = true
				if event.has("projectile_index"):
					cast.contacts[event.projectile_index] = event.contact_position
			if event.geometry.has("attachments"):
				cast.attachments = event.geometry.attachments.duplicate(true)
				_refresh_attachments(cast)
			cast.receipt_ids.clear()
			for receipt in event.get("receipts",[]):cast.receipt_ids.append(receipt.unit_id)
			_animate(cast)
	_counts.accepted += 1
	return true

func _same_locked_geometry(a: Dictionary, b: Dictionary) -> bool:
	var aa := a.duplicate(true)
	var bb := b.duplicate(true)
	aa.erase("attachments")
	bb.erase("attachments")
	return aa == bb

func _clear_casts() -> void:
	for cast in _casts.values():
		if is_instance_valid(cast.root):cast.root.free()
	_casts.clear()

func _retire(id: int) -> void:
	if not _casts.has(id):return
	var cast: Dictionary = _casts[id]
	cast.root.free()
	_casts.erase(id)
	_retired[id] = true
	if _retired.size() > 64:_retired.erase(_retired.keys()[0])

func reset() -> void:
	_clear_casts()
	# Keep the epoch/high-water mark: a delayed same-epoch begin cannot revive a cast.
	_retired.clear()

func set_suspended(value: bool) -> void:
	_suspended = value

func set_options(options: Dictionary) -> void:
	if options.get("reduced_effects",false) is bool:_reduced_effects = options.get("reduced_effects",false)
	if options.get("reduced_motion",false) is bool:_reduced_motion = options.get("reduced_motion",false)
	for cast in _casts.values():_animate(cast)

func step(delta: float) -> void:
	if not is_finite(delta) or delta < 0 or delta > 1 or _suspended or (is_inside_tree() and get_tree().paused):return
	_elapsed += delta
	for id in _casts.keys():
		var cast: Dictionary = _casts[id]
		cast.age += delta
		if cast.age > cast.lifetime+.25:
			_counts.expired += 1
			_retire(id)
		else:_animate(cast)

func _mat(color: Color, alpha: float, emission: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(color,alpha)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = emission
	material.no_depth_test = false
	material.disable_receive_shadows = true
	return material

func _tri(vertices: Array, a: Vector3, b: Vector3, c: Vector3) -> void:
	vertices.append(a)
	vertices.append(b)
	vertices.append(c)

func _tube(vertices: Array, points: Array, radius: float, sides := 4) -> void:
	if points.size() < 2:return
	for index in range(points.size()-1):
		var a: Vector3 = points[index]
		var b: Vector3 = points[index+1]
		if a.distance_squared_to(b) < .0000001:continue
		var along := (b-a).normalized()
		var u := along.cross(Vector3.UP).normalized()
		if u.length_squared() < .1:u = Vector3.RIGHT
		var v := along.cross(u).normalized()
		for k in range(sides):
			var p := (u*cos(TAU*k/sides)+v*sin(TAU*k/sides))*radius
			var q := (u*cos(TAU*(k+1)/sides)+v*sin(TAU*(k+1)/sides))*radius
			_tri(vertices,a+p,b+p,b+q)
			_tri(vertices,a+p,b+q,a+q)

func _band(vertices: Array, points: Array, width: float) -> void:
	for index in range(points.size()-1):
		var a: Vector3 = points[index]
		var b: Vector3 = points[index+1]
		var side := (b-a).cross(Vector3.UP).normalized()*width*.5
		_tri(vertices,a-side,b-side,b+side)
		_tri(vertices,a-side,b+side,a+side)

func _arc(radius: float, start: float, stop: float, y := 0.0, segments := 64) -> Array:
	var points: Array = []
	for i in range(segments+1):
		var angle := lerpf(start,stop,float(i)/segments)
		points.append(Vector3(sin(angle)*radius,y,cos(angle)*radius))
	return points

func _leaf(vertices: Array, at: Vector3, direction: Vector3, length: float, width: float) -> void:
	var axis := direction.normalized()
	var side := axis.cross(Vector3.UP).normalized()
	if side.length_squared() < .1:side = Vector3.RIGHT
	var a := at-axis*length*.5
	var b := at+side*width
	var c := at+axis*length*.5
	var d := at-side*width
	var tip := at+Vector3.UP*width*.35
	_tri(vertices,a,b,tip)
	_tri(vertices,b,c,tip)
	_tri(vertices,c,d,tip)
	_tri(vertices,d,a,tip)

func _mesh(vertices: Array) -> ArrayMesh:
	var mesh := ArrayMesh.new()
	if vertices.is_empty():return mesh
	var arrays: Array = []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array(vertices)
	var normals := PackedVector3Array()
	for i in range(0,vertices.size(),3):
		var normal: Vector3 = (vertices[i+1]-vertices[i]).cross(vertices[i+2]-vertices[i]).normalized()
		normals.append(normal)
		normals.append(normal)
		normals.append(normal)
	arrays[Mesh.ARRAY_NORMAL] = normals
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return mesh

func _part(parent: Node3D, name_: String, vertices: Array, material: Material) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name_
	node.mesh = _mesh(vertices)
	node.material_override = material
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	node.set_meta("triangles",vertices.size()/3)
	parent.add_child(node)
	return node

func _basis(forward: Vector3) -> Basis:
	return Basis(Vector3(forward.z,0,-forward.x),Vector3.UP,forward)

func _warning(geometry: Dictionary, transform_: Transform3D) -> Array:
	var vertices: Array = []
	var inverse := transform_.affine_inverse()
	var y := .055
	match geometry.kind:
		"disk","zone_disk":
			# The outer stroke edge is the exact radius; centre is empty.
			_band(vertices,_arc(geometry.radius_m-.035,0,TAU,y,96),.07)
		"sector":
			var angle := acos(float(geometry.half_angle_cos))-.001
			_band(vertices,_arc(geometry.range_m-.035,-angle,angle,y,64),.07)
			for sign_ in [-1,1]:
				var edge := Vector3(sin(angle*sign_),0,cos(angle*sign_))
				var inward := Vector3(-sign_*cos(angle),0,sin(angle))*.065
				var start := Vector3(0,y,0)
				var end: Vector3 = edge*(geometry.range_m-.002)+start
				var inner: Vector3 = edge*(geometry.range_m-.07)+inward+start
				_tri(vertices,start,end,inner)
				_tri(vertices,start,inner,edge*.1+inward+start)
		"projectile_volley":
			for arrow in geometry.projectiles:
				var start: Vector3 = inverse*arrow.origin
				start.y = 0
				var direction: Vector3 = inverse.basis*arrow.forward
				var basis_ := _basis(direction)
				var length_: float = geometry.range_m
				var radius: float = geometry.radius_m-.025
				var points: Array = []
				for p in _arc(radius,-PI*.5,PI*.5,y,24):points.append(start+basis_*(p+Vector3(0,0,length_)))
				for p in _arc(radius,PI*.5,PI*1.5,y,24):points.append(start+basis_*p)
				points.append(points[0])
				_band(vertices,points,.05)
		"summon_pair":
			for placement in geometry.placements:
				var at: Vector3 = inverse*placement
				at.y = 0
				_band(vertices,[at+Vector3(-.65,y,0),at+Vector3(0,y,.65),at+Vector3(.65,y,0),at+Vector3(0,y,-.65),at+Vector3(-.65,y,0)],.07)
	return vertices

func _build(event: Dictionary) -> Dictionary:
	var g: Dictionary = event.geometry.duplicate(true)
	var center: Vector3 = g.center if g.kind in ["disk","zone_disk"] else g.origin
	center.y = 0
	var transform_ := Transform3D(_basis(g.forward),center)
	var group := Node3D.new()
	group.name = "Invocation_%d_%s"%[event.cast_id,event.hero_id]
	add_child(group)
	group.top_level = true
	group.global_transform = transform_
	var color: Color = COLORS[HEROES.find(event.hero_id)]
	var warning_material := _mat(Color("efcc83"),.78,.15)
	var main_material := _mat(color,.52,.20)
	var detail_material := _mat(Color("e9d6a0"),.40,.12)
	var receipt_material := _mat(Color("b8e3d7"),.72,.15)
	var warning := _part(group,"AuthorityBoundary",_warning(g,transform_),warning_material)
	var shapes := _motif(event.hero_id,g,transform_)
	var ornaments: Array = []
	for i in range(shapes.size()):
		var part := _part(group,"OriginalMotif%d"%i,shapes[i],main_material if i%2 == 0 else detail_material)
		ornaments.append(part)
	var attachments := _part(group,"AcceptedRecipientMarks",[],receipt_material)
	var arrows: Array = []
	if g.kind == "projectile_volley":
		for projectile in g.projectiles:
			var vertices: Array = []
			_tube(vertices,[Vector3(0,0,-.8),Vector3(0,0,.45)],.035,6)
			_leaf(vertices,Vector3(0,0,.55),Vector3.FORWARD,.7,.16)
			var arrow := _part(group,"AcceptedArrow%d"%projectile.index,vertices,receipt_material)
			arrows.append(arrow)
	var lifetime := 0.0
	for value in event.timing.values():lifetime += float(value)
	var cast := {"root":group,"hero":event.hero_id,"geometry":g,"seq":event.event_seq,"last_time":event.time_s,"start_time":event.time_s,"age":0.0,"lifetime":lifetime,"timing":event.timing.duplicate(true),"phase":"begin","released":false,"impacted":false,"warning":warning,"warning_material":warning_material,"main_material":main_material,"detail_material":detail_material,"ornaments":ornaments,"arrows":arrows,"contacts":{},"attachments":[],"attachment_node":attachments,"receipt_ids":[],"boundary_vertices":warning.mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX].duplicate(),"transform":transform_}
	_animate(cast)
	return cast

func _motif(hero: String, g: Dictionary, transform_: Transform3D) -> Array:
	var main: Array = []
	var detail: Array = []
	var radius: float = float(g.get("radius_m",6))
	match hero:
		"rama":
			for offset in [-1,0,1]:
				var bow: Array = []
				for i in range(21):
					var angle := lerpf(-1.35,1.35,i/20.0)
					bow.append(Vector3(offset*1.4+cos(angle)*.65,2+sin(angle)*1.55,.4))
				_tube(main,bow,.055,6)
				_tube(detail,[bow[0],bow[-1]],.018)
			_tube(detail,_vertical_arc(.65,0,TAU,Vector3(0,2,.1)),.05,6)
		"arjuna":
			for distance in [4.0,9.0,15.0]:
				_tube(main,[Vector3(-.9,.3,distance),Vector3(-.9,2.7,distance),Vector3(.9,2.7,distance),Vector3(.9,.3,distance)],.055,4)
				_leaf(detail,Vector3(0,2.9,distance),Vector3.UP,.8,.17)
		"ravana":
			for i in range(10):
				var a := TAU*i/10
				var at := Vector3(sin(a)*2.7,1.1,cos(a)*2.7)
				_leaf(main,at,Vector3(sin(a)*.4,1,cos(a)*.4),2.5,.48)
				_tube(detail,[at-Vector3.UP*.85,at+Vector3.UP*1.45],.035)
		"duryodhana":
			_tube(main,_vertical_arc(2.9,-1.2,1.2,Vector3(0,.8,2)),.16,6)
			for i in range(7):
				var angle := lerpf(-acos(g.half_angle_cos),acos(g.half_angle_cos),i/6.0)
				_tube(detail,[Vector3(0,.15,0),Vector3(sin(angle)*7,.2,cos(angle)*7)],.075,4)
		"hanuman":
			for i in range(3):
				var z := (i-1)*.75
				_tube(main,[Vector3(-2.8,.3,z),Vector3(-1.4,1.7+i*.3,z),Vector3(-.5,1.0,z),Vector3(.5,2.8-i*.2,z),Vector3(1.3,1.3,z),Vector3(2.8,.3,z)],.09,5)
			for i in range(8):
				var a := TAU*i/8
				_leaf(detail,Vector3(sin(a)*3,.5,cos(a)*3),Vector3(sin(a),.7,cos(a)),1.2,.2)
		"karna":
			for i in range(6):
				var a := TAU*i/6
				var at := Vector3(sin(a)*2,1.2,cos(a)*2)
				_leaf(main,at,Vector3(sin(a),.35,cos(a)),2.2,.65)
				_tube(detail,[at*.4+Vector3.UP*.5,at*1.5],.055,5)
			_tube(detail,_vertical_arc(.7,0,TAU,Vector3(0,1.2,0)),.08,6)
		"bhima":
			for i in range(8):
				var a := TAU*i/8
				var out := Vector3(sin(a),0,cos(a))
				_leaf(main,out*3+Vector3.UP*.5,out,3,.7)
				_tube(detail,[out*1.5+Vector3.UP*.2,out*2.6+Vector3.UP*.7,out*4.5+Vector3.UP*.2],.07,5)
		"meghnad":
			for k in range(3):
				var points: Array = []
				for i in range(25):
					var t := i/24.0
					points.append(Vector3((k-1)*6*t,1.0+sin(t*TAU+k)*.45,t*16))
				_tube(main,points,.10,5)
				var end: Vector3 = points[-1]
				_tube(detail,[end+Vector3(-.3,0,0),end+Vector3(.3,.5,0),end+Vector3(0,1,0)],.055)
		"sita":
			for i in range(4):
				var a := TAU*i/4
				var at := Vector3(sin(a),0,cos(a))*radius*.62
				var right := Vector3(cos(a),0,-sin(a))
				var path: Array = []
				for j in range(17):
					var t := j/16.0
					path.append(at+right*lerpf(-1.4,1.4,t)+Vector3.UP*(.15+sin(t*PI)*3.5))
				_tube(main,path,.075,5)
				_leaf(detail,at+Vector3.UP*2.75,Vector3.UP,.6,.2)
				for sign_ in [-1,1]:_leaf(detail,at+right*sign_+Vector3.UP*2.2,right*sign_+Vector3.UP,.8,.25)
		"draupadi":
			for i in range(5):
				var a := TAU*i/5
				var at := Vector3(sin(a),0,cos(a))*3.7
				_tube(detail,[at,at+Vector3.UP*3.5],.035)
				var side := Vector3(cos(a),0,-sin(a))*.65
				_tri(main,at+Vector3.UP*3.4,at+side+Vector3.UP*3.25,at+Vector3.UP*1.2)
				_tri(main,at+side+Vector3.UP*3.25,at+side*.8+Vector3.UP*1.3,at+Vector3.UP*1.2)
				_tube(detail,[at,Vector3(0,.06,0)],.025)
		"subhadra","hidimbi":
			var inverse := transform_.affine_inverse()
			for place in g.placements:
				var at: Vector3 = inverse*place
				if hero == "subhadra":
					_tube(main,[at,at+Vector3.UP*2.5,at+Vector3(.8,2.5,0),at+Vector3(.8,1.7,0)],.06,5)
					_tri(detail,at+Vector3(0,2.4,0),at+Vector3(.7,2.4,0),at+Vector3(.7,1.8,0))
					for sign_ in [-1,1]:_tube(detail,_vertical_arc(.3,0,TAU,at+Vector3(sign_*.5,.4,0)),.045)
				else:
					_tube(main,[at+Vector3(-.6,.1,0),at+Vector3(-.3,.8,0),at+Vector3(0,2.7,0),at+Vector3(.7,3.1,0)],.08,5)
					_tube(main,[at+Vector3(0,1.4,0),at+Vector3(-.8,2.2,0)],.06,5)
					for sign_ in [-1,1]:_leaf(detail,at+Vector3(sign_*.6,2.4,.1),Vector3(sign_,.4,0),1.2,.4)
		"chitrangada":
			for i in range(6):
				var a := TAU*i/6
				var path: Array = []
				for p in _vertical_arc(1.3,-1.2,1.2,Vector3.ZERO):path.append(Basis(Vector3.UP,a)*p+Vector3(sin(a)*2,1,cos(a)*2))
				_tube(main,path,.09,5)
				_leaf(detail,Vector3(sin(a)*2,2,cos(a)*2),Vector3.UP,.7,.17)
		"ulupi":
			for k in range(2):
				var path: Array = []
				for i in range(65):
					var a := TAU*i/64+k*PI
					path.append(Vector3(sin(a)*(radius*.78+sin(a*3+k)*.15),.6+sin(a*3+k)*.35,cos(a)*(radius*.78+sin(a*3+k)*.15)))
				_tube(main,path,.10,6)
				var head: Vector3 = path[0]
				_leaf(detail,head+Vector3.UP*.1,-head+Vector3.UP*.5,1.05,.3)
	return [main,detail]

func _vertical_arc(radius: float, start: float, stop: float, at: Vector3) -> Array:
	var result: Array = []
	for i in range(33):
		var a := lerpf(start,stop,i/32.0)
		result.append(at+Vector3(sin(a)*radius,cos(a)*radius,0))
	return result

func _refresh_attachments(cast: Dictionary) -> void:
	var vertices: Array = []
	var inverse: Transform3D = cast.transform.affine_inverse()
	for a in cast.attachments:
		if a.remaining_s <= 0 or (a.kind == "shield" and a.shield <= 0):continue
		var at: Vector3 = inverse*a.position
		if a.kind == "shield":
			var path := _arc(.65,-1.3,1.3,0,8)
			for i in range(path.size()):path[i] += at+Vector3.UP*1.1
			_tube(vertices,path,.045,4)
		else:
			_tube(vertices,[at+Vector3.UP*1.5,at+Vector3.UP*2.8],.035,4)
			if cast.hero == "subhadra":
				var h := clampf(a.remaining_s/9.0,0,1)*.8
				_tri(vertices,at+Vector3(0,2.7,0),at+Vector3(.55,2.7,0),at+Vector3(.55,2.7-h,0))
			else:
				_leaf(vertices,at+Vector3.UP*2.5,Vector3.RIGHT,1.2,.25)
	cast.attachment_node.mesh = _mesh(vertices)
	cast.attachment_node.set_meta("triangles",vertices.size()/3)

func _animate(cast: Dictionary) -> void:
	var windup: float = cast.timing.windup_s
	var preparation := clampf(cast.age/maxf(windup,.001),0,1)
	var elapsed_after := maxf(0,cast.age-windup-float(cast.timing.travel_s))
	var fade := clampf((cast.lifetime-cast.age)/maxf(float(cast.timing.recovery_s),.1),0,1)
	cast.warning.visible = not cast.impacted
	if cast.geometry.kind == "projectile_volley":cast.warning.visible = not cast.released
	if cast.geometry.kind == "zone_disk":cast.warning.visible = cast.age < windup+float(cast.timing.travel_s)+float(cast.timing.active_s)
	cast.warning_material.albedo_color.a = .78
	cast.main_material.albedo_color.a = (.30 if _reduced_effects else .52)*fade
	cast.detail_material.albedo_color.a = .40*fade
	for i in range(cast.ornaments.size()):
		var node: MeshInstance3D = cast.ornaments[i]
		node.visible = not (_reduced_effects and i == 1)
		node.position = Vector3.ZERO
		node.rotation = Vector3.ZERO
		node.scale = Vector3.ONE
		var growth := .35+.65*preparation
		node.scale.y = growth
		if cast.hero in ["subhadra","hidimbi"] and cast.impacted:node.visible = false
		if _reduced_motion:continue
		match cast.hero:
			"ravana":node.rotation.y = -.2*(1-preparation)+minf(elapsed_after,.5)*.35
			"karna":node.rotation.y = .6*preparation+minf(elapsed_after,.6)*1.4
			"bhima":node.position.y = sin(preparation*PI)*.45 if not cast.impacted else .08*exp(-elapsed_after*5)
			"hanuman":node.position.y = 2.2*(1-clampf((cast.age-windup)/maxf(float(cast.timing.travel_s),.01),0,1)) if cast.released else .3
			"ulupi":node.rotation.y = cast.age*.16 if i == 0 else 0.0
			"meghnad":node.scale.z = .25+.75*preparation
			"chitrangada":node.rotation.y = .4*sin(minf(elapsed_after,.6)/.6*PI)
			"arjuna":node.scale.x = maxf(.03,1-elapsed_after*3) if cast.released else growth
	for i in range(cast.arrows.size()):
		var arrow: MeshInstance3D = cast.arrows[i]
		var spec: Dictionary = cast.geometry.projectiles[i]
		arrow.visible = cast.released and not cast.contacts.has(spec.index)
		var travelled := minf(cast.geometry.range_m,maxf(0,cast.age-windup)*float(cast.geometry.speed_mps))
		var at: Vector3 = spec.origin+spec.forward*travelled+Vector3.UP*1.0
		arrow.transform = cast.transform.affine_inverse()*Transform3D(_basis(spec.forward),at)

func report() -> Dictionary:
	var states: Array = []
	var nodes := 0
	var triangles := 0
	var finite := true
	for id in _casts:
		var cast: Dictionary = _casts[id]
		var meshes := 0
		var cast_triangles := 0
		for child in cast.root.get_children():
			nodes += 1
			finite = finite and child.transform.is_finite()
			if child is MeshInstance3D:
				meshes += 1
				cast_triangles += int(child.get_meta("triangles",0))
		nodes += 1
		triangles += cast_triangles
		states.append({"cast_id":id,"hero_id":cast.hero,"phase":cast.phase,"age":cast.age,"geometry":cast.geometry.duplicate(true),"warning_vertices":cast.boundary_vertices.duplicate(),"warning_visible":cast.warning.visible,"warning_transform":cast.transform,"instances":meshes,"draw_calls_upper_bound":meshes,"triangles":cast_triangles,"attachments":cast.attachments.duplicate(true),"receipt_ids":cast.receipt_ids.duplicate(),"live_projectiles":cast.arrows.filter(func(a):return a.visible).size()})
	return {"active":_casts.size(),"peak_active":_peak_casts,"epoch":_epoch,"elapsed":_elapsed,"suspended":_suspended,"reduced_effects":_reduced_effects,"reduced_motion":_reduced_motion,"nodes":nodes,"triangles":triangles,"particles":0,"lights":0,"voices":0,"finite":finite,"counts":_counts.duplicate(),"casts":states,"scope":"Original local invocation presentation only; no authority, hero models or online claim."}
