import unittest

import derive_p2
import inikit


P1 = (
    "[Profile]\n"
    "Device = XInput/0/Gamepad\n"
    "Buttons/A = `Button A`\n"
    "IR/Up = `Left Y-`\n"
    "IR/Total Yaw = 16.\n"
    "IMUGyroscope/Pitch Up = `DSUClient/0/vrlf-wiimotes:Gyro Pitch Up`\n"
    "Extension = Nunchuk\n"
    "Nunchuk/IMUAccelerometer/Up = `DSUClient/0/vrlf-nunchuks:Accel Up`\n"
)


class TestDeriveP2(unittest.TestCase):
    def setUp(self):
        self.p2 = inikit.parse_flat(derive_p2.derive_p2(P1))
        self.p1 = inikit.parse_flat(P1)

    def test_device_moves_to_the_second_pad(self):
        self.assertEqual(self.p2["Device"], "XInput/1/Gamepad")

    def test_wiimote_dsu_slot_moves_to_one(self):
        self.assertEqual(
            self.p2["IMUGyroscope/Pitch Up"], "`DSUClient/1/vrlf-wiimotes:Gyro Pitch Up`"
        )

    def test_nunchuk_dsu_slot_moves_to_one(self):
        self.assertEqual(
            self.p2["Nunchuk/IMUAccelerometer/Up"], "`DSUClient/1/vrlf-nunchuks:Accel Up`"
        )

    def test_nothing_else_changes(self):
        changed = {k for k in self.p1 if self.p1[k] != self.p2.get(k)}
        self.assertEqual(
            changed,
            {"Device", "IMUGyroscope/Pitch Up", "Nunchuk/IMUAccelerometer/Up"},
        )

    def test_key_set_is_identical(self):
        self.assertEqual(set(self.p1), set(self.p2))


if __name__ == "__main__":
    unittest.main()
