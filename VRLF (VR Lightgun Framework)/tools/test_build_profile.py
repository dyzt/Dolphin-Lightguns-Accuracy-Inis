import unittest

import build_profile
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


class TestPerGameExtras(unittest.TestCase):
    """Extras exist so a setting that changes how the emulated remote BEHAVES
    can be scoped to the one game that asks for it, instead of riding the
    shared base into all 37."""

    def test_a_game_without_extras_is_untouched(self):
        out = build_profile.build_profile(BASE, PACK, "GHOSTSQUAD_P1")
        self.assertNotIn("Tilt/", out)

    def test_dead_space_gets_the_tilt_bindings(self):
        out = build_profile.build_profile(BASE, PACK, "DEADSPACE_P1")
        keys = inikit.parse_flat(out)
        self.assertEqual(keys["Tilt/Left"], "`Trigger L`")
        self.assertEqual(keys["Tilt/Right"], "`Trigger R`")
        self.assertEqual(keys["Tilt/Angle"], "90.")

    def test_extras_reach_player_two_as_well(self):
        # P2 is built from the P2 base with the SAME stem, and Trigger L/R are
        # device-relative, so they address P2's own pad without rewriting.
        p2_base = BASE.replace("XInput/0/Gamepad", "XInput/1/Gamepad")
        out = build_profile.build_profile(p2_base, PACK, "DEADSPACE_P1")
        self.assertIn("Tilt/Left = `Trigger L`", out)

    def test_extras_do_not_displace_calibration(self):
        out = build_profile.build_profile(BASE, PACK, "DEADSPACE_P1")
        keys = inikit.parse_flat(out)
        self.assertEqual(keys["IR/Total Yaw"], "19.0")

    def test_an_extra_overrides_a_base_line_rather_than_duplicating_it(self):
        base = BASE + "Tilt/Angle = 45.\n"
        out = build_profile.build_profile(base, PACK, "DEADSPACE_P1")
        self.assertEqual(out.count("Tilt/Angle"), 1)
        self.assertEqual(inikit.parse_flat(out)["Tilt/Angle"], "90.")


if __name__ == "__main__":
    unittest.main()
