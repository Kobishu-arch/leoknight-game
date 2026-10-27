extends SceneTree
## Headless check of the player on the test map: WASD movement, facing and animations,
## and that water and the map edge block her.
## Run from the project root:  godot4 --headless --path . -s tests/test_movement.gd

var failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var main: Node2D = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	await physics_frame
	var p: CharacterBody2D = main.get_node("Objects/Player")
	var sprite: AnimatedSprite2D = p.get_node("Sprite")
	_check(sprite.animation == "idle_down", "starts in idle_down")

	var start := p.position
	await _hold("move_right", 30)
	_check(p.position.x > start.x + 30, "walks right (moved %.0f px)" % (p.position.x - start.x))
	_check(sprite.animation == "walk_right" and sprite.is_playing(), "plays walk_right")
	await _hold("", 2)
	_check(p.facing == "right" and not sprite.is_playing() and sprite.frame == 1, "stands facing right")

	await _hold("move_up", 20)
	_check(sprite.animation == "walk_up", "plays walk_up")
	await _hold("move_down", 20)
	_check(sprite.animation == "walk_down", "plays walk_down")
	await _hold("", 2)
	_check(sprite.animation == "idle_down" and sprite.is_playing(), "idles facing down")

	# walk west across the meadow until the river stops her
	await _hold("move_left", 400)
	_check(sprite.animation == "walk_left", "plays walk_left")
	var row: String = main.rows[int(p.position.y) / 32]
	var water_edge := (row.rfind("~", int(p.position.x) / 32) + 1) * 32
	_check(p.position.x >= water_edge, "stopped by the river (x %.0f, water ends at %d)" % [p.position.x, water_edge])
	_check(p.position.x < water_edge + 100, "reached the river bank (x %.0f)" % p.position.x)

	# the map edge holds even where the road leaves the map
	p.position = Vector2(main.rows[0].length() * 32 - 40, 7 * 32)
	await _hold("move_right", 120)
	_check(p.position.x <= main.rows[0].length() * 32, "stays inside the map at the east edge")

	print("FAILED: %d" % failures if failures else "ALL PASSED")
	quit(1 if failures else 0)


func _hold(action: String, frames: int) -> void:
	if action:
		Input.action_press(action)
	for i in frames:
		await physics_frame
	if action:
		Input.action_release(action)


func _check(ok: bool, what: String) -> void:
	print(("  ok   " if ok else "  FAIL ") + what)
	if not ok:
		failures += 1
