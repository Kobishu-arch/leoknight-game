extends CharacterBody2D
## A warrior guarding his spot. He wanders a little around home; when the bard comes within
## aggro range he shouts "!" and runs at her, pokes her with his spear when he is close, and
## walks back home when she gets away. When he spots her, the warriors near him join in.
## One note from the flute is enough to beat him.

enum State { IDLE, WANDER, CHASE, ATTACK, RETURN }

const PUFF := preload("res://scenes/puff.tscn")
const WIND_UP := 0.22       # attack_* frame 1; the poke lands at the end of it
const ATTACK_TIME := 0.5    # length of attack_*
const COOLDOWN := 0.6       # pause after a poke before the next one

@export var aggro_range := 64.0
## warriors within this distance of one who spots the bard join the chase
@export var rally_range := 72.0
@export var give_up_range := 150.0
@export var poke_range := 18.0
@export var walk_speed := 22.0
@export var run_speed := 50.0

var state := State.IDLE
var home := Vector2.ZERO
## the bard; set by the world when it places the warrior
var target: Node2D
var facing := "down"
var timer := 0.0
var cooldown := 0.0
var wander_to := Vector2.ZERO
var poked := false
var dead := false

@onready var sprite: AnimatedSprite2D = $Sprite
@onready var alert: Sprite2D = $Alert


func _ready() -> void:
	home = position
	timer = randf_range(0.5, 2.5)
	alert.visible = false


func _process(delta: float) -> void:
	if dead:
		return
	timer -= delta
	cooldown -= delta
	var to_bard := target.global_position - global_position if target else Vector2(9999, 9999)
	var dist := to_bard.length()
	var sees := dist <= aggro_range and _bard_reachable()
	velocity = Vector2.ZERO
	match state:
		State.IDLE:
			if sees:
				_aggro()
			elif timer <= 0.0:
				wander_to = home + Vector2(randf_range(-24, 24), randf_range(-16, 16))
				state = State.WANDER
				timer = 2.5
		State.WANDER:
			if sees:
				_aggro()
			elif position.distance_to(wander_to) < 3.0 or timer <= 0.0:
				_rest()
			else:
				velocity = position.direction_to(wander_to) * walk_speed
		State.CHASE:
			if dist > give_up_range or not _bard_reachable():
				state = State.RETURN
			elif dist <= poke_range and cooldown <= 0.0:
				_start_poke(to_bard)
			elif dist > poke_range * 0.8:
				velocity = to_bard.normalized() * run_speed
		State.ATTACK:
			if not poked and timer <= ATTACK_TIME - WIND_UP:
				poked = true
				if dist <= poke_range + 6.0 and target.has_method("hurt"):
					target.hurt(global_position)
			if timer <= 0.0:
				state = State.CHASE
				cooldown = COOLDOWN
		State.RETURN:
			if sees:
				_aggro()
			elif position.distance_to(home) < 3.0:
				_rest()
			else:
				velocity = position.direction_to(home) * walk_speed
	move_and_slide()
	_animate()


## Hit by the bard's flute: one note is enough.
func hit() -> void:
	if dead:
		return
	dead = true
	alert.visible = false
	$Feet.set_deferred("disabled", true)
	var puff: Node2D = PUFF.instantiate()
	puff.position = position + Vector2(0, -8)
	get_parent().add_child(puff)
	var tween := create_tween()
	tween.tween_property(sprite, "modulate", Color(4, 4, 4, 1), 0.05)
	tween.tween_property(sprite, "modulate", Color(1, 1, 1, 0), 0.2)
	tween.tween_callback(queue_free)


## Warriors stay on the ground; the bard up on the raised meadow is out of their reach.
func _bard_reachable() -> bool:
	return target != null and target.get("level") == 0


func _aggro(rally := true) -> void:
	if state in [State.CHASE, State.ATTACK]:
		return
	state = State.CHASE
	alert.visible = true
	alert.scale = Vector2(0.5, 0.5)
	var tween := create_tween()
	tween.tween_property(alert, "scale", Vector2.ONE, 0.12)
	tween.tween_interval(0.6)
	tween.tween_callback(func() -> void: alert.visible = false)
	if rally:
		for other in get_parent().get_children():
			if other != self and other.has_method("hit") and not other.dead \
					and other.position.distance_to(position) <= rally_range:
				other._aggro(false)


func _rest() -> void:
	state = State.IDLE
	timer = randf_range(1.0, 3.0)


func _start_poke(to_bard: Vector2) -> void:
	state = State.ATTACK
	timer = ATTACK_TIME
	poked = false
	facing = _facing_for(to_bard)
	sprite.play("attack_" + facing)


func _facing_for(dir: Vector2) -> String:
	if absf(dir.x) > absf(dir.y):
		return "right" if dir.x > 0 else "left"
	return "down" if dir.y > 0 else "up"


func _animate() -> void:
	if state == State.ATTACK:
		return
	if velocity.length() > 0.1:
		facing = _facing_for(velocity)
		var anim := "walk_" + facing
		if sprite.animation != anim or not sprite.is_playing():
			sprite.play(anim)
		sprite.speed_scale = 1.6 if state == State.CHASE else 1.0
	elif facing == "down":
		if sprite.animation != "idle_down":
			sprite.play("idle_down")
	elif sprite.animation != "walk_" + facing or sprite.is_playing():
		sprite.animation = "walk_" + facing
		sprite.stop()
		sprite.frame = 1
