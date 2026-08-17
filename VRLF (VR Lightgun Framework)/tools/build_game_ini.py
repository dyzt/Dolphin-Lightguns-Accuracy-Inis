"""Rewrite a per-game INI's [Controls] block, leaving every other byte alone.

The pack's video/core/Gecko sections are its own tuning and are none of our
business; only the controller wiring changes. Note Dolphin's inconsistent
indexing: WiimoteSource<N> is 0-indexed while WiimoteProfile<N> is 1-indexed.
Both sets below refer to players 1 and 2.
"""

import inikit


def referenced_profile(text):
    return inikit.parse_flat(text).get("WiimoteProfile1")


def rewrite_game_ini(text, p1_name, p2_name):
    body = [
        "WiimoteSource0 = 1",
        "WiimoteSource1 = 1",
        "WiimoteProfile1 = %s" % p1_name,
        "WiimoteProfile2 = %s" % p2_name,
    ]
    body.extend("PadType%d = 0" % index for index in range(4))
    return inikit.replace_section(text, "Controls", body)
