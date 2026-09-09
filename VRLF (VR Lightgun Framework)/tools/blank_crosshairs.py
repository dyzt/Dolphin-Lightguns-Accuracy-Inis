"""Turn Dolphin texture dumps into blank (fully transparent) replacement textures.

The pack's crosshair removal is Dolphin custom-texture replacement: a fully
transparent RGBA PNG whose filename is the game texture's hash. Matching is by
hash, so a second player's differently-coloured reticle is a DIFFERENT texture
and is not covered by the P1 set -- it has to be dumped from a real 2-player
session and blanked separately.

Workflow
--------
1. Dolphin -> Graphics -> Advanced -> Utility: tick "Dump Textures" and UNTICK
   "Load Custom Textures" (so nothing is already hidden and the dump is complete).
2. Empty <Dolphin user folder>/Dump/Textures/<GameID>/, then play a session with
   both crosshairs on screen. Cover every state you care about: normal, firing,
   reloading/empty, and each sub-game in a compilation.
3. python blank_crosshairs.py list --dump <that folder>
      -> every dumped texture, smallest first, with "COVERED" against the ones
         the pack already blanks. The P2 reticle is normally the same size and
         format as a covered P1 one, with a different hash.
4. Open the candidates in an image viewer and pick the reticles.
5. python blank_crosshairs.py blank --dump <that folder> tex1_...png tex1_...png
      -> writes transparent copies into "Crosshair removal/Load/Textures/<GameID>".
6. Re-tick "Load Custom Textures", untick "Dump Textures", verify in game.

Stdlib only, to match the rest of tools/.
"""

import argparse
import os
import struct
import sys
import zlib

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CROSSHAIR_ROOT = os.path.join(REPO_ROOT, "Crosshair removal", "Load", "Textures")


def parse_name(filename):
    """('tex1_32x16_abc_5.png') -> (32, 16) or None if it is not a tex dump name."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    parts = stem.split("_")
    if len(parts) < 3 or parts[0] != "tex1":
        return None
    dims = parts[1].split("x")
    if len(dims) != 2:
        return None
    try:
        return int(dims[0]), int(dims[1])
    except ValueError:
        return None


def png_chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def transparent_png(width, height):
    """A fully transparent 8-bit RGBA PNG -- every byte, colour and alpha, zero."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00" * (width * 4) for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(raw, 9))
            + png_chunk(b"IEND", b""))


def game_id_from_dump(dump_dir):
    return os.path.basename(os.path.normpath(dump_dir))


def covered_names(game_id):
    folder = os.path.join(CROSSHAIR_ROOT, game_id)
    if not os.path.isdir(folder):
        return set()
    return {n for n in os.listdir(folder) if n.lower().endswith(".png")}


def cmd_list(args):
    game_id = game_id_from_dump(args.dump)
    covered = covered_names(game_id)
    rows = []
    for name in sorted(os.listdir(args.dump)):
        dims = parse_name(name)
        if dims is None:
            continue
        w, h = dims
        if max(w, h) > args.max_dim:
            continue
        rows.append((w * h, w, h, name))
    rows.sort()
    print("game %s -- %d dumped texture(s) at or under %dpx, %d already blanked by the pack"
          % (game_id, len(rows), args.max_dim, len(covered)))
    for _, w, h, name in rows:
        mark = "COVERED  " if name in covered else "candidate"
        print("  %s  %4dx%-4d  %s" % (mark, w, h, name))
    if not covered:
        print("\nNote: the pack blanks nothing for this game id -- check the id is right"
              " (USA discs only) before assuming these are all new.")
    return 0


def cmd_blank(args):
    game_id = game_id_from_dump(args.dump)
    out_dir = args.out or os.path.join(CROSSHAIR_ROOT, game_id)
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for name in args.names:
        name = os.path.basename(name)
        dims = parse_name(name)
        if dims is None:
            print("skip (not a tex1_ dump name): %s" % name, file=sys.stderr)
            continue
        if not os.path.exists(os.path.join(args.dump, name)):
            print("skip (not in the dump folder -- copy the filename exactly): %s" % name,
                  file=sys.stderr)
            continue
        dest = os.path.join(out_dir, name)
        if os.path.exists(dest) and not args.force:
            print("skip (already blanked): %s" % name)
            continue
        with open(dest, "wb") as handle:
            handle.write(transparent_png(*dims))
        print("blanked %dx%d -> %s" % (dims[0], dims[1], dest))
        written += 1
    print("%d file(s) written" % written)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    lister = sub.add_parser("list", help="show dumped textures and what the pack already blanks")
    lister.add_argument("--dump", required=True,
                        help="Dolphin Dump/Textures/<GameID> folder (the game id is read from it)")
    lister.add_argument("--max-dim", type=int, default=128,
                        help="ignore textures larger than this on either axis (default 128)")
    lister.set_defaults(func=cmd_list)

    blanker = sub.add_parser("blank", help="write transparent replacements for named dumps")
    blanker.add_argument("--dump", required=True, help="the same dump folder")
    blanker.add_argument("--out", default=None,
                         help="output folder (default: the pack's Crosshair removal folder for this game)")
    blanker.add_argument("--force", action="store_true", help="overwrite an existing blank")
    blanker.add_argument("names", nargs="+", help="dumped filenames to blank")
    blanker.set_defaults(func=cmd_blank)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
