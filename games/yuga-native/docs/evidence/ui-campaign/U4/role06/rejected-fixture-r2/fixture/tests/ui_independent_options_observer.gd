extends "res://tests/ui_independent_base_observer.gd"
## Adds observations only; all product actions still come through XTest.
func snapshot() -> Dictionary:
	var state := super.snapshot()
	if current_scene and current_scene.has_method("independent_snapshot"):
		state.independent = current_scene.independent_snapshot()
	return state
