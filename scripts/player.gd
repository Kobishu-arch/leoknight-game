extends CharacterBody2D
## The bard: walks in eight directions with WASD or the arrow keys and plays the
## walk animation of the direction she faces (four directions, like Zelda).

@export var speed := 100.0

## "down", "up", "left" or "right"
var facing := "down"

@onready var sprite: AnimatedSprite2D = $Sprite


func _physics_process(_delta: float) -> void:
	var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = dir * speed
	move_and_slide()

	if dir == Vector2.ZERO:
		_stand()
	else:
		facing = _facing_for(dir)
		_play("walk_" + facing)


## Diagonals keep the current facing while it still matches one of the pressed keys,
## so walking diagonally does not flicker between two animations.
func _facing_for(dir: Vector2) -> String:
	var horizontal := "right" if dir.x > 0 else "left"
	var vertical := "down" if dir.y > 0 else "up"
	if absf(dir.x) > absf(dir.y) + 0.01:
		return horizontal
	if absf(dir.y) > absf(dir.x) + 0.01:
		return vertical
	return facing if facing in [horizontal, vertical] else horizontal


func _play(anim: String) -> void:
	if sprite.animation != anim or not sprite.is_playing():
		sprite.play(anim)


## Only "down" has its own idle animation; the other directions hold the walk frame
## with both feet together.
func _stand() -> void:
	if facing == "down":
		_play("idle_down")
	elif sprite.animation != "walk_" + facing or sprite.is_playing():
		sprite.animation = "walk_" + facing
		sprite.stop()
		sprite.frame = 1
