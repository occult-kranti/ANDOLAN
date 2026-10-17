extends RefCounted
## Original raised courts and luminous tether relics. Eight solid decks are
## declared separately in the manifest; this builder adds no hidden collision.
const DeckShader = preload("res://scripts/traversal_stone.gdshader")

var materials: Dictionary = {}
var meshes := 0

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
	var shape := BoxMesh.new()
	shape.size=size_
	return _mesh(parent,shape,at,material,label_)

func build(parent: Node3D, data: Dictionary) -> Dictionary:
	var root := Node3D.new()
	root.name="TraversalRelics"
	parent.add_child(root)
	var shade := _material(Color("756f63"))
	var warm := _material(Color("d1ad68"))
	var cool := _material(Color("71adb3"))
	for entry in data.get("landmarks",[]):
		var node := Node3D.new()
		node.name=entry.id
		node.position=Vector3(entry.position[0],entry.position[1],entry.position[2])
		root.add_child(node)
		var size_ := Vector3(entry.size[0],entry.size[1],entry.size[2])
		var trim := warm if entry.team=="sun" else cool
		# All opaque architectural volume stays within the matching deck AABB.
		_box(node,Vector3(0,size_.y*.5,0),size_,_deck_material(size_),"SolidLandingDeck")
		for level in [0.18,size_.y*.45,size_.y-.18]:
			# Recessed trim faces prevent coplanar overlay/z-fighting.
			for side in [-1.0,1.0]:
				_box(node,Vector3(side*(size_.x*.5+.004),level,0),Vector3(.008,.12,size_.z-.2),trim,"CorniceFace")
				_box(node,Vector3(0,level,side*(size_.z*.5+.004)),Vector3(size_.x-.2,.12,.008),trim,"CorniceFace")
		# Shallow chhatri/lotus motifs are facade ornament, below the landing top.
		for side in [-1.0,1.0]:
			var arch := SphereMesh.new()
			arch.radius=.9
			arch.height=.9
			arch.is_hemisphere=true
			arch.radial_segments=12
			arch.rings=6
			var dome := _mesh(node,arch,Vector3(side*(size_.x*.5-.12),size_.y*.63,0),trim,"ChhatriRelief")
			dome.scale=Vector3(.16,1,1)
			for pillar in [-.65,.65]:
				_box(node,Vector3(side*(size_.x*.5+.006),size_.y*.49,pillar),Vector3(.012,size_.y*.25,.10),shade,"ReliefColumn")
		var disk := CylinderMesh.new()
		disk.top_radius=1.5
		disk.bottom_radius=1.5
		disk.height=.012
		disk.radial_segments=24
		_mesh(node,disk,Vector3(0,size_.y+.006,0),shade,"ClearLandingMedallion")
		for petal in range(6):
			var angle := float(petal)*TAU/6.0
			var lamp := SphereMesh.new()
			lamp.radius=.10
			lamp.height=.18
			lamp.radial_segments=8
			lamp.rings=4
			_mesh(node,lamp,Vector3(cos(angle)*1.8,size_.y+.10,sin(angle)*1.8),_material(Color("ecb45e"),1.4),"DiyaEmber")
	for anchor in data.get("anchors",[]):
		var position_ := Vector3(anchor.position[0],anchor.position[1],anchor.position[2])
		var ring := TorusMesh.new()
		ring.inner_radius=.70
		ring.outer_radius=.92
		ring.rings=24
		ring.ring_segments=6
		var halo := _mesh(root,ring,position_,_material(Color("e9c877"),1.1),anchor.id)
		halo.rotation.x=PI*.5
		halo.set_meta("grapple_anchor_id",anchor.id)
		for notch in [-1.0,1.0]:
			_box(root,position_+Vector3(notch*1.14,0,0),Vector3(.25,.12,.12),warm,"AnchorBracket")
	# Bounded original geometry; count reported for integrated stress/render review.
	return {"landmarks":data.get("landmarks",[]).size(),"anchors":data.get("anchors",[]).size(),"mesh_instances":meshes,"mesh_budget":300,"materials":materials.size(),"scope":"Original procedural stone decks, chhatri facade relief, lotus courts and luminous fictional traversal relics. No historical reconstruction."}
