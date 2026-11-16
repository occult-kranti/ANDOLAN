extends SceneTree
const Contracts = preload("res://scripts/native_contracts.gd")
func _initialize() -> void:
 var guard = Contracts.new()
 assert(guard.load_catalog().ok)
 var value: Dictionary = guard.descriptor("native-offline-triad")
 assert(value.versions.content == 9)
 var target := "res://tests/fixtures/contracts/native-content9-descriptor.json"
 assert(not FileAccess.file_exists(target))
 var stream := FileAccess.open(target, FileAccess.WRITE)
 stream.store_string(JSON.stringify(value, "\t", true) + "\n")
 stream.close()
 print(JSON.stringify({"descriptor":value,"validator_sha256":FileAccess.get_sha256("res://scripts/native_contracts.gd"),"catalog_sha256":FileAccess.get_sha256(Contracts.CATALOG_PATH),"descriptor_sha256":FileAccess.get_sha256(target),"engine":Engine.get_version_info()}))
 quit(0)
