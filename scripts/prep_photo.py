#!/usr/bin/env python3
"""Prepare a portrait for monochrome ASCII conversion."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", nargs="?", default="source-photo.jpg")
    parser.add_argument("-o", "--output", default="source-prepped.png")
    parser.add_argument("--clahe", type=float, default=2.2, help="CLAHE clip limit")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    try:
        import cv2
        import numpy as np
        from PIL import Image, ImageOps
        from rembg import remove
    except ImportError as exc:
        raise SystemExit(
            "Missing portrait dependencies. Run:\n"
            "pip install -r scripts/requirements-portrait.txt"
        ) from exc

    source = Path(args.input)
    if not source.exists():
        raise SystemExit(f"Portrait not found: {source}")

    image = Image.open(source).convert("RGBA")
    isolated = remove(image)
    if not isinstance(isolated, Image.Image):
        raise RuntimeError("rembg did not return a PIL image")

    isolated = isolated.convert("RGBA")
    white = Image.new("RGBA", isolated.size, (255, 255, 255, 255))
    flattened = Image.alpha_composite(white, isolated).convert("L")

    gray = np.asarray(flattened, dtype=np.uint8)
    clahe = cv2.createCLAHE(
        clipLimit=max(0.1, float(args.clahe)),
        tileGridSize=(8, 8),
    )
    enhanced = clahe.apply(gray)
    blended = cv2.addWeighted(gray, 0.30, enhanced, 0.70, 0)
    result = Image.fromarray(blended, mode="L")
    result = ImageOps.autocontrast(result, cutoff=0.5)

    output = Path(args.output)
    result.save(output)
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
