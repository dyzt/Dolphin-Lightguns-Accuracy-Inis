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

You also need VRLF's own Dolphin setup — the global `WiimoteNew.ini` mapping plus two DSU
servers on `127.0.0.1:26760` and `127.0.0.1:26761`. See the `Wii (DSU)` profile's
`INSTRUCTIONS.txt` in VRLF.

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

## Regenerating

Committed output means you do not need Python to use this. If you have your own bindings and
want the calibration applied to *them*:

```
cd "VRLF (VR Lightgun Framework)/tools"
python build_vrlf_profiles.py --base /path/to/your/profile.ini
python build_vrlf_profiles.py --verify
```

`--base` takes a Dolphin Wiimote profile (a `[Profile]` section). The P2 variant is derived
from it automatically. `--verify` re-reads the emitted tree and checks that no binding
drifted from your base, that every calibration value matches upstream, and that every
profile a game INI references actually exists.

Run the tests with `python -m unittest discover -p "test_*.py"` from `tools/`.
