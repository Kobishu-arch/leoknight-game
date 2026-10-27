extends SceneTree
## Records a little fight for looking at the enemies: the bard stands west of the warriors near
## the pasture, they spot her and charge, and she plays notes at them.
## Run from the project root:  godot4 --path . -s tests/demo_fight.gd --write-movie /tmp/fight.png --fixed-fps 60

var main: Node2D
var p: CharacterBody2D
var frames := 0


func _initialize() -> void:
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)


func _process(_delta: float) -> bool:
	frames += 1
	if frames == 1:
		p = main.get_node("Objects/Player")
		var warriors: Array = p.get_parent().get_children().filter(func(n: Node) -> bool: return n.has_method("hit"))
		var goal := Vector2(45, 40) * 16
		warriors.sort_custom(func(a: Node2D, b: Node2D) -> bool: return a.position.distance_to(goal) < b.position.distance_to(goal))
		p.position = warriors[0].position + Vector2(-84, 0)
		p.facing = "right"
	if frames in [60, 95, 130, 165, 200, 235]:
		var near: Array = p.get_parent().get_children().filter(func(n: Node) -> bool: return n.has_method("hit") and not n.dead)
		near.sort_custom(func(a: Node2D, b: Node2D) -> bool: return a.position.distance_to(p.position) < b.position.distance_to(p.position))
		if near:
			p.facing = p._facing_for(near[0].position - p.position)
		Input.action_press("attack")
	if frames in [61, 96, 131, 166, 201, 236]:
		Input.action_release("attack")
	return frames > 300
