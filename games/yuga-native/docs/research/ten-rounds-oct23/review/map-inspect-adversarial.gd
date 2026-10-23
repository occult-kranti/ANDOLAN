extends SceneTree
## Bounded field-type counterexamples for the callable pure known-source guard.
const Loader=preload("res://map_loader.gd")
var checks: Array=[]
func _initialize()->void:call_deferred("run")
func glb(document: Dictionary)->PackedByteArray:
	var json:=JSON.stringify(document).to_utf8_buffer()
	while json.size()%4:json.append(32)
	var bytes:=PackedByteArray();bytes.resize(28+json.size()+4)
	bytes.encode_u32(0,0x46546c67);bytes.encode_u32(4,2);bytes.encode_u32(8,bytes.size())
	bytes.encode_u32(12,json.size());bytes.encode_u32(16,0x4e4f534a)
	for i in json.size():bytes[20+i]=json[i]
	bytes.encode_u32(20+json.size(),4);bytes.encode_u32(24+json.size(),0x004e4942)
	return bytes
func run()->void:
	var source:={"asset":{"version":"2.0"},"buffers":[{"byteLength":4}]}
	var positive: Variant=Loader.inspect(glb(source))
	checks.append({"name":"minimal embedded static preflight reaches declared positive contract","passed":positive is Dictionary and positive.get("ok",false)==true,"result":positive})
	var mutations: Array=[
		["asset:null","asset",null],
		["asset:boolean","asset",false],
		["skins:null","skins",null],
		["skins:emptydictionary","skins",{}],
		["skins:emptystring","skins",""],
		["animations:null","animations",null],
		["animations:emptydictionary","animations",{}],
		["extensionsUsed:null","extensionsUsed",null],
		["extensionsUsed:dictionary","extensionsUsed",{"KHR_materials_emissive_strength":{}}],
		["required-only unsupported extension","extensionsRequired",["EXT_meshopt_compression"]]
	]
	for mutation in mutations:
		var candidate: Dictionary=source.duplicate(true);candidate[mutation[1]]=mutation[2]
		var result: Variant=Loader.inspect(glb(candidate))
		checks.append({"name":mutation[0],"passed":result is Dictionary and result.get("ok",true)==false and result.has("reason"),"result":result})
	var passed:=checks.all(func(row):return row.passed)
	var report:={"passed":passed,"cases":checks.size(),"checks":checks,"loader_sha256":FileAccess.get_sha256("res://map_loader.gd"),"scope":"Independent pure preflight field-type counterexamples only; no native parser, renderer or canonical integration. A structured rejection is required, not a Godot script error or untyped acceptance."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file:=FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file==null:quit(2);return
			file.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"cases":checks.size()}));quit(0 if passed else 1)
