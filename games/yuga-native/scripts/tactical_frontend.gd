extends Control
const T = preload("res://scripts/tactical_theme.gd")
const Dossier = preload("res://scripts/tactical_hero_dossier.gd")
const Showcase = preload("res://scripts/tactical_hero_showcase.gd")
const WORLD := "res://scenes/tactical_world.tscn"
var page := "home"
var loading_path := ""
var load_status := ""
var body: VBoxContainer
var content_scroll: ScrollContainer
var status: Label
var progress: ProgressBar
var settings_controls := {}
var _settings := T.DEFAULTS.duplicate()
var _shell: MarginContainer
var _page_actions: HBoxContainer
var _navigation := {}
var _content_row: HBoxContainer
var _key_art: TextureRect
var hero_showcase: Control
var hero_dossier: VBoxContainer

func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	_settings=T.load_settings()
	_apply_settings()
	_build()
	show_page("home")

func _apply_settings() -> void:
	theme=T.create(_settings.ui_scale)
	T.rescale(self,_settings.ui_scale)
	AudioServer.set_bus_volume_db(0,linear_to_db(maxf(.0001,_settings.master_volume)))

func _build() -> void:
	var background := ColorRect.new();background.color=T.INK;background.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(background);background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var art_path := "res://assets/tactical/menu-keyart.png"
	if ResourceLoader.exists(art_path):
		var art := TextureRect.new();_key_art=art;art.texture=load(art_path);art.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;art.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_COVERED;art.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(art);art.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var gradient := Gradient.new();gradient.set_color(0,Color(.035,.055,.085,.98));gradient.set_color(1,Color(.035,.055,.085,.12));gradient.add_point(.55,Color(.035,.055,.085,.86))
	var texture := GradientTexture2D.new();texture.gradient=gradient;texture.fill_from=Vector2.ZERO;texture.fill_to=Vector2.RIGHT
	var veil := TextureRect.new();veil.texture=texture;veil.mouse_filter=Control.MOUSE_FILTER_IGNORE;add_child(veil);veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_shell=MarginContainer.new();add_child(_shell);_shell.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left","right","top","bottom"]:_shell.add_theme_constant_override("margin_"+side,40 if side in ["left","right"] else 24)
	var column := T.stack(16);_shell.add_child(column)
	var navigation := T.row(10);column.add_child(navigation)
	navigation.add_child(T.icon("crest",40));navigation.add_child(T.label("YUGA",28,T.IVORY,true))
	var space := Control.new();space.custom_minimum_size.x=24;navigation.add_child(space)
	for nav in [["home","Home"],["casual","Play"],["hero","Rama"],["settings","Settings"]]:
		var button := T.button(nav[1],func():show_page(nav[0]));button.name="Nav_"+nav[0];T.quiet(button);navigation.add_child(button);_navigation[nav[0]]=button
	_content_row=T.row(28);_content_row.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(_content_row)
	content_scroll=ScrollContainer.new();content_scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;content_scroll.size_flags_horizontal=Control.SIZE_SHRINK_BEGIN;content_scroll.follow_focus=true;content_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;_content_row.add_child(content_scroll)
	body=T.stack(18);body.size_flags_horizontal=Control.SIZE_EXPAND_FILL;content_scroll.add_child(body)
	_page_actions=T.row(12);column.add_child(_page_actions)
	var footer := T.row();footer.add_child(T.label("CASUAL  /  LOCAL 5V5",13,T.GOLD));var fill:=Control.new();fill.size_flags_horizontal=Control.SIZE_EXPAND_FILL;footer.add_child(fill)
	for control in [T.button("Controls",func():show_page("help")),T.button("Quit",func():get_tree().quit())]:T.quiet(control);footer.add_child(control)
	column.add_child(footer)
	resized.connect(_layout)
	_layout()

func _layout() -> void:
	if body==null:return
	body.custom_minimum_size.x=minf(480,maxf(340,size.x*.4)) if page=="hero" else minf(550,maxf(320,size.x-112))
	content_scroll.custom_minimum_size.x=body.custom_minimum_size.x+16
	body.size_flags_horizontal=Control.SIZE_SHRINK_BEGIN
	for child in body.get_children():
		if child is Button:
			child.size_flags_horizontal=Control.SIZE_SHRINK_BEGIN;child.custom_minimum_size.x=280
		elif child is Control:child.size_flags_horizontal=Control.SIZE_EXPAND_FILL

func _clear() -> void:
	if is_instance_valid(hero_showcase):_content_row.remove_child(hero_showcase);hero_showcase.queue_free();hero_showcase=null
	for node in body.get_children():body.remove_child(node);node.queue_free()
	content_scroll.scroll_vertical=0
	settings_controls.clear();hero_dossier=null
	for node in _page_actions.get_children():_page_actions.remove_child(node);node.queue_free()
	_page_actions.hide()
	status=null;progress=null

