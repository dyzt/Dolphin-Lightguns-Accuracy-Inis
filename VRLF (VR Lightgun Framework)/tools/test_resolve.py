import unittest

import build_vrlf_profiles as bvp


CALIBRATED = "[Profile]\nIR/Total Yaw = 19.0\nIR/Total Pitch = 19.0\nIR/Vertical Offset = 15.0\n"
UNCALIBRATED = "[Profile]\nDevice = DInput/0/Keyboard Mouse\n"


class TestNames(unittest.TestCase):
    def test_strips_the_p1_suffix(self):
        self.assertEqual(
            bvp.vrlf_names("HOTDOverkill_P1"),
            ("VRLF-HOTDOverkill-P1", "VRLF-HOTDOverkill-P2"),
        )

    def test_leaves_a_stem_without_the_suffix_alone(self):
        self.assertEqual(bvp.vrlf_names("MDM"), ("VRLF-MDM-P1", "VRLF-MDM-P2"))


class TestResolve(unittest.TestCase):
    def test_calibrated_and_referenced_gets_a_profile_and_a_game_ini(self):
        plan = bvp.resolve(
            {"GHOSTSQUAD_P1": CALIBRATED},
            {"RGSE8P": "[Controls]\nWiimoteProfile1 = GHOSTSQUAD_P1\n"},
        )
        self.assertEqual(plan.profiles, {"GHOSTSQUAD_P1"})
        self.assertEqual(plan.games, {"RGSE8P": "GHOSTSQUAD_P1"})
        self.assertEqual(plan.dangling, {})

    def test_calibrated_but_unreferenced_gets_a_profile_only(self):
        plan = bvp.resolve({"BBHPRO_P1": CALIBRATED}, {})
        self.assertEqual(plan.profiles, {"BBHPRO_P1"})
        self.assertEqual(plan.games, {})

    def test_uncalibrated_is_skipped_entirely(self):
        plan = bvp.resolve(
            {"MDM_P1": UNCALIBRATED},
            {"RQ5E5G": "[Controls]\nWiimoteProfile1 = MDM_P1\n"},
        )
        self.assertEqual(plan.profiles, set())
        self.assertEqual(plan.games, {})
        self.assertEqual(plan.skipped_no_calibration, {"MDM_P1"})

    def test_dangling_reference_emits_nothing_and_is_reported(self):
        plan = bvp.resolve({}, {"RCJE8P": "[Controls] WiimoteProfile1 = CONDUIT_P1\n"})
        self.assertEqual(plan.games, {})
        self.assertEqual(plan.dangling, {"RCJE8P": "CONDUIT_P1"})


if __name__ == "__main__":
    unittest.main()
