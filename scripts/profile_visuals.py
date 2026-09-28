"""Render small profile SVGs from GitHub data; no third-party dependencies."""

import json
import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.request import Request, urlopen


def svg(width, height, title, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title"><title id="title">{escape(title)}</title>'
        f'<rect width="{width}" height="{height}" rx="8" fill="#0d1117"/>'
        '<g font-family="system-ui, sans-serif" fill="#c9d1d9">'
        f'{body}</g></svg>\n'
    )


def text(x, y, value, size=12, color="#c9d1d9"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}">'
            f'{escape(str(value))}</text>')


def render(user, updated):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    metrics = (
        ("Public repos", user["repositories"]["totalCount"]),
        ("Followers", user["followers"]["totalCount"]),
        ("Contributions / year", calendar["totalContributions"]),
    )
    body = text(20, 27, "rehnx / github", 14, "#58a6ff")
    for x, (label, value) in zip((20, 145, 265), metrics):
        body += text(x, 66, f"{value:,}", 24) + text(x, 88, label, 11)
    body += text(20, 117, f"Updated {updated} · GitHub contribution calendar", 10)
    stats = svg(420, 132, "Rehan's GitHub statistics", body)

    days = [day for week in calendar["weeks"] for day in week["contributionDays"]][-31:]
    if not days:
        raise ValueError("GitHub returned no contribution calendar days")
    maximum = max(1, max(day["contributionCount"] for day in days))
    body = text(20, 26, "contributions / last 31 days", 14, "#58a6ff")
    body += text(20, 53, maximum, 10) + text(20, 133, "0", 10)
    body += '<path d="M48 50H680 M48 130H680" stroke="#30363d"/>'
    points = []
    for i, day in enumerate(days):
        x = 48 + i * 632 / max(1, len(days) - 1)
        y = 130 - day["contributionCount"] * 80 / maximum
        points.append(f"{x:.1f},{y:.1f}")
    body += f'<polyline points="{" ".join(points)}" fill="none" stroke="#58a6ff" stroke-width="2"/>'
    for point, day in zip(points, days):
        x, y = point.split(",")
        label = f'{day["date"]}: {day["contributionCount"]} contributions'
        body += f'<circle cx="{x}" cy="{y}" r="2" fill="#79c0ff"><title>{escape(label)}</title></circle>'
    body += text(48, 153, days[0]["date"], 10)
    body += text(610, 153, days[-1]["date"], 10)
    total = sum(day["contributionCount"] for day in days)
    body += text(20, 180, f"{total:,} contributions · Updated {updated}", 10)
    return stats, svg(700, 195, "Rehan's contribution activity", body)


def main():
    query = '''query {
      user(login: "rehnx") {
        repositories(privacy: PUBLIC, ownerAffiliations: OWNER) { totalCount }
        followers { totalCount }
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
          }
        }
      }
    }'''
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f'Bearer {os.environ["GITHUB_TOKEN"]}',
                 "Content-Type": "application/json", "User-Agent": "rehnx-profile"},
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors") or not result.get("data", {}).get("user"):
        raise RuntimeError("GitHub could not return complete profile data")
    updated = datetime.now(timezone.utc).strftime("%Y-%m-%d UTC")
    stats, activity = render(result["data"]["user"], updated)
    output = Path("dist")
    output.mkdir(exist_ok=True)
    (output / "github-stats.svg").write_text(stats, encoding="utf-8")
    (output / "github-activity.svg").write_text(activity, encoding="utf-8")


if __name__ == "__main__":
    main()
