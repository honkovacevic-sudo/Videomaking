"""The Strategist — map & chart motion-graphics engine for vertical Shorts.

Everything is drawn with Skia onto a 1080x1920 canvas, frame by frame, and
streamed into ffmpeg. An episode is just a camera path plus a list of
timed elements (see episodes/*.py).
"""
from __future__ import annotations

import math
import pickle
import random
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import skia

from .geo import WORLD, project

W, H, FPS = 1080, 1920, 30
FOCUS_Y = 0.42 * H          # where the camera centre sits on screen
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

# ----------------------------------------------------------------------------
# Brand palette
# ----------------------------------------------------------------------------
PALETTE = {
    "white": "#FFFFFF",
    "yellow": "#FFC83D",      # highlight / brand accent
    "blue": "#3B63E0",        # "our side" / neutral highlight
    "red": "#E5383B",         # threat / adversary
    "green": "#2FB36D",
    "grey": "#8E959E",
    "ink": "#0D0F14",         # tag & card background
    "ocean": "#071631",
}


def C(name_or_hex: str, a: float = 1.0) -> int:
    h = PALETTE.get(name_or_hex, name_or_hex).lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return skia.Color(r, g, b, int(max(0, min(1, a)) * 255))


# ----------------------------------------------------------------------------
# Easing
# ----------------------------------------------------------------------------
def clamp01(x):
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_in_out(x):
    x = clamp01(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out(x):
    x = clamp01(x)
    return 1 - (1 - x) ** 3


def ease_out_back(x, k=1.9):
    x = clamp01(x)
    return 1 + (k + 1) * (x - 1) ** 3 + k * (x - 1) ** 2


# ----------------------------------------------------------------------------
# Assets (loaded once, shared by forked render workers)
# ----------------------------------------------------------------------------
class _Assets:
    def __init__(self):
        self._basemap = None
        self._countries = {}
        self._paths = {}
        self._fonts = {}
        self._grain = None
        self._terrain = None

    @property
    def basemap(self) -> skia.Image:
        if self._basemap is None:
            from PIL import Image
            arr = np.asarray(Image.open(ASSETS / "basemap_mercator.png").convert("RGBA"))
            self._basemap = skia.Image.fromarray(np.ascontiguousarray(arr), colorType=skia.kRGBA_8888_ColorType)
        return self._basemap

    def countries(self, res: str) -> dict:
        if res not in self._countries:
            with open(ASSETS / f"countries_{res}.pkl", "rb") as fh:
                self._countries[res] = pickle.load(fh)
        return self._countries[res]

    def path(self, name: str, res: str = "10m") -> skia.Path:
        key = (name, res)
        if key not in self._paths:
            c = self.countries(res).get(name)
            if c is None:
                raise KeyError(f"Unknown country '{name}'. Known: {sorted(self.countries(res))}")
            p = skia.Path()
            p.setFillType(skia.PathFillType.kEvenOdd)
            for ring in c["rings"]:
                p.addPoly([skia.Point(float(x), float(y)) for x, y in ring], True)
            self._paths[key] = p
        return self._paths[key]

    def font(self, weight: str = "Black", size: float = 60) -> skia.Font:
        if weight not in self._fonts:
            self._fonts[weight] = skia.Typeface.MakeFromFile(str(ASSETS / "fonts" / f"InterDisplay-{weight}.otf"))
        f = skia.Font(self._fonts[weight], size)
        f.setEdging(skia.Font.Edging.kAntiAlias)
        f.setSubpixel(True)
        return f

    @property
    def terrain(self) -> skia.Image:
        """Tileable fractal noise (1/f spectrum) used as fine land texture."""
        if self._terrain is None:
            rng = np.random.default_rng(11)
            n = 1024
            f = np.fft.rfft2(rng.standard_normal((n, n)))
            ky = np.fft.fftfreq(n)[:, None]
            kx = np.fft.rfftfreq(n)[None, :]
            k = np.sqrt(kx ** 2 + ky ** 2); k[0, 0] = 1
            z = np.fft.irfft2(f / k ** 1.15, s=(n, n))
            z = (z - z.mean()) / (z.std() * 3.2)
            v = np.clip(128 + z * 127, 0, 255).astype(np.uint8)
            self._terrain = skia.Image.fromarray(np.stack([v, v, v, np.full_like(v, 255)], -1),
                                                 colorType=skia.kRGBA_8888_ColorType)
        return self._terrain

    @property
    def grain(self) -> skia.Image:
        if self._grain is None:
            rng = np.random.default_rng(7)
            n = rng.integers(0, 256, (384, 384), dtype=np.uint8)
            arr = np.stack([n, n, n, np.full_like(n, 255)], -1)
            self._grain = skia.Image.fromarray(arr, colorType=skia.kRGBA_8888_ColorType)
        return self._grain


A = _Assets()


def load_all(res_list=("10m", "50m")):
    _ = A.basemap, A.grain, A.terrain
    for r in res_list:
        A.countries(r)


# ----------------------------------------------------------------------------
# Camera
# ----------------------------------------------------------------------------
@dataclass
class Key:
    t: float
    lon: float
    lat: float
    span: float          # horizontal field of view in degrees of longitude
    ease: str = "inout"


class Camera:
    """Keyframed camera. Moves between keys use ease-in-out; zoom is
    interpolated in log space so it feels constant-speed. A slow push-in
    (drift) keeps static shots alive."""

    def __init__(self, keys: list[Key], drift: float = 0.018):
        self.keys = sorted(keys, key=lambda k: k.t)
        self.drift = drift

    def at(self, t: float):
        ks = self.keys
        if t <= ks[0].t:
            a = b = ks[0]; u = 0.0
        elif t >= ks[-1].t:
            a = b = ks[-1]; u = 0.0
        else:
            i = max(j for j in range(len(ks)) if ks[j].t <= t)
            a, b = ks[i], ks[i + 1]
            u = (t - a.t) / (b.t - a.t)
            u = ease_in_out(u) if b.ease == "inout" else ease_out(u) if b.ease == "out" else u
        ax, ay = project(a.lon, a.lat)
        bx, by = project(b.lon, b.lat)
        cx, cy = ax + (bx - ax) * u, ay + (by - ay) * u
        span = math.exp(math.log(a.span) + (math.log(b.span) - math.log(a.span)) * u)
        span *= math.exp(-self.drift * t)
        s = W / (span / 360.0 * WORLD)
        return float(cx), float(cy), s

    def moves(self):
        """(start, end) of every camera move — used for whoosh SFX."""
        out = []
        for a, b in zip(self.keys, self.keys[1:]):
            if (a.lon, a.lat, a.span) != (b.lon, b.lat, b.span):
                out.append((a.t, b.t))
        return out


class Ctx:
    def __init__(self, surface, canvas, t, cam: Camera):
        self.surface, self.canvas, self.t = surface, canvas, t
        self.cx, self.cy, self.s = cam.at(t)
        self.matrix = skia.Matrix.MakeAll(self.s, 0, W / 2 - self.cx * self.s,
                                          0, self.s, FOCUS_Y - self.cy * self.s, 0, 0, 1)

    def w2s(self, x, y):
        return (x - self.cx) * self.s + W / 2, (y - self.cy) * self.s + FOCUS_Y

    def ll(self, lon, lat):
        x, y = project(lon, lat)
        return self.w2s(float(x), float(y))

    def view_bbox(self, pad=0.15):
        hw, top, bot = W / 2 / self.s, FOCUS_Y / self.s, (H - FOCUS_Y) / self.s
        p = pad * hw
        return self.cx - hw - p, self.cy - top - p, self.cx + hw + p, self.cy + bot + p

    def res(self):
        return "10m" if self.s > 2.2 else "50m"

    def countries_in_view(self, res=None):
        res = res or self.res()
        x0, y0, x1, y1 = self.view_bbox()
        for name, c in A.countries(res).items():
            bx0, by0, bx1, by1 = c["bbox"]
            if bx1 >= x0 and bx0 <= x1 and by1 >= y0 and by0 <= y1:
                yield name


# ----------------------------------------------------------------------------
# Drawing helpers
# ----------------------------------------------------------------------------
def paint(color, style="fill", width=1.0, blur=0.0, aa=True):
    p = skia.Paint(AntiAlias=aa, Color=color)
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(width)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        p.setStrokeCap(skia.Paint.kRound_Cap)
    if blur > 0:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur, False))
    return p


