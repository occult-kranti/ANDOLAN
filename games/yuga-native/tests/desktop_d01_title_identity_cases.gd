extends SceneTree
## Fresh focus at real content scale: identity/decision, unchanged type, full Tab access.
const Shell=preload("res://scripts/launch_shell.gd")
const UI=preload("res://scripts/hero_ui_theme.gd")
var output:="/tmp/desktop-d01-title.json"
var checks:Array[Dictionary]=[]
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func frames(n:=4)->void:
	for unused in n:await process_frame
func tab()->void:
	for down in [true,false]:
		var event:=InputEventKey.new();event.keycode=KEY_TAB;event.physical_keycode=KEY_TAB;event.pressed=down
		root.push_input(event);await frames(2)
func check(label:String,passed:bool,detail:Dictionary={})->void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)
func heading_visible(shell:Control)->bool:
	var word:Rect2=shell.title_wordmark.get_global_rect()
	var subtitle:Rect2=shell._subtitle.get_global_rect()
	return root.get_visible_rect().encloses(word) and root.get_visible_rect().encloses(subtitle) and (not shell.scroll.is_ancestor_of(shell.title_wordmark) or (shell.scroll.get_global_rect().encloses(word) and shell.scroll.get_global_rect().encloses(subtitle)))
func run()->void:
	var source:=FileAccess.get_sha256("res://scripts/launch_shell.gd")
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	for scale in [1.0,1.25,1.5,2.0]:
		root.content_scale_factor=scale
		for mode in ["world","train"]:
			var shell:=Shell.new();shell.set_mode(mode);root.add_child(shell)
			shell.focus_primary() # Same public focus action as courtyard._build_ui.
			await frames(8)
			var context:String=mode+" at scale "+str(scale)
			check("Fresh title identity and primary focus visible "+context,heading_visible(shell) and root.gui_get_focus_owner()==shell.primary_button,{"wordmark":str(shell.title_wordmark.get_global_rect()),"scroll":str(shell.scroll.get_global_rect()),"scroll_offset":shell.scroll.scroll_vertical})
			var decision_fits:=true
			for control in [shell.world_mode_button,shell.train_mode_button,shell.mode_description,shell.primary_button]:decision_fits=decision_fits and shell.scroll.get_global_rect().encloses(control.get_global_rect())
			check("Both choices description and primary fit initially "+context,decision_fits and shell.selected_mode==mode)
			check("Readable title and control type preserved "+context,shell.title_wordmark.get_theme_font_size("font_size")==int(UI.TYPE_LAUNCH_WORDMARK_COMPACT if shell._compact else UI.TYPE_LAUNCH_WORDMARK) and shell.mode_description.get_theme_font_size("font_size")==UI.TYPE_BODY and shell.primary_button.get_theme_font_size("font_size")==UI.TYPE_ACTION)
			var reachable:=true
			var visited:Array[Control]=[]
			for unused in shell._actions.size():
				var focused:=root.gui_get_focus_owner()
				reachable=reachable and focused in shell._actions and shell.scroll.get_global_rect().encloses(focused.get_global_rect())
				visited.append(focused)
				if scale==2.0:reachable=reachable and heading_visible(shell)
				await tab()
			check("Native Tab reaches every action without focus obstruction "+context,reachable and visited.size()==shell._actions.size() and root.gui_get_focus_owner()==shell.primary_button)
			shell.queue_free();await frames(6)
	check("Title source unchanged during observations",source==FileAccess.get_sha256("res://scripts/launch_shell.gd"))
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":{"res://scripts/launch_shell.gd":source,get_script().resource_path:FileAccess.get_sha256(get_script().resource_path)},"scope":"Fresh native shell in both actual modes at production100/125/150/200% content scaling, initial clipping, unchanged type and actual Tab loop. No manual layout repair, mocked labels, pixels, OS input or camera changes."},"  ")+"\n")
	await frames(8);quit(0 if passed else 1)
