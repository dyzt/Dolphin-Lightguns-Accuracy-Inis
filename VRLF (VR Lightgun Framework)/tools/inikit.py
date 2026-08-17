"""Minimal INI surgery for Dolphin config files.

Deliberately not configparser: Dolphin INIs contain bare lines inside [Gecko]
blocks, values wrapped in backticks, and at least one file with a section
header and a key on the same line. We only ever need two operations, so we do
them on raw text and keep every other byte exactly as it was.
"""

import re

_SECTION = re.compile(r"^\s*\[([^\]]+)\]\s*(.*)$")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        return fh.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as fh:
        fh.write(text)


def parse_flat(text):
    """Every `key = value` pair in the file, section headers ignored."""
    out = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("*"):
            continue
        match = _SECTION.match(line)
        if match:
            line = match.group(2).strip()
            if not line:
                continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def _newline_of(text):
    return "\r\n" if "\r\n" in text else "\n"


def replace_section(text, name, body_lines):
    """Replace the body of [name], leaving every other byte alone.

    Appends the section if absent. Normalises upstream's one-line
    `[Controls] Key = Value` form into a proper header plus body. The file's
    trailing newline is held aside so the body-skipping walk cannot eat it.
    """
    newline = _newline_of(text)
    lines = text.split(newline)
    trailing = lines.pop() if lines and lines[-1] == "" else None

    out = []
    index = 0
    replaced = False
    while index < len(lines):
        match = _SECTION.match(lines[index])
        if match and match.group(1).strip().lower() == name.lower():
            out.append("[%s]" % name)
            out.extend(body_lines)
            index += 1
            # Skip the old body, stopping at the next section header.
            while index < len(lines) and not _SECTION.match(lines[index]):
                index += 1
            replaced = True
            continue
        out.append(lines[index])
        index += 1

    if not replaced:
        if out and out[-1] != "":
            out.append("")
        out.append("[%s]" % name)
        out.extend(body_lines)

    if trailing is not None:
        out.append(trailing)
    return newline.join(out)