def text_width(text, font, tracking=0.0):
    return font.measureText(text) + tracking * max(0, len(text) - 1)


def draw_text(cv, text, x, y, font, color, align="left", tracking=0.0, shadow=0.0, stroke=0.0):
    """Draw single-line text with optional letter-spacing, soft shadow and outline."""
    w = text_width(text, font, tracking)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w

    def run(p, dx=0.0, dy=0.0):
        if tracking == 0:
            cv.drawString(text, x + dx, y + dy, font, p)
            return
        cx = x
        for ch in text:
            cv.drawString(ch, cx + dx, y + dy, font, p)
            cx += font.measureText(ch) + tracking

    alpha = skia.Color4f.FromColor(color).fA
    if shadow:
        run(paint(skia.Color(0, 0, 0, int(200 * alpha)), blur=shadow), 0, shadow * 0.45)
    if stroke:
        run(paint(skia.Color(0, 0, 0, int(150 * alpha)), "stroke", stroke))
    run(paint(color))
    return w


def rrect(cv, x, y, w, h, r, fill=None, stroke=None, sw=2.0, glow=None):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    if glow:
        cv.drawRRect(rr, paint(glow, blur=18))
    if fill is not None:
        cv.drawRRect(rr, paint(fill))
    if stroke is not None:
        cv.drawRRect(rr, paint(stroke, "stroke", sw))


