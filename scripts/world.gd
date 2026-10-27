extends Node2D
## Builds the test map from maps/forchach_test.txt (format and legend in tools/gen_test_map.py).
##
## $Ground gets one grass tile per map cell. Gravel, path, water and the two cliff layers are
## dual-grid layers shifted by half a tile: each of their tiles sits between four map cells and
## shows a rounded shape for the cells that have that terrain (see tools/gen_map_art.py).
## The cliff wall covers the whole raised meadow; its grass top leaves out the two southern rows
## of cells, so a two-cell wall shows along the front. Bridge and stairs are plain tiles on top.
##
## The raised meadow has two sets of walls: "low" ones keep the bard off it while she is on the
## ground, "high" ones keep her from walking off its edge while she is up there. Which set she
## collides with follows the cell under her feet; on the stairs she keeps the one she had.

const TILE := 16
const TERRAIN := preload("res://art/tiles/terrain.png")
const PROPS := {
	"T": preload("res://scenes/spruce.tscn"),
	"o": preload("res://scenes/tree.tscn"),
	"b": preload("res://scenes/bush.tscn"),
	"r": preload("res://scenes/rock.tscn"),
	"u": preload("res://scenes/stump.tscn"),
	"f": preload("res://scenes/fence.tscn"),
	"w": preload("res://scenes/warrior.tscn"),
}
const RAISED := "^S"
## collision layers (bits): 1 trees, rocks and the map edge, 2 cliff walls seen from below,
## 3 cliff edges seen from above, 4 water (the flute's notes fly over it), 5 the bard, 6 enemies
const LAYER_LOW := 2
const LAYER_HIGH := 4
const LAYER_WATER := 8

@export_file("*.txt") var map_file := "res://maps/forchach_test.txt"

var terrain: PackedStringArray
var objects_map: PackedStringArray

@onready var objects: Node2D = $Objects
@onready var player: CharacterBody2D = $Objects/Player


func _ready() -> void:
	var parts := FileAccess.get_file_as_string(map_file).strip_edges().split("\n\n")
	terrain = parts[0].split("\n")
	objects_map = parts[1].split("\n")
	var w := terrain[0].length()
	var h := terrain.size()
	var tiles := _make_tileset()
	for layer in [$Ground, $Gravel, $Path, $Water, $Bridge, $CliffWall, $CliffTop, $Stairs]:
		layer.tile_set = tiles
	for y in h:
		for x in w:
			$Ground.set_cell(Vector2i(x, y), 0, _ground_tile(x, y))
			var c := terrain[y][x]
			if c == "H":
				$Bridge.set_cell(Vector2i(x, y), 0, Vector2i(0 if _at(x, y - 1) != "H" else 1, 6))
			elif c == "S":  # wide stairs join up: walls only at their outer ends
				var joins := (1 if _at(x - 1, y) == "S" else 0) | (2 if _at(x + 1, y) == "S" else 0)
				$Stairs.set_cell(Vector2i(x, y), 0, Vector2i([2, 4, 3, 5][joins], 6))
			_place_object(x, y, objects_map[y][x])
	_fill_dual($Gravel, 1, func(c: String, _x: int, _y: int) -> bool: return c in ":~H")
	_fill_dual($Path, 2, func(c: String, _x: int, _y: int) -> bool: return c == "=")
	_fill_dual($Water, 3, func(c: String, _x: int, _y: int) -> bool: return c in "~H")
	_fill_dual($CliffWall, 4, func(c: String, _x: int, _y: int) -> bool: return c in RAISED)
	_fill_dual($CliffTop, 5, func(c: String, x: int, y: int) -> bool: return c in RAISED and not _is_face(x, y))
	_add_walls(func(x: int, y: int) -> bool: return _at(x, y) == "~", LAYER_WATER, "WaterWalls")
	_add_walls(_low_wall, LAYER_LOW, "CliffLow")
	_add_walls(_high_wall, LAYER_HIGH, "CliffHigh")
	var size := Vector2i(w, h) * TILE
	_add_bounds(size)
	player.level_at = level_at
	var cam: Camera2D = player.get_node("Camera2D")
	cam.limit_right = size.x
	cam.limit_bottom = size.y


## 0 = ground, 1 = on the raised meadow, -1 = on the stairs (keep the current level)
func level_at(pos: Vector2) -> int:
	var x := floori(pos.x / TILE)
	var y := floori(pos.y / TILE)
	var c := _at(x, y)
	if c == "S":
		return -1
	return 1 if c == "^" else 0


func _is_face(x: int, y: int) -> bool:
	return _at(x, y) in RAISED and not (_at(x, y + 1) in RAISED and _at(x, y + 2) in RAISED)


