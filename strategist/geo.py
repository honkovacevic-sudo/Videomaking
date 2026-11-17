"""Web Mercator helpers shared by asset prep and the renderer."""
import math

import numpy as np

WORLD = 4096  # side length (px) of the full Mercator world image


def project(lon, lat):
    """lon/lat (degrees, scalars or arrays) -> Mercator world pixels."""
    lon = np.asarray(lon, dtype=np.float64)
    lat = np.radians(np.clip(np.asarray(lat, dtype=np.float64), -85.05, 85.05))
    x = (lon + 180.0) / 360.0 * WORLD
    y = WORLD / 2 - WORLD / (2 * math.pi) * np.log(np.tan(math.pi / 4 + lat / 2))
    return x, y


def unproject(x, y):
    lon = x / WORLD * 360.0 - 180.0
    lat = math.degrees(math.atan(math.sinh((WORLD / 2 - y) / (WORLD / (2 * math.pi)))))
    return lon, lat