def smooth_path(pts, tension=0.5):
    """Catmull-Rom spline through screen points -> skia.Path."""
    p = skia.Path()
    if len(pts) < 2:
        return p
    p.moveTo(*pts[0])
    ext = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) * tension / 3, p1[1] + (p2[1] - p0[1]) * tension / 3)
        c2 = (p2[0] - (p3[0] - p1[0]) * tension / 3, p2[1] - (p3[1] - p1[1]) * tension / 3)
        p.cubicTo(*c1, *c2, *p2)
    return p


# ----------------------------------------------------------------------------
# Elements
# ----------------------------------------------------------------------------
class El:
    """Base timed element. `a` = envelope alpha, `lt` = local time."""
    sfx_in: str | None = None

    def __init__(self, t0: float, t1: float, fade_in=0.35, fade_out=0.3):
        self.t0, self.t1, self.fi, self.fo = t0, t1, fade_in, fade_out

    def alpha(self, t):
        if t < self.t0 or t > self.t1:
            return 0.0
        a = clamp01((t - self.t0) / self.fi) if self.fi else 1.0
        b = clamp01((self.t1 - t) / self.fo) if self.fo else 1.0
        return ease_out(min(a, b))

    def render(self, ctx: Ctx):
        a = self.alpha(ctx.t)
        if a > 0.001:
            self.draw(ctx, a, ctx.t - self.t0)

    def draw(self, ctx, a, lt):
        raise NotImplementedError

    def shake(self, t):
        return 0.0

    def sfx(self):
        return [(self.t0, self.sfx_in)] if self.sfx_in else []


class Borders(El):
    """Thin borders/coastlines of every country in view, for context."""

    def __init__(self, t0=0, t1=999, alpha=0.22, fade_in=0.0):
        super().__init__(t0, t1, fade_in, 0.3)
        self.a = alpha

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        cv.save(); cv.concat(ctx.matrix)
        p = paint(C("white", self.a * a), "stroke", 1.4 / ctx.s)
        for n in ctx.countries_in_view():
            cv.drawPath(A.path(n, ctx.res()), p)
        cv.restore()


class Region(El):
    """Highlighted country (or group of countries) with glow + outline."""
    sfx_in = "pop"

    def __init__(self, names, t0, t1, color="blue", fill_alpha=0.78, glow=True, outline=True,
                 fade_in=0.45, fade_out=0.35, flash=True):
        super().__init__(t0, t1, fade_in, fade_out)
        self.names = [names] if isinstance(names, str) else list(names)
        self.color, self.fa, self.glow, self.outline, self.flash = color, fill_alpha, glow, outline, flash
        if color == "grey":
            self.sfx_in = None

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        res = "10m"
        flash = (1 - ease_out(lt / 0.6)) * 0.35 if self.flash else 0
        cv.save(); cv.concat(ctx.matrix)
        for n in self.names:
            path = A.path(n, res)
            if self.glow:
                cv.drawPath(path, paint(C("white", 0.75 * a), "stroke", 5 / ctx.s, blur=16))
            cv.drawPath(path, paint(C(self.color, min(1, self.fa + flash) * a)))
            if self.outline:
                cv.drawPath(path, paint(C("white", 0.95 * a), "stroke", 3.0 / ctx.s))
        cv.restore()


class Tag(El):
    """Boxed uppercase label (like the 'PRUSSIA' tag)."""
    sfx_in = "tick"

    def __init__(self, text, lon, lat, t0, t1, size=50, bg="ink", fg="white", dx=0, dy=0, tilt=0.0):
        super().__init__(t0, t1, 0.12, 0.25)
        self.text, self.lon, self.lat, self.size = text.upper(), lon, lat, size
        self.bg, self.fg, self.dx, self.dy, self.tilt = bg, fg, dx, dy, tilt

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        x, y = ctx.ll(self.lon, self.lat)
        x, y = x + self.dx, y + self.dy
        f = A.font("Black", self.size)
        tr = self.size * 0.06
        tw = text_width(self.text, f, tr)
        px, py = self.size * 0.42, self.size * 0.30
        bw, bh = tw + 2 * px, self.size * 0.98 + 2 * py
        sc = 0.55 + 0.45 * ease_out_back(lt / 0.32)
        cv.save(); cv.translate(x, y); cv.rotate(self.tilt); cv.scale(sc, sc)
        rrect(cv, -bw / 2, -bh / 2, bw, bh, 6, fill=C(self.bg, 0.93 * a), stroke=C("white", 0.35 * a),
              sw=2, glow=C("#000000", 0.6 * a))
        draw_text(cv, self.text, 0, self.size * 0.36, f, C(self.fg, a), "center", tr)
        cv.restore()


