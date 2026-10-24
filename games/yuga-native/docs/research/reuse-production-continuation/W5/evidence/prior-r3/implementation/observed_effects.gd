extends "res://scripts/rama_ability_effects.gd"
## Offline instrumentation only. Return and state come from the real receiver.
var observer := Callable()
func consume_event(event: Dictionary) -> bool:
	var before := report()
	var accepted := super.consume_event(event)
	if observer.is_valid(): observer.call(event, accepted, before, report())
	return accepted
