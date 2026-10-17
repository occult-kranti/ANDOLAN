extends RefCounted
## Strict offline invocation rules and planar hit geometry. No actor mutation.

const PATH := "res://assets/design/native-ultimate-rules.json"
const HEROES := ["rama","ravana","arjuna","duryodhana","hanuman","karna","bhima","meghnad","sita","draupadi","subhadra","hidimbi","chitrangada","ulupi"]
const KINDS := ["projectile_volley","disk","projectile_volley","sector","disk","disk","disk","sector","zone_disk","disk","summon_pair","summon_pair","disk","zone_disk"]
const EFFECTS := [["damage"],["damage"],["damage"],["damage"],["damage","heal"],["damage"],["damage"],["damage"],["shield","heal_rate"],["heal"],["summon"],["summon"],["shield"],["damage_rate","slow"]]
const MAX_BYTES := 65536

static func number(value, lower: float, upper: float) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value) >= lower and float(value) <= upper

static func load_rules(path := PATH) -> Dictionary:
	var file := FileAccess.open(path,FileAccess.READ)
	if file == null or file.get_length() > MAX_BYTES:
		return {"valid":false,"errors":["Missing or oversized practice rules"],"data":{}}
	var text := file.get_as_text()
	# Bound nesting before handing untrusted bytes to the native JSON parser.
	if _duplicate_or_deep(text):
		return {"valid":false,"errors":["Duplicate keys or excessive nesting"],"data":{}}
	var parser := JSON.new()
	if parser.parse(text) != OK or not parser.data is Dictionary:
		return {"valid":false,"errors":["Malformed practice rules JSON"],"data":{}}
	var errors := validate(parser.data)
	return {"valid":errors.is_empty(),"errors":errors,"data":parser.data if errors.is_empty() else {}}

static func _duplicate_or_deep(text: String) -> bool:
	var stack: Array = []
	var index := 0
	while index < text.length():
		var character := text[index]
		if character in ["{","["]:
			stack.append({} if character == "{" else null)
			if stack.size() > 16:return true
		elif character in ["}","]"]:
			if not stack.is_empty():stack.pop_back()
		elif character == '"':
			var start := index
			index += 1
			while index < text.length():
				if text[index] == "\\":index += 2;continue
				if text[index] == '"':break
				index += 1
			var after := index+1
			while after < text.length() and text[after] in [" ","\t","\r","\n"]:after += 1
			if after < text.length() and text[after] == ":" and not stack.is_empty() and stack[-1] is Dictionary:
				var key = JSON.parse_string(text.substr(start,index-start+1))
				if stack[-1].has(key):return true
				stack[-1][key] = true
		index += 1
	return false

