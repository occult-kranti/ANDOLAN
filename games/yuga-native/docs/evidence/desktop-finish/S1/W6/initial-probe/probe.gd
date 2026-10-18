extends SceneTree
var loader: Control
var boot: Control
func _initialize(): call_deferred("run")
func run():
 boot=load("res://scenes/boot.tscn").instantiate()
 root.add_child(boot)
 current_scene=boot
 await process_frame
 loader=root.get_node("YugaSceneTransitionLayer/SceneTransition")
 root.remove_child(boot)
 var host=Control.new()
 var button=Button.new()
 host.add_child(button)
 root.add_child(host)
 current_scene=host
 button.grab_focus()
 for i in 8: await process_frame
 print("S1_DETACH_PHASE=",loader.phase," focus_preserved=",root.gui_get_focus_owner()==button)
 boot.free()
 host.queue_free()
 root.get_node("YugaSceneTransitionLayer").queue_free()
 for i in 3: await process_frame
 quit()
