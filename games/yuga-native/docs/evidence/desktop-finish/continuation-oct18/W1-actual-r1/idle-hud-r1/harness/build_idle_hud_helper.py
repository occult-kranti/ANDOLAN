from pathlib import Path
W=Path(__file__).parent.parent;H=W/'harness';s=(H/'capture_landmarks.gd').read_text()
a=s.index('\treview_camera=Camera3D.new();review_camera.name="ReviewLandmarkCamera"');b=s.index('\tif not take_frontage(',a)
s=s[:a]+'''	await frames(SETTLE_FRAMES)
	check("unchanged live product camera",root.get_camera_3d()==scene.player.camera and scene.player.active and not scene.overview and not paused)
	production_admission={"scope":"Actual live idle default product camera, fullworld retained; only declaredTraversalStatus UI differs. No physics/pose/camera/light/material/clock overrides.","world_ready":scene.world_ready,"hero_ready":scene.player.model_ready}
''' + s[b:]
s=s.replace('00-landmarks-fullworld','00-idle-traversal-hud').replace('"case":"landmark-resource-parity"','"case":"idle-traversal-hud"')
s=s.replace('One same-camera full-world landmark view; only traversal primitive sharing is the declared difference. No FPS or whole-world quality acceptance.','One default live product-camera idle-world view; only declared traversal HUD geometry/copy changes. No FPS or whole-world quality acceptance.')
s=s.replace('\tstate.serialization_errors = serialization_errors.duplicate()','''	var traversal_panel: Control=scene.hud.get_node("TraversalStatus")
	state.traversal_hud={"visible":traversal_panel.is_visible_in_tree(),"rect":encode_value(traversal_panel.get_global_rect()),"custom_minimum":encode_value(traversal_panel.custom_minimum_size),"ability":scene.ability_label.text,"ability_rect":encode_value(scene.ability_label.get_global_rect()),"goal":scene.goal_label.text,"goal_rect":encode_value(scene.goal_label.get_global_rect()),"goal_minimum":encode_value(scene.goal_label.custom_minimum_size),"energy":scene.energy_bar.value,"energy_max":scene.energy_bar.max_value,"energy_rect":encode_value(scene.energy_bar.get_global_rect()),"energy_visible":scene.energy_bar.is_visible_in_tree()}
	state.serialization_errors = serialization_errors.duplicate()''')
(H/'capture_idle_hud.gd').write_text(s);print('idle helper prepared; unstaged/unrun; declared product camera')
