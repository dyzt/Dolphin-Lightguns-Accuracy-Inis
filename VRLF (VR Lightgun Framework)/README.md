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

**This release and VRLF's `Dolphin` profile must match.** Wii B and Nunchuk Z are on the pad's
stick clicks here, and the triggers carry the gun's roll. Play it with the `Dolphin` profile from
the same VRLF release, and update the global mapping (vrlf-mods: Emulators > Dolphin) too: an
older mapping still has B and Z on the triggers, so rolling the gun would press them.

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

- **Unplug the Nunchuk from the headset.** Hold the Nunchuk hand's stick click for 1.5 s to
  unplug it, and again to plug it back. Every profile and both base presets set `Extension` to
  the input expression `` !toggle(hold(`Back`, 1.5)) `` instead of `Nunchuk`; a game boots with
  it plugged in. A quick click is still Minus, and a hold presses Minus as it starts.

- **The pointer rolls with the gun, in every game.** Turn the gun on its side and the emulated
  remote rolls with it: the Wii menu hand turns, and Dead Space Extraction reaches its alt fire.
  See below.

## Controller rotation

A real Wii Remote reports how it is *rotated* as well as where it points: the IR camera sees the
sensor bar's two dots, and the angle between them is the remote's roll. Games turn their cursor
with it, and Dead Space Extraction reads it for its alt fire. The accelerometer alone does not
rotate the emulated IR camera, so something has to.

Dolphin's **Tilt** group does, fed the gun's roll on the pad's two analog triggers:

```
Tilt/Left  = `Trigger L`
Tilt/Right = `Trigger R`
Tilt/Angle = 90.
Buttons/B         = `Thumb R`
Nunchuk/Buttons/Z = `Thumb L`
```

Tilt rolls the camera about its own axis, separately from Point (Dolphin `bd067875e`, 2020), so
the stick keeps the aim. It also rotates the accelerometer it hands the game, so VRLF takes the
roll out of the motion it reports and Tilt puts it back once:

```json
"dsu_orientation": { "mode": "tilt_roll", "max_deg": 90 }
```

`max_deg` must equal `Tilt/Angle`. Only Tilt Left/Right are bound: Forward/Backward would put the
gun's pitch on top of the stick aim.

**Routes tried first, and why they are not here.** IMU Point (`IMUIR/Enabled`) rotates the camera
too, but it takes the gun's whole orientation and nothing clamps its pitch, so it doubles
vertical aim unless the lane is locked to roll, which costs every game its true gravity
(`vrlf-v1.1` did that). Tilt was first rejected as Euler-summed with the pointer; what actually
scrambled aim then was VRLF's own mirrored motion frame, Tilt Forward/Backward bound, and raw
accelerometer values saturating at 6 degrees.

**Shake and Swing deliberately get no simulation binding.** Games read those from the
accelerometer values directly, so a simulation binding would add synthetic spikes on top of the
real ones, and Swing would move the emulated camera as well.

**Point > Hide stays on Button B**: VRLF presses pad B as aim leaves the screen and Dolphin
blanks the pointer. Ghost Squad is the one exception, with Hide unbound: its off-screen aiming
broke with it on.

To scope a setting to one game instead of the whole set, add it to `EXTRAS` in
`tools/build_profile.py` and regenerate. Ghost Squad's unbound Hide is the only entry.

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