class Pin(El):
    """Pulsing dot with a leader line and a city-style label."""
    sfx_in = "tick"

    def __init__(self, text, lon, lat, t0, t1, dx=-120, dy=60, size=46, color="white"):
        super().__init__(t0, t1, 0.25, 0.25)
        self.text, self.lon, self.lat, self.dx, self.dy, self.size, self.color = text, lon, lat, dx, dy, size, color

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        x, y = ctx.ll(self.lon, self.lat)
        grow = ease_out(lt / 0.5)
        lx, ly = x + self.dx * grow, y + self.dy * grow
        cv.drawLine(x, y, lx, ly, paint(C("white", 0.9 * a), "stroke", 3))
        for k in range(2):
            ph = ((lt + k * 0.8) % 1.6) / 1.6
            cv.drawCircle(x, y, 12 + 38 * ph, paint(C(self.color, a * (1 - ph) * 0.8), "stroke", 3))
        cv.drawCircle(x, y, 12, paint(C("#000000", 0.5 * a), blur=6))
        cv.drawCircle(x, y, 10, paint(C(self.color, a)))
        f = A.font("ExtraBold", self.size)
        align = "right" if self.dx < 0 else "left" if self.dx > 0 else "center"
        off = -12 if self.dx < 0 else 12 if self.dx > 0 else 0
        draw_text(cv, self.text, lx + off, ly + self.size * 0.35, f, C("white", a * grow), align, shadow=10)


class WaterLabel(El):
    def __init__(self, text, lon, lat, t0, t1, size=32, angle=0.0, alpha=0.6):
        super().__init__(t0, t1, 0.6, 0.4)
        self.text, self.lon, self.lat, self.size, self.angle, self.al = text, lon, lat, size, angle, alpha

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        x, y = ctx.ll(self.lon, self.lat)
        cv.save(); cv.translate(x, y); cv.rotate(self.angle)
        draw_text(cv, self.text, 0, 0, A.font("MediumItalic", self.size), C("#BFD3FF", self.al * a),
                  "center", self.size * 0.18, shadow=6)
        cv.restore()


class Route(El):
    """Animated route/flow arrow along lon/lat waypoints."""
    sfx_in = "swoosh"

    def __init__(self, pts, t0, t1, draw_time=1.2, color="yellow", width=7, head=True, flow=True,
                 start_at=0.0):
        super().__init__(t0, t1, 0.05, 0.35)
        self.pts, self.dt, self.color, self.width, self.head, self.flow = pts, draw_time, color, width, head, flow
        self.start_at = start_at

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        sp = [ctx.ll(lo, la) for lo, la in self.pts]
        path = smooth_path(sp)
        pm = skia.PathMeasure(path, False)
        L = pm.getLength()
        prog = ease_in_out(lt / self.dt)
        seg = skia.Path()
        pm.getSegment(L * self.start_at * prog, L * prog, seg, True)
        w = self.width
        cv.drawPath(seg, paint(C(self.color, 0.55 * a), "stroke", w * 2.2, blur=10))
        cv.drawPath(seg, paint(C("#000000", 0.35 * a), "stroke", w + 4))
        cv.drawPath(seg, paint(C(self.color, a), "stroke", w))
        if self.flow and prog > 0.02:
            fp = paint(C("white", 0.7 * a), "stroke", w * 0.45)
            fp.setPathEffect(skia.DashPathEffect.Make([14, 26], -lt * 70))
            cv.drawPath(seg, fp)
        if self.head and prog > 0.02:
            pos, tan = pm.getPosTan(max(0.01, L * prog - 1))
            ang = math.degrees(math.atan2(tan.y(), tan.x()))
            cv.save(); cv.translate(pos.x(), pos.y()); cv.rotate(ang)
            s = w * 3.2
            tri = skia.Path.Polygon([skia.Point(s * 0.9, 0), skia.Point(-s * 0.6, -s * 0.75),
                                     skia.Point(-s * 0.6, s * 0.75)], True)
            cv.drawPath(tri, paint(C("#000000", 0.5 * a), blur=6))
            cv.drawPath(tri, paint(C(self.color, a)))
            cv.restore()


