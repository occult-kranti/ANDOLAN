extends RefCounted
## Original raised courts and luminous tether relics. Eight solid decks are
## declared separately in the manifest. The reviewed opt-in pilot owns explicit
## detailed collision; its caller must omit the replaced manifest box.
const DeckShader = preload("res://scripts/traversal_stone.gdshader")
const RenderResources = preload("res://scripts/world_render_resources.gd")

var materials: Dictionary = {}
var meshes := 0
var geometry = RenderResources.new()

# The pilot is deliberately opt-in. Its owner must replace the manifest's old
# full-box collider with the returned detailed boxes before using it in play.
const WIND_COURT_ID := "sun-lift-west"
const WIND_COURT_COLLISION_ID := "sun-lift-west-deck"
const WIND_COURT_SIZE := Vector3(8,8,8)

func wind_court_parts() -> Array[Dictionary]:
	# Metres in the existing eight-metre local envelope. Every bay is backed by
	# the solid core: these are engaged supports, never pretend open doorways.
	var parts: Array[Dictionary] = [
		{"name":"GroundedFoot","at":Vector3(0,.24,0),"size":Vector3(8,.48,8),"group":0,"solid":true},
		{"name":"UpperPlinth","at":Vector3(0,.815,0),"size":Vector3(7.66,.67,7.66),"group":0,"solid":true},
		{"name":"ClosedCore","at":Vector3(0,3.865,0),"size":Vector3(6.64,5.43,6.64),"group":0,"solid":true},
		{"name":"CrownBed","at":Vector3(0,6.755,0),"size":Vector3(7.08,.35,7.08),"group":0,"solid":true},
		{"name":"CrownStep","at":Vector3(0,7.165,0),"size":Vector3(7.52,.47,7.52),"group":0,"solid":true},
		{"name":"LandingCrown","at":Vector3(0,7.7,0),"size":Vector3(8,.6,8),"group":0,"solid":true},
		{"name":"PlinthShadow","at":Vector3(0,1.095,0),"size":Vector3(7.69,.11,7.69),"group":2,"solid":true},
		{"name":"CrownShadow","at":Vector3(0,6.605,0),"size":Vector3(7.1,.12,7.1),"group":2,"solid":true},
		{"name":"CrownWarmBand","at":Vector3(0,7.365,0),"size":Vector3(7.56,.07,7.56),"group":1,"solid":false},
	]
	for x in [-3.2,3.2]:
		for z in [-3.2,3.2]:
			parts.append({"name":"CornerPier","at":Vector3(x,3.9,z),"size":Vector3(1.24,5.5,1.24),"group":0,"solid":true})
	for side in [-1.0,1.0]:
		for along in [-2.05,0.0,2.05]:
			for axis in range(2):
				var at := Vector3(side*3.52,3.87,along) if axis==0 else Vector3(along,3.87,side*3.52)
				var size_ := Vector3(.64,5.44,.66) if axis==0 else Vector3(.66,5.44,.64)
				parts.append({"name":"EngagedPier","at":at,"size":size_,"group":0,"solid":true})
				var capital_at := Vector3(at.x,6.39,at.z)
				var capital_size := Vector3(.78,.28,.85) if axis==0 else Vector3(.85,.28,.78)
				parts.append({"name":"PierCapital","at":capital_at,"size":capital_size,"group":0,"solid":true})
				var collar_at := Vector3(at.x,1.34,at.z)
				var collar_size := Vector3(.71,.16,.77) if axis==0 else Vector3(.77,.16,.71)
				parts.append({"name":"PierWarmCollar","at":collar_at,"size":collar_size,"group":1,"solid":false,"near_only":true})
	return parts

func _wind_court_mesh(parts: Array[Dictionary], palette: Array[Material], near: bool) -> ArrayMesh:
	var result := ArrayMesh.new()
	for group in range(3):
		var surface := SurfaceTool.new()
		surface.begin(Mesh.PRIMITIVE_TRIANGLES)
		surface.set_material(palette[group])
		for part in parts:
			if int(part.group)!=group or (not near and part.get("near_only",false)): continue
			# Keep the existing shader's local origin at the old deck centre.
			var transform := Transform3D(Basis.IDENTITY,part.at-Vector3(0,4,0))
			surface.append_from(geometry.box(part.size),0,transform)
		surface.commit(result)
	return result

func _wind_court(node: Node3D, stone: Material, warm: Material, shade: Material, collision: bool) -> Dictionary:
	var parts := wind_court_parts()
	var palette: Array[Material] = [stone,warm,shade]
	var triangles := {}
	for detail in ["near","mid"]:
		var mesh := _wind_court_mesh(parts,palette,detail=="near")
		var visual := _mesh(node,mesh,Vector3(0,4,0),null,"WindCourt"+detail.capitalize())
		visual.visibility_range_end=38.0 if detail=="near" else 0.0
		visual.visibility_range_begin=0.0 if detail=="near" else 38.0
		visual.visibility_range_fade_mode=GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		var count := 0
		for index in range(mesh.get_surface_count()):
			count+=mesh.surface_get_array_index_len(index)/3
		triangles[detail]=count
	var shapes := 0
	if collision:
		var body := StaticBody3D.new()
		body.name="WindCourtDetailedCollision"
		body.collision_layer=1
		body.collision_mask=0
		body.set_meta("replaces_manifest_landmark",WIND_COURT_ID)
		body.set_meta("replaces_manifest_collision",WIND_COURT_COLLISION_ID)
		node.add_child(body)
		for part in parts:
			if not part.solid: continue
			var shape := CollisionShape3D.new()
			shape.name=part.name+str(shapes)
			var box := BoxShape3D.new()
			box.size=part.size
			shape.shape=box
			shape.position=part.at
			body.add_child(shape)
			shapes+=1
	node.set_meta("wind_court_pilot",true)
	return {"id":WIND_COURT_ID,"enabled":true,"replaces_manifest_collision":WIND_COURT_COLLISION_ID,"near_triangles":triangles.near,"mid_triangles":triangles.mid,"architecture_surfaces_per_lod":3,"collision_shapes":shapes,"envelope":WIND_COURT_SIZE,"landing_height":8.0,"replacement_requires_old_collider_removed":true,"roof_signals":"Existing medallion and six embers unchanged; outside merged opaque architecture count."}

