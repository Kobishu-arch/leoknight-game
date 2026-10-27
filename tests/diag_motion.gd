extends SceneTree
## Diagnostic (needs a window): walks the bard right for a few seconds and prints, per
## rendered frame, how far she and the camera moved. Even steps = smooth motion.
## Run from the project root:  godot4 --path . -s tests/diag_motion.gd

var main: Node2D
var player: CharacterBody2D
var cam: Camera2D
var frames := 0
var last_p := Vector2.ZERO
var last_c := Vector2.ZERO
var steps_p: Array[float] = []
var steps_on_screen: Array[float] = []
var onscreen: Array[float] = []


func _initialize() -> void:
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	player = main.get_node("Objects/Player")
	cam = player.get_node("Camera2D")
	print("refresh %.1f Hz, physics %d tps, vsync %d, interpolation %s" % [
		DisplayServer.screen_get_refresh_rate(), Engine.physics_ticks_per_second,
		DisplayServer.window_get_vsync_mode(), ProjectSettings.get_setting("physics/common/physics_interpolation")])


func _process(_delta: float) -> bool:
	frames += 1
	if frames == 30:
		Input.action_press("move_right")
	# what the screen shows: player position relative to the camera's view, and the camera itself
	var screen_p := player.get_global_transform_with_canvas().origin
	var c := -root.get_viewport().canvas_transform.origin
	var p := player.global_position
	if frames > 60 and frames < 300:
		steps_p.append(snappedf(p.x - last_p.x, 0.01))
		steps_on_screen.append(snappedf(c.x - last_c.x, 0.01))
		onscreen.append(snappedf(screen_p.x, 0.01))
	last_p = p
	last_c = c
	if frames == 300:
		print("fps %d" % Engine.get_frames_per_second())
		print("player world step per frame: ", _hist(steps_p))
		print("world scroll per frame:       ", _hist(steps_on_screen))
		print("player on-screen x jitter: ", _hist(onscreen))
		return true
	return false


func _hist(a: Array[float]) -> Dictionary:
	var h := {}
	for v in a:
		h[v] = h.get(v, 0) + 1
	return h
