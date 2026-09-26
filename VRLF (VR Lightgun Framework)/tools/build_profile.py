"""Compose a VRLF Wiimote profile: our bindings, their calibration.

Dolphin applies a game-INI profile by REPLACING the controller's whole config
(InputConfig::LoadConfig), never by merging it over WiimoteNew.ini. So a
profile has to be a complete controller definition, which is why this starts
from the full base rather than emitting a calibration-only delta.
"""

import inikit

TRIO = ("IR/Total Yaw", "IR/Total Pitch", "IR/Vertical Offset")
EXTENSION_KEYS = ("Extension", "Extension/Attach MotionPlus")
CARRIED = TRIO + EXTENSION_KEYS

# Holding the Nunchuk hand's stick click (pad Back, Wii Minus) for 1.5 s unplugs
# the Nunchuk; holding it again plugs it back. Dolphin reads an attachment name
# OR an input expression for `Extension` (Attachments::LoadConfig), valued as
# the attachment index: 0 None, 1 Nunchuk. toggle() starts off, so `!` boots
# attached. hold() keeps an ordinary click on Minus from unplugging anything,
# though Dolphin cannot take back the Minus press a hold begins with.
NUNCHUK_TOGGLE = "!toggle(hold(`Back`, 1.5))"


def carried_value(key, value):
    """What a carried pack value becomes in our profile."""
    if key == "Extension" and value == "Nunchuk":
        return NUNCHUK_TOGGLE
    return value

# Per-game additions on top of the shared base, keyed by upstream stem. The P2
# transform below stops an entry from pointing player 2 at player 1's motion.
#
# Dead Space Extraction reads the remote's ROTATION for its alt fire, through
# Dolphin's IMU Point path. That path needs VRLF's roll-only
# orientation (`dsu_orientation: {mode: roll_only}`), which only
# VRLF's "Dead Space Extraction (Dolphin)" profile sends. Every other game runs
# on VRLF's "Dolphin" profile, which reports the gun's TRUE orientation so
# motion games (Wii Sports) read real gravity and real swings. IMU Point on a
# true orientation breaks aim: nothing clamps its pitch, so the gun's pitch
# lands on top of the stick aim. So the path is off in base/ and on here only.
#
# History: from 2026-09-09 to 2026-09-26 the path sat in base/ for all 70
# profiles, fed by a roll lock on every VRLF Wii controller. That cost every
# game truthful gravity, which broke motion titles. Split back out on
# 2026-09-26.
#
# Two routes were built and abandoned before the IMU Point path, and both look
# correct on paper, so they are recorded:
#
#   * The raw accelerometer alone never reaches the camera. With IMUIR off,
#     EmulateIMUCursor early-outs and nothing rotates the emulated IR camera,
#     so the game sees a tilted accelerometer over a level sensor bar.
#   * The Tilt group, bound to the DSU accelerometer, rotates the camera but is
#     composed with the stick-driven pointer as Euler angles, so rolling the
#     gun scrambled aim. Measured in the headset 2026-09-09.
#
# And one knob that is not free: IMUIR/Accelerometer Influence stays at
# Dolphin's default (2%). Zero cannot ship, because Dolphin resets the IMU
# orientation to identity whenever the gyro input is unbound and VRLF samples
# a lane only while its gun is held, so every holster-and-regrab would leave a
# roll offset that only the correction removes. The sway that knob was probed
# for is answered in VRLF's DSU server (the linear gate) instead.
#
# The full record is VRLF's docs/DECISIONS.md -> "Wii Remote rotation rides the
# IMU Point path, from a roll-only orientation".
EXTRAS = {
    "DEADSPACE_P1": {
        "IMUIR/Enabled": "True",
        # Zero, so sweeping the gun cannot add to the stick's horizontal aim.
        "IMUIR/Total Yaw": "0.",
    },
}

HEADER = """\
# Generated for the VR Lightgun Framework (VRLF) - this file is MODIFIED.
# Aim calibration derived from {source}.ini by Prof_gLX, PiperCalls,
# Ego_bizarro, Tovarichtch and Bratwurstmensch (GPL-3.0). Only
# IR/Total Yaw, IR/Total Pitch, IR/Vertical Offset and the Extension keys
# come from that file; every binding below is VRLF's pad + DSU mapping.
# Regenerate with tools/build_vrlf_profiles.py - do not hand-edit.
"""


def calibration_of(pack_text):
    """The keys worth carrying, or None if this profile has no calibration."""
    keys = inikit.parse_flat(pack_text)
    if not all(key in keys for key in TRIO):
        return None
    return {key: keys[key] for key in CARRIED if key in keys}


def build_profile(base_text, pack_text, source_stem, transform=None):
    """Compose one profile. `transform` rewrites EXTRAS values for player 2.

    Extras are inserted AFTER derive_p2 has already rewritten the base, so
    without this an extra naming DSUClient/0 would survive into P2's profile
    and player 2 would read player 1's motion. Passing derive_p2.derive_p2 here
    keeps the P1 -> P2 relationship stated in exactly one place.
    """
    calibration = calibration_of(pack_text)
    if calibration is None:
        raise ValueError("%s has no calibration to carry" % source_stem)

    extras = EXTRAS.get(source_stem, {})
    if transform is not None:
        extras = {key: transform(value) for key, value in extras.items()}

    # Extras override the base in place where the key already exists, so a base
    # that later grows its own Tilt/Angle cannot end up with two of them and let
    # Dolphin pick.
    overrides = {key: carried_value(key, value) for key, value in calibration.items()}
    overrides.update(extras)

    out, seen = [], set()
    for raw in base_text.splitlines():
        line = raw.rstrip()
        key = line.partition("=")[0].strip()
        if key in overrides:
            out.append("%s = %s" % (key, overrides[key]))
            seen.add(key)
        else:
            out.append(line)
    for key, value in overrides.items():
        if key not in seen:
            out.append("%s = %s" % (key, value))

    return HEADER.format(source=source_stem) + "\n".join(out) + "\n"
