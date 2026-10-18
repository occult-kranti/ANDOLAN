extends SceneTree
## Isolated native-control state board; no game scenes, meshes or imported models.
const UI = preload("res://scripts/hero_ui_theme.gd")
var output := ""
var controls := {}
var captured: Array[String] = []
var capturing := false
var elapsed := 0.0
var activations := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("build")

func build() -> void:
	root.title = "YUGA independent theme states"
	root.gui_embed_subwindows = true
	var host := Control.new()
	host.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	host.theme = UI.create()
	root.add_child(host)
	for index in 2:
		var prefix := "Light" if index==0 else "Dark"
		var x := float(index*640)
		var background := ColorRect.new()
		background.color = Color("f3f0e8") if index==0 else UI.DEEP
		background.position = Vector2(x,0)
		background.size = Vector2(640,720)
		background.mouse_filter = Control.MOUSE_FILTER_IGNORE
		host.add_child(background)
		var heading := UI.label(prefix+" background · native controls",20,UI.DEEP if index==0 else UI.CREAM)
		heading.position = Vector2(x+20,20)
		host.add_child(heading)
		for row in 4:
			var variant: StringName = [&"primary",&"secondary",&"utility",&"selected"][row]
			for disabled in [false,true]:
				var button := Button.new()
				button.name = prefix+String(variant).capitalize()+("Disabled" if disabled else "")
				button.text = "Disabled" if disabled else String(variant).capitalize()+" action"
				button.position = Vector2(x+(382 if disabled else 20),68+row*58)
				button.size = Vector2(216 if disabled else 350,48)
				button.disabled = disabled
				UI.button_variant(button,variant)
				host.add_child(button)
				controls[button.name] = button
				activations[button.name] = 0
				button.pressed.connect(func(): activations[button.name] += 1)
		var toggle := CheckButton.new()
		toggle.name = prefix+"Toggle"
		toggle.text = "Motion enabled" if index==0 else "Motion disabled"
		toggle.position = Vector2(x+20,312)
		toggle.size = Vector2(578,48)
		toggle.button_pressed = index==0
		host.add_child(toggle)
		controls[toggle.name] = toggle
		var option := OptionButton.new()
		option.name = prefix+"Option"
		option.position = Vector2(x+20,380)
		option.size = Vector2(578,48)
		option.layout_direction = Control.LAYOUT_DIRECTION_LTR if index==0 else Control.LAYOUT_DIRECTION_RTL
		option.add_item("Fullscreen · high contrast display")
		option.add_item("Windowed")
		option.add_item("Unavailable")
		option.set_item_disabled(2,true)
		host.add_child(option)
		controls[option.name] = option
		var slider := HSlider.new()
		slider.name = prefix+"Slider"
		slider.position = Vector2(x+20,454)
		slider.size = Vector2(578,44)
		slider.value = 50
		host.add_child(slider)
		controls[slider.name] = slider
		var disabled_slider := HSlider.new()
		disabled_slider.name = prefix+"DisabledSlider"
		disabled_slider.position = Vector2(x+20,518)
		disabled_slider.size = Vector2(578,44)
		disabled_slider.value = 50
		disabled_slider.editable = false
		host.add_child(disabled_slider)
		controls[disabled_slider.name] = disabled_slider
		var check := CheckButton.new()
		check.name = prefix+"DisabledToggle"
		check.text = "Unavailable option"
		check.position = Vector2(x+20,582)
		check.size = Vector2(578,48)
		check.disabled = true
		check.button_pressed = index==0
		host.add_child(check)
		controls[check.name] = check
		var scroll := VScrollBar.new()
		scroll.name = prefix+"Scroll"
		scroll.position = Vector2(x+610,68)
		scroll.size = Vector2(18,222)
		scroll.max_value = 100
		scroll.page = 20
		scroll.value = 35
		host.add_child(scroll)
		controls[scroll.name] = scroll
	controls.LightPrimary.grab_focus.call_deferred()

func snapshot() -> Dictionary:
	var result := {"frame":Engine.get_process_frames(),"size":[root.size.x,root.size.y],"controls":{},"focus":"","activations":activations.duplicate()}
	var focused := root.gui_get_focus_owner()
	if focused: result.focus = String(focused.name)
	for id in controls:
		var control: Control = controls[id]
		var r := control.get_global_rect()
		var row := {"rect":[r.position.x,r.position.y,r.size.x,r.size.y],"focus":control.has_focus()}
		if control is BaseButton:
			row.merge({"draw_mode":control.get_draw_mode(),"disabled":control.disabled,"pressed":control.button_pressed})
		if control is OptionButton: row.popup = control.get_popup().visible
		if control is Range: row.value = control.value
		result.controls[id] = row
	return result

func write(path: String, value: Dictionary) -> void:
	var file := FileAccess.open(path+".tmp",FileAccess.WRITE)
	file.store_string(JSON.stringify(value,"  ")+"\n")
	file.close()
	DirAccess.rename_absolute(path+".tmp",path)

func _process(delta: float) -> bool:
	if controls.is_empty(): return false
	elapsed += delta
	if elapsed<.08: return false
	elapsed = 0
	write(output+"/state.json",snapshot())
	var request_path := output+"/capture-request.json"
	if not capturing and FileAccess.file_exists(request_path):
		var request = JSON.parse_string(FileAccess.get_file_as_string(request_path))
		if request is Dictionary and request.get("name","") not in captured: capture(request.name)
	return false

func capture(id: String) -> void:
	capturing = true
	await RenderingServer.frame_post_draw
	var path := output+"/"+id+".png"
	var status := root.get_texture().get_image().save_png(path)
	var state := snapshot()
	state.merge({"png_status":status,"sha256":FileAccess.get_sha256(path),"file":id+".png"})
	write(output+"/"+id+".json",state)
	captured.append(id)
	capturing = false
