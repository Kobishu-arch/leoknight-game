# Leoknight

A Zelda-like adventure through Forchach (Lech valley, Tyrol), starring a bard who
fights with her transverse flute. Made with Godot 4.7, in the style of *A Link to the Past*:
16×16 tiles, a Link-sized hero, soft round shapes.

This is an early prototype: a small test map, the bard walking around in it and playing her flute,
and warriors who guard their spots, charge when she comes close and poke her with spears.

## Play it

In the browser: **https://kobishu-arch.github.io/leoknight-game/** (rebuilt and published by
`.github/workflows/pages.yml` on every push to `main`, after the tests pass).

## Run it

Open the folder in Godot 4.7 and press **F5**, or from the terminal:

```bash
godot4 --path .
```

| Key | Action |
|---|---|
| W A S D / arrow keys | walk |
| Space | play the flute: a glowing note flies out in the direction she faces; one note beats a warrior |

A warrior's poke knocks her back; after three pokes she starts over at the beginning (no hearts on
screen yet).

The game renders at 320×180 and scales up 4× (1280×720 window).

## What is here

| Path | What |
|---|---|
| `scenes/main.tscn` | the test map; `scripts/world.gd` builds it from `maps/forchach_test.txt` |
| `scenes/player.tscn`, `scripts/player.gd` | the bard: movement, facing, animations, flute attack, ground / raised-meadow level |
| `scenes/warrior.tscn`, `scripts/warrior.gd` | the warrior enemy: idles, spots her ("!"), charges with his group, pokes, gives up; vanishes in a `puff.tscn` |
| `scenes/note.tscn`, `scripts/note.gd` | the flute's glowing note: halo, sparkle trail, wobble; fades out or bursts (`note_burst.tscn`) on what it hits |
| `scenes/sound_wave.tscn`, `scripts/sound_wave.gd` | the golden sound wave that sweeps out of the flute |
| `scripts/canopy.gd` | makes treetops see-through while the bard is behind them |
| `shaders/grade.gdshader` | colour grade over the whole picture: warm light, cool shadows, soft vignette |
| `art/bard/bard_animations.aseprite` | bard sprite (24×28): `idle_down`, `walk_*` and `play_*` for down, up, left, right |
| `art/warrior/warrior_animations.aseprite` | warrior sprite (32×36): `idle_down`, `walk_*` and `attack_*` for down, up, left, right |
| `art/fx/` | notes (12×12), their halo, the sparkle, the sound wave, the smoke puff and the alert mark |
| `art/bard/bard_sheet.png` + `.json` | sheet exported from Aseprite; `bard_frames.tres` is built from it |
| `art/tiles/terrain.png` | 16×16 tileset: grass, flowers, gravel, path, water, cliff wall and top, bridge, stairs |
| `art/props/` | clover bush, stone, stump, fence (4 variants), round tree, spruce |
| `art/bard/earlier/` | earlier sprite versions (not imported by Godot) |
| `art/ui/` | dialogue portraits (Leo, warrior) and 16×16 item icons (flute, lion head), from `tools/gen_ui.py` |
| `art/reference/` | concept sprites kept as models for new poses (not imported by Godot); see its README |
| `art/palettes/` | the concept palette for Aseprite |
| `tools/` | scripts that generate the characters (`bard_frames.py`, `warrior_frames.py`, shared `sprite_kit.py`), the tileset and props, the map and the SpriteFrames |
| `tests/` | headless test of movement, cliffs, flute and warriors; a motion check; screenshot and fight-recording helpers |

## The map

`maps/forchach_test.txt` holds two grids of the same size, separated by an empty line:

- **terrain:** `.` grass, `*` flowers, `=` path, `:` gravel, `~` water, `H` bridge, `^` raised meadow, `S` stairs
- **objects:** `.` none, `T` spruce, `o` leafy tree, `b` bush, `r` stone, `u` stump, `f` fence, `w` warrior, `@` player start

Gravel, path, water and cliffs are drawn on half-tile-shifted layers, so their borders are round
(see `tools/gen_map_art.py`). The last two rows of a raised meadow show as a cliff wall; stairs
(`S`) in the wall lead up. Edit the file directly, or change and rerun `python3 tools/gen_test_map.py`.

## Changing the art

- **Characters:** the frames come from `tools/bard_frames.py` and `tools/warrior_frames.py`;
  `python3 tools/build_sprite.py bard` (or `warrior`) rebuilds the `.aseprite` file, the sheet, Godot's
  SpriteFrames and the preview GIFs from it. For a hand fix,
  edit `art/bard/bard_animations.aseprite` instead, then export the sheet and rebuild the frames:

  ```bash
  aseprite -b art/bard/bard_animations.aseprite --list-tags --sheet art/bard/bard_sheet.png --sheet-type rows --sheet-columns 4 --data art/bard/bard_sheet.json --format json-array
  python3 tools/make_spriteframes.py bard
  ```

- **Effects** (notes, halo, sparkle, sound wave, smoke puff, alert mark): `python3 tools/gen_fx.py`.
- **Portraits and item icons:** `python3 tools/gen_ui.py` (portraits are cleaned up from `art/reference/ui/`).

- **Tiles and props:** `python3 tools/gen_map_art.py` (needs Pillow), then let Godot re-import
  (`godot4 --headless --path . --import`, or just open the editor). The PNGs can also be edited in
  Aseprite directly, but rerunning the script overwrites them.
- **Look at a spot of the map:** `godot4 --path . -s tests/shot.gd --write-movie /tmp/shot.png --fixed-fps 60 -- 57 20`
  writes frames of the view around map cell (57, 20); the last one shows it. Add `down`, `up`,
  `left` or `right` after the numbers to see her play the flute that way.

## Web build

`export_presets.cfg` has a single-threaded **Web** preset (runs on GitHub Pages without special
headers). To build it yourself (needs Godot's 4.7.2 export templates):

```bash
godot4 --headless --path . --export-release "Web" build/index.html
```

`tools/fetch_web_templates.py` fetches just the web templates; `tools/cachebust.py` makes sure
returning visitors get the newest build instead of Pages' ten-minute cache.

## Test

To watch a fight with the warriors: `godot4 --path . -s tests/demo_fight.gd` (add
`--write-movie /tmp/fight.png --fixed-fps 60` to record it).


```bash
godot4 --headless --path . -s tests/test_movement.gd
```

To check that movement is smooth on your monitor (opens a window, prints how far the bard
and the view move per frame; even steps mean smooth motion):

```bash
godot4 --path . -s tests/diag_motion.gd
```
