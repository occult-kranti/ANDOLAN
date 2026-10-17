extends RefCounted
## Shared keyboard controls and bounded, data-only local settings.
const SAVE_PATH := "user://courtyard-settings.cfg"
const MAX_CONFIG_BYTES := 65536
const DEFAULTS := {"move_forward":KEY_W,"move_back":KEY_S,"move_left":KEY_A,"move_right":KEY_D,"jump":KEY_SPACE,"sprint":KEY_SHIFT,"reload":KEY_R,"pulse":KEY_Q,"dash":KEY_E,"grapple":KEY_G,"fly":KEY_F,"descend":KEY_CTRL,"ultimate":KEY_X}
const TITLES := {"move_forward":"Move forward","move_back":"Move back","move_left":"Move left","move_right":"Move right","jump":"Jump / ascend in flight","sprint":"Sprint","reload":"Reload","pulse":"Sunburst","dash":"Dash","grapple":"Grapple / release","fly":"Toggle flight","descend":"Descend in flight","ultimate":"Cast invocation (Confluence)"}
const FIXED := {"pause_game":KEY_ESCAPE,"reset_training":KEY_F5,"world_respawn":KEY_F5,"world_night":KEY_N,"world_overview":KEY_F1,"help_controls":KEY_F2,"open_invocations":KEY_F3}
const ALIASES := {"move_forward":KEY_UP,"move_back":KEY_DOWN,"move_left":KEY_LEFT,"move_right":KEY_RIGHT}
static var bindings: Dictionary = DEFAULTS.duplicate()
static var config_path := SAVE_PATH
static var load_notice := ""

static func install(path: String = SAVE_PATH) -> Dictionary:
	config_path = path
	bindings = DEFAULTS.duplicate()
	var result := read_config(path)
	load_notice = result.message
	if result.ok:
		var config: ConfigFile = result.config
		var candidate = config.get_value("controls", "bindings", DEFAULTS.duplicate())
		var validated := _validate(_extend_legacy_bindings(candidate))
		if validated.ok: bindings = validated.bindings
		else: load_notice = validated.message + " Default controls are active."
	_apply()
	return {"ok": result.ok and load_notice.is_empty(), "message":load_notice}

static func current() -> Dictionary:
	return bindings.duplicate()

static func _extend_legacy_bindings(candidate: Variant) -> Variant:
	# Old saved layouts may already use X. Preserve every old assignment and
	# choose a deterministic free key only for the newly introduced action.
	# Ordinary rebinding still rejects duplicates; invalid old data stays invalid.
	if not candidate is Dictionary or candidate.has("ultimate"): return candidate
	var extended: Dictionary = candidate.duplicate()
	var used: Array[int] = []
	for action in DEFAULTS:
		if action == "ultimate": continue
		var value: Variant = candidate.get(action, DEFAULTS[action])
		if value is int: used.append(value)
	for key in [KEY_X, KEY_V, KEY_B, KEY_C, KEY_Z, KEY_T, KEY_Y, KEY_U, KEY_I, KEY_O, KEY_P, KEY_H, KEY_J, KEY_K, KEY_L, KEY_1, KEY_2, KEY_3]:
		if key not in used:
			extended["ultimate"] = key
			break
	return extended

static func label(action: String) -> String:
	if action == "fire": return "LMB"
	return OS.get_keycode_string(int(bindings.get(action, FIXED.get(action, 0))))

static func _allowed(key: int) -> bool:
	return ((key >= KEY_A and key <= KEY_Z) or (key >= KEY_0 and key <= KEY_9) or key in [KEY_SPACE, KEY_SHIFT, KEY_CTRL]) and key != KEY_N

