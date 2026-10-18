extends RefCounted
## Keep an existing modal focus visible after native containers finish resizing.
## Both callers retain their own _accepts_input policy and focus ownership.

static func reveal_after_layout(owner: Control, scroll: ScrollContainer) -> void:
	if not is_instance_valid(owner) or not owner.is_inside_tree(): return
	var tree := owner.get_tree()
	var focused := owner.get_viewport().gui_get_focus_owner()
	if not _current(owner, scroll, focused, tree): return
	var owner_ref: WeakRef = weakref(owner)
	var scroll_ref: WeakRef = weakref(scroll)
	var focus_ref: WeakRef = weakref(focused)
	for unused in 2:
		await tree.process_frame
		# Resolve before crossing a typed call boundary: a freed Node otherwise
		# raises an argument-type error before _current can reject it.
		owner = owner_ref.get_ref()
		scroll = scroll_ref.get_ref()
		focused = focus_ref.get_ref()
		if not _current(owner, scroll, focused, tree): return
	if not scroll.get_global_rect().encloses(focused.get_global_rect()):
		scroll.ensure_control_visible(focused)

static func _current(owner: Control, scroll: ScrollContainer, focused: Control, tree: SceneTree) -> bool:
	return (is_instance_valid(owner) and not owner.is_queued_for_deletion()
		and owner.is_inside_tree() and owner.get_tree() == tree
		and owner.is_visible_in_tree() and owner._accepts_input()
		and is_instance_valid(scroll) and not scroll.is_queued_for_deletion()
		and scroll.is_visible_in_tree() and owner.is_ancestor_of(scroll)
		and is_instance_valid(focused) and not focused.is_queued_for_deletion()
		and focused.is_visible_in_tree() and focused.focus_mode != Control.FOCUS_NONE
		and (not focused is BaseButton or not focused.disabled)
		and scroll.is_ancestor_of(focused)
		and owner.get_viewport().gui_get_focus_owner() == focused)
