extends SceneTree
## Real bundled resources, decoded-image equivalence and collision preservation.
## No rendered-art, VRAM, performance or package-size claim.
const Palette = preload("res://scripts/lanka_texture_palette.gd")
const Gate = preload("res://scripts/lanka_lane_gate.gd")
const Garden = preload("res://scripts/lanka_water_garden.gd")
var checks: Array[Dictionary] = []
var unrun: Array[String] = []
var report_path := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": passed, "detail": detail})
	print("PASS " if passed else "FAIL ", label)

func digest(value: Variant) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	hash.update(var_to_bytes(value))
	return hash.finish().hex_encode()

func texture_state(texture: Texture2D) -> Dictionary:
	var image := texture.get_image()
	return {"width": image.get_width(), "height": image.get_height(), "format": image.get_format(),
		"mips": image.get_mipmap_count(), "has_mips": image.has_mipmaps(), "pixels": digest(image.get_data()), "bytes": image.get_data_size()}

func material_state(material: Material) -> Dictionary:
	var state := {}
	for property in material.get_property_list():
		var key: String = property.name
		if not (property.usage & PROPERTY_USAGE_STORAGE) or key in ["resource_name", "resource_path", "resource_local_to_scene"]: continue
		var value: Variant = material.get(key)
		state[key] = texture_state(value) if value is Texture2D else value
	return state

func visuals(node: Node3D) -> Dictionary:
	var state := {}
	for visual in node.find_children("*", "MeshInstance3D", true, false):
		var surfaces: Array = []
		for index in visual.mesh.get_surface_count():
			surfaces.append({"geometry": digest(visual.mesh.surface_get_arrays(index)), "material": material_state(visual.mesh.surface_get_material(index))})
		state[String(node.get_path_to(visual))] = {"transform": visual.transform, "aabb": visual.mesh.get_aabb(), "surfaces": surfaces}
	return state

func texture_inventory(nodes: Array) -> Dictionary:
	var resources := {}
	var contents := {}
	var bytes := 0
	for node in nodes:
		for visual in node.find_children("*", "MeshInstance3D", true, false):
			for index in visual.mesh.get_surface_count():
				var material := visual.mesh.surface_get_material(index) as StandardMaterial3D
				for channel: StringName in Palette.CHANNELS:
					var texture := material.get(channel) as Texture2D
					if texture == null: continue
					var state := texture_state(texture)
					var key := digest(state)
					contents[key] = state
					if not resources.has(texture.get_instance_id()): bytes += int(state.bytes)
					resources[texture.get_instance_id()] = key
	return {"resources": resources, "contents": contents, "decoded_bytes": bytes}

func collisions(node: Node3D) -> Dictionary:
	var state := {}
	for body in node.find_children("*", "StaticBody3D", true, false):
		for holder in body.get_children():
			if holder is CollisionShape3D:
				state[String(node.get_path_to(holder))] = {"body_transform": body.transform, "shape_transform": holder.transform,
					"layer": body.collision_layer, "mask": body.collision_mask, "faces": digest(holder.shape.get_faces()), "backface": holder.shape.backface_collision}
	return state

func texture_weakrefs(node: Node3D) -> Dictionary:
	var references := {}
	for visual in node.find_children("*", "MeshInstance3D", true, false):
		for index in visual.mesh.get_surface_count():
			var material := visual.mesh.surface_get_material(index) as StandardMaterial3D
			for channel: StringName in Palette.CHANNELS:
				var texture := material.get(channel) as Texture2D
				if texture != null: references[texture.get_instance_id()] = weakref(texture)
	return references

func render_resource_ids(node: Node3D) -> Dictionary:
	var ids := {}
	for visual in node.find_children("*", "MeshInstance3D", true, false):
		var materials: Array = []
		for index in visual.mesh.get_surface_count(): materials.append(visual.mesh.surface_get_material(index).get_instance_id())
		ids[String(node.get_path_to(visual))] = {"mesh": visual.mesh.get_instance_id(), "materials": materials}
	return ids

func synthetic_node(material: StandardMaterial3D) -> Node3D:
	var node := Node3D.new()
	var visual := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.material = material
	visual.mesh = mesh
	node.add_child(visual)
	return node

