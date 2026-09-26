# VRLF (VR Lightgun Framework) profiles

This folder is the accuracy pack's **per-game aim calibration** carried on top of
**VRLF's controller bindings**, for people playing Wii lightgun games in VR through the
[VR Lightgun Framework](https://store.steampowered.com/app/4711510/).

The rest of this repo maps the Wii pointer to a **mouse**, which is right for a Sinden or
Gun4IR. VRLF instead drives the pointer from a **virtual gamepad stick** (a VR controller →
ViGEmBus pad) and streams the Wiimote's accelerometer and gyro over **DSU**. Those two
mappings cannot coexist in one profile, and Dolphin applies a game profile by replacing the
controller's entire configuration — so installing the original accuracy pack silently
replaces a VRLF user's aim, buttons *and* motion on every covered game.

Everything here is generated: **the calibration is the original authors' work**, the
bindings are VRLF's, and nothing else crosses between them.

## Credit

Aim calibration by **Prof_gLX, PiperCalls, Ego_bizarro, Tovarichtch and Bratwurstmensch**,
from [ProfgLX/Dolphin-Lightguns-Accuracy-Inis](https://github.com/ProfgLX/Dolphin-Lightguns-Accuracy-Inis)
(GPL-3.0), synced at upstream commit `e5a6dce`. Every generated file names the upstream
profile it came from in its header and is marked as modified, per GPL-3.0 §5(a). If you use
this, credit them — the numbers are the hard part and they did that work.

Only five keys are taken from each upstream profile:

```
IR/Total Yaw          IR/Total Pitch          IR/Vertical Offset
Extension             Extension/Attach MotionPlus
```

## Install

1. Copy this folder's **`Config`** into your Dolphin user folder.
2. Copy this folder's **`GameSettings`** into the same place.

The Dolphin user folder is `%APPDATA%\Dolphin Emulator` for a normal install, or `User\`
inside the Dolphin folder for a portable one.

This **replaces** the equivalent files from `Accuracy and control mappings` — install one or
the other, not both. `Crosshair removal` from the original pack is unchanged and works with
either: copy its `Load` folder across and tick **Graphics → Advanced → Load Custom Textures**.

You also need VRLF's own Dolphin setup: the global mapping for each Wii Remote plus two DSU
servers on `127.0.0.1:26760` and `127.0.0.1:26761`. VRLF's
[`Dolphin` profile on the Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3788054425)
ships both presets (`VRLF-Dolphin-Base` for player 1, `VRLF-Dolphin-Base-P2` for player 2)
and lists the setup steps in its description.

**Use VRLF's `Dolphin` profile for every game except Dead Space Extraction**, and VRLF's
`Dead Space Extraction (Dolphin)` profile for that one. The main profile reports the gun's true
motion, which motion games such as Wii Sports need; the Dead Space profile locks it to roll for
the alt fire. See [Controller rotation](#controller-rotation).

**USA game IDs only.** The pack was built against USA discs; a PAL or NTSC-J disc has a
different game ID and simply gets no per-game profile, falling back to your global mapping.

## What you get

- **27 games** get a profile pair *and* a per-game INI, so they apply automatically.
- **8 more** have calibration that no game INI in the pack ever referenced. Their profiles
  are here, but you must select them by hand in Dolphin (right-click the game → Properties →
  Controllers, or the controller GUI):

  ```
  VRLF-ARCADESHOOT-P1     VRLF-BBHPRO-P1        VRLF-CHICKENRIOT-P1
  VRLF-CHICKENSHOOT-P1    VRLF-GUNBLADE-LAM-P1  VRLF-HeavyFireBA-P1
  VRLF-PIRATEBLAST-P1     VRLF-WILDWESTSHOOTOUT-P1
  ```

- **Both players.** Every game gets a `-P1` and a `-P2` profile and has its second Wiimote
  enabled. P2 is P1 on the second pad and the second DSU slot.
- **23 games are deliberately omitted.** Upstream's `GameSettings` points them at profiles
  that live in `Missing Accuracy values` and are never installed, which makes Dolphin raise
  *"Selected controller profile does not exist"* at boot. They have no calibration to carry,
  so they get nothing here and fall back to your global mapping.

- **Dead Space Extraction also gets controller rotation.** Its profile pair is the only one that
  enables Dolphin's IMU Point path, so turning the gun on its side reaches the game's alt fire.
  See below.

## Controller rotation

A real Wii Remote reports how it is *rotated* as well as where it points: the IR camera sees the
sensor bar's two dots, and the angle between them is the remote's roll. Dead Space Extraction
reads it for its alt fire; other games rotate their cursor with it or ignore it. The
accelerometer alone does not rotate the on-screen reticle: with `IMUIR/Enabled = False`
Dolphin's `EmulateIMUCursor` early-outs, so nothing in the accelerometer path rotates the
emulated IR camera.

Dolphin's **IMU Point** path does rotate it, so Dead Space's profile pair enables it:

```
IMUIR/Enabled   = True
IMUIR/Total Yaw = 0.
```

`Total Yaw` is zeroed so that sweeping the gun cannot add to the horizontal aim the stick is
already driving. There is no equivalent clamp for pitch, and the rotation also enters Dolphin's
camera transform un-negated where the Tilt group's angle enters negated. Both are answered on
the VRLF side, by a field that makes the lane report a mirrored, roll-only orientation:

```json
"dsu_orientation": { "mode": "roll_only", "invert": true }
```

Only VRLF's `Dead Space Extraction (Dolphin)` profile carries it. Played through the main
`Dolphin` profile, this pair puts the gun's pitch on top of the stick aim and rotates the reticle
the wrong way.

**Why only Dead Space.** From `vrlf-v1.1` every profile here enabled IMU Point, fed by a roll lock
on every VRLF Wii controller. The lock costs the lane its truthful gravity, which broke games
that read real motion (Wii Sports). So the main profile went back to true motion, IMU Point went
back to one game, and the roll lock moved to a profile of its own.

**Dolphin's Tilt group was tried first and does not work for this.** Tilt is summed with the
stick-driven pointer as *Euler angles* (`GetRotationalMatrix(-tilt - swing - cursor)`), so roll
re-frames the pitch axis and aim scrambles the moment the gun is rolled. The IMU rotation is
composed by multiplication instead and cannot disturb the pointer. If you are tempted by the
Tilt route, that is why it is not here.

**Shake and Swing deliberately get no simulation binding.** Games read those from the
accelerometer values directly, so a simulation binding would add synthetic spikes on top of the
real ones, and Swing would move the emulated camera as well.

**Point > Hide stays on Button B here too**, exactly as in every other profile: VRLF presses pad B
as aim leaves the screen and Dolphin blanks the pointer. Dead Space reloads on a shake rather than
off screen, and the pair had Hide unbound for one build before going straight back, so the whole
set behaves the same off screen.

**Sway on fast moves is answered on the VRLF side.** Hand acceleration reaches Dolphin's
accelerometer correction (`IMUIR/Accelerometer Influence`, left at its default of 2%) and used to
add a little vertical movement on a fast sweep. The Dead Space profile expresses that acceleration in the
gun's own heading and gates it under the same field's `linear_gate` (m/s²), so a
sweep never reaches the correction while a reload shake still does. Raise the number if sway is
still visible, lower it if reload shakes stop registering. Do not zero the influence instead:
Dolphin restarts the IMU orientation from identity whenever the gyro input is unbound, so without
the correction every gun pickup would leave the reticle rotation offset for the rest of the session.

To scope a setting to one game instead of the whole set, add it to `EXTRAS` in
`tools/build_profile.py` and regenerate. Dead Space's IMU Point keys live there.

## Which VRLF gun layout these assume

The committed profiles target the **combined** layout — one gun (a Wii Zapper) carrying the
Wii Remote and Nunchuk together on a single ViGEm pad.

If you run the **split** layout instead — Remote and Nunchuk as two separate VRLF guns, each
on its own pad — the calibration is identical (it describes the game, not your hardware) but
the bindings are not: split profiles name their pads explicitly, as
`` Nunchuk/Buttons/C = `XInput/1/Gamepad:Shoulder L` ``. Regenerate the whole set against your
own base in one command; see below. You need one layout or the other, never both.

## Regenerating

Committed output means you do not need Python to use this. If you have your own bindings and
want the calibration applied to *them*:

```
cd "VRLF (VR Lightgun Framework)/tools"
python build_vrlf_profiles.py --base /path/to/your-P1.ini
python build_vrlf_profiles.py --verify
```

`--base` takes a Dolphin Wiimote profile (a file with a `[Profile]` section). By default
player 2 is derived from it — the same bindings on the next pad and the next DSU slot.

**If your layout spreads one Wiimote across several pads, pass `--base-p2` as well.** Player 2
there is not player 1 shifted by one, so deriving it would point half the controls at player
1's hardware:

```
python build_vrlf_profiles.py --base your-Split-P1.ini --base-p2 your-Split-P2.ini
python build_vrlf_profiles.py --base your-Split-P1.ini --base-p2 your-Split-P2.ini --verify
```

`--verify` re-reads the emitted tree and checks that no binding drifted from your base, that
every calibration value matches upstream, and that every profile a game INI references
actually exists.

Run the tests with `python -m unittest discover -p "test_*.py"` from `tools/`.