static func _validate(candidate: Variant) -> Dictionary:
	if not candidate is Dictionary: return {"ok":false,"message":"Saved controls must be a key map."}
	var merged := DEFAULTS.duplicate()
	for action in candidate:
		if not action is String or not DEFAULTS.has(action): return {"ok":false,"message":"Unknown control action."}
		if not candidate[action] is int or not _allowed(candidate[action]): return {"ok":false,"message":"That key is reserved for navigation or unsupported."}
		merged[action] = candidate[action]
	var used := {}
	for action in merged:
		if used.has(merged[action]): return {"ok":false,"message":"That key is already assigned to " + String(TITLES[used[merged[action]]]) + "."}
		used[merged[action]] = action
	return {"ok":true,"bindings":merged,"message":""}

static func set_binding(action: String, keycode: int) -> Dictionary:
	if not DEFAULTS.has(action): return {"ok":false,"message":"Unknown control action."}
	var candidate := bindings.duplicate()
	candidate[action] = keycode
	var valid := _validate(candidate)
	if not valid.ok: return valid
	var saved := merge_settings({"controls":{"bindings":candidate,"binding_version":2}},config_path)
	if not saved.ok: return saved
	bindings = candidate
	load_notice = ""
	_apply()
	return {"ok":true,"message":String(TITLES[action]) + ": " + label(action)}

static func reset_defaults() -> Dictionary:
	var result: Dictionary
	if read_config(config_path).ok:
		result = merge_settings({"controls":{"bindings":DEFAULTS.duplicate(),"binding_version":2}},config_path)
	else:
		result = _recover_invalid_config(config_path)
	if result.ok:
		bindings = DEFAULTS.duplicate()
		load_notice = ""
		_apply()
		if not result.has("backup_path"): result.message = "Default controls restored and saved."
	return result

static func _recover_invalid_config(path: String) -> Dictionary:
	# Explicit Reset is the only operation allowed to replace invalid bytes.
	# Rename on the same filesystem preserves even oversized files without
	# loading/copying them. Stage the small valid replacement before mutation.
	var failure := {"ok":false,"message":"Could not preserve invalid settings. Original file is unchanged."}
	if not path.begins_with("user://") or path.get_file().to_utf8_buffer().size() > 160:
		return failure
	if not FileAccess.file_exists(path): return failure
	var backup := ""
	var temporary := ""
	var stamp := str(int(Time.get_unix_time_from_system())) + "-" + str(Time.get_ticks_usec())
	for attempt in range(16):
		var candidate := path + ".invalid-" + stamp + "-" + str(attempt) + ".bak"
		var staged := candidate + ".new"
		if not FileAccess.file_exists(candidate) and not DirAccess.dir_exists_absolute(candidate) and not FileAccess.file_exists(staged) and not DirAccess.dir_exists_absolute(staged):
			backup = candidate
			temporary = staged
			break
	if backup.is_empty(): return failure
	var config := ConfigFile.new()
	config.set_value("controls","bindings",DEFAULTS.duplicate())
	config.set_value("controls","binding_version",2)
	if config.save(temporary) != OK:
		DirAccess.remove_absolute(temporary)
		return failure
	if DirAccess.rename_absolute(path,backup) != OK:
		DirAccess.remove_absolute(temporary)
		return failure
	if DirAccess.rename_absolute(temporary,path) != OK:
		var restored := DirAccess.rename_absolute(backup,path)
		DirAccess.remove_absolute(temporary)
		if restored != OK:
			return {"ok":false,"backup_path":backup,"message":"Reset could not finish. Your original settings are preserved at " + backup + "."}
		return failure
	return {"ok":true,"backup_path":backup,"message":"Defaults saved. Invalid settings preserved as " + backup.get_file() + "."}

static func _apply() -> void:
	release_gameplay()
	var all := bindings.duplicate()
	all.merge(FIXED)
	for action in all:
		if not InputMap.has_action(action): InputMap.add_action(action)
		InputMap.action_erase_events(action)
		_add_key(action,all[action])
		if ALIASES.has(action): _add_key(action,ALIASES[action])
	if not InputMap.has_action("fire"): InputMap.add_action("fire")
	InputMap.action_erase_events("fire")
	var mouse := InputEventMouseButton.new()
	mouse.button_index = MOUSE_BUTTON_LEFT
	InputMap.action_add_event("fire",mouse)

