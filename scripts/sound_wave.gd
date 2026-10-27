extends Sprite2D
## The golden sound wave that sweeps out of the flute when the bard plays: three frames that
## grow and fade while the wave drifts a little in the playing direction.

var direction := Vector2.RIGHT


func _ready() -> void:
	rotation = direction.angle()
	var tween := create_tween()
	tween.set_parallel()
	tween.tween_property(self, "position", position + direction * 10.0, 0.24)
	tween.tween_method(func(t: float) -> void: frame = mini(int(t * 3.0), 2), 0.0, 0.999, 0.24)
	tween.tween_property(self, "modulate:a", 0.0, 0.12).set_delay(0.12)
	tween.chain().tween_callback(queue_free)
