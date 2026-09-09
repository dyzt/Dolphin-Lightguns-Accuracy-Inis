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
# its alt fire. Getting that to Dolphin took three attempts, and the two dead
# ends are recorded here because both look correct on paper:
#
#   * The raw accelerometer alone cannot do it. With IMUIR disabled,
#     EmulateIMUCursor early-outs and the IMU never rotates the emulated IR
#     camera, while GetTotalAcceleration still reports the tilt. The game sees a
#     remote whose accelerometer says 90 degrees and whose sensor bar is level.
#   * The Tilt group moves both halves together, but Dolphin sums it with the
#     stick-driven pointer as EULER ANGLES
#     (`GetRotationalMatrix(-tilt - swing - cursor)`), so roll re-frames the
#     pitch axis and aim scrambles the moment the gun is rolled. Measured in the
#     headset 2026-09-09.
#
# What works is the IMU Point path below. That rotation enters as
# `extra_rotation * ...`, a real composition, so it cannot disturb the pointer.
EXTRAS = {
    "DEADSPACE_P1": {
        # Rotation comes through the IMU POINT path, not the Tilt group.
        #
        # Tilt was tried first and had to be abandoned: Dolphin sums it with the
        # stick-driven pointer as EULER ANGLES
        # (`GetRotationalMatrix(-tilt - swing - cursor)`), so roll sits between
        # yaw and pitch in the resulting product and re-frames the pitch axis.
        # Aim scrambled as soon as the gun was rolled. Measured in the headset
        # 2026-09-09.
        #
        # The IMU rotation instead enters as `extra_rotation * ...`, a real
        # composition, so it cannot disturb the pointer. Two consequences that
        # are handled on the VRLF side, not here:
        #   * `extra_rotation` is NOT negated where the tilt angle is, so a
        #     truthful orientation turns the reticle backwards.
        #   * Total Yaw clamps the IMU's yaw but nothing clamps its pitch, so a
        #     truthful orientation doubles vertical aim.
        # VRLF's `dsu_orientation: {mode: roll_only, invert: true}` sends a
        # mirrored roll-only orientation on this lane, which answers both.
        "IMUIR/Enabled": "True",
        # Zero, so sweeping the gun cannot add to the stick's horizontal aim.
        "IMUIR/Total Yaw": "0.",
        # DIAGNOSTIC / candidate fix, 2026-09-09. Dolphin's complementary filter
        # corrects PITCH AND ROLL from the accelerometer, and its weight is
        # applied per update rather than scaled by elapsed time, so it has far
        # more authority than "2%" reads. VRLF's DSU server rotates world-space
        # linear acceleration into the local frame using the REPORTED
        # orientation, and a roll-only orientation has yaw pinned to zero - so a
        # horizontal sweep leaks into that frame's forward/back axis by
        # sin(yaw offset), Dolphin reads fore/aft acceleration, and corrects
        # pitch. That is vertical sway whose sign follows the sweep direction.
        #
        # Zero removes the only path from hand acceleration to the emulated
        # camera. Affordable here because the gyro this lane sends is now the
        # exact derivative of the roll angle it reports, so integration alone
        # reproduces the roll; what is given up is drift correction over a long
        # session.
        "IMUIR/Accelerometer Influence": "0.",
        # No off-screen reload in this game, so Point > Hide is pure cost here.
        # VRLF's aim_zone block presses pad B whenever aim leaves the screen,
        # and every other Wii profile wants that to blank the pointer. Dead
        # Space instead reloads on a shake, so all hiding did was drop the
        # pointer at the screen edge and re-acquire it from centre on the way
        # back in. Unbound rather than removed: the base still ships the line,
        # and an empty expression is how Dolphin spells "never true". `Button B`
        # is bound to nothing else in the base, so nothing else changes.
        "IR/Hide": "",
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
