#!/usr/bin/env python3
"""Convert a preprocessed portrait into a self-typing monochrome SVG."""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path

RAMP = " .`:-=+*cs#%@"

WIDTH = 370
HEIGHT = 420
MAX_COLS = 82
MAX_ROWS = 48
FONT_SIZE = 6.6
LINE_HEIGHT = 7.25
CHAR_ASPECT = 0.55

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#39d353"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="source-prepped.png")
    parser.add_argument("output", nargs="?", default="ascii-portrait.svg")
    parser.add_argument("--cols", type=int, default=MAX_COLS)
    parser.add_argument("--rows", type=int, default=MAX_ROWS)
    return parser.parse_args()


def fit_grid(image_width: int, image_height: int, max_cols: int, max_rows: int) -> tuple[int, int]:
    source_ratio = image_height / max(1, image_width)
    cols = max_cols
    rows = round(cols * source_ratio * CHAR_ASPECT)
    if rows > max_rows:
        rows = max_rows
        cols = round(rows / max(0.01, source_ratio * CHAR_ASPECT))
    return max(8, cols), max(8, rows)


def pixel_to_char(value: int) -> str:
    darkness = (255 - value) / 255
    index = round(darkness * (len(RAMP) - 1))
    return RAMP[max(0, min(index, len(RAMP) - 1))]


def main() -> None:
    args = parse_args()
    source = Path(args.input)
    if not source.exists():
        raise SystemExit(
            f"Missing {source}. Run `python scripts/prep_photo.py source-photo.jpg` first."
        )

    try:
        from PIL import Image, ImageEnhance
    except ImportError as exc:
        raise SystemExit(
            "Missing Pillow. Run: pip install -r scripts/requirements-portrait.txt"
        ) from exc

    image = Image.open(source).convert("L")
    image = ImageEnhance.Contrast(image).enhance(1.08)

    cols, rows = fit_grid(image.width, image.height, args.cols, args.rows)
    image = image.resize((cols, rows), Image.Resampling.LANCZOS)

    data = list(image.getdata())
    ascii_rows = []
    for row_index in range(rows):
        start = row_index * cols
        values = data[start : start + cols]
        ascii_rows.append("".join(pixel_to_char(v) for v in values))

    static = os.getenv("STATIC") == "1"

    char_width = FONT_SIZE * 0.60
    art_width = cols * char_width
    art_height = rows * LINE_HEIGHT
    left = max(18.0, (WIDTH - art_width) / 2)
    top = 49 + max(0.0, (HEIGHT - 68 - art_height) / 2)

    defs = []
    body = []

    body.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{HEIGHT-1}" '
        f'rx="12" fill="{BG}" stroke="{BORDER}"/>'
    )
    body.append('<circle cx="17" cy="18" r="3" fill="#f85149"/>')
    body.append('<circle cx="29" cy="18" r="3" fill="#d29922"/>')
    body.append('<circle cx="41" cy="18" r="3" fill="#3fb950"/>')
    body.append(
        f'<text x="56" y="22" fill="{MUTED}" font-size="10.5" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
        'ascii-portrait</text>'
    )

    for i, row in enumerate(ascii_rows):
        y = top + i * LINE_HEIGHT
        escaped = html.escape(row)

        if static:
            body.append(
                f'<text x="{left:.2f}" y="{y:.2f}" fill="{TEXT}" font-size="{FONT_SIZE}" '
                'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace" '
                f'xml:space="preserve">{escaped}</text>'
            )
            continue

        clip_id = f"rowClip{i}"
        defs.append(
            f'<clipPath id="{clip_id}"><rect x="{left:.2f}" y="{y-LINE_HEIGHT:.2f}" '
            f'width="0" height="{LINE_HEIGHT+2:.2f}">'
            f'<animate attributeName="width" from="0" to="{art_width+2:.2f}" '
            f'begin="{i*0.050:.3f}s" dur="0.58s" fill="freeze"/></rect></clipPath>'
        )

        body.append(
            f'<text x="{left:.2f}" y="{y:.2f}" fill="{TEXT}" font-size="{FONT_SIZE}" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace" '
            f'clip-path="url(#{clip_id})" xml:space="preserve">{escaped}</text>'
        )

        cursor_y = y - LINE_HEIGHT + 1
        start_t = i * 0.050
        body.append(
            f'<rect x="{left:.2f}" y="{cursor_y:.2f}" width="2.2" height="{LINE_HEIGHT-0.8:.2f}" '
            f'fill="{ACCENT}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.95;0.95;0" '
            f'keyTimes="0;0.05;0.88;1" begin="{start_t:.3f}s" dur="0.62s" fill="freeze"/>'
            f'<animate attributeName="x" from="{left:.2f}" to="{left+art_width:.2f}" '
            f'begin="{start_t:.3f}s" dur="0.58s" fill="freeze"/>'
            '</rect>'
        )

    duration = rows * 0.050 + 0.65
    body.append(
        f'<text x="18" y="{HEIGHT-17}" fill="{ACCENT}" font-size="10.5" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
        f'rehnx@github:~$ <tspan fill="{MUTED}">rendered in {duration:.1f}s</tspan></text>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">'
        '<title id="title">ASCII portrait of Rehan</title>'
        '<desc id="desc">A monochrome portrait rendered as terminal ASCII characters.</desc>'
        f'<defs>{"".join(defs)}</defs>'
        f'{"".join(body)}'
        '</svg>\n'
    )

    output = Path(args.output)
    output.write_text(svg, encoding="utf-8")
    print(f"wrote {output} ({cols}x{rows} characters)")


if __name__ == "__main__":
    main()