func run() -> void:
	if not report_path.is_absolute_path() or FileAccess.file_exists(report_path):
		push_error("fresh absolute --report required"); quit(1); return
	var immutable := {Gate.ASSET: FileAccess.get_sha256(Gate.ASSET), Garden.ASSET: FileAccess.get_sha256(Garden.ASSET),
		"res://assets/world/confluence-map.json": FileAccess.get_sha256("res://assets/world/confluence-map.json")}
	var gate_source: Node3D = ResourceLoader.load(Gate.ASSET, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE).instantiate()
	var garden_source: Node3D = ResourceLoader.load(Garden.ASSET, "PackedScene", ResourceLoader.CACHE_MODE_IGNORE).instantiate()
	var before_gate := visuals(gate_source)
	var before_garden := visuals(garden_source)
	var before_collision := collisions(garden_source)
	var before := texture_inventory([gate_source, garden_source])
	check("two bundled caches start with24distinct resources and12equal image contents", before.resources.size() == 24 and before.contents.size() == 12, {"resources": before.resources.size(), "contents": before.contents.size()})
	var cached_garden: Node3D = ResourceLoader.load(Garden.ASSET, "PackedScene", ResourceLoader.CACHE_MODE_REUSE).instantiate()
	var duplicate_refs := texture_weakrefs(cached_garden)
	var first := Node3D.new()
	var second := Node3D.new()
	root.add_child(first)
	root.add_child(second)
	var gate := Gate.build(first)
	var garden := Garden.build(first, true)
	check("both verified production adapters mount", gate.get("enabled", false) and garden.get("enabled", false))
	if not gate.get("enabled", false) or not garden.get("enabled", false): quit(1); return
	var after := texture_inventory([gate.root, garden.root])
	check("gate and garden now reference12actual shared Texture2D resources", after.resources.size() == 12 and after.contents == before.contents, {"resources": after.resources.size(), "contents": after.contents.size()})
	var released := 0
	for reference: WeakRef in duplicate_refs.values():
		if reference.get_ref() == null: released += 1
	check("all12replaced embedded garden textures are actually released", released == 12, {"released": released, "observed_original_textures": duplicate_refs.size()})
	check("exact decoded-resource census removes9437184duplicate bytes", before.decoded_bytes - after.decoded_bytes == 9437184, {"before": before.decoded_bytes, "after": after.decoded_bytes, "delta": before.decoded_bytes - after.decoded_bytes})
	check("all geometry transforms and every stored material channel/setting are identical", visuals(gate.root) == before_gate and visuals(garden.root) == before_garden)
	check("garden collision faces transforms and masks are unchanged", collisions(garden.root) == before_collision)
	check("gate collider retains exact source face metadata", gate.shape.get_faces() == gate.root.get_meta("source_collision_faces") and gate.shape.backface_collision and gate.body.collision_layer == 1 and gate.body.collision_mask == 0)
	var gate_again := Gate.build(second)
	var garden_again := Garden.build(second, true)
	var repeated := texture_inventory([gate.root, garden.root, gate_again.root, garden_again.root])
	check("multiple cached instances retain12textures and exact presentation", repeated.resources.size() == 12 and visuals(gate_again.root) == before_gate and visuals(garden_again.root) == before_garden)
	check("each scene cache retains its original shared mesh and material identities across instances", render_resource_ids(gate.root) == render_resource_ids(gate_again.root) and render_resource_ids(garden.root) == render_resource_ids(garden_again.root))
	check("repeated gate keeps collider state private", gate.shape != gate_again.shape and gate.body != gate_again.body and gate.shape.get_faces() == gate_again.shape.get_faces())
	check("pooling is idempotent", Palette.share(gate.root).replaced == 0 and Palette.share(garden.root).replaced == 0 and Palette.cache_report().images == 12)
	Gate.clear_cache()
	var third := Node3D.new()
	root.add_child(third)
	var reloaded_gate := Gate.build(third)
	check("clearing and reloading gate cache preserves canonical12textures and surviving peers", reloaded_gate.enabled and texture_inventory([gate.root, garden.root, reloaded_gate.root]).resources.size() == 12 and visuals(gate.root) == before_gate and visuals(reloaded_gate.root) == before_gate and collisions(garden.root) == before_collision)
	var raw_manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var gate_manifest := Gate.prepare_army_manifest(raw_manifest, gate.root)
	var garden_manifest := Garden.prepare_army_manifest(gate_manifest.manifest, garden.root)
	check("source-derived10gate and4garden footprints remain exact copies", gate_manifest.ok and garden_manifest.ok and gate_manifest.boxes.size() == 10 and garden_manifest.boxes.size() == 4 and raw_manifest.traversal.native_collision_boxes.size() == 8)
	# Adverse source types and empty images retain the old material semantics.
	var material := StandardMaterial3D.new()
	var empty := ImageTexture.new()
	var gradient := GradientTexture2D.new()
	material.normal_texture = empty
	material.roughness_texture = gradient
	material.albedo_color = Color(.2, .3, .4, .5)
	material.roughness = .77
	var original_roughness := material.roughness
	var original_color := material.albedo_color
	var synthetic := synthetic_node(material)
	var skipped := Palette.share(synthetic)
	check("null empty and non-image textures are preserved without replacement", material.albedo_texture == null and material.normal_texture == empty and material.roughness_texture == gradient and skipped.replaced == 0 and skipped.skipped == 2 and material.roughness == original_roughness and material.albedo_color == original_color, skipped)
	check("null scene is a no-op", Palette.share(null) == {"eligible": 0, "replaced": 0, "skipped": 0})
	var image := Image.create(2, 2, false, Image.FORMAT_RGBA8)
	image.fill(Color(.13, .27, .41, 1))
	var distinct := ImageTexture.create_from_image(image)
	material.albedo_texture = distinct
	Palette.share(synthetic)
	check("new exact pixel content never aliases an unrelated source image", material.albedo_texture == distinct and Palette.cache_report().images == 13)
	image.generate_mipmaps()
	var mipmapped := ImageTexture.create_from_image(image)
	material.metallic_texture = mipmapped
	Palette.share(synthetic)
	check("same base pixels with different mipmaps are separate resources", material.albedo_texture != material.metallic_texture and material.metallic_texture == mipmapped and Palette.cache_report().images == 14)
	var original_image := image.duplicate() as Image
	original_image.clear_mipmaps()
	var size_override := ImageTexture.create_from_image(original_image)
	size_override.set_size_override(Vector2i(4, 2))
	material.roughness_texture = size_override
	Palette.share(synthetic)
	check("same pixel data with different texture size override stays distinct", material.roughness_texture == size_override and material.roughness_texture != distinct)
	var changed_image := Image.create(2, 2, false, Image.FORMAT_RGBA8)
	changed_image.fill(Color(.9, .8, .7, 1))
	distinct.set_image(changed_image)
	var original_pixels := ImageTexture.create_from_image(original_image)
	material.normal_texture = original_pixels
	Palette.share(synthetic)
	if distinct.get_image().get_data() != changed_image.get_data():
		unrun.append("Headless dummy renderer did not expose ImageTexture pixel replacement; mutable-canonical guard needs a rendered backend. Source-cache textures are immutable.")
	else:
		check("externally mutated canonical image cannot replace original pixels under a stale key", material.albedo_texture == distinct and material.normal_texture == original_pixels and material.albedo_texture != material.normal_texture and material.normal_texture.get_image().get_data() == original_image.get_data())
	var assets_unchanged := true
	for path in immutable: assets_unchanged = assets_unchanged and FileAccess.get_sha256(path) == immutable[path]
	check("serialized assets map and accepted asset pins remain immutable", assets_unchanged and immutable[Gate.ASSET] == Gate.ASSET_SHA and immutable[Garden.ASSET] == Garden.ASSET_SHA)
	var passed := checks.all(func(row): return row.passed)
	var report := {"schema": 1, "passed": passed, "count": checks.size(), "checks": checks, "unrun": unrun,
		"before_texture_resources": before.resources.size(), "after_texture_resources": after.resources.size(),
		"before_decoded_bytes": before.decoded_bytes, "after_decoded_bytes": after.decoded_bytes,
		"decoded_resource_bytes_removed": before.decoded_bytes - after.decoded_bytes, "source_asset_sha256": immutable,
		"scope": "Real native source texture identity and exact pixel/material/geometry/collision equivalence only. No GPU allocation, frame-time, package-size or rendered visual acceptance.", "engine": Engine.get_version_info()}
	for path in ["res://scripts/lanka_texture_palette.gd", "res://scripts/lanka_lane_gate.gd", "res://scripts/lanka_water_garden.gd", get_script().resource_path]:
		if not report.has("source_sha256"): report.source_sha256 = {}
		report.source_sha256[path] = FileAccess.get_sha256(path)
	FileAccess.open(report_path, FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	synthetic.free()
	gate_source.free()
	garden_source.free()
	cached_garden.free()
	first.free()
	second.free()
	third.free()
	await process_frame
	quit(0 if passed else 1)
