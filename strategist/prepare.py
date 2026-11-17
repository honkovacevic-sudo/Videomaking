"""One-time asset preparation.

* Reprojects the NASA Blue Marble image (equirectangular) to Web Mercator
  and applies the channel's dark, cinematic colour grade.
* Projects every country polygon (Natural Earth via world-atlas) into the
  same Mercator pixel space and caches it as a pickle.

Run:  python -m strategist.prepare
"""
import json
import math
import pickle
from pathlib import Path

import numpy as np
from PIL import Image

from .geo import WORLD, project

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "assets" / "raw"
OUT = ROOT / "assets"


def build_basemap():
    src = np.asarray(Image.open(RAW / "earth-blue-marble.jpg").convert("RGB")).astype(np.float32) / 255
    sh, sw, _ = src.shape
    # Output rows -> latitude (inverse Mercator), columns map linearly.
    ys = np.arange(WORLD) + 0.5
    merc = (WORLD / 2 - ys) / (WORLD / (2 * math.pi))
    lat = np.degrees(np.arctan(np.sinh(merc)))
    src_rows = (90 - lat) / 180 * sh - 0.5
    r0 = np.clip(np.floor(src_rows).astype(int), 0, sh - 1)
    r1 = np.clip(r0 + 1, 0, sh - 1)
    fr = (src_rows - np.floor(src_rows))[:, None, None]
    rows = src[r0] * (1 - fr) + src[r1] * fr                     # (WORLD, sw, 3)
    img = np.asarray(Image.fromarray((rows * 255).astype(np.uint8)).resize((WORLD, WORLD), Image.LANCZOS)).astype(np.float32) / 255

    # --- colour grade: darker, slightly desaturated, cool shadows -------------
    lum = img @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    img = lum[..., None] + (img - lum[..., None]) * 0.78           # desaturate
    img = np.power(np.clip(img, 0, 1), 1.12) * 0.80                # darken
    shadow = np.clip(1 - lum * 2.2, 0, 1)[..., None]
    img = img + shadow * np.array([-0.004, 0.006, 0.022], dtype=np.float32)  # cool shadows
    img = np.clip(img, 0, 1)
    Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(OUT / "basemap_mercator.png", optimize=False)
    print("basemap ->", OUT / "basemap_mercator.png")


def build_countries():
    for res in ("10m", "50m"):
        data = json.loads((RAW / f"countries-{res}.geojson").read_text())
        out = {}
        for f in data["features"]:
            name = f["properties"]["name"]
            g = f["geometry"]
            if g is None:
                continue
            polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
            rings = []
            for poly in polys:
                for ring in poly:
                    a = np.asarray(ring, dtype=np.float64)
                    a[:, 1] = np.clip(a[:, 1], -85, 85)
                    # unwrap rings that cross the antimeridian (Fiji, Chukotka...)
                    a[:, 0] = np.degrees(np.unwrap(np.radians(a[:, 0])))
                    x, y = project(a[:, 0], a[:, 1])
                    rings.append(np.stack([x, y], 1).astype(np.float32))
            allp = np.concatenate(rings)
            out[name] = {"rings": rings, "bbox": (*allp.min(0), *allp.max(0))}
        with open(OUT / f"countries_{res}.pkl", "wb") as fh:
            pickle.dump(out, fh)
        print(f"countries {res}: {len(out)}")


if __name__ == "__main__":
    build_countries()
    build_basemap()
