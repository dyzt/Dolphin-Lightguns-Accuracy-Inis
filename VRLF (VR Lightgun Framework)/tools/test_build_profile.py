import unittest

import build_profile
import inikit


BASE = (
    "[Profile]\n"
    "Device = XInput/0/Gamepad\n"
    "Buttons/A = `Button A`\n"
    "IR/Up = `Left Y-`\n"
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


if __name__ == "__main__":
    unittest.main()
