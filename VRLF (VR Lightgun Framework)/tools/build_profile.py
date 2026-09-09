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

# Per-game additions on top of the shared base, keyed by upstream stem.
#
# Scoped deliberately rather than folded into the base: everything here changes
# how the emulated remote BEHAVES, not just how it is calibrated, and a setting
# that rotates the remote must not reach the games that never asked to be
# rotated.
#
# Dead Space Extraction reads the remote's ROTATION, not just its pointer. The
# accelerometer alone cannot deliver that under Dolphin: with IMUIR disabled,
# EmulateIMUCursor early-outs and the IMU never rotates the emulated IR camera,
# while GetTotalAcceleration still reports the tilt. The game then sees a remote
# whose accelerometer says 90 degrees and whose sensor bar is level, loses
# pointer lock, and hides the crosshair. The Tilt group is the one input that
# moves both halves together: m_tilt_state.angle feeds GetTransformation, which
# the IR camera and the accelerometer both read.
#
# VRLF drives these two axes from the physical gun's roll, which is why its Wii
# profile moves the B and Z bindings to Thumb R / Thumb L - LT and RT have to be
# free for the axis.
EXTRAS = {
    "DEADSPACE_P1": {
        "Tilt/Left": "`Trigger L`",
        "Tilt/Right": "`Trigger R`",
        # Full pull = 90 degrees, matching the roll at which VRLF's axis
        # saturates, so the emulated remote tracks the real gun 1:1.
        "Tilt/Angle": "90.",
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


def build_profile(base_text, pack_text, source_stem):
    calibration = calibration_of(pack_text)
    if calibration is None:
        raise ValueError("%s has no calibration to carry" % source_stem)

    # Extras override the base in place where the key already exists, so a base
    # that later grows its own Tilt/Angle cannot end up with two of them and let
    # Dolphin pick.
    overrides = dict(calibration)
    overrides.update(EXTRAS.get(source_stem, {}))

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