class Measure(El):
    """Distance callout between two lon/lat points."""
    sfx_in = "tick"

    def __init__(self, p1, p2, label, t0, t1, side=1, color="yellow"):
        super().__init__(t0, t1, 0.1, 0.3)
        self.p1, self.p2, self.label, self.side, self.color = p1, p2, label, side, color

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        (x1, y1), (x2, y2) = ctx.ll(*self.p1), ctx.ll(*self.p2)
        g = ease_in_out(lt / 0.6)
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax, ay = mx + (x1 - mx) * g, my + (y1 - my) * g
        bx, by = mx + (x2 - mx) * g, my + (y2 - my) * g
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n * 22, dx / n * 22
        p = paint(C(self.color, a), "stroke", 5)
        cv.drawLine(ax, ay, bx, by, paint(C(self.color, 0.6 * a), "stroke", 12, blur=8))
        cv.drawLine(ax, ay, bx, by, p)
        for (ex, ey) in ((ax, ay), (bx, by)):
            cv.drawLine(ex - nx, ey - ny, ex + nx, ey + ny, p)
        if g > 0.6:
            la = a * clamp01((g - 0.6) / 0.4)
            f = A.font("Black", 54)
            tw = text_width(self.label, f, 2)
            lx = mx + self.side * (tw / 2 + 60)
            rrect(cv, lx - tw / 2 - 22, my - 42, tw + 44, 82, 8, fill=C("ink", 0.92 * la),
                  stroke=C(self.color, 0.9 * la), sw=3)
            draw_text(cv, self.label, lx, my + 20, f, C(self.color, la), "center", 2)


class Stamp(El):
    """Slammed rubber-stamp text (like 'DELETED'). Screen coordinates."""
    sfx_in = "hit"

    def __init__(self, text, x, y, t0, t1, size=120, angle=-9, color="red"):
        super().__init__(t0, t1, 0.08, 0.3)
        self.text, self.x, self.y, self.size, self.angle, self.color = text.upper(), x, y, size, angle, color
        rng = random.Random(hash(text) & 0xFFFF)
        self.specks = [(rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), rng.uniform(1.2, 4.5)) for _ in range(260)]

    def shake(self, t):
        lt = t - self.t0
        return 0.0 if lt < 0.12 or lt > 0.5 else 16 * (1 - (lt - 0.12) / 0.38)

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        f = A.font("Black", self.size)
        tr = self.size * 0.05
        tw = text_width(self.text, f, tr)
        bw, bh = tw + self.size * 0.7, self.size * 1.25
        k = ease_out(lt / 0.16)
        sc = 2.3 - 1.3 * k
        cv.save(); cv.translate(self.x, self.y); cv.rotate(self.angle); cv.scale(sc, sc)
        cv.saveLayerAlpha(None, int(255 * a * clamp01(lt / 0.08)))
        col = C(self.color)
        rrect(cv, -bw / 2, -bh / 2, bw, bh, 14, fill=C("#000000", 0.25), stroke=col, sw=10)
        rrect(cv, -bw / 2 + 16, -bh / 2 + 16, bw - 32, bh - 32, 8, stroke=col, sw=4)
        draw_text(cv, self.text, 0, self.size * 0.36, f, col, "center", tr)
        erase = paint(C("#000000"))
        erase.setBlendMode(skia.BlendMode.kDstOut)
        for sx, sy, r in self.specks:
            cv.drawCircle(sx * bw, sy * bh, r, erase)
        cv.restore()
        cv.restore()


