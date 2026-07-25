#!/usr/bin/env python3
"""Render hollow white annotation arrows from a coordinate CSV.

Coordinates are in source-image pixels.  The CSV must contain:
output_filename,source_file,tail_x,tail_y,tip_x,tip_y,head_length,head_width
"""
from pathlib import Path
import csv
import subprocess
import sys


def render(row, source_root, output_root):
    source = source_root / row["source_file"]
    output = output_root / row["output_filename"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Use one closed, unfilled arrow polygon.  The reference arrows are hollow
    # block arrows: a rectangular shaft widening into a triangular head, not
    # three independent leader lines.
    tx, ty = float(row["tail_x"]), float(row["tail_y"])
    x, y = float(row["tip_x"]), float(row["tip_y"])
    length = float(row.get("head_length") or 120)
    width = float(row.get("head_width") or 160)
    shaft_width = float(row.get("shaft_width") or max(70, width * 0.42))
    dx, dy = x - tx, y - ty
    norm = (dx * dx + dy * dy) ** 0.5 or 1
    ux, uy = dx / norm, dy / norm
    px, py = -uy, ux
    bx, by = x - ux * length, y - uy * length
    head_top = (bx + px * width / 2, by + py * width / 2)
    head_bottom = (bx - px * width / 2, by - py * width / 2)
    shaft_top = (bx + px * shaft_width / 2, by + py * shaft_width / 2)
    shaft_bottom = (bx - px * shaft_width / 2, by - py * shaft_width / 2)
    tail_top = (tx + px * shaft_width / 2, ty + py * shaft_width / 2)
    tail_bottom = (tx - px * shaft_width / 2, ty - py * shaft_width / 2)
    points = " ".join(f"{a},{b}" for a, b in [
        tail_top, shaft_top, head_top, (x, y), head_bottom, shaft_bottom,
        tail_bottom,
    ])
    draw = f"polygon {points}"
    if row.get("stroke_width"):
        stroke_width = float(row["stroke_width"])
    else:
        image_width = int(subprocess.check_output([
            "magick", "identify", "-format", "%w", str(source)
        ], text=True).strip())
        stroke_width = max(4.0, image_width * 0.006)
    subprocess.run([
        "magick", str(source), "-stroke", "white", "-strokewidth", str(stroke_width),
        "-fill", "none", "-draw", draw, str(output)
    ], check=True)


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: render_gpt_annotations.py COORDS.csv SOURCE_ROOT OUTPUT_ROOT")
    coords, source_root, output_root = map(Path, sys.argv[1:])
    with coords.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        render(row, source_root, output_root)
    print(f"rendered {len(rows)} annotation rows")


if __name__ == "__main__":
    main()
