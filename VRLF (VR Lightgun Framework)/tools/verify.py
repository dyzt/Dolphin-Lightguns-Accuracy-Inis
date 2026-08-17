"""Assert three things about a generated tree.

1. No binding key differs from the base - the whole point is that our
   bindings survive.
2. Every calibration value matches its upstream source - the whole point is
   that their numbers survive.
3. Every WiimoteProfile<N> reference resolves - this is the check upstream
   lacks, and the reason a large share of its game INIs make Dolphin raise
   "Selected controller profile does not exist" at boot.
"""

import os

import build_profile
import build_vrlf_profiles as bvp
import derive_p2
import inikit


def check(pack_profiles, game_inis, out_profiles, out_games, base_p1, base_p2):
    problems = []
    bases = {"P1": inikit.parse_flat(base_p1), "P2": inikit.parse_flat(base_p2)}
    plan = bvp.resolve(pack_profiles, game_inis)

    for stem in sorted(plan.profiles):
        calibration = build_profile.calibration_of(pack_profiles[stem])
        for name, player in zip(bvp.vrlf_names(stem), ("P1", "P2")):
            if name not in out_profiles:
                problems.append("missing generated profile %s" % name)
                continue
            keys = inikit.parse_flat(out_profiles[name])
            for key, value in bases[player].items():
                if key in build_profile.CARRIED:
                    continue
                if keys.get(key) != value:
                    problems.append(
                        "%s: binding %s is %r, base says %r"
                        % (name, key, keys.get(key), value)
                    )
            for key, value in calibration.items():
                if keys.get(key) != value:
                    problems.append(
                        "%s: calibration %s is %r, %s.ini says %r"
                        % (name, key, keys.get(key), stem, value)
                    )

    for game_id, text in sorted(out_games.items()):
        keys = inikit.parse_flat(text)
        for slot in ("WiimoteProfile1", "WiimoteProfile2"):
            wanted = keys.get(slot)
            if wanted and wanted not in out_profiles:
                problems.append("%s.ini: %s -> %s does not exist" % (game_id, slot, wanted))

    return problems


def verify(pack_root, out_root, base_path):
    pack_profiles = bvp._read_dir(os.path.join(pack_root, "Config", "Profiles", "Wiimote"))
    game_inis = bvp._read_dir(os.path.join(pack_root, "GameSettings"))
    out_profiles = bvp._read_dir(os.path.join(out_root, "Config", "Profiles", "Wiimote"))
    out_games = bvp._read_dir(os.path.join(out_root, "GameSettings"))
    base_p1 = inikit.read_text(base_path)

    problems = check(
        pack_profiles,
        game_inis,
        out_profiles,
        out_games,
        base_p1,
        derive_p2.derive_p2(base_p1),
    )
    for problem in problems:
        print("FAIL %s" % problem)
    print(
        "%d problem(s); %d profiles, %d game inis checked"
        % (len(problems), len(out_profiles), len(out_games))
    )
    return 1 if problems else 0