class Captions(El):
    """Bold karaoke-style captions. Wrap a word in *asterisks* to highlight it."""

    def __init__(self, segments, y=1300, size=84, max_w=880, stagger=0.11):
        super().__init__(0, 9999, 0, 0)
        self.segs, self.y, self.size, self.max_w, self.stagger = segments, y, size, max_w, stagger

    def _layout(self, text):
        f = A.font("Black", self.size)
        words, on = [], False
        for raw in text.split():
            if raw.startswith("*"):
                on = True
            words.append((raw.replace("*", ""), on))
            if raw.rstrip(".,!?:;'\"").endswith("*"):
                on = False
        lines, cur, cw = [], [], 0
        space = f.measureText(" ")
        for w, hl in words:
            ww = f.measureText(w)
            if cur and cw + space + ww > self.max_w:
                lines.append(cur); cur, cw = [], 0
            cur.append((w, hl, ww)); cw += (space if len(cur) > 1 else 0) + ww
        if cur:
            lines.append(cur)
        out, lh = [], self.size * 1.12
        y0 = self.y - (len(lines) - 1) * lh / 2
        for li, line in enumerate(lines):
            tot = sum(w[2] for w in line) + space * (len(line) - 1)
            x = W / 2 - tot / 2
            for w, hl, ww in line:
                out.append((w, hl, x + ww / 2, y0 + li * lh))
                x += ww + space
        return f, out

    def render(self, ctx):
        t = ctx.t
        for t0, t1, text in self.segs:
            if t0 <= t <= t1:
                self._draw_seg(ctx, text, t - t0, t1 - t)

    def _draw_seg(self, ctx, text, lt, remain):
        cv = ctx.canvas
        f, words = self._layout(text)
        out = clamp01(remain / 0.12)
        for i, (w, hl, cx, cy) in enumerate(words):
            wt = lt - i * self.stagger
            if wt <= 0:
                continue
            a = clamp01(wt / 0.08) * out
            sc = 0.65 + 0.35 * ease_out_back(wt / 0.2, 2.4)
            cv.save(); cv.translate(cx, cy); cv.scale(sc, sc)
            draw_text(cv, w, 0, self.size * 0.36, f, C("yellow" if hl else "white", a), "center",
                      shadow=14, stroke=8)
            cv.restore()


class TopCard(El):
    """Hook card at the top (kicker / big title / sub-line)."""
    sfx_in = "whoosh_short"

    def __init__(self, kicker, title, sub, t0, t1, y=230):
        super().__init__(t0, t1, 0.35, 0.3)
        self.k, self.title, self.sub, self.y = kicker.upper(), title.upper(), sub, y

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        fk, ft, fs = A.font("Bold", 26), A.font("Black", 72), A.font("SemiBold", 32)
        tw = max(text_width(self.k, fk, 5), text_width(self.title, ft, 2), text_width(self.sub, fs))
        bw, bh = tw + 90, 245
        dy = -40 * (1 - ease_out(lt / 0.45))
        x0, y0 = W / 2 - bw / 2, self.y - bh / 2 + dy
        rrect(cv, x0, y0, bw, bh, 18, fill=C("ink", 0.88 * a), stroke=C("white", 0.18 * a), sw=2,
              glow=C("#000000", 0.6 * a))
        draw_text(cv, self.k, W / 2, y0 + 56, fk, C("white", 0.75 * a), "center", 5)
        draw_text(cv, self.title, W / 2, y0 + 138, ft, C("yellow", a), "center", 2)
        uw = text_width(self.title, ft, 2) * ease_out((lt - 0.2) / 0.5)
        cv.drawRect(skia.Rect.MakeXYWH(W / 2 - uw / 2, y0 + 158, uw, 5), paint(C("yellow", a)))
        draw_text(cv, self.sub, W / 2, y0 + 210, fs, C("white", 0.85 * a), "center")


class Backdrop(El):
    """Blurs + darkens everything drawn so far (use before charts/end cards)."""

    def __init__(self, t0, t1, dark=0.6, blur=22, fade_in=0.4, fade_out=0.4):
        super().__init__(t0, t1, fade_in, fade_out)
        self.dark, self.blur = dark, blur

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        snap = ctx.surface.makeImageSnapshot()
        p = skia.Paint(ImageFilter=skia.ImageFilters.Blur(self.blur * a, self.blur * a, skia.TileMode.kClamp))
        cv.drawImage(snap, 0, 0, skia.SamplingOptions(), p)
        cv.drawRect(skia.Rect.MakeWH(W, H), paint(C("#04070D", self.dark * a)))


def _fmt(v, decimals):
    return f"{v:,.{decimals}f}"


class Donut(El):
    sfx_in = "rise"

    def __init__(self, t0, t1, value, center_label, title, caption, source, cy=800, r=225, color="yellow",
                 decimals=0, suffix="%"):
        super().__init__(t0, t1, 0.3, 0.35)
        self.v, self.cl, self.title, self.cap, self.src = value, center_label, title.upper(), caption, source
        self.cy, self.r, self.color, self.dec, self.suffix = cy, r, color, decimals, suffix

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        draw_text(cv, self.title, W / 2, self.cy - self.r - 95, A.font("ExtraBold", 40), C("white", 0.9 * a),
                  "center", 4)
        rect = skia.Rect.MakeXYWH(W / 2 - self.r, self.cy - self.r, 2 * self.r, 2 * self.r)
        th = 62
        cv.drawOval(rect, paint(C("white", 0.12 * a), "stroke", th))
        prog = ease_in_out((lt - 0.2) / 1.4)
        sweep = 360 * self.v / 100 * prog
        arc = skia.Path(); arc.addArc(rect, -90, max(0.01, sweep))
        gp = paint(C(self.color, 0.6 * a), "stroke", th, blur=18); gp.setStrokeCap(skia.Paint.kButt_Cap)
        cv.drawPath(arc, gp)
        sp = paint(C(self.color, a), "stroke", th); sp.setStrokeCap(skia.Paint.kButt_Cap)
        cv.drawPath(arc, sp)
        draw_text(cv, _fmt(self.v * prog, self.dec) + self.suffix, W / 2, self.cy + 40, A.font("Black", 150),
                  C("white", a), "center")
        draw_text(cv, self.cl, W / 2, self.cy + 95, A.font("SemiBold", 34), C("white", 0.7 * a), "center")
        draw_text(cv, self.cap, W / 2, self.cy + self.r + 100, A.font("Bold", 42), C("white", a), "center")
        draw_text(cv, self.src, W / 2, self.cy + self.r + 150, A.font("Medium", 24), C("white", 0.45 * a),
                  "center")


