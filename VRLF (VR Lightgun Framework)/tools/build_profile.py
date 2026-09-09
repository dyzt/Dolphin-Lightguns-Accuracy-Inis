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
# Dead Space Extraction reads the remote's ROTATION, not just its pointer, for
# its alt fire. What works is Dolphin's IMU Point path, fed a roll-only,
# mirrored orientation from VRLF (`dsu_orientation: {mode: roll_only,
# invert: true}`). Two routes were built and abandoned first, and both look
# correct on paper, so they are recorded:
#
#   * The raw accelerometer alone never reaches the camera. With IMUIR off,
#     EmulateIMUCursor early-outs and nothing rotates the emulated IR camera,
#     so the game sees a tilted accelerometer over a level sensor bar.
#   * The Tilt group, bound to the DSU accelerometer, rotates the camera but is
#     composed with the stick-driven pointer as Euler angles, so rolling the
#     gun scrambled aim. Measured in the headset 2026-09-09.
#
# The full record is VRLF's docs/DECISIONS.md -> "Wii Remote rotation rides the
# IMU Point path, from a roll-only orientation".
EXTRAS = {
    "DEADSPACE_P1": {
        # The IMU rotation enters Dolphin's camera transform as
        # `extra_rotation * ...`, a real composition, so unlike Tilt it cannot
        # disturb the pointer. Two consequences are handled on the VRLF side,
        # not here: nothing clamps the IMU's pitch, and the rotation enters
        # with the opposite sign to Tilt's. That is why VRLF sends a roll-only,
        # mirrored orientation on this lane.
        "IMUIR/Enabled": "True",
        # Zero, so sweeping the gun cannot add to the stick's horizontal aim.
        "IMUIR/Total Yaw": "0.",
        # Deliberately NOT set here, and worth knowing why:
        #
        #   IMUIR/Accelerometer Influence stays at Dolphin's default (2%). It
        #   was zeroed for one build as a probe for the slight vertical sway a
        #   fast sideways sweep adds, and zero cannot ship: Dolphin resets the
        #   IMU orientation to identity whenever the gyro input is unbound, and
        #   VRLF samples a lane only while its gun is held, so every bind and
        #   every holster-and-regrab leaves a roll offset that only the
        #   accelerometer correction ever removes. The sway is hand
        #   acceleration reaching that correction; the fix for it is in VRLF's
        #   DSU server, not in this file.
        #
        #   IR/Hide stays exactly as the base binds it (Button B), like every
        #   other profile. It was unbound here for one build on the theory that
        #   a shake-reload game had no use for it, and went straight back so the
        #   whole set behaves the same off screen.
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
    overrides = dict(calibration)
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
