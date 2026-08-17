"""Player 2 is player 1 on the second pad and the second DSU slot.

Kept as one function so the P1/P2 relationship is stated exactly once. The
DSU slot substitution also fixes a long-standing bug in the hand-written
[Wiimote2] block of a typical VRLF setup, where the Wiimote IMU read slot 0
(player 1's gun) while the Nunchuk gyro read slot 1 — so player 2's motion
followed player 1's controller.
"""

P1_DEVICE = "Device = XInput/0/Gamepad"
P2_DEVICE = "Device = XInput/1/Gamepad"


def derive_p2(p1_text):
    out = p1_text.replace(P1_DEVICE, P2_DEVICE)
    return out.replace("DSUClient/0/", "DSUClient/1/")
