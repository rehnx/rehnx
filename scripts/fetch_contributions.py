#!/usr/bin/env python3
"""Fetch a GitHub user's public contribution calendar without an API token."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

COUNT_RE = re.compile(r"([\d,]+)\s+contribution(?:s)?\b", re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="rehnx")
    parser.add_argument("--output", default="data/contributions.json")
    return parser.parse_args()


def parse_count(cell, soup: BeautifulSoup) -> int | None:
    raw = cell.get("data-count")
    if raw is not None:
        try:
            return int(str(raw).replace(",", ""))
        except ValueError:
            pass

    text_candidates = [cell.get("aria-label"), cell.get("title")]

    cell_id = cell.get("id")
    if cell_id:
        tooltip = soup.find(attrs={"for": cell_id})
        if tooltip is not None:
            text_candidates.append(tooltip.get_text(" ", strip=True))

    for text in text_candidates:
        if not text:
            continue
        if "no contribution" in text.lower():
            return 0
        match = COUNT_RE.search(text)
        if match:
            return int(match.group(1).replace(",", ""))

    return None


def calculate_stats(days: list[dict]) -> dict:
    if not days:
        return {
            "total": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": None,
            "monthly_totals": {},
        }

    parsed = [(date.fromisoformat(item["date"]), int(item["count"])) for item in days]
    by_date = {d: count for d, count in parsed}

    total = sum(count for _, count in parsed)
    best_date, best_count = max(parsed, key=lambda item: (item[1], item[0]))

    longest = 0
    running = 0
    previous = None

    for current, count in parsed:
        consecutive = previous is not None and current == previous + timedelta(days=1)
        if count > 0:
            running = running + 1 if consecutive else 1
            longest = max(longest, running)
        else:
            running = 0
        previous = current

    today = date.today()
    cursor = min(today, parsed[-1][0])
    if by_date.get(cursor, 0) == 0:
        cursor -= timedelta(days=1)

    current_streak = 0
    while by_date.get(cursor, 0) > 0:
        current_streak += 1
        cursor -= timedelta(days=1)

    monthly = defaultdict(int)
    for d, count in parsed:
        monthly[d.strftime("%Y-%m")] += count

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest,
        "best_day": {"date": best_date.isoformat(), "count": best_count},
        "monthly_totals": dict(sorted(monthly.items())),
    }


def fetch(username: str) -> list[dict]:
    url = f"https://github.com/users/{username}/contributions"
    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": f"{username}-profile-readme/1.0",
            "Accept": "text/html,application/xhtml+xml",
            "X-Requested-With": "XMLHttpRequest",
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("[data-date]")

    if not cells:
        raise RuntimeError(
            "GitHub returned no contribution day cells. "
            "Its public contribution markup may have changed."
        )

    unique: dict[str, dict] = {}
    unresolved_positive = []

    for cell in cells:
        raw_date = cell.get("data-date")
        if not raw_date:
            continue

        try:
            day = date.fromisoformat(raw_date)
        except ValueError:
            continue

        try:
            level = int(cell.get("data-level", 0))
        except (TypeError, ValueError):
            level = 0
        level = max(0, min(level, 4))

        count = parse_count(cell, soup)
        if count is None:
            if level == 0:
                count = 0
            else:
                unresolved_positive.append(raw_date)
                continue

        unique[day.isoformat()] = {
            "date": day.isoformat(),
            "count": max(0, int(count)),
            "level": level,
        }

    days = [unique[key] for key in sorted(unique)]

    if unresolved_positive:
        raise RuntimeError(
            "GitHub returned positive contribution cells whose counts could not "
            "be parsed. Refusing to write misleading statistics."
        )

    if len(days) < 300:
        raise RuntimeError(
            f"Only {len(days)} contribution days were parsed; expected roughly a year."
        )

    return days


def main() -> None:
    args = parse_args()
    days = fetch(args.username)
    payload = {
        "username": args.username,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "days": days,
        "stats": calculate_stats(days),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output} with {len(days)} days")


if __name__ == "__main__":
    main()
