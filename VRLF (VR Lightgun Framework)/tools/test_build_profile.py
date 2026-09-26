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
    "IMUIR/Enabled = False\n"
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


class TestNunchukToggle(unittest.TestCase):
    """Holding the Nunchuk hand's stick click unplugs the Nunchuk, and again
    plugs it back. Dolphin takes an input expression where the attachment name
    goes, valued as the attachment index (0 None, 1 Nunchuk)."""

    def _keys(self, pack):
        return inikit.parse_flat(build_profile.build_profile(BASE, pack, "SOMEGAME_P1"))

    def test_a_pack_nunchuk_becomes_the_toggle(self):
        keys = self._keys(PACK + "Extension = Nunchuk\n")
        self.assertEqual(keys["Extension"], build_profile.NUNCHUK_TOGGLE)

    def test_a_pack_that_wants_no_attachment_keeps_none(self):
        self.assertEqual(self._keys(PACK + "Extension = None\n")["Extension"], "None")

    def test_the_toggle_holds_the_stick_click_and_starts_attached(self):
        # toggle() starts off, so ! reads 1 (Nunchuk) at boot; hold() keeps a
        # plain click on Minus from unplugging anything.
        self.assertEqual(build_profile.NUNCHUK_TOGGLE, "!toggle(hold(`Back`, 1.5))")

    def test_the_toggle_names_no_dsu_slot_for_player_two_to_move(self):
        self.assertEqual(derive_p2.derive_p2(build_profile.NUNCHUK_TOGGLE),
                         build_profile.NUNCHUK_TOGGLE)

    def test_every_base_carries_the_toggle(self):
        # A game the pack does not cover uses the base (as the global mapping).
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(inikit.read_text(os.path.join(BASE_DIR, name)))
            self.assertEqual(keys.get("Extension"), build_profile.NUNCHUK_TOGGLE, name)


class TestShippedBases(unittest.TestCase):
    """The two templates every generated profile starts from."""

    def _text(self, name):
        return inikit.read_text(os.path.join(BASE_DIR, name))

    def test_the_imu_point_path_is_off_in_every_base(self):
        # VRLF's main Dolphin profile reports the gun's TRUE orientation, and
        # IMU Point on that puts the gun's pitch on top of the stick aim. The
        # pointer rolls through Tilt instead.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertEqual(keys.get("IMUIR/Enabled"), "False", name)

    def test_tilt_is_never_bound_to_the_accelerometer(self):
        # Tried 2026-09-09: raw DSU accel saturated Tilt at about 6 degrees and
        # carried pitch into the pointer. Tilt takes VRLF's trigger roll only.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            for key, value in keys.items():
                if key.startswith("Tilt/"):
                    self.assertNotIn("DSUClient", value, "%s %s" % (name, key))

    def test_the_bases_keep_the_accelerometer_correction(self):
        # Zeroing IMUIR/Accelerometer Influence cannot ship: Dolphin resets the
        # IMU orientation to identity whenever the gyro is unbound, and VRLF
        # samples a lane only while its gun is held, so every holster-and-regrab
        # leaves a roll offset that only the accelerometer correction removes.
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertNotEqual(keys.get("IMUIR/Accelerometer Influence"), "0.", name)

    def test_the_bases_carry_point_hide(self):
        for name in SHIPPED_BASES:
            keys = inikit.parse_flat(self._text(name))
            self.assertEqual(keys.get("IR/Hide"), "`Button B`", name)


class TestTiltRoll(unittest.TestCase):
    """The pointer rolls with the gun through Dolphin's Tilt group, fed the
    gun's roll on the pad's two triggers by VRLF's `tilt_roll` lanes. Tilt
    rolls the emulated camera without touching the stick's aim. So B and Z
    move off the triggers, onto the stick clicks, and no game needs a
    per-game exception any more."""

    def _keys(self, name):
        return inikit.parse_flat(inikit.read_text(os.path.join(BASE_DIR, name)))

    def test_tilt_takes_the_roll_from_the_triggers(self):
        for name in SHIPPED_BASES:
            keys = self._keys(name)
            self.assertEqual(keys.get("Tilt/Left"), "`Trigger L`", name)
            self.assertEqual(keys.get("Tilt/Right"), "`Trigger R`", name)

    def test_tilt_takes_roll_only(self):
        # Forward/Backward would put the gun's pitch on top of the stick aim.
        for name in SHIPPED_BASES:
            keys = self._keys(name)
            self.assertNotIn("Tilt/Forward", keys, name)
            self.assertNotIn("Tilt/Backward", keys, name)

    def test_the_tilt_angle_matches_vrlf(self):
        # VRLF's tilt_roll max_deg defaults to 90; the two must agree or the
        # accelerometer gets back a different roll than was taken out.
        for name in SHIPPED_BASES:
            self.assertEqual(self._keys(name).get("Tilt/Angle"), "90.", name)

    def test_b_and_z_are_off_the_triggers(self):
        for name in SHIPPED_BASES:
            keys = self._keys(name)
            self.assertEqual(keys.get("Buttons/B"), "`Thumb R`", name)
            self.assertEqual(keys.get("Nunchuk/Buttons/Z"), "`Thumb L`", name)

    def test_only_ghost_squad_is_an_exception(self):
        self.assertEqual(list(build_profile.EXTRAS), ["GHOSTSQUAD_P1"])


class TestGhostSquadHide(unittest.TestCase):
    """Ghost Squad alone leaves Point > Hide unbound (James, 2026-09-26: its
    off-screen aiming broke with Hide on)."""

    def test_ghost_squad_unbinds_hide_for_both_players(self):
        p1 = build_profile.build_profile(BASE, PACK, "GHOSTSQUAD_P1")
        p2 = build_profile.build_profile(derive_p2.derive_p2(BASE), PACK, "GHOSTSQUAD_P1",
                                         transform=derive_p2.derive_p2)
        for out in (p1, p2):
            self.assertEqual(out.count("IR/Hide"), 1)
            self.assertEqual(inikit.parse_flat(out)["IR/Hide"], "")

    def test_every_other_game_keeps_hide(self):
        out = build_profile.build_profile(BASE, PACK, "HOTD23_P1")
        self.assertEqual(inikit.parse_flat(out)["IR/Hide"], "`Button B`")


class TestExtrasMechanism(unittest.TestCase):
    """A setting that should reach ONE game goes in EXTRAS rather than the
    base. These pin how an entry behaves, using a synthetic entry."""

    EXTRA = {
        "IMUIR/Enabled": "True",
        "IMUIR/Total Yaw": "25.",
        "Tilt/Forward": "`DSUClient/0/vrlf-wiimotes:Accel Forward`",
    }

    def _build(self, base=BASE, stem="SOMEGAME_P1", transform=None):
        with mock.patch.dict(build_profile.EXTRAS, {"SOMEGAME_P1": self.EXTRA}, clear=True):
            return build_profile.build_profile(base, PACK, stem, transform=transform)

    def test_an_extra_overrides_a_base_line_rather_than_duplicating_it(self):
        # Two of the same key would let Dolphin pick.
        out = self._build()
        self.assertEqual(out.count("IMUIR/Enabled"), 1)
        self.assertEqual(inikit.parse_flat(out)["IMUIR/Enabled"], "True")

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
        self.assertNotIn("IMUIR/Total Yaw", out)


if __name__ == "__main__":
    unittest.main()
