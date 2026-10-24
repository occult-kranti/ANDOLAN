extends "res://scripts/rama_action_audio.gd"
## Offline instrumentation only; inherited code retains all voice/timing guards.
var observer := Callable()
func consume_event(event: Variant) -> Dictionary:
	var before := report()
	var acknowledgement := super.consume_event(event)
	if observer.is_valid(): observer.call(event, acknowledgement, before, report())
	return acknowledgement
