extends Area2D
## A glowing note from the bard's flute. It flies straight on with a little wobble, leaves a
## trail of sparkles, and fades out at the end of its range or bursts when it hits something.
## Like everything in a top-down world it collides at ground level (its position); the note
## itself is drawn higher up, in $Float, at the height of the flute.
## (It has to stay monitorable: with that off, Godot never pairs it with static bodies like rocks.)

const BURST := preload("res://scenes/note_burst.tscn")

@export var speed := 150.0
@export var life := 0.9

var direction := Vector2.DOWN
var age := 0.0
var done := false

@onready var sprite: Sprite2D = $Float/Sprite
@onready var glow: Sprite2D = $Float/Glow
@onready var trail: CPUParticles2D = $Float/Trail


func _ready() -> void:
	sprite.region_rect = Rect2(12 * (randi() % 2), 0, 12, 12)  # eighth note or beamed pair
	body_entered.connect(func(_body: Node) -> void: _finish(true))


func _process(delta: float) -> void:
	if done:
		return
	age += delta
	position += direction * speed * delta
	var across := Vector2(-direction.y, direction.x)
	sprite.position = (across * sin(age * 14.0) * 2.5).round()
	glow.position = sprite.position
	glow.scale = Vector2.ONE * (1.0 + 0.15 * sin(age * 18.0))
	sprite.self_modulate = Color.WHITE if int(age * 16.0) % 2 == 0 else Color(1.0, 1.0, 0.8)
	if age >= life:
		_finish(false)


func _finish(hit: bool) -> void:
	if done:
		return
	done = true
	set_deferred("monitoring", false)
	trail.emitting = false
	if hit:
		var burst: Node2D = BURST.instantiate()
		burst.position = position + $Float.position
		get_parent().add_child(burst)
	var tween := create_tween()
	tween.set_parallel()
	tween.tween_property(sprite, "scale", Vector2.ONE * (1.75 if hit else 1.25), 0.15)
	tween.tween_property(sprite, "modulate:a", 0.0, 0.15 if hit else 0.25)
	tween.tween_property(glow, "modulate:a", 0.0, 0.2)
	# let the last sparkles of the trail fade before the note goes away
	tween.chain().tween_interval(trail.lifetime)
	tween.tween_callback(queue_free)
