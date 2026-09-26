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
# Ghost Squad alone unbinds Point > Hide: its off-screen aiming broke with Hide
# on (James, 2026-09-26), so VRLF's off-screen press of pad B does nothing
# there and the pointer rides the stick to the edge instead.
#
# Otherwise every game gets the same remote: the pointer rolls through Dolphin's
# Tilt group, fed the gun's roll on the pad's triggers by VRLF's `tilt_roll`
# lanes, and the base carries that for all 70. Tilt rolls the emulated camera
# without touching the stick's aim, and VRLF takes the roll out of the motion
# it reports so Tilt puts it back into the accelerometer exactly once.
#
# History, because every route here was tried: IMU Point (`IMUIR/Enabled`) sat
# in the base from 2026-09-09, then on Dead Space alone, fed a roll-only lane
# that cost every game truthful gravity; with a true lane it doubles vertical
# aim, since nothing clamps its pitch. Tilt was first rejected on 2026-09-09 as
# Euler-summed with the pointer, which Dolphin stopped doing in 2020
# (bd067875e); what scrambled aim then was VRLF's own mirrored DSU frame, Tilt
# Forward/Backward bound, and raw accel saturating at 6 degrees.
#
# One knob that is not free if IMU Point ever comes back:
# IMUIR/Accelerometer Influence must stay above zero. Dolphin resets the IMU
# orientation to identity whenever the gyro input is unbound and VRLF samples
# a lane only while its gun is held, so every holster-and-regrab would leave a
# roll offset that only the correction removes.
#
# The full record is VRLF's docs/DECISIONS.md -> "Pointer roll rides Dolphin's
# Tilt".
EXTRAS = {
    "GHOSTSQUAD_P1": {"IR/Hide": ""},
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