static func validate(data: Dictionary) -> Array:
	var errors: Array = []
	if data.get("schema_version") != 1 or typeof(data.get("schema_version")) not in [TYPE_INT,TYPE_FLOAT]:errors.append("Unsupported schema")
	if not number(data.get("revision"),1,1):errors.append("Unsupported revision")
	if data.get("receiver_policy") != "ground_root_center_with_height_and_authority_xz_los":errors.append("Receiver geometry policy drift")
	if data.get("rules_id") != "yuga.native_invocations.practice.v1":errors.append("Unknown rules ID")
	if data.get("codex_sha256") != FileAccess.get_sha256("res://assets/design/hero-codex.json"):errors.append("Codex source drift")
	var scope = data.get("scope")
	if not scope is Dictionary:return ["Missing scope"]
	for key in ["network_enabled","hero_health_enabled","core_spell_damage_enabled","avatar_changes_enabled"]:
		if scope.get(key) != false or typeof(scope.get(key)) != TYPE_BOOL:errors.append("Unsupported scope "+key)
	if scope.get("offline_only") != true or scope.get("receiver") != "living_lane_troops":errors.append("Receiver scope drift")
	for pair in [["shared_cooldown_s",12.0],["max_active_casts",1.0],["max_receipts_per_event",72.0],["history_capacity",64.0],["grounded_max_height_m",.35]]:
		if not number(data.get(pair[0]),pair[1],pair[1]):errors.append("Invalid limit "+pair[0])
	var rules = data.get("rules")
	if not rules is Array or rules.size() != 14:return errors+["Exactly fourteen invocation rules required"]
	for index in range(14):
		var rule = rules[index]
		if not rule is Dictionary:errors.append("Rule is not an object");continue
		var hero: String = HEROES[index]
		if rule.get("hero_id") != hero or rule.get("effect_id") != hero+".r.v1":errors.append("Hero/effect identity drift "+hero)
		if not rule.get("name") is String or rule.name.is_empty() or rule.name.length()>80:errors.append("Invalid name "+hero)
		var timing = rule.get("timing")
		if not timing is Dictionary:errors.append("Missing timing "+hero);continue
		var total := 0.0
		for key in ["windup_s","travel_s","active_s","recovery_s"]:
			if not number(timing.get(key),.35 if key == "windup_s" else 0,9):errors.append("Invalid timing "+hero+"/"+key)
			else:total += float(timing[key])
		if total <= 0 or total >= 12:errors.append("Timing exceeds shared cooldown "+hero)
		if hero in ["sita","ulupi"] and not number(timing.get("active_s"),6,6):errors.append("Zone active lifetime drift "+hero)
		if hero in ["subhadra","hidimbi"] and not number(timing.get("active_s"),9,9):errors.append("Summon appearance lifetime drift "+hero)
		if hero=="chitrangada" and not number(timing.get("active_s"),4,4):errors.append("Ward appearance lifetime drift")
		if hero=="hanuman" and not number(timing.get("travel_s"),.45,.45):errors.append("Landing projection travel drift")
		if hero not in ["rama","arjuna","hanuman"] and not number(timing.get("travel_s"),0,0):errors.append("Unexpected payload travel "+hero)
		var geometry = rule.get("geometry")
		if not geometry is Dictionary:errors.append("Missing geometry "+hero);continue
		if geometry.get("kind") != KINDS[index]:errors.append("Wrong geometry "+hero)
		var anchor: String = "ground_target" if hero in ["hanuman","ulupi"] else "caster"
		if geometry.get("anchor") != anchor or not number(geometry.get("height_m"),2.5,2.5):errors.append("Invalid anchor/height "+hero)
		if anchor == "ground_target" and not number(geometry.get("target_range_m"),1,28):errors.append("Invalid target range "+hero)
		if KINDS[index] in ["disk","zone_disk"] and not number(geometry.get("radius_m"),.1,8):errors.append("Invalid disk "+hero)
		if KINDS[index] == "sector":
			if not number(geometry.get("range_m"),1,28) or not number(geometry.get("half_angle_cos"),.55 if hero=="duryodhana" else .25,.55 if hero=="duryodhana" else .25):errors.append("Invalid sector "+hero)
		if KINDS[index] == "projectile_volley":
			if not number(geometry.get("range_m"),28,28) or not number(geometry.get("radius_m"),.5,.5) or not number(geometry.get("speed_mps"),62,62):errors.append("Invalid projectile "+hero)
			var offsets = geometry.get("yaw_offsets_rad")
			var expected := [-.12,0.0,.12] if hero=="rama" else [0.0]
			if not offsets is Array or offsets.size()!=expected.size():errors.append("Invalid projectile count "+hero)
			else:
				for j in expected.size():
					if not number(offsets[j],expected[j],expected[j]):errors.append("Invalid projectile angle "+hero)
			if not number(timing.get("travel_s"),28.0/62.0-.000001,28.0/62.0+.000001):errors.append("Projectile lifetime differs from range/speed "+hero)
		if KINDS[index] == "summon_pair":
			if not number(geometry.get("maximum_route_distance_m"),5,5) or geometry.get("lateral_offsets_m") != [-1.3,1.3]:errors.append("Invalid pair placement "+hero)
		var effects = rule.get("effects")
		if not effects is Array or effects.size()!=EFFECTS[index].size():errors.append("Wrong payload count "+hero);continue
		for j in effects.size():
			var effect = effects[j]
			if not effect is Dictionary:errors.append("Invalid effect "+hero);continue
			var kind: String = EFFECTS[index][j]
			if effect.get("kind")!=kind:errors.append("Wrong payload kind "+hero)
			var team: String = "enemy" if kind in ["damage","damage_rate","slow"] else "ally"
			if effect.get("team")!=team:errors.append("Wrong payload team "+hero)
			if kind in ["damage","heal","shield"] and not number(effect.get("amount"),.1,100):errors.append("Invalid amount "+hero)
			if kind in ["heal_rate","damage_rate"] and not number(effect.get("amount_per_s"),.1,20):errors.append("Invalid rate "+hero)
			if kind in ["shield","summon","slow"] and not number(effect.get("duration_s"),.05,9):errors.append("Invalid status duration "+hero)
			if kind=="shield" and (not number(effect.get("duration_s"),.05,9) or not number(timing.get("active_s"),.05,9) or float(effect.duration_s)>float(timing.active_s)):errors.append("Shield outlives visible active window "+hero)
			if kind=="slow" and not number(effect.get("multiplier"),.55,.55):errors.append("Invalid slow "+hero)
			if kind=="summon":
				if effect.get("role") != ("bow_guard" if hero=="subhadra" else "spearman"):errors.append("Wrong summon role "+hero)
				for pair in [["count",2.0],["duration_s",9.0],["health",105.0],["core_damage",0.0],["gold_on_expiry",0.0]]:
					if not number(effect.get(pair[0]),pair[1],pair[1]):errors.append("Invalid summon "+pair[0])
				if not number(effect.get("attack_damage"),1,40):errors.append("Invalid summon attack")
	return errors

static func contains(geometry: Dictionary, point: Vector3) -> bool:
	if not point.is_finite():return false
	var center: Vector3 = geometry.get("center",Vector3.ZERO)
	if absf(point.y-center.y)>float(geometry.height_m):return false
	var offset := Vector2(point.x-center.x,point.z-center.z)
	var kind: String = geometry.kind
	if kind in ["disk","zone_disk"]:return offset.length_squared() <= pow(float(geometry.radius_m),2)+1e-8
	if kind=="sector":
		if offset.length_squared()>pow(float(geometry.range_m),2)+1e-8:return false
		if offset.length_squared()<1e-12:return true
		var forward: Vector3 = geometry.forward
		return offset.normalized().dot(Vector2(forward.x,forward.z)) >= float(geometry.half_angle_cos)-1e-8
	return false

static func segment_circle_fraction(start: Vector3, finish: Vector3, center: Vector3, radius: float) -> float:
	var direction := Vector2(finish.x-start.x,finish.z-start.z)
	var offset := Vector2(start.x-center.x,start.z-center.z)
	var c := offset.length_squared()-radius*radius
	if c<=0:return 0.0
	var a := direction.length_squared()
	if a<1e-12:return INF
	var b := 2.0*offset.dot(direction)
	var discriminant := b*b-4*a*c
	if discriminant<0:return INF
	var value := (-b-sqrt(discriminant))/(2*a)
	return value if value>=0 and value<=1 else INF
