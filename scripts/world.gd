extends Node2D
## Builds the test map from an ASCII layout (see tools/gen_test_map.py for the legend):
## ground tiles go on $Ground, trees and rocks under $Objects, which sorts by y so the
## bard can walk behind them.

const TILE := 32
const TERRAIN := preload("res://art/tiles/terrain.png")
const SPRUCE := preload("res://scenes/spruce.tscn")
const ROCK := preload("res://scenes/rock.tscn")

@export_file("*.txt") var map_file := "res://maps/forchach_test.txt"

var rows: PackedStringArray

@onready var ground: TileMapLayer = $Ground
@onready var objects: Node2D = $Objects
@onready var player: CharacterBody2D = $Objects/Player


func _ready() -> void:
	rows = FileAccess.get_file_as_string(map_file).strip_edges().split("\n")
	ground.tile_set = _make_tileset()
	for y in rows.size():
		for x in rows[y].length():
			_place(x, y, rows[y][x])
	var size := Vector2i(rows[0].length(), rows.size()) * TILE
	_add_bounds(size)
	var cam: Camera2D = player.get_node("Camera2D")
	cam.limit_right = size.x
	cam.limit_bottom = size.y
	cam.reset_smoothing()


func _place(x: int, y: int, c: String) -> void:
	var cell := Vector2i(x, y)
	match c:
		"~":
			ground.set_cell(cell, 0, Vector2i(_mask(x, y, func(n: String) -> bool: return n != "~"), 2))
		"=", "P":
			ground.set_cell(cell, 0, Vector2i(_mask(x, y, func(n: String) -> bool: return n != "=" and n != "P"), 1))
		":":
			ground.set_cell(cell, 0, Vector2i(4 + _hash(x, y) % 2, 0))
		"*":
			ground.set_cell(cell, 0, Vector2i(3, 0))
		_:
			ground.set_cell(cell, 0, Vector2i(_hash(x, y) % 3, 0))
	var foot := Vector2(x * TILE + TILE / 2.0, y * TILE + TILE - 4)
	match c:
		"T":
			_spawn(SPRUCE, foot + Vector2(_hash(x, y) % 9 - 4, _hash(y, x) % 7 - 3))
		"r":
			_spawn(ROCK, foot)
		"P":
			player.position = foot


## Bitmask of the four neighbours (N=1, E=2, S=4, W=8) that match `test`;
## it picks the tile with the matching edges.
func _mask(x: int, y: int, test: Callable) -> int:
	var m := 0
	for i in 4:
		var d: Vector2i = [Vector2i.UP, Vector2i.RIGHT, Vector2i.DOWN, Vector2i.LEFT][i]
		if test.call(_at(x + d.x, y + d.y)):
			m |= 1 << i
	return m


func _at(x: int, y: int) -> String:
	if y < 0 or y >= rows.size() or x < 0 or x >= rows[y].length():
		return "."
	return rows[y][x]


func _hash(x: int, y: int) -> int:
	return absi((x * 73856093) ^ (y * 19349663))


func _spawn(scene: PackedScene, pos: Vector2) -> void:
	var node: Node2D = scene.instantiate()
	node.position = pos
	objects.add_child(node)


## Atlas layout is documented in tools/gen_map_art.py; water tiles are solid.
func _make_tileset() -> TileSet:
	var ts := TileSet.new()
	ts.tile_size = Vector2i(TILE, TILE)
	ts.add_physics_layer()
	var src := TileSetAtlasSource.new()
	src.texture = TERRAIN
	src.texture_region_size = Vector2i(TILE, TILE)
	ts.add_source(src, 0)
	var h := TILE / 2.0
	var square := PackedVector2Array([Vector2(-h, -h), Vector2(h, -h), Vector2(h, h), Vector2(-h, h)])
	for row in 3:
		for col in (6 if row == 0 else 16):
			var coords := Vector2i(col, row)
			src.create_tile(coords)
			if row == 2:
				var data := src.get_tile_data(coords, 0)
				data.add_collision_polygon(0)
				data.set_collision_polygon_points(0, 0, square)
	return ts


## Invisible walls around the map, so the road does not lead off the edge.
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
