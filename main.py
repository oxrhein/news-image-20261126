#!/usr/bin/env python3
"""Entrypoint: render the newspaper and write it to the output directory.

Writes ONLY to $MAKEFUN_OUTPUT_DIR (or /output when it exists, else a
fresh temp dir). Never writes into the repository: the grader runs with
a read-only /bot.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_image import render  # noqa: E402
import json  # noqa: E402


def output_dir():
    env = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if env:
        return env
    if os.path.isdir("/output"):
        return "/output"
    return tempfile.mkdtemp(prefix="makefun-entry-")


def main():
    with open(os.path.join(HERE, "news.json"), encoding="utf-8") as fh:
        data = json.load(fh)
    img = render(data)
    out_dir = output_dir()
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img.save(out_path, format="PNG", optimize=True)
    size = os.path.getsize(out_path)
    print(out_path)
    print("bytes:", size)
    assert size <= 1048576, "entry.png exceeds the 1 MiB cap"


if __name__ == "__main__":
    main()
