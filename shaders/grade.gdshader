shader_type canvas_item;
// Gentle colour grade over the whole picture: a little more saturation and contrast,
// warm light, cool shadows and a soft vignette - the cosy mood of the concept art.

uniform sampler2D screen : hint_screen_texture, filter_nearest;
uniform float saturation = 1.08;
uniform float contrast = 1.05;
uniform float warmth = 0.05;
uniform float shadow_cool = 0.06;
uniform float vignette = 0.28;

void fragment() {
	vec3 c = texture(screen, SCREEN_UV).rgb;
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(vec3(l), c, saturation);
	c = (c - 0.5) * contrast + 0.5;
	c += vec3(warmth, warmth * 0.5, -warmth * 0.5) * smoothstep(0.35, 1.0, l);
	c += vec3(-shadow_cool * 0.5, 0.0, shadow_cool) * (1.0 - smoothstep(0.0, 0.45, l));
	vec2 d = (SCREEN_UV - 0.5) * vec2(1.25, 1.0);
	c *= 1.0 - vignette * smoothstep(0.3, 0.8, length(d));
	COLOR = vec4(clamp(c, 0.0, 1.0), 1.0);
}