func show_page(next: String) -> void:
	if not loading_path.is_empty():return
	page=next
	if is_instance_valid(_key_art):_key_art.visible=page!="hero"
	_clear()
	body.add_theme_constant_override("separation",14)
	for id in _navigation:T.quiet(_navigation[id],id==page)
	match page:
		"home":
			body.add_child(T.label("Mythic\nprecision.",52,T.IVORY,true))
			body.add_child(T.prose("Five on each side. First to thirteen.\nOne life to change the round.",20))
			body.add_child(T.prose("Enter Sangam as Rama. Master mythic firearms and utility. Attune the Astra; hold the line.",16))
			body.add_child(T.button("PLAY CASUAL",func():show_page("casual"),true))
			var meet:=T.button("Rama / abilities",func():show_page("hero"));T.quiet(meet);body.add_child(meet)
			body.add_child(T.label("Local match with allied and opposing bots.",14,T.MUTED))
		"casual":
			body.add_child(T.label("Casual",44,T.IVORY,true))
			body.add_child(T.prose("5 versus 5  ·  First to 13  ·  Sangam",22,T.GOLD))
			body.add_child(T.prose("Attackers hold F at A or B to attune the Astra. Defenders stop the attunement or hold F to sever it. An attuned Astra stays active after the attackers fall."))
			body.add_child(T.prose("Buy before each round. One life per round. Teams switch sides after round 12. Casual ends at 13; there is no overtime."))
			body.add_child(T.button("DEPLOY AS RAMA",func():begin_loading(WORLD),true))
			var ranked := T.button("Ranked — planned",func():pass);ranked.disabled=true;body.add_child(ranked)
			body.add_child(T.prose("Local match with bots. Online matchmaking and ranks are planned.",14))
		"hero":
			body.add_theme_constant_override("separation",10)
			body.add_child(T.label("Rama",40,T.IVORY,true));body.add_child(T.prose("Ability & loadout studio",16,T.GOLD))
			hero_showcase=Showcase.new();_content_row.add_child(hero_showcase)
			hero_dossier=Dossier.new();body.add_child(hero_dossier);hero_dossier.configure(hero_showcase,_settings)
			_page_actions.add_child(T.button("Choose Casual",func():show_page("casual"),true));_page_actions.show()
		"settings":
			body.add_theme_constant_override("separation",8)
			body.add_child(T.label("Settings",36,T.IVORY,true));settings_controls=T.settings_form(body,_settings)
			status=T.prose("Changes apply when you save.",14);body.add_child(status)
			_page_actions.add_child(T.button("Save settings",_save_settings,true));_page_actions.add_child(T.button("Discard & return",func():show_page("home")));_page_actions.show()
		"help":
			body.add_child(T.label("Make every round count.",36,T.IVORY,true))
			for text_ in ["WASD move · Shift walk · Space jump", "Mouse aim · LMB fire · RMB aim down sights", "R reload · Q / E / C utility · X ultimate", "F hold to attune or sever at a site", "B buy in your spawn during preparation", "Hold Tab scoreboard · F1 kit guide · Escape pause"]:body.add_child(T.prose(text_,17,T.IVORY))
			body.add_child(T.button("Back to Casual",func():show_page("casual"),true))
	_layout()
	var buttons := body.find_children("*","Button",true,false)
	if page=="settings":settings_controls.sensitivity.grab_focus()
	elif not buttons.is_empty():buttons[0].grab_focus()
	elif _page_actions.get_child_count()>0:_page_actions.get_child(0).grab_focus()

static func _add_abilities(parent: VBoxContainer, compact: bool = false) -> void:
	for ability in T.ABILITIES:
		var line := T.row(16);parent.add_child(line);line.add_child(T.icon(ability.id,32 if compact else 42))
		var copy := T.stack(4);copy.size_flags_horizontal=Control.SIZE_EXPAND_FILL;line.add_child(copy)
		copy.add_child(T.label(ability.key+"  /  "+ability.name,17 if compact else 19,T.GOLD));copy.add_child(T.prose(ability.detail,14 if compact else 15));parent.add_child(HSeparator.new())

func _save_settings() -> void:
	var values := T.settings_values(settings_controls)
	if T.save_settings(values)!=OK:status.text="Could not save settings. Your previous settings are unchanged.";return
	_settings=values;_apply_settings();status.text="Settings saved."

func begin_loading(path: String = WORLD) -> void:
	if not loading_path.is_empty():return
	_clear();page="loading";loading_path=path
	body.add_child(T.label("Entering Sangam",40,T.IVORY,true));status=T.prose("Loading match resources…",18);body.add_child(status)
	progress=ProgressBar.new();progress.custom_minimum_size.y=8;progress.show_percentage=false;body.add_child(progress)
	body.add_child(T.prose("Loading progress describes resource loading. The match opens after the scene is ready.",14))
	body.add_child(T.button("Cancel",cancel_loading))
	if not ResourceLoader.exists(path):_load_failed("The match scene is unavailable. Return to the menu or try again.");return
	var state:=ResourceLoader.load_threaded_get_status(path)
	var error := OK if state in [ResourceLoader.THREAD_LOAD_IN_PROGRESS,ResourceLoader.THREAD_LOAD_LOADED] else ResourceLoader.load_threaded_request(path,"PackedScene",false)
	if error!=OK:_load_failed("The match scene could not be requested.")

func cancel_loading() -> void:
	loading_path="";show_page("casual")

func _process(_delta: float) -> void:
	if loading_path.is_empty():return
	var values: Array=[]
	var state := ResourceLoader.load_threaded_get_status(loading_path,values)
	if not values.is_empty():progress.value=clampf(float(values[0]),0,1)*100
	if state==ResourceLoader.THREAD_LOAD_LOADED:
		var scene=ResourceLoader.load_threaded_get(loading_path)
		loading_path=""
		if not scene is PackedScene or get_tree().change_scene_to_packed(scene)!=OK:_load_failed("The match could not open.")
	elif state in [ResourceLoader.THREAD_LOAD_FAILED,ResourceLoader.THREAD_LOAD_INVALID_RESOURCE]:_load_failed("Match resources could not be loaded.")

func _load_failed(message: String) -> void:
	loading_path="";_clear();page="load_error";load_status=message
	body.add_child(T.label("Deployment interrupted",34,T.IVORY,true));body.add_child(T.prose(message));body.add_child(T.button("Try again",func():begin_loading(WORLD),true));body.add_child(T.button("Back to menu",func():show_page("home")))

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_ESCAPE:
		if not loading_path.is_empty():cancel_loading()
		else:show_page("home")
		get_viewport().set_input_as_handled()
