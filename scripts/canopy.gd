extends Area2D
## Fades a treetop while the bard is behind it, so she never gets lost under a tree.
## The area covers the crown above the trunk; only the bard (collision layer 5) triggers it.

@export var faded_alpha := 0.45

var inside := 0

@onready var sprite: CanvasItem = get_parent().get_node("Sprite")


func _ready() -> void:
	body_entered.connect(func(_body: Node) -> void:
		inside += 1
		_fade(faded_alpha))
	body_exited.connect(func(_body: Node) -> void:
		inside -= 1
		if inside == 0:
			_fade(1.0))


func _fade(alpha: float) -> void:
	create_tween().tween_property(sprite, "modulate:a", alpha, 0.2)
