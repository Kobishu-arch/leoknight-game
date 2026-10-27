extends SceneTree
## Headless check of the player on the test map: WASD movement, facing and animations,
## water, the map edge, and the cliffs (walls from below, stairs up, edges from above).
## Run from the project root:  godot4 --headless --path . -s tests/test_movement.gd

const TILE := 16

var failures := 0
var main: Node2D
var p: CharacterBody2D


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	await physics_frame
	p = main.get_node("Objects/Player")
	var sprite: AnimatedSprite2D = p.get_node("Sprite")
	_check(sprite.animation == "idle_down", "starts in idle_down")

	var start := p.position
	await _hold("move_right", 30)
	_check(p.position.x > start.x + 15, "walks right (moved %.0f px)" % (p.position.x - start.x))
	_check(sprite.animation == "walk_right" and sprite.is_playing(), "plays walk_right")
	await _hold("", 2)
	_check(p.facing == "right" and not sprite.is_playing() and sprite.frame == 1, "stands facing right")
	await _hold("move_up", 10)
	_check(sprite.animation == "walk_up", "plays walk_up")
	await _hold("move_down", 10)
	_check(sprite.animation == "walk_down", "plays walk_down")
	await _hold("", 2)
	_check(sprite.animation == "idle_down" and sprite.is_playing(), "idles facing down")

	# west along the start row until the river stops her
	await _hold("move_left", 400)
	_check(sprite.animation == "walk_left", "plays walk_left")
	var row: String = main.terrain[int(p.position.y) / TILE]
	var water_edge := (row.rfind("~", int(p.position.x) / TILE) + 1) * TILE
	_check(p.position.x >= water_edge and p.position.x < water_edge + 60,
		"stopped at the river bank (x %.0f, water ends at %d)" % [p.position.x, water_edge])

	# the map edge holds even where the road leaves the map
	_teleport(Vector2(main.terrain[0].length() * TILE - 20, 24 * TILE + 8))
	await _hold("move_right", 120)
	_check(p.position.x <= main.terrain[0].length() * TILE, "stays inside the map at the east edge")

	# cliffs: find the stairs and a stretch of cliff front without stairs
	var stairs := _find("S")
	var face := _cliff_front_away_from(stairs)
	_teleport(Vector2(face.x * TILE + 8, (face.y + 2) * TILE + 8))
	await _hold("move_up", 90)
	_check(p.level == 0 and p.position.y >= (face.y + 1) * TILE, "the cliff wall stops her from below (y %.0f)" % p.position.y)

	_teleport(Vector2(stairs.x * TILE + 8, (stairs.y + 3) * TILE + 8))
	await _hold("move_up", 90)
	_check(p.level == 1 and p.position.y < stairs.y * TILE, "climbs the stairs onto the meadow (level %d, y %.0f)" % [p.level, p.position.y])
	await _hold("move_right", 60)
	await _hold("move_down", 90)
	_check(p.level == 1 and main.level_at(p.position) == 1, "the cliff edge stops her from walking off (y %.0f)" % p.position.y)
	# back to the top of the stairs (the cells beside them are cliff front), then down
	await _hold("move_up", 25)
	_teleport(Vector2(stairs.x * TILE + 8, (stairs.y - 1) * TILE + 8))
	await _hold("move_down", 150)
	_check(p.level == 0 and p.position.y > (stairs.y + 2) * TILE, "walks back down the stairs (level %d, y %.0f)" % [p.level, p.position.y])

	# the flute: Space plays it and a note flies out in the facing direction
	_teleport(Vector2(30 * TILE, 30 * TILE))
	await _hold("move_right", 5)
	var x0 := p.position.x
	Input.action_press("attack")
	await physics_frame
	Input.action_release("attack")
	await _hold("move_right", 12)
	_check(sprite.animation == "play_right", "Space plays the flute (%s)" % sprite.animation)
	_check(absf(p.position.x - x0) < 4, "she stands still while playing")
	var notes := p.get_parent().get_children().filter(func(n: Node) -> bool: return n.name.begins_with("Note"))
	_check(notes.size() == 1, "one note flies out (%d)" % notes.size())
	if notes.size() == 1:
		var n0: float = notes[0].position.x
		await _hold("", 10)
		_check(is_instance_valid(notes[0]) and notes[0].position.x > n0 + 15, "the note flies to the right")
		await _hold("", 90)
		_check(not is_instance_valid(notes[0]), "the note fades out at the end of its range")
	await _hold("move_down", 10)
	_check(sprite.animation == "walk_down", "walks again after playing")

	# a note that hits a rock bursts into sparkles
	var rock: Node2D = p.get_parent().get_children().filter(func(n: Node) -> bool: return n.name.begins_with("Rock"))[0]
	_teleport(rock.position + Vector2(-40, 0))
	await _hold("move_right", 2)
	Input.action_press("attack")
	await physics_frame
	Input.action_release("attack")
	var burst_seen := false
	for i in 40:
		await physics_frame
		if p.get_parent().get_children().any(func(n: Node) -> bool: return n.name.begins_with("NoteBurst")):
			burst_seen = true
	_check(burst_seen, "a note bursts when it hits a rock")

	# walking behind a leafy tree makes its crown see-through
	var tree: Node2D = p.get_parent().get_children().filter(func(n: Node) -> bool: return n.name.begins_with("Tree"))[0]
	var crown: CanvasItem = tree.get_node("Sprite")
	_teleport(tree.position + Vector2(0, -12))
	await _hold("", 30)
	_check(crown.modulate.a < 0.6, "the treetop fades while she is behind it (alpha %.2f)" % crown.modulate.a)
	_teleport(tree.position + Vector2(0, 40))
	await _hold("", 30)
	_check(crown.modulate.a > 0.95, "and comes back when she leaves (alpha %.2f)" % crown.modulate.a)

	print("FAILED: %d" % failures if failures else "ALL PASSED")
	quit(1 if failures else 0)


func _teleport(pos: Vector2) -> void:
	p.position = pos
	p.level = main.level_at(pos) if main.level_at(pos) >= 0 else 0
	p.collision_mask = p._walls()


func _find(c: String) -> Vector2i:
	for y in main.terrain.size():
		var x: int = main.terrain[y].find(c)
		if x >= 0:
			return Vector2i(x, y)
	return Vector2i(-1, -1)


func _cliff_front_away_from(stairs: Vector2i) -> Vector2i:
	for x in range(stairs.x + 6, main.terrain[0].length()):
		for y in main.terrain.size() - 3:
			if main.terrain[y][x] == "^" and main.terrain[y + 1][x] in ".*=" and main.terrain[y + 2][x] in ".*="\
					and main.objects_map[y + 1][x] == "." and main.objects_map[y + 2][x] == "." and main.terrain[y - 1][x] == "^":
				return Vector2i(x, y)
	return Vector2i(-1, -1)


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
