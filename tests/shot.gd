extends SceneTree
## Renders the map with the bard standing at a map cell, for looking at the art.
## Run from the project root:
##   godot4 --path . -s tests/shot.gd --write-movie /tmp/shot.png --fixed-fps 60 -- 57 20 [down|up|left|right]
## The numbers are the map cell. With a direction she turns that way and plays the flute;
## frames are written for about two seconds (the note is in flight around frame 75).

var main: Node2D
var frames := 0
var dir := ""


func _initialize() -> void:
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)


func _process(_delta: float) -> bool:
	frames += 1
	var args := OS.get_cmdline_user_args()
	var p: Node2D = main.get_node("Objects/Player")
	if frames == 1 and args.size() >= 2:  # after the map has placed her at the start
		p.position = Vector2(int(args[0]) * 16 + 8, int(args[1]) * 16 + 14)
		dir = args[2] if args.size() >= 3 else ""
	if dir:
		if frames == 50: Input.action_press("move_" + dir)
		if frames == 52: Input.action_release("move_" + dir)
		if frames == 60: Input.action_press("attack")
		if frames == 61: Input.action_release("attack")
	return frames > (120 if dir else 90)
