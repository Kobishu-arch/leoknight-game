extends CharacterBody2D
## The bard: walks in eight directions with WASD or the arrow keys and plays the
## walk animation of the direction she faces (four directions, like Zelda).
## Space plays the flute: she stands still for a moment and a glowing note flies out.

const NOTE := preload("res://scenes/note.tscn")
const WAVE := preload("res://scenes/sound_wave.tscn")
const ATTACK_TIME := 0.36  # length of the play_* animation
const NOTE_AT := 0.12      # when the flute reaches her lips
## where the note starts on the ground (from her feet; it is drawn 12 px higher, at the flute)
## and where it flies, per facing
const NOTE_FROM := {
	"down": [Vector2(-3, 6), Vector2.DOWN], "up": [Vector2(6, -2), Vector2.UP],
	"left": [Vector2(-12, -1), Vector2.LEFT], "right": [Vector2(12, -1), Vector2.RIGHT],
}

@export var speed := 70.0

## "down", "up", "left" or "right"
var facing := "down"
## 0 on the ground, 1 up on the raised meadow (decides which cliff walls stop her)
var level := 0
## set by the world: level of the cell at a position, or -1 to keep the current one
var level_at: Callable
var attack_left := 0.0
var note_fired := false

@onready var sprite: AnimatedSprite2D = $Sprite


# Moving every rendered frame (not only on the 60 Hz physics ticks) keeps the motion
# smooth on monitors faster than 60 Hz; the camera follows in the same step.
func _process(delta: float) -> void:
	if attack_left > 0.0:
		attack_left -= delta
		if not note_fired and attack_left <= ATTACK_TIME - NOTE_AT:
			note_fired = true
			_fire_note()
		if attack_left > 0.0:
			return
	if Input.is_action_just_pressed("attack"):
		attack_left = ATTACK_TIME
		note_fired = false
		velocity = Vector2.ZERO
		sprite.play("play_" + facing)
		return

	var dir := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = dir * speed
	move_and_slide()
	_update_level()

	if dir == Vector2.ZERO:
		_stand()
	else:
		facing = _facing_for(dir)
		_play("walk_" + facing)


func _update_level() -> void:
	if not level_at.is_valid():
		return
	var l: int = level_at.call(global_position)
	if l >= 0:
		level = l
	collision_mask = _walls()


## collision layers: 1 trees, rocks, map edge; 2 cliff walls seen from below;
## 3 cliff edges seen from above; 4 water (notes fly over it, she cannot walk into it).
## She herself is on layer 5, so her own notes fly through her.
func _walls() -> int:
	return 1 | (4 if level == 1 else 2) | 8


func _fire_note() -> void:
	var note: Area2D = NOTE.instantiate()
	note.position = position + NOTE_FROM[facing][0]
	note.direction = NOTE_FROM[facing][1]
	note.collision_mask = _walls() & ~8
	get_parent().add_child(note)
	var wave: Sprite2D = WAVE.instantiate()
	wave.position = note.position + Vector2(0, -12)
	wave.direction = note.direction
	get_parent().add_child(wave)


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