class Bars(El):
    """Horizontal bar comparison with count-up values."""
    sfx_in = "rise"

    def __init__(self, t0, t1, title, items, unit, source, y=560, decimals=1, stagger=0.35):
        super().__init__(t0, t1, 0.3, 0.35)
        self.title, self.items, self.unit, self.src = title.upper(), items, unit, source
        self.y, self.dec, self.stagger = y, decimals, stagger

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        draw_text(cv, self.title, W / 2, self.y, A.font("ExtraBold", 40), C("white", 0.9 * a), "center", 4)
        draw_text(cv, self.unit, W / 2, self.y + 48, A.font("Medium", 30), C("white", 0.55 * a), "center")
        vmax = max(v for _, v, _ in self.items)
        x0, maxw, bh, gap = 110, 860, 84, 175
        for i, (label, v, col) in enumerate(self.items):
            y = self.y + 140 + i * gap
            p = ease_in_out((lt - 0.3 - i * self.stagger) / 1.1)
            draw_text(cv, label, x0, y, A.font("Bold", 38), C("white", a * clamp01(p * 4)))
            bw = max(4, maxw * v / vmax * p)
            rrect(cv, x0, y + 22, maxw, bh, 10, fill=C("white", 0.08 * a))
            rrect(cv, x0, y + 22, bw, bh, 10, fill=C(col, a), glow=C(col, 0.45 * a))
            vt = _fmt(v * p, self.dec)
            f = A.font("Black", 56)
            inside = bw > text_width(vt, f) + 60
            draw_text(cv, vt, x0 + bw - 24 if inside else x0 + bw + 22, y + 22 + bh / 2 + 20, f,
                      C("ink" if inside else "white", a), "right" if inside else "left")
        draw_text(cv, self.src, W / 2, self.y + 140 + len(self.items) * gap + 30, A.font("Medium", 24),
                  C("white", 0.45 * a), "center")


class EndCard(El):
    sfx_in = "hit_soft"

    def __init__(self, t0, t1, cta="FOLLOW FOR DAILY STRATEGY"):
        super().__init__(t0, t1, 0.4, 0.3)
        self.cta = cta

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        y = 760
        sc = 0.85 + 0.15 * ease_out_back(lt / 0.5)
        cv.save(); cv.translate(W / 2, y); cv.scale(sc, sc)
        draw_logo(cv, 0, -150, 120, a)
        draw_text(cv, "THE STRATEGIST", 0, 40, A.font("Black", 92), C("white", a), "center", 4, shadow=16)
        draw_text(cv, "GEOPOLITICS  ·  ECONOMICS  ·  MARKETS", 0, 105, A.font("Bold", 30), C("yellow", a),
                  "center", 4)
        cv.restore()
        pa = a * clamp01((lt - 0.5) / 0.3)
        f = A.font("Black", 38)
        tw = text_width(self.cta, f, 3)
        rrect(cv, W / 2 - tw / 2 - 40, y + 190, tw + 80, 84, 42, fill=C("yellow", pa), glow=C("yellow", 0.4 * pa))
        draw_text(cv, self.cta, W / 2, y + 245, f, C("ink", pa), "center", 3)


def draw_logo(cv, x, y, size, a=1.0):
    """Brand mark: a compass-style diamond with a yellow core."""
    s = size / 2
    outer = skia.Path.Polygon([skia.Point(x, y - s), skia.Point(x + s, y), skia.Point(x, y + s),
                               skia.Point(x - s, y)], True)
    inner = skia.Path.Polygon([skia.Point(x, y - s * 0.52), skia.Point(x + s * 0.52, y),
                               skia.Point(x, y + s * 0.52), skia.Point(x - s * 0.52, y)], True)
    cv.drawPath(outer, paint(C("yellow", 0.5 * a), blur=14))
    cv.drawPath(outer, paint(C("white", a), "stroke", max(2, size * 0.06)))
    cv.drawPath(inner, paint(C("yellow", a)))