func _deck_material(dimensions: Vector3) -> ShaderMaterial:
	var key := "deck:"+str(dimensions)
	if materials.has(key): return materials[key]
	var value := ShaderMaterial.new()
	value.shader=DeckShader
	value.set_shader_parameter("deck_height",dimensions.y)
	value.set_shader_parameter("deck_width",dimensions.x)
	materials[key]=value
	return value

func _material(color: Color, glow: float=0.0) -> StandardMaterial3D:
	var key := str(color)+":"+str(glow)
	if materials.has(key): return materials[key]
	var value := StandardMaterial3D.new()
	value.albedo_color=color
	value.roughness=.76
	value.emission_enabled=glow>0
	value.emission=color
	value.emission_energy_multiplier=glow
	materials[key]=value
	return value

func _mesh(parent: Node3D, shape: Mesh, at: Vector3, material: Material, label_: String) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name=label_
	node.mesh=shape
	node.position=at
	node.material_override=material
	parent.add_child(node)
	meshes+=1
	return node

func _box(parent: Node3D, at: Vector3, size_: Vector3, material: Material, label_: String) -> MeshInstance3D:
	var shape := geometry.box(size_)
	return _mesh(parent,shape,at,material,label_)

func build(parent: Node3D, data: Dictionary, options: Dictionary={}) -> Dictionary:
	# A reused builder must not couple mutable materials or retain old worlds.
	materials = {}
	meshes = 0
	geometry = RenderResources.new()
	var root := Node3D.new()
	root.name="TraversalRelics"
	parent.add_child(root)
	var shade := _material(Color("756f63"))
	var warm := _material(Color("d1ad68"))
	var cool := _material(Color("71adb3"))
	var pilot := {"enabled":false}
	for entry in data.get("landmarks",[]):
		var node := Node3D.new()
		node.name=entry.id
		node.position=Vector3(entry.position[0],entry.position[1],entry.position[2])
		root.add_child(node)
		var size_ := Vector3(entry.size[0],entry.size[1],entry.size[2])
		var trim := warm if entry.team=="sun" else cool
		# All opaque architectural volume stays within the matching deck AABB.
		var use_pilot: bool=options.get("wind_court_pilot",false) and entry.id==WIND_COURT_ID and size_==WIND_COURT_SIZE
		if use_pilot:
			pilot=_wind_court(node,_deck_material(size_),warm,shade,options.get("pilot_collision",true))
		else:
			_box(node,Vector3(0,size_.y*.5,0),size_,_deck_material(size_),"SolidLandingDeck")
		for level in ([] if use_pilot else [0.18,size_.y*.45,size_.y-.18]):
			# Recessed trim faces prevent coplanar overlay/z-fighting.
			for side in [-1.0,1.0]:
				_box(node,Vector3(side*(size_.x*.5+.004),level,0),Vector3(.008,.12,size_.z-.2),trim,"CorniceFace")
				_box(node,Vector3(0,level,side*(size_.z*.5+.004)),Vector3(size_.x-.2,.12,.008),trim,"CorniceFace")
		# Shallow chhatri/lotus motifs are facade ornament, below the landing top.
		for side in ([] if use_pilot else [-1.0,1.0]):
			var arch := geometry.sphere(.9,.9,12,6,true)
			var dome := _mesh(node,arch,Vector3(side*(size_.x*.5-.12),size_.y*.63,0),trim,"ChhatriRelief")
			dome.scale=Vector3(.16,1,1)
			for pillar in [-.65,.65]:
				_box(node,Vector3(side*(size_.x*.5+.006),size_.y*.49,pillar),Vector3(.012,size_.y*.25,.10),shade,"ReliefColumn")
		var disk := geometry.cylinder(1.5,1.5,.012,24)
		_mesh(node,disk,Vector3(0,size_.y+.006,0),shade,"ClearLandingMedallion")
		for petal in range(6):
			var angle := float(petal)*TAU/6.0
			var lamp := geometry.sphere(.10,.18,8,4)
			_mesh(node,lamp,Vector3(cos(angle)*1.8,size_.y+.10,sin(angle)*1.8),_material(Color("ecb45e"),1.4),"DiyaEmber")
	for anchor in data.get("anchors",[]):
		var position_ := Vector3(anchor.position[0],anchor.position[1],anchor.position[2])
		var ring := geometry.torus(.70,.92,24,6)
		var halo := _mesh(root,ring,position_,_material(Color("e9c877"),1.1),anchor.id)
		halo.rotation.x=PI*.5
		halo.set_meta("grapple_anchor_id",anchor.id)
		for notch in [-1.0,1.0]:
			_box(root,position_+Vector3(notch*1.14,0,0),Vector3(.25,.12,.12),warm,"AnchorBracket")
	# Bounded original geometry; count reported for integrated stress/render review.
	return {"landmarks":data.get("landmarks",[]).size(),"anchors":data.get("anchors",[]).size(),"mesh_instances":meshes,"mesh_budget":300,"materials":materials.size(),"wind_court_pilot":pilot,"scope":"Original procedural stone decks, chhatri facade relief, lotus courts and luminous fictional traversal relics. No historical reconstruction."}
