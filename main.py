#!/usr/bin/env python3
"""make.fun entry: news-image-20261126.

The graded program. It takes the newspaper image that build_image.py
rendered from news.json (image.png, 1024x1024, 36 stories from Thursday
26 November 2026) and places an exact copy of it where the grader
expects the entry, as entry.png.

Nothing here reaches the network, reads a clock, or rolls dice: the
output is a byte-for-byte copy of the image shipped in this repo, so
every run writes the same bytes. Only the standard library is used:
no Pillow import, no build_image import at runtime, so the minimal
grader Python (which has no Pillow installed) can run it.

Local run:
    python3 main.py            # writes entry.png to a temp dir

Grader run:
    python3 -P -s /bot/main.py # writes $MAKEFUN_OUTPUT_DIR/entry.png
"""
import os
import shutil
import tempfile
from pathlib import Path

SHIPPED = Path(__file__).resolve().parent / "image.png"
NAME = "entry.png"


def out_path():
    # The grader sets MAKEFUN_OUTPUT_DIR; a local run without it falls
    # back to a fresh temp dir. Never writes into the repository: the
    # grader runs with a read-only /bot.
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "")
    if raw:
        folder = Path(raw)
    else:
        folder = Path(tempfile.mkdtemp(prefix="makefun-entry-"))
    folder.mkdir(parents=True, exist_ok=True)
    return folder / NAME


def main():
    # A plain copy: the shipped image.png is the entry, byte for byte.
    target = out_path()
    shutil.copyfile(SHIPPED, target)
    # Read-back check: the written entry must be an exact copy of the
    # shipped image. Fail loudly instead of shipping a truncated file.
    if target.read_bytes() != SHIPPED.read_bytes():
        raise SystemExit("entry.png does not match image.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
