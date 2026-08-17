import unittest

import build_game_ini
import inikit


GAME = (
    "[Controls]\n"
    "WiimoteSource0 = 1\n"
    "WiimoteSource1 = 0\n"
    "WiimoteProfile1 = HOTDOverkill_P1\n"
    "PadType0 = 0\n"
    "[Core]\n"
    "FastDiscSpeed = True\n"
    "[Gecko]\n"
    "$60FPS\n"
    "04158204 60000000\n"
    "*Some minor issues\n"
)

ONE_LINER = "[Controls] WiimoteProfile1 = CONDUIT_P1\n"


class TestReferencedProfile(unittest.TestCase):
    def test_reads_the_profile_name(self):
        self.assertEqual(build_game_ini.referenced_profile(GAME), "HOTDOverkill_P1")

    def test_reads_it_from_the_one_line_form(self):
        self.assertEqual(build_game_ini.referenced_profile(ONE_LINER), "CONDUIT_P1")

    def test_returns_none_when_absent(self):
        self.assertIsNone(build_game_ini.referenced_profile("[Core]\nFastDiscSpeed = True\n"))


class TestRewrite(unittest.TestCase):
    def setUp(self):
        self.out = build_game_ini.rewrite_game_ini(
            GAME, "VRLF-HOTDOverkill-P1", "VRLF-HOTDOverkill-P2"
        )
        self.keys = inikit.parse_flat(self.out)

    def test_points_both_players_at_the_vrlf_profiles(self):
        self.assertEqual(self.keys["WiimoteProfile1"], "VRLF-HOTDOverkill-P1")
        self.assertEqual(self.keys["WiimoteProfile2"], "VRLF-HOTDOverkill-P2")

    def test_reenables_the_second_wiimote(self):
        self.assertEqual(self.keys["WiimoteSource0"], "1")
        self.assertEqual(self.keys["WiimoteSource1"], "1")

    def test_gamecube_pads_stay_off(self):
        for index in range(4):
            self.assertEqual(self.keys["PadType%d" % index], "0")

    def test_other_sections_survive_byte_for_byte(self):
        self.assertIn("[Core]\nFastDiscSpeed = True\n", self.out)
        self.assertIn("[Gecko]\n$60FPS\n04158204 60000000\n*Some minor issues\n", self.out)

    def test_gecko_codes_are_not_enabled(self):
        self.assertNotIn("[Gecko_Enabled]", self.out)


if __name__ == "__main__":
    unittest.main()
