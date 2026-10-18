extends SceneTree
## CPU/resource accounting, not a renderer benchmark. The counting subclass
## calls the unchanged production sampler; untouched-player timings are separate.
const FIXTURE := preload("res://tests/r4_secondary_fixture.gd")
class CountedMotion extends "res://scripts/rama_motion.gd":
	var sample_calls := 0
	var sample_slots := 0
	var samples_by_clip := {}
	func _sample(clip: String, normalized: float) -> Dictionary:
		var result := super._sample(clip,normalized)
		sample_calls += 1
		sample_slots += result.positions.size()+result.rotations.size()
		samples_by_clip[clip] = int(samples_by_clip.get(clip,0))+1
		return result

var output := "/tmp/r4-secondary-allocation.json"
var checks: Array[Dictionary] = []
var retained_imports: Array[Resource] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func memory() -> Dictionary:
	return {"allocator_live_bytes":OS.get_static_memory_usage(),"process_peak_allocator_bytes":OS.get_static_memory_peak_usage(),"objects":int(Performance.get_monitor(Performance.OBJECT_COUNT)),"resources":int(Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)),"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT))}

func tape(player: Node3D, frame: int, hz: int) -> void:
	var cycle_frame := frame % (hz*2)
	var motion: Node = player.rama_motion
	if cycle_frame==0: motion.request_action("kodanda",.18,.22)
	if cycle_frame==int(hz*.4): motion.release_action("kodanda")
	if cycle_frame==int(hz*.8): motion.request_action("piercing_dawn",.18,.22)
	if cycle_frame==int(hz*1.1): motion.cancel_action("allocation tape cancel")
	var velocity := Vector3(2,0,6) if cycle_frame<hz else Vector3(-1,0,3)
	FIXTURE.step(player,1.0/hz,velocity,float(cycle_frame)/hz*.2)
	if cycle_frame in [int(hz*.5),hz,int(hz*1.5)]:
		player.rama_lod._apply_level(1 if cycle_frame<hz else (2 if cycle_frame==hz else 0))
	if cycle_frame==hz*2-1: player.reset()

func digest(player: Node3D) -> Dictionary:
	return {"bones":FIXTURE.bones(player.rama_motion.rig),"motion":player.rama_motion.diagnostics(),"secondary":player.rama_secondary.report(),"lod":player.rama_lod.report()}

