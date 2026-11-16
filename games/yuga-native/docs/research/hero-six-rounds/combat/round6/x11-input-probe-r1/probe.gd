extends SceneTree
class Listener extends Node:
	var last_fire := false
	func _input(event: InputEvent) -> void:
		if event is InputEventMouseButton:
			print("INPUT_AUDIT ", JSON.stringify({"kind":"mouse_button","index":event.button_index,"pressed":event.pressed,"mask":event.button_mask,"event_fire":event.is_action("fire"),"fire":Input.is_action_pressed("fire"),"ticks_ms":Time.get_ticks_msec()}))
	func _physics_process(_delta: float) -> void:
		var value:=Input.is_action_pressed("fire")
		if value != last_fire:
			print("INPUT_AUDIT ",JSON.stringify({"kind":"fire_edge","fire":value,"mouse_mask":Input.get_mouse_button_mask(),"ticks_ms":Time.get_ticks_msec()}))
			last_fire=value
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	if not InputMap.has_action("fire"): InputMap.add_action("fire")
	InputMap.action_erase_events("fire")
	var mouse:=InputEventMouseButton.new()
	mouse.button_index=MOUSE_BUTTON_LEFT
	InputMap.action_add_event("fire",mouse)
	root.add_child(Listener.new())
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	print("INPUT_AUDIT ",JSON.stringify({"kind":"ready","left":MOUSE_BUTTON_LEFT,"right":MOUSE_BUTTON_RIGHT,"engine":Engine.get_version_info()}))
