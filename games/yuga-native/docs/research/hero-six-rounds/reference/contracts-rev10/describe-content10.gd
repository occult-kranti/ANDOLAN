extends SceneTree
const Contracts = preload("res://scripts/native_contracts.gd")
func _initialize() -> void:
 var guard = Contracts.new()
 assert(guard.load_catalog().ok)
 var value: Dictionary = guard.descriptor("native-offline-triad")
 assert(value.versions.content == 10)
 var target := "res://docs/research/hero-six-rounds/reference/contracts-rev10/native-content10-descriptor.json"
 assert(not FileAccess.file_exists(target))
 var stream := FileAccess.open(target, FileAccess.WRITE)
 stream.store_string(JSON.stringify(value, "\t", true) + "\n")
 stream.close()
 print(JSON.stringify(value))
 quit(0)
