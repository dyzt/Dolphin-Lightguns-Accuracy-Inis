import os
import unittest
from unittest import mock

import build_profile
import derive_p2
import inikit


BASE = (
    "[Profile]\n"
    "Device = XInput/0/Gamepad\n"
    "Buttons/A = `Button A`\n"
    "IR/Up = `Left Y-`\n"
    "IR/Hide = `Button B`\n"
    "IR/Total Yaw = 16.\n"
    "IR/Total Pitch = 12.\n"
    "IR/Vertical Offset = 15.\n"
    "IMUIR/Enabled = True\n"
    "IMUIR/Total Yaw = 0.\n"
    "Extension = Nunchuk\n"
)

PACK = (
    "[Profile]\n"
    "Device = DInput/0/Keyboard Mouse\n"
    "Buttons/A = `Click 1`\n"
    "IR/Up = `Cursor Y-`\n"
    "IR/Total Yaw = 19.0\n"
    "IR/Total Pitch = 19.0\n"
    "IR/Vertical Offset = 15.0\n"
    "Shake/X = SPACE\n"
    "Extension/Attach MotionPlus = False\n"
)

PACK_NO_CALIBRATION = "[Profile]\nDevice = DInput/0/Keyboard Mouse\nButtons/A = `Click 1`\n"

BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "base")
SHIPPED_BASES = ("VRLF-Dolphin-Base-P1.ini", "VRLF-Dolphin-Base-P2.ini")


class TestCalibrationOf(unittest.TestCase):
    def test_returns_none_without_the_trio(self):
        self.assertIsNone(build_profile.calibration_of(PACK_NO_CALIBRATION))

    def test_extracts_the_trio_and_extension_keys(self):
        self.assertEqual(
            build_profile.calibration_of(PACK),
            {
                "IR/Total Yaw": "19.0",
                "IR/Total Pitch": "19.0",
                "IR/Vertical Offset": "15.0",
                "Extension/Attach MotionPlus": "False",
            },
        )


class TestBuildProfile(unittest.TestCase):
    def setUp(self):
        self.text = build_profile.build_profile(BASE, PACK, "HOTDOverkill_P1")
        self.keys = inikit.parse_flat(self.text)

    def test_calibration_is_taken_from_the_pack(self):
        self.assertEqual(self.keys["IR/Total Yaw"], "19.0")
        self.assertEqual(self.keys["IR/Total Pitch"], "19.0")
        self.assertEqual(self.keys["IR/Vertical Offset"], "15.0")

    def test_extension_motionplus_is_carried(self):
        self.assertEqual(self.keys["Extension/Attach MotionPlus"], "False")

    def test_bindings_stay_ours(self):
        self.assertEqual(self.keys["Device"], "XInput/0/Gamepad")
        self.assertEqual(self.keys["Buttons/A"], "`Button A`")
        self.assertEqual(self.keys["IR/Up"], "`Left Y-`")

    def test_ir_hide_is_carried_from_the_base(self):
        # Wii lightgun games reload by pointing OFF screen; VRLF's Dolphin
        # profile presses pad B for that and Dolphin has to be told B means
        # Point > Hide. A per-game profile replaces the WiimoteNew.ini section
        # wholesale, so a base without this line silently disabled every
        # off-screen reload (HOTD 2&3 Returns two-player, 2026-09-06).
        self.assertEqual(self.keys["IR/Hide"], "`Button B`")

    def test_pack_only_binding_keys_are_never_carried(self):
        self.assertNotIn("Shake/X", self.keys)

    def test_base_extension_survives_when_pack_is_silent(self):
        self.assertEqual(self.keys["Extension"], "Nunchuk")

    def test_header_credits_the_upstream_source_and_marks_modification(self):
        lines = self.text.splitlines()
        self.assertTrue(lines[0].startswith("#"))
        self.assertIn("HOTDOverkill_P1", lines[1])
        self.assertIn("modified", self.text.lower())

    def test_section_header_is_profile(self):
        self.assertIn("[Profile]", self.text)

    def test_raises_when_there_is_no_calibration_to_carry(self):
        with self.assertRaises(ValueError):
            build_profile.build_profile(BASE, PACK_NO_CALIBRATION, "MDM_P1")


