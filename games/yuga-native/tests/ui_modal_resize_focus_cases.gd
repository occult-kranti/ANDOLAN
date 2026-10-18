extends SceneTree
## Engine-dispatched modal controls and bounded resize races; actual pixels separate.
const Controls = preload("res://scripts/controls_overlay.gd")
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""
var opener: Button
var host: Control
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func frames(count := 6) -> void:
	for unused in count: await process_frame
func press(key: int, shift := false) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=key;event.physical_keycode=key;event.shift_pressed=shift;event.pressed=down
		root.push_input(event)
		await process_frame
func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)
func inside(control: Control) -> bool:
	if not control.is_visible_in_tree() or not root.get_visible_rect().encloses(control.get_global_rect()): return false
	var parent := control.get_parent()
	while parent:
		if parent is Control and (parent is ScrollContainer or parent.clip_contents) and not parent.get_global_rect().encloses(control.get_global_rect()): return false
		parent=parent.get_parent()
	return true
func open_modal(modal: Control, kind: String) -> void:
	if kind=="guide": modal.open("courtyard",opener)
	else: modal.open()
func exercise(kind: String) -> void:
	root.content_scale_factor=1.0
	var modal: Control = Controls.new() if kind=="controls" else Guide.new()
	host.add_child(modal)
	if kind=="controls": modal.closed.connect(func():opener.grab_focus())
	open_modal(modal,kind)
	await frames()
	for unused in (4 if kind=="controls" else 2): await press(KEY_TAB,true)
	await press(KEY_ENTER)
	await frames()
	var target: Control = modal.binding_buttons.guardian_circle if kind=="controls" else modal.ability_buttons.dawn_volley
	var scroll: ScrollContainer = modal.card.find_child("MappingsScroll",true,false) if kind=="controls" else modal.abilities_scroll
	check(kind+" native keyboard route establishes final control and state",root.gui_get_focus_owner()==target and (modal.capture_action=="guardian_circle" if kind=="controls" else modal.selected_id=="dawn_volley"))
	check(kind+" selected control initially inside all clips at100",inside(target))
	var original := Bindings.current()
	root.content_scale_factor=2.0
	await frames(10)
	check(kind+" unchanged focus is revealed after200 layout",inside(target) and root.gui_get_focus_owner()==target,{"target":str(target.get_global_rect()),"clip":str(scroll.get_global_rect()),"scroll":scroll.scroll_vertical})
	check(kind+" resize preserves capture or selection and binding authority",Bindings.current()==original and (modal.capture_action=="guardian_circle" if kind=="controls" else modal.selected_id=="dawn_volley"))
	if kind=="controls":
		await press(KEY_ESCAPE)
		check("controls first Escape cancels capture without closing",modal.visible and modal.capture_action.is_empty() and root.gui_get_focus_owner()==target and Bindings.current()==original)
	await press(KEY_ESCAPE)
	check(kind+" close returns to opener after resize",not modal.visible and root.gui_get_focus_owner()==opener and Bindings.current()==original)
	open_modal(modal,kind)
	await frames()
	target.grab_focus()
	await frames()
	scroll.scroll_vertical=0
	await frames()
	check(kind+" later intentional scroll is not repeatedly overridden",scroll.scroll_vertical==0 and root.gui_get_focus_owner()==target)
	root.content_scale_factor=1.0
	await frames()
	root.content_scale_factor=2.0
	modal._layout()
	opener.grab_focus()
	var before_scroll: int=scroll.scroll_vertical
	await frames()
	check(kind+" pending resize does not scroll or steal focus after focus moves elsewhere",root.gui_get_focus_owner()==opener and scroll.scroll_vertical==before_scroll)
	root.content_scale_factor=1.0
	await frames()
	target.grab_focus()
	await frames()
	root.content_scale_factor=2.0
	modal._layout()
	modal.hide()
	opener.grab_focus()
	await frames()
	check(kind+" hidden pending modal cannot steal focus",not modal.is_visible_in_tree() and root.gui_get_focus_owner()==opener)
	root.content_scale_factor=1.0
	open_modal(modal,kind)
	await frames()
	target.grab_focus()
	await frames()
	root.content_scale_factor=2.0
	modal._layout()
	host.process_mode=Node.PROCESS_MODE_DISABLED
	opener.grab_focus()
	await frames()
	check(kind+" disabled owner rejects pending work",root.gui_get_focus_owner()==opener)
	host.process_mode=Node.PROCESS_MODE_ALWAYS
	root.content_scale_factor=1.0
	await frames()
	target.grab_focus()
	await frames()
	root.content_scale_factor=2.0
	modal._layout()
	target.queue_free()
	opener.grab_focus()
	await frames()
	check(kind+" freed focused peer is safe across deferred frames",not is_instance_valid(target) and root.gui_get_focus_owner()==opener)
	root.content_scale_factor=1.0
	await frames()
	var first: Control = modal.binding_buttons.move_forward if kind=="controls" else modal.ability_buttons.kodanda
	first.grab_focus()
	root.content_scale_factor=2.0
	modal._layout()
	modal.queue_free()
	opener.grab_focus()
	await frames()
	check(kind+" freed modal is safe across deferred frames",not is_instance_valid(modal) and root.gui_get_focus_owner()==opener)
func run() -> void:
	root.size=Vector2i(960,540)
	root.content_scale_size=Vector2i(1280,720)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	Bindings.install("user://modal-resize-focus.cfg")
	host=Control.new();host.process_mode=Node.PROCESS_MODE_ALWAYS;root.add_child(host)
	opener=Button.new();opener.text="Host opener";root.add_child(opener)
	await exercise("controls")
	await exercise("guide")
	host.queue_free();opener.queue_free()
	await frames()
	var passed := checks.all(func(row: Dictionary):return row.passed)
	var result := {"passed":passed,"count":checks.size(),"checks":checks,"scope":"Viewport-dispatched native keys and actual100→200 canvas layouts, modal eligibility/lifetime adversaries. No OS-window or pixel acceptance.","sources":{}}
	for path in ["res://scripts/controls_overlay.gd","res://scripts/rama_hero_panel.gd","res://scripts/ui_scroll_focus.gd",get_script().resource_path]:
		if FileAccess.file_exists(path):result.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty():FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if passed else 1)
