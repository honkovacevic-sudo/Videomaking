"""Still-graphic toolkit in The Strategist house style (see DESIGN.md).

Boards are 1080x1920 PNGs built from: text styles, flat maps, icons,
tables, timelines and unit charts.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import skia

from .geo import project
from .theme import COLORS, SAFE, TYPE
from .engine import A as _ASSETS  # country geometry cache

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
_FACES: dict = {}


def col(name, a=1.0):
    h = COLORS.get(name, name).lstrip("#")
    return skia.Color(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), int(max(0, min(1, a)) * 255))


def font(style_or_file, size=None):
    stem, sz = TYPE.get(style_or_file, (style_or_file, size))
    if stem not in _FACES:
        p = FONTS / f"{stem}.ttf"
        _FACES[stem] = skia.Typeface.MakeFromFile(str(p if p.exists() else FONTS / f"{stem}.otf"))
    f = skia.Font(_FACES[stem], size or sz)
    f.setEdging(skia.Font.Edging.kSubpixelAntiAlias)
    f.setSubpixel(True)
    return f


def P(color, style="fill", w=1.0, blur=0.0, cap="round"):
    p = skia.Paint(AntiAlias=True, Color=color)
    if style == "stroke":
        p.setStyle(skia.Paint.kStroke_Style)
        p.setStrokeWidth(w)
        p.setStrokeJoin(skia.Paint.kRound_Join)
        p.setStrokeCap(skia.Paint.kRound_Cap if cap == "round" else skia.Paint.kButt_Cap)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur, False))
    return p


class Board:
    def __init__(self, w=1080, h=1920, brand=True, brand_x=None):
        self.w, self.h = w, h
        self.surface = skia.Surface.MakeRasterN32Premul(w, h)
        self.cv = self.surface.getCanvas()
        self.cv.clear(col("bg"))           # pure black, no vignette / lighting
        self.brand_x = brand_x if brand_x is not None else SAFE["left"]
        if brand:
            self.brand()

    # ------------------------------------------------------------- text ----
    def text(self, s, x, y, style="body", color="text", align="left", tracking=0.0, max_w=None,
             lh=1.3, hl="orange", alpha=1.0):
        """Draw (optionally wrapped) text. *word spans* render in the highlight colour.
        Returns the y of the next line."""
        f = font(style)
        size = f.getSize()
        tokens, on = [], False
        for raw in s.split(" "):
            if raw.startswith("*"):
                on = True
            tokens.append((raw.replace("*", ""), on))
            if raw.endswith("*") or raw.rstrip(".,;:!?").endswith("*"):
                on = False
        space = f.measureText(" ") + tracking

        def wlen(t):
            return f.measureText(t) + tracking * max(0, len(t) - 1)

        lines, cur, cw = [], [], 0.0
        for t, h in tokens:
            tw = wlen(t)
            if max_w and cur and cw + space + tw > max_w:
                lines.append((cur, cw)); cur, cw = [], 0.0
            cw += (space if cur else 0) + tw
            cur.append((t, h, tw))
        if cur:
            lines.append((cur, cw))
        for i, (line, lw) in enumerate(lines):
            xx = x - lw / 2 if align == "center" else x - lw if align == "right" else x
            yy = y + i * size * lh
            for t, h, tw in line:
                self._run(t, xx, yy, f, col(hl if h else color, alpha), tracking)
                xx += tw + space
        return y + len(lines) * size * lh

    def _run(self, t, x, y, f, c, tracking):
        p = P(c)
        if not tracking:
            self.cv.drawString(t, x, y, f, p); return
        for ch in t:
            self.cv.drawString(ch, x, y, f, p)
            x += f.measureText(ch) + tracking

    def width(self, s, style="body", tracking=0.0):
        f = font(style)
        return f.measureText(s) + tracking * max(0, len(s) - 1)

    # ----------------------------------------------------------- blocks ----
    def brand(self):
        self.text("THE STRATEGIST", self.brand_x, 121, "meta", "muted", tracking=4)

    def header(self, kicker, title, y=250, title_color="orange", sub=None):
        self.text(kicker.upper(), SAFE["left"], y, "kicker", "muted", tracking=4)
        y2 = self.text(title, SAFE["left"], y + 82, "title", title_color, max_w=SAFE["right"] - SAFE["left"], lh=1.08)
        if sub:
            y2 = self.text(sub, SAFE["left"], y2 + 4, "subtitle", "muted", max_w=900)
        return y2

    def source(self, s, y=1500):
        self.text(s, SAFE["left"], y, "meta", "faint", max_w=SAFE["right"] - SAFE["left"])

    def rule(self, y, x0=None, x1=None, c="grid", w=2):
        self.cv.drawLine(x0 or SAFE["left"], y, x1 or SAFE["right"], y, P(col(c), "stroke", w))

    def save(self, path):
        from PIL import Image
        arr = self.surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        Image.fromarray(arr[..., :3]).save(path)
        return path


# ---------------------------------------------------------------- maps ------
class FlatMap:
    """Flat vector map fitted into a rectangle on a board."""

    def __init__(self, board, bbox, rect, res="50m", fade=60):
        self.b, self.cv = board, board.cv
        lon0, lat0, lon1, lat1 = bbox
        x0, y1 = project(lon0, lat0)
        x1, y0 = project(lon1, lat1)
        rx, ry, rw, rh = rect
        s = min(rw / (x1 - x0), rh / (y1 - y0))
        self.s = float(s)
        self.ox = rx + (rw - (x1 - x0) * s) / 2 - float(x0) * s
        self.oy = ry + (rh - (y1 - y0) * s) / 2 - float(y0) * s
        self.rect = skia.Rect.MakeXYWH(rx, ry, rw, rh)
        self.res, self.fade = res, fade
        self.wbox = (float(x0), float(y0), float(x1), float(y1))

    def xy(self, lon, lat):
        x, y = project(lon, lat)
        return float(x) * self.s + self.ox, float(y) * self.s + self.oy

    def _visible(self):
        x0, y0, x1, y1 = self.wbox
        mx, my = (x1 - x0) * 0.3, (y1 - y0) * 0.3
        for n, c in _ASSETS.countries(self.res).items():
            bx0, by0, bx1, by1 = c["bbox"]
            if bx1 >= x0 - mx and bx0 <= x1 + mx and by1 >= y0 - my and by0 <= y1 + my and n != "Antarctica":
                yield n

    def land_path(self):
        """Union of all visible land, in screen coordinates (for clipping)."""
        m = skia.Matrix.MakeAll(self.s, 0, self.ox, 0, self.s, self.oy, 0, 0, 1)
        out = skia.Path()
        for n in self._visible():
            out.addPath(_ASSETS.path(n, self.res), m)
        return out

    def land(self, borders=False, names=None, fill="land", edge="land_edge"):
        cv = self.cv
        cv.save()
        cv.clipRect(self.rect, True)
        cv.saveLayer(None, None)
        cv.save(); cv.concat(skia.Matrix.MakeAll(self.s, 0, self.ox, 0, self.s, self.oy, 0, 0, 1))
        fp = P(col(fill))
        ep = P(col(edge), "stroke", 1.6 / self.s)
        for n in (names or self._visible()):
            path = _ASSETS.path(n, self.res)
            cv.drawPath(path, fp)
            if borders:
                cv.drawPath(path, ep)
        cv.restore()
        if self.fade:
            self._fade_edges()
        cv.restore()
        cv.restore()

    def highlight(self, names, color="orange", alpha=0.85, edge="text", edge_a=0.6):
        cv = self.cv
        cv.save(); cv.clipRect(self.rect, True)
        cv.concat(skia.Matrix.MakeAll(self.s, 0, self.ox, 0, self.s, self.oy, 0, 0, 1))
        for n in ([names] if isinstance(names, str) else names):
            path = _ASSETS.path(n, self.res)
            cv.drawPath(path, P(col(color, alpha)))
            cv.drawPath(path, P(col(edge, edge_a), "stroke", 2 / self.s))
        cv.restore()

    def _fade_edges(self):
        r, f = self.rect, self.fade
        for (p0, p1, rect) in (
            ((r.left(), r.top()), (r.left(), r.top() + f), skia.Rect.MakeLTRB(r.left(), r.top(), r.right(), r.top() + f)),
            ((r.left(), r.bottom()), (r.left(), r.bottom() - f), skia.Rect.MakeLTRB(r.left(), r.bottom() - f, r.right(), r.bottom())),
            ((r.left(), 0), (r.left() + f, 0), skia.Rect.MakeLTRB(r.left(), r.top(), r.left() + f, r.bottom())),
            ((r.right(), 0), (r.right() - f, 0), skia.Rect.MakeLTRB(r.right() - f, r.top(), r.right(), r.bottom())),
        ):
            p = skia.Paint(Shader=skia.GradientShader.MakeLinear(
                [skia.Point(*p0), skia.Point(*p1)], [col("#000000", 1), col("#000000", 0)]))
            p.setBlendMode(skia.BlendMode.kDstOut)
            self.cv.drawRect(rect, p)

    def city(self, lon, lat, label=None, color="text", r=7, ring=False, dx=14, dy=10, style="map_city",
             label_color="text", align="left"):
        x, y = self.xy(lon, lat)
        cv = self.cv
        cv.drawCircle(x, y, r * 2.4, P(col(color, 0.35), blur=r * 1.2))
        if ring:
            cv.drawCircle(x, y, r * 2.1, P(col(color, 0.9), "stroke", 3))
        cv.drawCircle(x, y, r, P(col(color)))
        if label:
            self.b.text(label, x + dx, y + dy, style, label_color, align=align)
        return x, y


# --------------------------------------------------------------- icons ------
def diamond(cv, x, y, size, c):
    s = size / 2
    outer = skia.Path.Polygon([skia.Point(x, y - s), skia.Point(x + s, y), skia.Point(x, y + s), skia.Point(x - s, y)], True)
    inner = skia.Path.Polygon([skia.Point(x, y - s * .45), skia.Point(x + s * .45, y), skia.Point(x, y + s * .45),
                               skia.Point(x - s * .45, y)], True)
    cv.drawPath(outer, P(c, "stroke", max(1.5, size * 0.08)))
    cv.drawPath(inner, P(c))


def icon_cross(cv, x, y, s, c, w=6):
    p = P(c, "stroke", w)
    cv.drawLine(x - s / 2, y - s / 2, x + s / 2, y + s / 2, p)
    cv.drawLine(x - s / 2, y + s / 2, x + s / 2, y - s / 2, p)


def icon_check(cv, x, y, s, c, w=6):
    path = skia.Path(); path.moveTo(x - s / 2, y); path.lineTo(x - s / 8, y + s * .38); path.lineTo(x + s / 2, y - s * .4)
    cv.drawPath(path, P(c, "stroke", w))


def icon_swords(cv, x, y, s, c):
    for sgn in (-1, 1):
        cv.save(); cv.translate(x, y); cv.rotate(45 * sgn)
        cv.drawLine(0, -s * .5, 0, s * .32, P(c, "stroke", s * .07))          # blade
        cv.drawLine(-s * .16, s * .3, s * .16, s * .3, P(c, "stroke", s * .07))  # guard
        cv.drawLine(0, s * .3, 0, s * .48, P(c, "stroke", s * .09))          # grip
        cv.restore()


def icon_coins(cv, x, y, s, c):
    for i in range(3):
        cy = y + s * .28 - i * s * .22
        r = skia.Rect.MakeXYWH(x - s * .38, cy - s * .12, s * .76, s * .24)
        cv.drawRect(skia.Rect.MakeXYWH(x - s * .38, cy, s * .76, s * .14), P(col("bg")))
        cv.drawOval(skia.Rect.MakeXYWH(x - s * .38, cy + s * .02, s * .76, s * .24), P(c, "stroke", s * .05))
        cv.drawLine(x - s * .38, cy + s * .14, x - s * .38, cy, P(c, "stroke", s * .05))
        cv.drawLine(x + s * .38, cy + s * .14, x + s * .38, cy, P(c, "stroke", s * .05))
        cv.drawOval(r, P(col("bg")))
        cv.drawOval(r, P(c, "stroke", s * .05))


def icon_crown(cv, x, y, s, c):
    pts = [(-.42, .25), (-.42, -.2), (-.21, .02), (0, -.32), (.21, .02), (.42, -.2), (.42, .25)]
    path = skia.Path.Polygon([skia.Point(x + a * s, y + b * s) for a, b in pts], True)
    cv.drawPath(path, P(c, "stroke", s * .06))
    for a, b in ((-.42, -.2), (0, -.32), (.42, -.2)):
        cv.drawCircle(x + a * s, y + b * s - s * .06, s * .05, P(c))
    cv.drawLine(x - s * .42, y + s * .36, x + s * .42, y + s * .36, P(c, "stroke", s * .06))


def icon_scales(cv, x, y, s, c):
    w = s * .055
    cv.drawLine(x, y - s * .38, x, y + s * .38, P(c, "stroke", w))
    cv.drawLine(x - s * .25, y + s * .4, x + s * .25, y + s * .4, P(c, "stroke", w))
    cv.drawLine(x - s * .42, y - s * .26, x + s * .42, y - s * .3, P(c, "stroke", w))
    for px, py in ((-.42, -.26), (.42, -.3)):
        bx, by = x + px * s, y + py * s
        cv.drawLine(bx, by, bx - s * .14, by + s * .3, P(c, "stroke", w * .7))
        cv.drawLine(bx, by, bx + s * .14, by + s * .3, P(c, "stroke", w * .7))
        arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(bx - s * .17, by + s * .14, s * .34, s * .3), 0, 180)
        cv.drawPath(arc, P(c, "stroke", w))
        cv.drawLine(bx - s * .17, by + s * .29, bx + s * .17, by + s * .29, P(c, "stroke", w))


def icon_junk(cv, x, y, s, c):
    """Chinese junk: upswept stern, slanted battened lug sails."""
    def pt(a, b):
        return skia.Point(x + a * s, y + b * s)
    hull = skia.Path()
    hull.moveTo(x + .52 * s, y - .02 * s)
    hull.quadTo(x + .40 * s, y + .26 * s, x + .22 * s, y + .27 * s)
    hull.lineTo(x - .28 * s, y + .27 * s)
    hull.quadTo(x - .46 * s, y + .18 * s, x - .54 * s, y - .16 * s)
    hull.lineTo(x - .40 * s, y + .02 * s)
    hull.close()
    cv.drawPath(hull, P(c))
    bg = P(col("bg"), "stroke", max(1.0, s * .035))
    for quad in (((-.33, -.66), (.02, -.76), (.05, -.06), (-.31, -.04)),
                 ((.10, -.54), (.36, -.62), (.40, -.06), (.12, -.05))):
        cv.drawPath(skia.Path.Polygon([pt(*q) for q in quad], True), P(c))
        (a0, b0), (a1, b1), (a2, b2), (a3, b3) = quad
        for k in (1, 2, 3):
            t = k / 4
            l = (a0 + (a3 - a0) * t, b0 + (b3 - b0) * t)
            r = (a1 + (a2 - a1) * t, b1 + (b2 - b1) * t)
            cv.drawLine(x + l[0] * s, y + l[1] * s, x + r[0] * s, y + r[1] * s, bg)


def icon_caravel(cv, x, y, s, c):
    """European caravel: curved hull, square + lateen sails."""
    hull = skia.Path()
    hull.moveTo(x - s * .5, y); hull.quadTo(x, y + s * .14, x + s * .5, y - s * .04)
    hull.lineTo(x + s * .32, y + s * .28); hull.lineTo(x - s * .36, y + s * .28); hull.close()
    cv.drawPath(hull, P(c))
    cv.drawLine(x - s * .05, y, x - s * .05, y - s * .7, P(c, "stroke", max(1, s * .04)))
    sq = skia.Path(); sq.moveTo(x - s * .3, y - s * .6); sq.quadTo(x - s * .05, y - s * .5, x + s * .2, y - s * .6)
    sq.lineTo(x + s * .17, y - s * .15); sq.quadTo(x - s * .05, y - s * .07, x - s * .27, y - s * .15); sq.close()
    cv.drawPath(sq, P(c))
    lat = skia.Path(); lat.moveTo(x + s * .3, y - s * .55); lat.lineTo(x + s * .46, y - s * .08); lat.lineTo(x + s * .26, y - s * .08); lat.close()
    cv.drawPath(lat, P(c))


def icon_waves(cv, x, y, s, c):
    """Three wavy lines: water / marsh (land reclamation)."""
    for k in range(3):
        yy = y + (k - 1) * s * 0.26
        path = skia.Path()
        path.moveTo(x - s * .45, yy)
        for j in range(3):
            x0 = x - s * .45 + j * s * .3
            path.cubicTo(x0 + s * .075, yy - s * .1, x0 + s * .225, yy + s * .1, x0 + s * .3, yy)
        cv.drawPath(path, P(c, "stroke", s * .07))


def icon_wheat(cv, x, y, s, c):
    """Ear of wheat: farming."""
    cv.drawLine(x, y + s * .48, x, y - s * .2, P(c, "stroke", s * .06))
    for k in range(4):
        gy = y - s * .3 + k * s * .17
        for sgn in (-1, 1):
            cv.save(); cv.translate(x + sgn * s * .11, gy); cv.rotate(sgn * 35)
            cv.drawOval(skia.Rect.MakeXYWH(-s * .07, -s * .12, s * .14, s * .24), P(c))
            cv.restore()
    cv.drawOval(skia.Rect.MakeXYWH(x - s * .07, y - s * .5, s * .14, s * .24), P(c))
