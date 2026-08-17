"""Generate VRLF-compatible Wiimote profiles from the community accuracy pack.

Usage:
  python build_vrlf_profiles.py                 # regenerate the committed tree
  python build_vrlf_profiles.py --base mine.ini # use your own bindings
  python build_vrlf_profiles.py --verify        # check the emitted tree

Four buckets, decided per upstream profile:
  calibrated + a game INI names it  -> profile pair + rewritten game INI
  calibrated, nothing names it      -> profile pair only (pick it by hand in
                                       Dolphin's controller GUI)
  no calibration                    -> nothing
  game INI names a missing profile  -> nothing (this is what stops Dolphin's
                                       "Selected controller profile does not
                                       exist" panic alert)
"""

import argparse
import collections
import os
import sys

import build_game_ini
import build_profile
import derive_p2
import inikit

HERE = os.path.dirname(os.path.abspath(__file__))
VRLF_ROOT = os.path.dirname(HERE)
DEFAULT_PACK = os.path.join(os.path.dirname(VRLF_ROOT), "Accuracy and control mappings")

Plan = collections.namedtuple("Plan", "profiles games skipped_no_calibration dangling")


def vrlf_names(stem):
    core = stem[:-3] if stem.endswith("_P1") else stem
    return ("VRLF-%s-P1" % core, "VRLF-%s-P2" % core)


def resolve(pack_profiles, game_inis):
    calibrated, skipped = set(), set()
    for stem, text in pack_profiles.items():
        if build_profile.calibration_of(text) is None:
            skipped.add(stem)
        else:
            calibrated.add(stem)

    games, dangling = {}, {}
    for game_id, text in game_inis.items():
        wanted = build_game_ini.referenced_profile(text)
        if wanted is None:
            continue
        if wanted in calibrated:
            games[game_id] = wanted
        elif wanted not in pack_profiles:
            dangling[game_id] = wanted

    return Plan(calibrated, games, skipped, dangling)


def _read_dir(path, suffix=".ini"):
    if not os.path.isdir(path):
        return {}
    out = {}
    for name in sorted(os.listdir(path)):
        if name.endswith(suffix):
            out[name[: -len(suffix)]] = inikit.read_text(os.path.join(path, name))
    return out


def generate(pack_root, out_root, base_path, base_p2_path=None):
    pack_profiles = _read_dir(os.path.join(pack_root, "Config", "Profiles", "Wiimote"))
    game_inis = _read_dir(os.path.join(pack_root, "GameSettings"))
    plan = resolve(pack_profiles, game_inis)

    base_p1 = inikit.read_text(base_path)
    # derive_p2 only knows the default layout's pad numbering. A layout that
    # spreads one Wiimote across several pads (VRLF's split Remote + Nunchuk)
    # has its own authored P2, so take it verbatim when offered.
    base_p2 = (
        inikit.read_text(base_p2_path) if base_p2_path else derive_p2.derive_p2(base_p1)
    )

    profile_dir = os.path.join(out_root, "Config", "Profiles", "Wiimote")
    game_dir = os.path.join(out_root, "GameSettings")
    os.makedirs(profile_dir, exist_ok=True)
    os.makedirs(game_dir, exist_ok=True)

    for stem in sorted(plan.profiles):
        p1_name, p2_name = vrlf_names(stem)
        pack_text = pack_profiles[stem]
        inikit.write_text(
            os.path.join(profile_dir, p1_name + ".ini"),
            build_profile.build_profile(base_p1, pack_text, stem),
        )
        inikit.write_text(
            os.path.join(profile_dir, p2_name + ".ini"),
            build_profile.build_profile(base_p2, pack_text, stem),
        )

    for game_id, stem in sorted(plan.games.items()):
        p1_name, p2_name = vrlf_names(stem)
        inikit.write_text(
            os.path.join(game_dir, game_id + ".ini"),
            build_game_ini.rewrite_game_ini(game_inis[game_id], p1_name, p2_name),
        )

    print("profiles: %d pairs" % len(plan.profiles))
    print("game inis: %d" % len(plan.games))
    print(
        "skipped (no calibration): %d %s"
        % (len(plan.skipped_no_calibration), sorted(plan.skipped_no_calibration))
    )
    print("upstream dangling references skipped: %d" % len(plan.dangling))
    for game_id, wanted in sorted(plan.dangling.items()):
        print("  %s -> %s" % (game_id, wanted))
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-root", default=DEFAULT_PACK)
    parser.add_argument("--out-root", default=VRLF_ROOT)
    parser.add_argument(
        "--base", default=os.path.join(VRLF_ROOT, "base", "VRLF-Dolphin-Base-P1.ini")
    )
    parser.add_argument(
        "--base-p2",
        default=None,
        help="player 2's base, when your layout's P2 is not P1 on the next pad",
    )
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(argv)

    if args.verify:
        import verify

        return verify.verify(args.pack_root, args.out_root, args.base, args.base_p2)

    generate(args.pack_root, args.out_root, args.base, args.base_p2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
