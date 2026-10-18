extends SceneTree
func _initialize(): call_deferred("run")
func frames():
 for unused in 5: await process_frame
func key(code):
 for down in [true,false]:
  var event=InputEventKey.new()
  event.keycode=code;event.physical_keycode=code;event.pressed=down
  root.push_input(event)
  await process_frame
func run():
 var scene=load("res://scenes/courtyard.tscn").instantiate()
 root.add_child(scene);current_scene=scene
 await frames()
 scene._open_settings(true)
 await frames()
 await key(KEY_END)
 await key(KEY_TAB)
 await key(KEY_HOME)
 var result={"sensitivity":scene.sensitivity,"volume":scene.volume,"focus":str(root.gui_get_focus_owner().name),"scope":"Plan-only native GUI key preflight against frozen source; no package or OS-input acceptance."}
 FileAccess.open("/tmp/yuga-i3-slider-input-preflight.json",FileAccess.WRITE).store_string(JSON.stringify(result))
 current_scene=null;scene.queue_free()
 await frames();OS.delay_msec(100);await process_frame
 quit(0 if result.sensitivity==2.5 and result.volume==0.0 and result.focus=="Volume" else 1)