## Walls from below: the whole raised meadow, except the stairs and the cell above them.
func _low_wall(x: int, y: int) -> bool:
	return _at(x, y) == "^" and _at(x, y + 1) != "S"


## Walls from above: the cliff front and every ground cell around the meadow, except the way
## down the stairs.
func _high_wall(x: int, y: int) -> bool:
	var c := _at(x, y)
	if c == "^":
		return _is_face(x, y)
	if c == "S" or _at(x, y - 1) == "S":
		return false
	for d in [Vector2i(-1, -1), Vector2i(0, -1), Vector2i(1, -1), Vector2i(-1, 0), Vector2i(1, 0),
			Vector2i(-1, 1), Vector2i(0, 1), Vector2i(1, 1)]:
		if _at(x + d.x, y + d.y) == "^":
			return true
	return false


func _fill_dual(layer: TileMapLayer, row: int, has: Callable) -> void:
	layer.position = Vector2(-TILE / 2.0, -TILE / 2.0)
	for y in terrain.size() + 1:
		for x in terrain[0].length() + 1:
			var mask := 0
			for i in 4:
				var cx := x - 1 + (i & 1)
				var cy := y - 1 + (i >> 1)
				if has.call(_at(cx, cy), cx, cy):
					mask |= 1 << i
			if mask:
				layer.set_cell(Vector2i(x, y), 0, Vector2i(mask, row))


func _ground_tile(x: int, y: int) -> Vector2i:
	if terrain[y][x] == "*":
		return Vector2i(4 + _hash(x, y) % 2, 0)
	var n := _hash(x, y) % 20
	return Vector2i(6 + n % 2 if n < 3 else n % 4, 0)


func _place_object(x: int, y: int, c: String) -> void:
	var foot := Vector2(x * TILE + TILE / 2.0, y * TILE + TILE - 2)
	if c == "@":
		player.position = foot
		player.spawn = foot
	elif PROPS.has(c):
		var node: Node2D = PROPS[c].instantiate()
		node.position = foot + (Vector2(_hash(x, y) % 5 - 2, 0) if c in "To" else Vector2.ZERO)
		if c == "w":
			node.target = player
		if c == "f":  # rails towards neighbouring fence posts
			var left := 1 if x > 0 and objects_map[y][x - 1] == "f" else 0
			var right := 2 if x + 1 < objects_map[y].length() and objects_map[y][x + 1] == "f" else 0
			node.get_node("Sprite").region_rect = Rect2((left | right) * 16, 0, 16, 16)
		objects.add_child(node)


## Cells outside the map repeat the nearest edge cell, so the river runs off the map.
func _at(x: int, y: int) -> String:
	y = clampi(y, 0, terrain.size() - 1)
	x = clampi(x, 0, terrain[y].length() - 1)
	return terrain[y][x]


func _hash(x: int, y: int) -> int:
	return absi((x * 73856093) ^ (y * 19349663))


func _make_tileset() -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	var src := TileSetAtlasSource.new()
	src.texture = TERRAIN
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	for row in 7:
		for col in 16:
			if (row == 0 and col > 7) or (row in [1, 2, 3, 4, 5] and col == 0) or (row == 6 and col > 5):
				continue
			src.create_tile(Vector2i(col, row))
	return ts


## One static body per wall kind; each run of wall cells in a row becomes one rectangle.
func _add_walls(is_wall: Callable, layer_bits: int, node_name: String) -> void:
	var body := StaticBody2D.new()
	body.name = node_name
	body.collision_layer = layer_bits
	body.collision_mask = 0
	add_child(body)
	for y in terrain.size():
		var x := 0
		while x < terrain[y].length():
			if not is_wall.call(x, y):
				x += 1
				continue
			var start := x
			while x < terrain[y].length() and is_wall.call(x, y):
				x += 1
			var shape := RectangleShape2D.new()
			shape.size = Vector2((x - start) * TILE, TILE)
			var col := CollisionShape2D.new()
			col.shape = shape
			col.position = Vector2((start + x) * TILE / 2.0, y * TILE + TILE / 2.0)
			body.add_child(col)


## Invisible walls around the map, so the roads do not lead off the edge.
func _add_bounds(size: Vector2i) -> void:
	var body := StaticBody2D.new()
	body.name = "Bounds"
	add_child(body)
	for seg in [[Vector2.ZERO, Vector2(size.x, 0)], [Vector2(size.x, 0), Vector2(size)],
			[Vector2(size), Vector2(0, size.y)], [Vector2(0, size.y), Vector2.ZERO]]:
		var shape := SegmentShape2D.new()
		shape.a = seg[0]
		shape.b = seg[1]
		var col := CollisionShape2D.new()
		col.shape = shape
		body.add_child(col)
