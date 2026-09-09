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
# Tilt is driven straight off the DSU accelerometer VRLF already streams. The
# accelerometer's X axis IS gravity's projection on the remote's left/right
# axis, i.e. sin(roll), which is exactly what Tilt wants - and Z gives
# forward/back tilt for free. Nothing on the pad had a spare analog pair for a
# second axis, so this covers strictly more than a pad route could.
#
# Note this binds a DEVICE input to a motion-SIMULATION group, which is not the
# usual pairing. Shake and Swing deliberately get no such binding: games read
# those from the accelerometer values directly, so a simulation binding would
# add synthetic spikes on top of the real ones (and Swing also feeds
# GetTransformation, so it would move the camera too). Tilt is the exception
# only because a pointer game reads reticle ROTATION from the IR dot angle, and
# nothing in the accelerometer path rotates the emulated camera.
# THE SCALE IS LOAD-BEARING. Dolphin's DSU client builds these inputs with
# `accel_scale = 1.0 / GRAVITY_ACCELERATION` and AccelerometerInput::GetState()
# returns `value / m_range`, so `Accel Left` reads 9.81 at 1 g, not 1.0. That is
# right for the IMUAccelerometer group, which wants m/s^2, and wrong for Tilt,
# which wants a normalised 0..1 stick-like input. Bound raw, the axis saturates
# at about 6 degrees of real roll and every hand acceleration slams the emulated
# camera around. Multiplying by 1/9.81 puts 1 g back at 1.0, so a full 90 degree
# roll is full deflection and the mapping is 1:1 at the extremes.
ACCEL_TO_UNIT = "0.102"  # 1 / GRAVITY_ACCELERATION

EXTRAS = {
    "DEADSPACE_P1": {
        "Tilt/Left": "`DSUClient/0/vrlf-wiimotes:Accel Left` * " + ACCEL_TO_UNIT,
        "Tilt/Right": "`DSUClient/0/vrlf-wiimotes:Accel Right` * " + ACCEL_TO_UNIT,
        "Tilt/Forward": "`DSUClient/0/vrlf-wiimotes:Accel Forward` * " + ACCEL_TO_UNIT,
        "Tilt/Backward": "`DSUClient/0/vrlf-wiimotes:Accel Backward` * " + ACCEL_TO_UNIT,
        # Gravity is what the axis measures, so it only reads a real angle while
        # the gun is still. A hand acceleration adds to it, and this dead zone is
        # what stops that jitter reaching the emulated IR camera at rest.
        "Tilt/Dead Zone": "15.",
        # Full deflection = 90 degrees, matching the roll that saturates the axis.
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
