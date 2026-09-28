#!/usr/bin/env python3
"""Generate an animated neofetch-inspired profile card."""

from __future__ import annotations

import html
import os
from pathlib import Path

WIDTH = 490
HEIGHT = 420

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#39d353"
BLUE = "#58a6ff"

PROFILE = [
    ("USER", "rehnx@github"),
    ("NAME", "Rehan"),
    ("ROLE", "B.Tech · CSE (AI)"),
    ("UNIVERSITY", "Marwadi University"),
    ("OS", "Arch Linux"),
    ("PROJECT", "Void Shell"),
    ("STACK", "Python · C++ · JavaScript"),
    ("FOCUS", "AI · Systems · Full Stack"),
    ("MODE", "Build → Break → Learn → Rebuild"),
    ("STATUS", "constantly evolving"),
]


def line_group(index: int, key: str, value: str, static: bool) -> str:
    y = 91 + index * 28
    key_text = html.escape(key)
    value_text = html.escape(value)

    content = (
        f'<text x="26" y="{y}" fill="{ACCENT}" font-size="12.5" font-weight="700" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
        f'{key_text:<10}</text>'
        f'<text x="124" y="{y}" fill="{TEXT}" font-size="12.5" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
        f'{value_text}</text>'
    )

    if static:
        return f'<g>{content}</g>'

    begin = 0.14 + index * 0.105
    return (
        '<g opacity="0" transform="translate(0 6)">'
        f'{content}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{begin:.3f}s" '
        'dur="0.28s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 6" to="0 0" '
        f'begin="{begin:.3f}s" dur="0.28s" fill="freeze"/>'
        '</g>'
    )


def main() -> None:
    static = os.getenv("STATIC") == "1"

    groups = "".join(
        line_group(i, key, value, static)
        for i, (key, value) in enumerate(PROFILE)
    )

    prompt = (
        f'<text x="26" y="388" fill="{BLUE}" font-size="11.5" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
        'rehnx@github:~$ <tspan fill="#c9d1d9">whoami</tspan></text>'
    )

    if not static:
        prompt = (
            '<g opacity="0">'
            + prompt
            + '<animate attributeName="opacity" from="0" to="1" begin="1.30s" '
              'dur="0.30s" fill="freeze"/></g>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">Rehan developer information</title>
<desc id="desc">A terminal-style neofetch card with role, stack, interests, and current project.</desc>
<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{HEIGHT-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<circle cx="17" cy="18" r="3" fill="#f85149"/>
<circle cx="29" cy="18" r="3" fill="#d29922"/>
<circle cx="41" cy="18" r="3" fill="#3fb950"/>
<text x="56" y="22" fill="{MUTED}" font-size="10.5"
font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">neofetch</text>
<text x="26" y="56" fill="{BLUE}" font-size="15" font-weight="700"
font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">rehnx@github</text>
<line x1="26" y1="66" x2="464" y2="66" stroke="{BORDER}"/>
{groups}
<line x1="26" y1="363" x2="464" y2="363" stroke="{BORDER}"/>
{prompt}
</svg>
"""
    Path("info-card.svg").write_text(svg, encoding="utf-8")
    print("wrote info-card.svg")


if __name__ == "__main__":
    main()
