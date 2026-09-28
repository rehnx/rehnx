#!/usr/bin/env python3
"""Render contribution JSON as a self-contained animated SVG."""

from __future__ import annotations

import argparse
import html
import json
import os
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

WIDTH = 860
HEIGHT = 218

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

BOX = 11
GAP = 3
STEP = BOX + GAP
GRID_X = 78
GRID_Y = 48


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/contributions.json")
    parser.add_argument("--output", default="contrib-heatmap.svg")
    return parser.parse_args()


def sunday_of(day: date) -> date:
    return day - timedelta(days=(day.weekday() + 1) % 7)


def main() -> None:
    args = parse_args()
    payload = json.loads(Path(args.input).read_text(encoding="utf-8"))
    days = payload.get("days", [])
    if not days:
        raise SystemExit("No contribution days found in input JSON.")

    normalized = []
    for item in days:
        normalized.append(
            {
                "date": date.fromisoformat(item["date"]),
                "count": max(0, int(item.get("count", 0))),
                "level": max(0, min(4, int(item.get("level", 0)))),
            }
        )
    normalized.sort(key=lambda item: item["date"])

    by_week = defaultdict(list)
    for item in normalized:
        by_week[sunday_of(item["date"])].append(item)

    week_starts = sorted(by_week)[-53:]
    week_index = {week: i for i, week in enumerate(week_starts)}

    max_count = max(item["count"] for item in normalized)
    static = os.getenv("STATIC") == "1"

    cells = []
    first_month_position = {}

    for item in normalized:
        week = sunday_of(item["date"])
        if week not in week_index:
            continue

        wi = week_index[week]
        di = (item["date"].weekday() + 1) % 7
        x = GRID_X + wi * STEP
        y = GRID_Y + di * STEP

        if item["date"].day <= 7:
            month_key = item["date"].strftime("%Y-%m")
            first_month_position.setdefault(month_key, (x, item["date"].strftime("%b")))

        palette_index = item["level"]
        if item["count"] > 0 and max_count > 0 and item["count"] == max_count:
            palette_index = 5

        fill = PALETTE[palette_index]
        label = html.escape(
            f'{item["date"].isoformat()}: {item["count"]} '
            f'contribution{"s" if item["count"] != 1 else ""}'
        )

        rect = (
            f'<rect x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="2.4" '
            f'fill="{fill}" opacity="1"><title>{label}</title></rect>'
        )

        if not static:
            delay = wi * 0.014 + di * 0.044
            rect = (
                f'<g opacity="0" transform="translate(0 -7)">'
                f'{rect}'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{delay:.3f}s" dur="0.24s" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="0 -7" to="0 0" begin="{delay:.3f}s" dur="0.30s" fill="freeze"/>'
                '</g>'
            )

        cells.append(rect)

    month_labels = []
    last_x = -999
    for _, (x, label) in sorted(first_month_position.items()):
        if x - last_x >= 34:
            month_labels.append(
                f'<text x="{x}" y="36" fill="{MUTED}" font-size="9.5" '
                'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
                f'{label}</text>'
            )
            last_x = x

    weekday_labels = []
    for name, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = GRID_Y + row * STEP + 9
        weekday_labels.append(
            f'<text x="45" y="{y}" fill="{MUTED}" font-size="8.5" text-anchor="end" '
            'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">'
            f'{name}</text>'
        )

    stats = payload.get("stats", {})
    total = int(stats.get("total", sum(item["count"] for item in normalized)))
    current = int(stats.get("current_streak", 0))
    longest = int(stats.get("longest_streak", 0))
    username = html.escape(str(payload.get("username", "rehnx")))

    stats_text = (
        f'{total:,} contributions'
        f'  ·  current streak {current}d'
        f'  ·  longest streak {longest}d'
    )

    legend_x = 665
    legend = [
        f'<text x="{legend_x-32}" y="190" fill="{MUTED}" font-size="9" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">Less</text>'
    ]
    for i, color in enumerate(PALETTE[:5]):
        legend.append(
            f'<rect x="{legend_x + i*17}" y="180" width="10" height="10" rx="2" fill="{color}"/>'
        )
    legend.append(
        f'<text x="{legend_x+91}" y="190" fill="{MUTED}" font-size="9" '
        'font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">More</text>'
    )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}"
viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">{username} contribution calendar</title>
<desc id="desc">A 53-week GitHub contribution calendar rendered from public contribution data.</desc>
<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{HEIGHT-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<circle cx="17" cy="18" r="3" fill="#f85149"/>
<circle cx="29" cy="18" r="3" fill="#d29922"/>
<circle cx="41" cy="18" r="3" fill="#3fb950"/>
<text x="56" y="22" fill="{MUTED}" font-size="10.5"
font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">{username} / contributions</text>
{"".join(month_labels)}
{"".join(weekday_labels)}
{"".join(cells)}
<line x1="24" y1="165" x2="836" y2="165" stroke="{BORDER}"/>
<text x="24" y="190" fill="{TEXT}" font-size="10.5"
font-family="ui-monospace,SFMono-Regular,Consolas,Liberation Mono,monospace">{html.escape(stats_text)}</text>
{"".join(legend)}
</svg>
"""

    Path(args.output).write_text(svg, encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