static func _add_key(action: String,keycode: int) -> void:
	var key := InputEventKey.new()
	key.physical_keycode = keycode
	InputMap.action_add_event(action,key)

static func release_gameplay() -> void:
	for action in DEFAULTS:
		if InputMap.has_action(action): Input.action_release(action)
	if InputMap.has_action("fire"): Input.action_release("fire")

static func _safe_text(source: String) -> bool:
	var quoted := false
	var escaped := false
	var comment := false
	var nesting := []
	for character in source:
		if comment:
			if character == "\n": comment = false
			continue
		if quoted:
			if escaped: escaped = false
			elif character == "\\": escaped = true
			elif character == '"': quoted = false
			continue
		if character == '"': quoted = true
		elif character == ";" or character == "#": comment = true
		elif character == "(" or character == ")": return false
		elif character == "[" or character == "{":
			nesting.append(character)
			if nesting.size() > 8: return false
		elif character == "]" or character == "}":
			if nesting.is_empty(): return false
			if nesting.pop_back() != ("[" if character == "]" else "{"): return false
	return not quoted and nesting.is_empty()

static func read_config(path: String = SAVE_PATH) -> Dictionary:
	var config := ConfigFile.new()
	if not FileAccess.file_exists(path): return {"ok":true,"config":config,"message":""}
	var file := FileAccess.open(path,FileAccess.READ)
	if not file: return {"ok":false,"config":config,"message":"Settings could not be read; defaults are active."}
	if file.get_length() > MAX_CONFIG_BYTES:
		file.close()
		return {"ok":false,"config":config,"message":"Settings are too large; defaults are active."}
	var source := file.get_as_text()
	file.close()
	if not _safe_text(source): return {"ok":false,"config":config,"message":"Settings contain unsupported data; defaults are active."}
	if config.parse(source) != OK: return {"ok":false,"config":ConfigFile.new(),"message":"Settings are malformed; defaults are active."}
	return {"ok":true,"config":config,"message":""}

static func _safe_value(value: Variant, depth: int = 0) -> bool:
	if depth > 8: return false
	if value == null or value is bool or value is int: return true
	if value is float: return is_finite(value)
	if value is String: return value.length() <= 4096
	if value is Dictionary:
		if value.size() > 64: return false
		for key in value:
			if not key is String or key.length() > 256 or not _safe_value(value[key],depth + 1): return false
		return true
	if value is Array:
		if value.size() > 64: return false
		for item in value:
			if not _safe_value(item,depth + 1): return false
		return true
	return false

static func merge_settings(updates: Dictionary, path: String = SAVE_PATH) -> Dictionary:
	if not _safe_value(updates): return {"ok":false,"message":"Settings update contains unsupported data."}
	for section in updates:
		if not updates[section] is Dictionary: return {"ok":false,"message":"Settings sections must be dictionaries."}
	var loaded := read_config(path)
	if not loaded.ok: return {"ok":false,"message":loaded.message + " Existing file was preserved."}
	var config: ConfigFile = loaded.config
	for section in updates:
		for key in updates[section]: config.set_value(section,key,updates[section][key])
	if config.encode_to_text().to_utf8_buffer().size() > MAX_CONFIG_BYTES: return {"ok":false,"message":"Settings update is too large."}
	var result := config.save(path)
	return {"ok":result == OK,"message":"" if result == OK else "Settings could not be saved: " + error_string(result)}

static func help_text() -> String:
	var lines := PackedStringArray()
	for action in DEFAULTS: lines.append(label(action) + "  ·  " + TITLES[action])
	lines.append("LMB  ·  Fire / aim with mouse\nArrow keys  ·  Move\nEsc  ·  Pause / back\nF2  ·  Help\nF3  ·  Invocation selection (Confluence)\nF1  ·  World overview\nF5  ·  Reset / respawn\nN  ·  World day / night")
	return "\n".join(lines)