func run() -> void:
	# Hold source PackedScenes across lifecycle churn to distinguish normal
	# resource caching from leaked instances or accidental per-frame resources.
	for path in [FIXTURE.PLAYER.HERO_PATH]+FIXTURE.PLAYER.HERO_LODS: retained_imports.append(load(path))
	var trials: Array[Dictionary] = []
	for hz in [30,60,120]:
		var player := FIXTURE.create(self)
		for frame in hz*2: tape(player,frame,hz)
		var identities := FIXTURE.identities(player)
		var before := memory()
		var first_samples: int = player.rama_motion.modified_samples
		var first_release: int = player.rama_motion.release_count
		var first_cancel: int = player.rama_motion.cancel_count
		var peak_live := int(before.allocator_live_bytes)
		var start := Time.get_ticks_usec()
		for frame in hz*6:
			tape(player,frame,hz)
			peak_live = maxi(peak_live,OS.get_static_memory_usage())
		var elapsed_us := Time.get_ticks_usec()-start
		var after := memory()
		var canonical_end := digest(player)
		var samples: int = player.rama_motion.modified_samples-first_samples
		var releases: int = player.rama_motion.release_count-first_release
		var cancellations: int = player.rama_motion.cancel_count-first_cancel
		check("%d Hz untouched player keeps resource identities and finite pose"%hz,identities==FIXTURE.identities(player) and player.rama_motion.finite and player.rama_secondary.report().finite)
		check("%d Hz executes declared callbacks and one release per cycle"%hz,samples==hz*6 and releases==3 and cancellations==3,{"pose_evaluations":samples,"release_events":releases,"cancel_and_reset_events":cancellations})
		check("%d Hz retains no new node resource or orphan objects during tape"%hz,before.nodes==after.nodes and before.resources==after.resources and before.objects==after.objects and before.orphans==after.orphans,{"before":before,"after":after})
		var canonical_weak: WeakRef = weakref(player)
		player.free()
		await process_frame
		await process_frame
		check("%d Hz untouched instance releases after lifecycle"%hz,canonical_weak.get_ref()==null)
		# Replace only the fixture's controller with a transparent counter, with
		# its old arrow removed first. Other real player components remain intact.
		player = FIXTURE.create(self)
		player.rama_motion.nocked_arrow.free()
		player.rama_motion.free()
		var counter := CountedMotion.new()
		var counter_bound := counter.configure(player.visual,player.animator)
		player.rama_motion = counter
		counter.active = false
		for frame in hz*2: tape(player,frame,hz)
		var start_calls := counter.sample_calls
		var start_slots := counter.sample_slots
		var start_clips: Dictionary = counter.samples_by_clip.duplicate()
		for frame in hz*6: tape(player,frame,hz)
		var calls := counter.sample_calls-start_calls
		var slots := counter.sample_slots-start_slots
		var clip_counts := {}
		for clip in counter.samples_by_clip: clip_counts[clip] = counter.samples_by_clip[clip]-int(start_clips.get(clip,0))
		var counted_end := digest(player)
		check("%d Hz counted sampler preserves exact untouched final state"%hz,counter_bound and canonical_end==counted_end and FIXTURE.collect(player,"SkeletonModifier3D").size()==1)
		check("%d Hz actual sampler performs populated pose copies"%hz,calls>=samples and slots==calls*164*2,{"sample_calls":calls,"sample_element_slots":slots,"calls_by_clip":clip_counts})
		trials.append({"simulation_hz":hz,"simulated_seconds":6,"explicit_player_callbacks":samples,"untouched_cpu_callback_wall_us":elapsed_us,"includes":"player motion update + secondary/face/LOD + evaluate_pose, test tape dispatch and live allocator sampling; shared host scheduling included","memory_before":before,"memory_after":after,"peak_live_allocator_bytes_sampled_after_callbacks":peak_live,"measured_sampler_calls":calls,"sampled_pose_array_copies":calls*2,"sampled_pose_dictionary_results":calls,"sampled_pose_element_slots":slots,"final_blend_array_copies_from_executed_pose_evaluations":samples*2,"calls_by_clip":clip_counts,"limitations":"Array/dictionary counts are a lower bound for these executed production sites, not total malloc count or allocated bytes. Memory is Godot CPU allocator accounting, not RSS or VRAM. Counter execution is separate from untouched timing. No achieved FPS."})
		player.free()
		await process_frame
		await process_frame
	# Repeated full bind/dispose across all real owners, after imports are warm.
	var samples_after_free: Array[Dictionary] = []
	var freed := true
	for cycle in 6:
		var player := FIXTURE.create(self)
		for frame in 30: tape(player,frame,30)
		player.rama_lod._apply_level(cycle%3)
		var weak_player: WeakRef = weakref(player)
		var weak_rig: WeakRef = weakref(player.rama_motion.rig)
		player.queue_free()
		await process_frame
		await process_frame
		freed = freed and weak_player.get_ref()==null and weak_rig.get_ref()==null
		samples_after_free.append(memory())
	check("six full queued player lifecycles release every player and rig",freed)
	var baseline: Dictionary = samples_after_free[0]
	var stable_objects := true
	for snapshot in samples_after_free:
		stable_objects = stable_objects and snapshot.nodes==baseline.nodes and snapshot.resources==baseline.resources and snapshot.objects==baseline.objects and snapshot.orphans==baseline.orphans
	check("warm lifecycle cycles retain constant native object counts",stable_objects,{"after_each_free":samples_after_free})
	# The receipt itself retains dictionaries. Measure that observer growth with
	# the same sample/await schedule and no player creation before attributing
	# allocator byte changes to a leaked runtime instance.
	var observer_control: Array[Dictionary] = []
	for cycle in 6:
		await process_frame
		await process_frame
		observer_control.append(memory())
	var lifecycle_growth: int = samples_after_free[-1].allocator_live_bytes-samples_after_free[0].allocator_live_bytes
	var observer_growth: int = observer_control[-1].allocator_live_bytes-observer_control[0].allocator_live_bytes
	var pins := FIXTURE.pins()
	for path in [get_script().resource_path,"res://tests/r4_secondary_fixture.gd"]: pins[path] = FileAccess.get_sha256(path)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"trials":trials,"lifecycle_samples":samples_after_free,"observer_control_samples":observer_control,"lifecycle_live_byte_growth":lifecycle_growth,"observer_live_byte_growth":observer_growth,"lifecycle_growth_minus_observer_bytes":lifecycle_growth-observer_growth,"source_sha256":pins,"scope":"Canonical imported real player presentation callbacks at declared 30/60/120 simulation; a separate transparent sampler subclass counts executed sample copies and is checked against exact canonical final state. Six warmed full bind/free cycles and a matching empty observer-control schedule. No scene imports, renderer, full-world benchmark, hardware FPS, total allocation count or VRAM claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	retained_imports.clear()
	quit(0 if result.passed else 1)