class Watermark(El):
    def __init__(self):
        super().__init__(0, 9999, 0, 0)

    def draw(self, ctx, a, lt):
        cv = ctx.canvas
        draw_logo(cv, 74, 92, 34, 0.85)
        draw_text(cv, "THE STRATEGIST", 104, 102, A.font("ExtraBold", 28), C("white", 0.8), tracking=4, shadow=6)


# ----------------------------------------------------------------------------
# Episode + frame rendering
# ----------------------------------------------------------------------------
@dataclass
class Episode:
    duration: float
    camera: Camera
    elements: list
    ocean_tint: bool = True
    watermark: bool = True

    def sfx_events(self):
        ev = []
        for el in self.elements:
            ev += [e for e in el.sfx() if e[1]]
        for a, b in self.camera.moves():
            ev.append((a, "whoosh", b - a))
        return ev


def draw_map(ctx: Ctx, ep: Episode):
    cv = ctx.canvas
    cv.save(); cv.concat(ctx.matrix)
    cv.drawImage(A.basemap, 0, 0, skia.SamplingOptions(skia.CubicResampler.Mitchell()), None)
    cv.restore()
    # Fine terrain texture on land when zoomed in (masks the soft satellite pixels).
    ta = clamp01((math.log2(max(ctx.s, 1e-3)) - 1.3) / 2.0) * 0.22
    if ta > 0.01:
        land = skia.Path()
        for n in ctx.countries_in_view():
            land.addPath(A.path(n, ctx.res()))
        cv.save(); cv.concat(ctx.matrix)
        cv.clipPath(land, skia.ClipOp.kIntersect, True)
        tp = skia.Paint(Shader=A.terrain.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat,
                                                    skia.SamplingOptions(skia.FilterMode.kLinear),
                                                    skia.Matrix.Scale(10 / 1024, 10 / 1024)))
        tp.setAlphaf(ta)
        tp.setBlendMode(skia.BlendMode.kOverlay)
        cv.drawPaint(tp)
        cv.restore()
    if ep.ocean_tint:
        # Crisp ocean with sharp coastlines — hides the softness of the satellite
        # image on close zooms. Stronger the closer we are.
        oa = clamp01(0.25 + 0.27 * math.log2(max(ctx.s, 1e-3)))
        cv.saveLayer(None, None)
        cv.drawPaint(paint(C("ocean", oa)))
        clear = paint(C("#000000")); clear.setBlendMode(skia.BlendMode.kClear)
        cv.save(); cv.concat(ctx.matrix)
        for n in ctx.countries_in_view():
            cv.drawPath(A.path(n, ctx.res()), clear)
        cv.restore()
        cv.restore()
    # grade: overall darken + vignette + caption/top gradients
    cv.drawPaint(paint(C("#000000", 0.18)))
    vg = skia.Paint(Shader=skia.GradientShader.MakeRadial(
        skia.Point(W / 2, FOCUS_Y), H * 0.72, [C("#000000", 0), C("#000000", 0), C("#000000", 0.62)], [0, 0.45, 1]))
    cv.drawPaint(vg)
    bot = skia.Paint(Shader=skia.GradientShader.MakeLinear(
        [skia.Point(0, H * 0.55), skia.Point(0, H)], [C("#000000", 0), C("#000000", 0.55)]))
    cv.drawRect(skia.Rect.MakeXYWH(0, H * 0.55, W, H * 0.45), bot)


def render_frame(ep: Episode, t: float, fi: int = 0) -> np.ndarray:
    surface = skia.Surface.MakeRasterN32Premul(W, H)
    cv = surface.getCanvas()
    cv.clear(C("#02060E"))
    ctx = Ctx(surface, cv, t, ep.camera)
    sh = sum(el.shake(t) for el in ep.elements)
    if sh:
        rng = random.Random(fi)
        cv.translate(rng.uniform(-sh, sh), rng.uniform(-sh, sh))
    draw_map(ctx, ep)
    for el in ep.elements:
        el.render(ctx)
    if ep.watermark:
        Watermark().render(ctx)
    # film grain
    rng = random.Random(fi * 31 + 7)
    gp = skia.Paint(Shader=A.grain.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(),
                                              skia.Matrix.Translate(rng.uniform(0, 384), rng.uniform(0, 384))))
    gp.setAlphaf(0.06)
    gp.setBlendMode(skia.BlendMode.kOverlay)
    cv.drawPaint(gp)
    return surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
