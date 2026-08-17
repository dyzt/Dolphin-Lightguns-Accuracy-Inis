"""Build the user-facing release zip: the drop-in payload and nothing else.

A user needs two folders and a licence. They do not need the generator, the base
templates or the tests -- those stay in the repo, which the zip's README links to.

    python package_release.py --version v1.0

Writes ../dist/VRLF-Dolphin-Accuracy-Profiles-<version>.zip, whose single top-level
folder carries Config/, GameSettings/, README.md and LICENSE.
"""

import argparse
import pathlib
import zipfile

TOOLS = pathlib.Path(__file__).resolve().parent
VRLF = TOOLS.parent
REPO = VRLF.parent

# Copied into the Dolphin user folder verbatim, so their names are the contract.
PAYLOAD_DIRS = ("Config", "GameSettings")

# GPL-3.0: the licence text travels with the work. The per-file "MODIFIED" headers
# the generator writes cover 5(a); this covers 4/5(c).
LICENSE = REPO / "LICENSE"

# The repo README owns install, credit and what-you-get. The zip only needs a
# different tail, because the generator it points at is not in the zip.
README = VRLF / "README.md"
REGEN_HEADING = "## Regenerating"

REGEN_TAIL = """## Regenerating these against your own bindings

This zip is the finished drop-in. The generator, the base templates and the tests
live in the repository, under `VRLF (VR Lightgun Framework)/`:

<{repo_url}>

If your VRLF bindings differ from the ones baked in here -- a different gun layout, your
own pad mapping -- clone that and rebuild the whole set against your base in one command.
The per-game calibration is unaffected: it describes the game's pointer cone, not your
hardware.
"""

REPO_URL = "https://github.com/dyzt/Dolphin-Lightguns-Accuracy-Inis"


def zip_readme(text: str, repo_url: str = REPO_URL) -> str:
    """Repo README with its Regenerating section swapped for a link to the repo.

    Raises if the heading moved -- silently shipping the repo's build instructions,
    which name paths the zip does not contain, is worse than failing the build.
    """
    marker = "\n" + REGEN_HEADING
    if marker not in text:
        raise SystemExit(
            f"README has no {REGEN_HEADING!r} section -- packaging would ship "
            f"regeneration steps for files the zip does not contain."
        )
    head = text.split(marker, 1)[0].rstrip() + "\n\n"
    return head + REGEN_TAIL.format(repo_url=repo_url)


def payload_files():
    """Every file the zip carries, as (source path, path inside the zip folder)."""
    for name in PAYLOAD_DIRS:
        root = VRLF / name
        if not root.is_dir():
            raise SystemExit(f"missing payload folder: {root}")
        for path in sorted(root.rglob("*")):
            if path.is_file():
                yield path, path.relative_to(VRLF).as_posix()


def build(version: str, out_dir: pathlib.Path) -> pathlib.Path:
    stem = f"VRLF-Dolphin-Accuracy-Profiles-{version}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{stem}.zip"

    files = list(payload_files())
    if not files:
        raise SystemExit("no payload files found -- nothing to package")

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, rel in files:
            z.write(src, f"{stem}/{rel}")
        z.writestr(f"{stem}/README.md", zip_readme(README.read_text(encoding="utf-8")))
        z.write(LICENSE, f"{stem}/LICENSE")

    profiles = sum(1 for _, rel in files if rel.startswith("Config/"))
    games = sum(1 for _, rel in files if rel.startswith("GameSettings/"))
    print(f"{out}")
    print(f"  {profiles} profiles, {games} game inis, {out.stat().st_size / 1024:.0f} KiB")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--version", required=True, help="release version, e.g. v1.0")
    ap.add_argument(
        "--out",
        type=pathlib.Path,
        default=VRLF / "dist",
        help="output directory (default: ../dist)",
    )
    args = ap.parse_args()
    build(args.version, args.out)


if __name__ == "__main__":
    main()