class TestShippedBases(unittest.TestCase):
    """The two templates every generated profile starts from. What they say
    about the IMU Point path reaches all 70 profiles, which is the point."""

    def _text(self, name):
        return inikit.read_text(os.path.join(BASE_DIR, name))

    def test_every_profile_starts_with_the_imu_point_path_enabled(self):
        # A real Wii Remote reports its roll to every game (the angle between
        # the two IR dots), so the emulated one does too. Fanned out from a
        # Dead Space-only extra on 2026-09-09: the IMU rotation is applied in
        # the camera frame, about the optical axis, exactly as a real remote
        # rolls, so a canted wrist does not skew a roll-corrected pointer.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertEqual(keys.get("IMUIR/Enabled"), "True", name)

    def test_imu_yaw_is_clamped_to_zero_in_every_base(self):
        # Otherwise the gun's own yaw adds to the stick's horizontal aim. Pitch
        # has no equivalent clamp, which is why VRLF sends a roll-only
        # orientation on the lane instead of relying on config alone.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertEqual(keys.get("IMUIR/Total Yaw"), "0.", name)

    def test_the_bases_never_bind_tilt(self):
        # Tilt is Euler-summed with the stick pointer, so rolling scrambles
        # aim. Tried and abandoned 2026-09-09; the live WiimoteNew.ini kept
        # the bindings for a while and that is how uncovered games broke.
        for name in SHIPPED_BASES:
            self.assertNotIn("Tilt/", self._text(name), name)

    def test_the_bases_keep_the_accelerometer_correction(self):
        # Zeroing IMUIR/Accelerometer Influence was tried as a probe for sweep
        # sway and cannot ship: Dolphin resets the IMU orientation to identity
        # whenever the gyro is unbound, and VRLF samples a lane only while its
        # gun is held, so every bind and every holster-and-regrab leaves a roll
        # offset that only the accelerometer correction removes.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertNotEqual(keys.get("IMUIR/Accelerometer Influence"), "0.", name)

    def test_the_bases_carry_point_hide(self):
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertEqual(keys.get("IR/Hide"), "`Button B`", name)

    def test_the_imu_point_path_survives_the_player_two_derivation(self):
        # derive_p2 rewrites pad and DSU slot numbers; neither IMUIR line names
        # either, so they must come through untouched.
        keys = inikit.parse_flat(derive_p2.derive_p2(self._text(SHIPPED_BASES[0])))
        self.assertEqual(keys["IMUIR/Enabled"], "True")
        self.assertEqual(keys["IMUIR/Total Yaw"], "0.")
        self.assertEqual(keys["Device"], "XInput/1/Gamepad")


class TestNoPerGameExceptions(unittest.TestCase):
    """Every game gets the same remote. Dead Space Extraction was the one
    exception for a day (it reads roll for its alt fire); now the whole set
    reports roll, because a real remote does."""

    def test_extras_is_empty(self):
        self.assertEqual(build_profile.EXTRAS, {})

    def test_dead_space_is_built_like_every_other_game(self):
        ds = build_profile.build_profile(BASE, PACK, "DEADSPACE_P1")
        gs = build_profile.build_profile(BASE, PACK, "GHOSTSQUAD_P1")
        self.assertEqual(ds.replace("DEADSPACE_P1", "X"), gs.replace("GHOSTSQUAD_P1", "X"))


class TestExtrasMechanism(unittest.TestCase):
    """EXTRAS is empty and stays available: a setting that should reach ONE
    game goes here rather than into the base. These pin how an entry behaves
    when someone adds one, using a synthetic entry."""

    EXTRA = {
        "IMUIR/Total Yaw": "25.",
        "Tilt/Forward": "`DSUClient/0/vrlf-wiimotes:Accel Forward`",
    }

    def _build(self, base=BASE, stem="SOMEGAME_P1", transform=None):
        with mock.patch.dict(build_profile.EXTRAS, {"SOMEGAME_P1": self.EXTRA}, clear=True):
            return build_profile.build_profile(base, PACK, stem, transform=transform)

    def test_an_extra_overrides_a_base_line_rather_than_duplicating_it(self):
        # Two of the same key would let Dolphin pick.
        out = self._build()
        self.assertEqual(out.count("IMUIR/Total Yaw"), 1)
        self.assertEqual(inikit.parse_flat(out)["IMUIR/Total Yaw"], "25.")

    def test_an_extra_the_base_lacks_is_appended(self):
        keys = inikit.parse_flat(self._build())
        self.assertEqual(keys["Tilt/Forward"], "`DSUClient/0/vrlf-wiimotes:Accel Forward`")

    def test_extras_are_transformed_for_player_two(self):
        # THE trap: derive_p2 rewrites the BASE, and extras are inserted after
        # it runs. Without the transform every extra would keep DSUClient/0 and
        # player 2 would read player 1's motion - the same bug that was found
        # in the hand-written [Wiimote2] block.
        out = self._build(transform=derive_p2.derive_p2)
        self.assertNotIn("DSUClient/0", out)
        self.assertIn("DSUClient/1", out)

    def test_transform_leaves_non_dsu_extras_alone(self):
        out = self._build(transform=derive_p2.derive_p2)
        self.assertEqual(inikit.parse_flat(out)["IMUIR/Total Yaw"], "25.")

    def test_extras_do_not_displace_calibration(self):
        self.assertEqual(inikit.parse_flat(self._build())["IR/Total Yaw"], "19.0")

    def test_a_game_without_an_extra_is_untouched(self):
        out = self._build(stem="OTHERGAME_P1")
        self.assertNotIn("Tilt/", out)
        self.assertEqual(inikit.parse_flat(out)["IMUIR/Total Yaw"], "0.")


if __name__ == "__main__":
    unittest.main()
