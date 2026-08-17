import unittest

import inikit


class TestParseFlat(unittest.TestCase):
    def test_reads_keys_ignoring_section_and_comments(self):
        text = "[Profile]\n# a comment\nDevice = XInput/0/Gamepad\nIR/Total Yaw = 19.0\n"
        self.assertEqual(
            inikit.parse_flat(text),
            {"Device": "XInput/0/Gamepad", "IR/Total Yaw": "19.0"},
        )

    def test_ignores_semicolon_comments_even_when_they_contain_equals(self):
        # VRLF's own split-layout base documents its pad order in ; comments,
        # and one of those lines contains an '=' that must not parse as a key.
        text = "[Profile]\n; gun2 Remote=XInput/0, gun3 Nunchuk=XInput/1\nDevice = XInput/0/Gamepad\n"
        self.assertEqual(inikit.parse_flat(text), {"Device": "XInput/0/Gamepad"})

    def test_keeps_backticked_values_intact(self):
        text = "[Profile]\nButtons/A = `Button A`\n"
        self.assertEqual(inikit.parse_flat(text)["Buttons/A"], "`Button A`")


class TestReplaceSection(unittest.TestCase):
    def test_replaces_only_the_named_section(self):
        text = "[Controls]\nWiimoteProfile1 = OLD\n[Core]\nFastDiscSpeed = True\n"
        out = inikit.replace_section(text, "Controls", ["WiimoteProfile1 = NEW"])
        self.assertEqual(out, "[Controls]\nWiimoteProfile1 = NEW\n[Core]\nFastDiscSpeed = True\n")

    def test_preserves_crlf_line_endings(self):
        text = "[Controls]\r\nWiimoteProfile1 = OLD\r\n[Core]\r\nFastDiscSpeed = True\r\n"
        out = inikit.replace_section(text, "Controls", ["WiimoteProfile1 = NEW"])
        self.assertIn("\r\n[Core]\r\nFastDiscSpeed = True\r\n", out)
        # No bare LF survives: strip every CRLF and nothing newline-shaped is left.
        self.assertNotIn("\n", out.replace("\r\n", ""))

    def test_handles_upstream_one_line_section_header(self):
        # RCJE8P.ini ships as: [Controls] WiimoteProfile1 = CONDUIT_P1
        text = "[Controls] WiimoteProfile1 = CONDUIT_P1\n"
        out = inikit.replace_section(text, "Controls", ["WiimoteProfile1 = NEW"])
        self.assertEqual(out, "[Controls]\nWiimoteProfile1 = NEW\n")

    def test_appends_section_when_absent(self):
        text = "[Core]\nFastDiscSpeed = True\n"
        out = inikit.replace_section(text, "Controls", ["WiimoteProfile1 = NEW"])
        self.assertTrue(out.startswith("[Core]\nFastDiscSpeed = True\n"))
        self.assertIn("[Controls]\nWiimoteProfile1 = NEW", out)

    def test_leaves_gecko_body_untouched(self):
        text = "[Controls]\nWiimoteProfile1 = OLD\n[Gecko]\n$60FPS\n04158204 60000000\n*Some minor issues\n"
        out = inikit.replace_section(text, "Controls", ["WiimoteProfile1 = NEW"])
        self.assertIn("[Gecko]\n$60FPS\n04158204 60000000\n*Some minor issues\n", out)


if __name__ == "__main__":
    unittest.main()
