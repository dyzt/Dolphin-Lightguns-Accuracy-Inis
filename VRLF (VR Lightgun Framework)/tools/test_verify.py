import unittest

import verify


BASE_P1 = (
    "[Profile]\nDevice = XInput/0/Gamepad\nButtons/A = `Button A`\n"
    "IR/Total Yaw = 16.\nIR/Total Pitch = 12.\nIR/Vertical Offset = 15.\n"
)
BASE_P2 = BASE_P1.replace("XInput/0", "XInput/1")
PACK = (
    "[Profile]\nDevice = DInput/0/Keyboard Mouse\n"
    "IR/Total Yaw = 19.0\nIR/Total Pitch = 19.0\nIR/Vertical Offset = 15.0\n"
)

GOOD_P1 = (
    "[Profile]\nDevice = XInput/0/Gamepad\nButtons/A = `Button A`\n"
    "IR/Total Yaw = 19.0\nIR/Total Pitch = 19.0\nIR/Vertical Offset = 15.0\n"
)
GOOD_P2 = GOOD_P1.replace("XInput/0", "XInput/1")
GAME = "[Controls]\nWiimoteProfile1 = VRLF-X-P1\nWiimoteProfile2 = VRLF-X-P2\n"


def _args(**overrides):
    args = dict(
        pack_profiles={"X_P1": PACK},
        game_inis={"RXXE01": "[Controls]\nWiimoteProfile1 = X_P1\n"},
        out_profiles={"VRLF-X-P1": GOOD_P1, "VRLF-X-P2": GOOD_P2},
        out_games={"RXXE01": GAME},
        base_p1=BASE_P1,
        base_p2=BASE_P2,
    )
    args.update(overrides)
    return args


class TestCheck(unittest.TestCase):
    def test_clean_tree_reports_nothing(self):
        self.assertEqual(verify.check(**_args()), [])

    def test_catches_a_binding_that_drifted_from_the_base(self):
        bad = GOOD_P1.replace("Buttons/A = `Button A`", "Buttons/A = `Click 0`")
        problems = verify.check(**_args(out_profiles={"VRLF-X-P1": bad, "VRLF-X-P2": GOOD_P2}))
        self.assertTrue(any("Buttons/A" in p for p in problems))

    def test_catches_calibration_that_does_not_match_upstream(self):
        bad = GOOD_P1.replace("IR/Total Yaw = 19.0", "IR/Total Yaw = 21.0")
        problems = verify.check(**_args(out_profiles={"VRLF-X-P1": bad, "VRLF-X-P2": GOOD_P2}))
        self.assertTrue(any("IR/Total Yaw" in p for p in problems))

    def test_catches_a_missing_generated_profile(self):
        problems = verify.check(**_args(out_profiles={"VRLF-X-P1": GOOD_P1}))
        self.assertTrue(any("VRLF-X-P2" in p for p in problems))

    def test_catches_a_game_ini_pointing_at_a_missing_profile(self):
        problems = verify.check(
            **_args(out_games={"RXXE01": "[Controls]\nWiimoteProfile1 = VRLF-GONE-P1\n"})
        )
        self.assertTrue(any("VRLF-GONE-P1" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
