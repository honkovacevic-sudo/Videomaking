"""EP02 — McNeill, *The Pursuit of Power* — animated 16:9 (1920x1080) version.

Run:
  python episodes/mcneill_wide.py                 # full MP4 -> out/mcneill_wide.mp4
  python episodes/mcneill_wide.py --stills 4,12   # PNG frames at those seconds

Each scene is a function scene(b, t) drawing onto a Board at local time t.
Facts: see the checklist at the top of episodes/mcneill_stills.py.
"""
import argparse
import multiprocessing as mp
import random
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import skia  # noqa: E402

from strategist.audio import build_soundtrack  # noqa: E402
from strategist.engine import clamp01, ease_in_out, ease_out, ease_out_back  # noqa: E402
from strategist.stills import (Board, FlatMap, P, col, diamond, font, icon_caravel, icon_coins,  # noqa: E402
                               icon_cross, icon_crown, icon_junk, icon_scales, icon_swords)

W, H, FPS = 1920, 1080, 30
L, R = 120, 1800
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
SOURCE = "Source: W. H. McNeill, The Pursuit of Power (1982)"


def pr(t, t0, d=0.5):
    return ease_out(clamp01((t - t0) / d))


def T(b, s, x, y, style, color="text", t=0.0, t0=0.0, d=0.5, rise=18, **kw):
    """Text that fades and rises in at t0."""
    a = pr(t, t0, d)
    if a <= 0:
        return y
    return b.text(s, x, y + rise * (1 - a), style, color, alpha=a, **kw)


def dot(cv, x, y, r, c, a=1.0, ring=False, pulse_t=None):
    if a <= 0:
        return
    s = ease_out_back(a, 2.2)
    cv.drawCircle(x, y, r * 2.4 * s, P(col(c, 0.35 * a), blur=r * 1.2))
    if ring:
        cv.drawCircle(x, y, r * 2.1 * s, P(col(c, 0.9 * a), "stroke", 3))
    if pulse_t is not None and pulse_t > 0:
        ph = (pulse_t % 1.6) / 1.6
        cv.drawCircle(x, y, r * (2 + 4 * ph), P(col(c, a * (1 - ph) * 0.8), "stroke", 3))
    cv.drawCircle(x, y, r * s, P(col(c, a)))


def header(b, t, kicker, title, title_color="orange"):
    T(b, kicker.upper(), L, 205, "kicker", "muted", t, 0.05, tracking=4)
    T(b, title, L, 282, "title", title_color, t, 0.15)


def source(b, t, s, t0=0.8):
    T(b, s, L, 1040, "meta", "faint", t, t0, rise=0)


# ───────────────────────────────────────────────────────────── 1. cover
EUROPE = [(-9.14, 38.72), (-4.02, 39.86), (-0.88, 41.65), (-1.64, 42.81), (2.35, 48.86), (-0.13, 51.5),
          (-3.19, 55.95), (12.57, 55.68), (18.07, 59.33), (19.94, 50.06), (25.28, 54.69), (37.62, 55.75),
          (16.37, 48.21), (14.42, 50.09), (19.04, 47.50), (12.33, 45.44), (9.19, 45.46), (8.93, 44.41),
          (11.25, 43.77), (12.50, 41.90), (14.27, 40.85), (28.98, 41.01), (4.48, 51.03), (10.69, 53.87),
          (7.45, 46.95), (11.34, 44.49), (10.40, 43.72), (13.40, 52.52), (6.96, 50.94), (30.52, 50.45)]
_order = list(range(len(EUROPE)))
random.Random(4).shuffle(_order)


def scene_cover(b, t):
    cv = b.cv
    T(b, "WILLIAM H. MCNEILL  ·  THE PURSUIT OF POWER", L, 205, "kicker", "muted", t, 0.05, tracking=4)
    T(b, "One empire.", L, 300, "title", "orange", t, 0.2)
    T(b, "Many rivals.", L, 385, "title", "text", t, 0.45)
    m = FlatMap(b, (-12, 4, 134, 68), (690, 170, 1230, 800), fade=80)
    a = pr(t, 0.3, 1.2)
    cv.saveLayerAlpha(None, int(255 * a)); m.land(); cv.restore()
    for k, i in enumerate(_order):
        x, y = m.xy(*EUROPE[i])
        dot(cv, x, y, 7, "orange", pr(t, 1.4 + k * 0.07, 0.35))
    ex, ey = m.xy(20, 64)
    T(b, "EUROPE", ex, ey - 30, "map_area", "orange", t, 3.2, align="center")
    T(b, "dozens of rival courts", ex, ey + 4, "map_city", "muted", t, 3.4, align="center")
    bx, by = m.xy(116.40, 39.90)
    dot(cv, bx, by, 12, "text", pr(t, 4.0, 0.5), ring=True, pulse_t=t - 4.3)
    T(b, "BEIJING", bx - 36, by - 40, "map_area", "text", t, 4.3, align="right")
    T(b, "one emperor", bx - 36, by - 6, "map_city", "muted", t, 4.5, align="right")
    T(b, "China had the money,", L, 640, "label", "text", t, 5.2)
    T(b, "the ships and the technology.", L, 684, "label", "text", t, 5.4)
    T(b, "What it lacked was", L, 790, "h2", "text", t, 6.2)
    T(b, "*competition.*", L, 868, "title", "text", t, 6.6)
    a = pr(t, 1.0)
    if a:
        cv.drawCircle(L + 8, 965, 6, P(col("orange", a)))
    T(b, "Seats of independent power, c. 1500 (selection)", L + 26, 974, "meta", "muted", t, 1.0, rise=0)
    source(b, t, SOURCE + "  ·  Coastlines: Natural Earth")


# ───────────────────────────────────────────────────────────── 2. ladder
ROWS = [
    (icon_swords, "Plunder", "Earliest times",
     "Distance was vast and travel slow. Cities and peoples dealt with each other by raiding."),
    (icon_coins, "Conquer & tax", "Ancient empires",
     "Rulers learned that taxing the conquered paid better, and longer, than looting them."),
    (icon_crown, "Command", "Bronze to the stirrup",
     "Elites with new military tech seized the surplus. Priests and kings ruled by fear, tradition and faith."),
    (icon_scales, "Markets", "From the 11th century, China first",
     "Prices and money began to coordinate human effort across long distances."),
]


def scene_power(b, t):
    cv = b.cv
    header(b, t, "From plunder to markets", "How power was organised")
    y0, gap, starts = 420, 150, [0.8, 2.4, 4.0, 5.6]
    # progress line grows with the rows
    reach = 0.0
    for i, s0 in enumerate(starts):
        reach = max(reach, (i + pr(t, s0, 0.8)) if t >= s0 else reach)
    yl = y0 - 30 + gap * min(reach, 3.3)
    cv.drawLine(L + 10, y0 - 30, L + 10, yl, P(col("orange_dim"), "stroke", 4))
    for i, (ico, name, era, desc) in enumerate(ROWS):
        s0 = starts[i]
        a = pr(t, s0, 0.5)
        if a <= 0:
            continue
        y = y0 + i * gap
        nxt = starts[i + 1] if i + 1 < len(starts) else 99
        act = 1 - pr(t, nxt, 0.5)                 # active until the next row arrives
        last = i == len(ROWS) - 1
        if last:
            ba = pr(t, s0 + 0.3, 0.5)
            rr = skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L + 50, y - 58, R, y + 74), 10, 10)
            cv.drawRRect(rr, P(col("orange", 0.07 * ba)))
            cv.drawRRect(rr, P(col("orange", 0.5 * ba), "stroke", 2))
        mix = lambda on, off: on if act > 0.5 else off  # noqa: E731
        dot(cv, L + 10, y - 8, 9, mix("orange", "faint"), a)
        cv.save(); cv.translate(-30 * (1 - a), 0)
        ico(cv, L + 125, y + 2, 86, col(mix("orange", "muted"), a))
        b.text(name, L + 200, y, "h2", mix("orange", "text"), alpha=a)
        b.text(era.upper(), L + 200 + b.width(name, "h2") + 22, y - 4, "meta", mix("orange", "muted"), tracking=2,
               alpha=a)
        b.text(desc, L + 200, y + 48, "body", mix("text", "muted"), max_w=1420, alpha=a)
        cv.restore()
    T(b, "Every technology that shrank time and space (the horse, rail, the telegraph, the phone) "
         "reset this balance.", L, 1000, "body", "muted", t, 7.4)
    source(b, t, "", 99)


# ───────────────────────────────────────────────────────────── 3. Song
def scene_song(b, t):
    cv = b.cv
    header(b, t, "11th-century China  ·  Song dynasty", "Money meets power")
    m = FlatMap(b, (97, 19.5, 125, 42.5), (40, 330, 900, 660), fade=70)
    cv.saveLayerAlpha(None, int(255 * pr(t, 0.3, 1.0))); m.land(); cv.restore()
    cx, cy = m.xy(104.07, 30.67)
    dot(cv, cx, cy, 9, "orange", pr(t, 1.2), ring=True, pulse_t=t - 1.5)
    T(b, "Chengdu", cx - 26, cy - 14, "map_city", "text", t, 1.4, align="right")
    T(b, "1024: first state-issued", cx - 26, cy + 22, "meta", "orange", t, 1.6, align="right")
    T(b, "paper money", cx - 26, cy + 50, "meta", "orange", t, 1.6, align="right")
    kx, ky = m.xy(114.31, 34.80)
    dot(cv, kx, ky, 8, "text", pr(t, 2.2), ring=True)
    T(b, "Kaifeng", kx + 24, ky - 12, "map_city", "text", t, 2.4)
    T(b, "Song capital", kx + 24, ky + 22, "meta", "muted", t, 2.5)

    X = 1010
    a = pr(t, 3.0, 0.4)
    if a:
        v = 80 * ease_in_out(clamp01((t - 3.0) / 1.4))
        b.text(f"~{v:.0f}%", X - 8, 560, "big", "orange", alpha=a)
    T(b, "of government income paid the soldiers", X, 630, "label", "text", t, 3.4)
    T(b, "guarding the frontiers", X, 672, "label", "text", t, 3.4)
    by, bh, bw = 730, 56, R - X
    g = ease_in_out(clamp01((t - 4.4) / 1.0))
    if t > 4.2:
        cv.drawRect(skia.Rect.MakeXYWH(X, by, bw, bh), P(col("bg_raised", pr(t, 4.2, 0.3))))
        army = bw * 0.8 * g
        cv.drawRect(skia.Rect.MakeXYWH(X, by, army, bh), P(col("orange")))
        T(b, "ARMY", X + bw * 0.8 - 14, by + 38, "kicker", "bg", t, 5.3, align="right", tracking=3, rise=0)
        T(b, "OTHER", X + bw * 0.9, by + 38, "kicker", "muted", t, 5.3, align="center", tracking=3, rise=0)
    hc = ease_in_out(clamp01((t - 5.6) / 0.8))
    if hc:
        cash = bw * 0.8 * 0.4 * hc
        cv.save(); cv.clipRect(skia.Rect.MakeXYWH(X, by, cash, bh))
        for k in range(-10, 60):
            x = X + k * 16
            cv.drawLine(x, by + bh, x + bh, by, P(col("bg", 0.55), "stroke", 5, cap="butt"))
        cv.restore()
        cv.drawLine(X, by + bh + 16, X + cash, by + bh + 16, P(col("orange"), "stroke", 3))
    T(b, "~40% of it paid in cash", X, by + bh + 64, "label", "orange", t, 6.2)
    T(b, "A state that bought its army with money", X, 930, "body", "text", t, 7.0)
    T(b, "was already *running on markets.*", X, 972, "body", "text", t, 7.2)
    source(b, t, "Figures as cited by W. H. McNeill, The Pursuit of Power (1982)  ·  Coastlines: Natural Earth")


# ───────────────────────────────────────────────────────────── 4. fleets
def scene_fleets(b, t):
    cv = b.cv
    header(b, t, "The scale of Ming sea power", "1405 vs 1492")
    T(b, "ZHENG HE'S FIRST VOYAGE  ·  1405", L, 400, "kicker", "orange", t, 0.5, tracking=4)
    cols, px, py, s = 22, 42, 33, 29
    for i in range(317):
        r, c = divmod(i, cols)
        a = pr(t, 0.8 + (r * 0.16 + c * 0.012), 0.25)
        if a <= 0:
            continue
        x, y = L + 18 + c * px, 456 + r * py
        cv.save(); cv.translate(x, y); sc = ease_out_back(a, 2.0); cv.scale(sc, sc)
        icon_junk(cv, 0, 0, s, col("orange", a))
        cv.restore()
    n = int(317 * clamp01((t - 0.8) / 2.6))
    if t > 0.8:
        b.text(f"{n} ships  ·  ~{int(28000 * n / 317):,} men", L, 1000, "h2", "text", alpha=pr(t, 0.8))
    X = 1180
    cv.drawLine(X - 60, 380, X - 60, 1010, P(col("grid", pr(t, 3.8)), "stroke", 2))
    T(b, "COLUMBUS  ·  1492", X, 400, "kicker", "muted", t, 4.0, tracking=4)
    for i in range(3):
        a = pr(t, 4.3 + i * 0.2, 0.3)
        if a:
            cv.save(); cv.translate(X + 18 + i * px, 456); sc = ease_out_back(a, 2.0); cv.scale(sc, sc)
            icon_caravel(cv, 0, 0, s, col("text", a)); cv.restore()
    T(b, "3 ships  ·  ~90 men", X, 530, "h2", "text", t, 4.6)
    T(b, "Then, in 1433,", X, 800, "title", "text", t, 5.8)
    T(b, "China stopped", X, 880, "title", "orange", t, 6.2)
    T(b, "sailing.", X, 960, "title", "orange", t, 6.4)
    source(b, t, "Fleet figures: Ming records, commonly cited estimates  ·  1 icon = 1 ship")


# ───────────────────────────────────────────────────────────── 5. timeline
def scene_timeline(b, t):
    cv = b.cv
    header(b, t, "China turns inward  ·  Europe sails out", "Two paths after 1433")
    ay = 650
    x0, brk0, brk1, x1 = 330, 470, 540, 1780

    def X(yr):
        return x0 + (yr - 1000) / 100 * (brk0 - x0) if yr <= 1100 else brk1 + (yr - 1400) / 150 * (x1 - brk1)

    head = x0 + (x1 - x0) * ease_in_out(clamp01((t - 0.5) / 6.0))       # playhead sweeps left->right
    lp = P(col("grid"), "stroke", 3)
    cv.drawLine(x0, ay, min(head, brk0), ay, lp)
    if head > brk1:
        cv.drawLine(brk1, ay, head, ay, lp)
    if head > brk0:
        for xx in (brk0 + 14, brk1 - 14):
            p = skia.Path(); p.moveTo(xx - 5, ay + 16); p.cubicTo(xx + 6, ay + 6, xx - 6, ay - 6, xx + 5, ay - 16)
            cv.drawPath(p, P(col("faint"), "stroke", 3))
    for yr in (1000, 1100, 1400, 1450, 1500, 1550):
        if X(yr) <= head + 1:
            cv.drawLine(X(yr), ay - 10, X(yr), ay + 10, P(col("faint"), "stroke", 3))
            if yr in (1000, 1100, 1450, 1550):
                b.text(str(yr), X(yr), ay - 22, "meta", "faint", align="center")
    T(b, "CHINA", L, ay - 24, "kicker", "orange", t, 0.3, tracking=4, rise=0)
    T(b, "EUROPE", L, ay + 44, "kicker", "blue", t, 0.3, tracking=4, rise=0)
    if head > X(1405):   # treasure-voyage era bar
        cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(X(1405), ay - 9, min(head, X(1433)), ay - 1), 3, 3),
                     P(col("orange")))

    def event(yr, title, text, side, ly, color, align="left", w=380):
        """ly = baseline of the description's first line; block spans ly-56 .. ly+58."""
        if head < X(yr):
            return
        a = ease_out(clamp01((head - X(yr)) / 120))
        x = X(yr)
        dot(cv, x, ay, 7, color, a)
        top = ly - 58
        y_from = ay - 12 if side == "up" else ay + 12
        cv.drawLine(x, y_from, x, top, P(col(color, 0.6 * a), "stroke", 2))
        cv.drawLine(x, top, x + (14 if align == "left" else -14), top, P(col(color, 0.6 * a), "stroke", 2))
        tx = x + (14 if align == "left" else -14)
        b.text(title, tx, ly - 18 + 10 * (1 - a), "h2", color, align=align, alpha=a)
        b.text(text, tx, ly + 22 + 10 * (1 - a), "body", "text", align=align, max_w=w, lh=1.2, alpha=a)

    event(1024, "1024", "First state paper money", "up", 520, "orange", w=190)
    event(1405, "1405–33", "Treasure fleets reach India, Arabia, East Africa", "up", 400, "orange")
    event(1433, "1433", "Last voyage. The fleets are never sent again", "up", 540, "orange")
    event(1525, "1525", "Edict orders ocean-going ships destroyed", "up", 420, "orange", align="right")
    event(1415, "1415", "Portugal takes Ceuta and pushes down Africa", "down", 760, "blue")
    event(1488, "1488", "Dias rounds the Cape of Good Hope", "down", 900, "blue", align="right")
    event(1492, "1492", "Columbus: Portugal said no, so Castile said yes", "down", 900, "blue")
    event(1498, "1498", "Da Gama reaches India", "down", 760, "blue")
    T(b, "China could stop. *Europe's rivals couldn't.*", L, 1010, "h2", "text", t, 7.4)
    source(b, t, "", 99)


# ───────────────────────────────────────────────────────────── 6. thesis
def scene_thesis(b, t):
    cv = b.cv
    header(b, t, "McNeill's thesis", "Not religion. Institutions.")
    c1, c2, c3 = L, 520, 1160
    T(b, "CHINA", c2, 400, "kicker", "orange", t, 0.4, tracking=4)
    T(b, "EUROPE", c3, 400, "kicker", "blue", t, 0.4, tracking=4)
    g = ease_in_out(clamp01((t - 0.3) / 0.8))
    cv.drawLine(L, 426, L + (R - L) * g, 426, P(col("grid"), "stroke", 2))

    def row(y, t0, label, left, right, h=110, mark=False):
        a = pr(t, t0)
        if a <= 0:
            return
        b.text(label.upper(), c1, y + 40, "meta", "muted", tracking=2, alpha=a)
        off = 0
        if mark:
            off = 46
            for k, cx in enumerate((c2, c3)):
                ma = pr(t, t0 + 0.4 + k * 0.3, 0.25)
                if ma:
                    cv.save(); cv.translate(cx + 14, y + 30); sc = 1.8 - 0.8 * ma; cv.scale(sc, sc)
                    icon_cross(cv, 0, 0, 24, col("red", ma), 5); cv.restore()
        b.text(left, c2 + off, y + 40, "body", "text", max_w=560 - off, alpha=a)
        b.text(right, c3 + off, y + 40, "body", "text", max_w=600 - off, alpha=a)
        cv.drawLine(L, y + h, L + (R - L) * a, y + h, P(col("grid"), "stroke", 2))

    row(430, 1.0, "Faith on profit", "Confucians ranked merchants last", "The Church condemned usury", mark=True)
    T(b, "Both distrusted profit, so religion isn't the difference.", c2, 525, "meta", "red", t, 2.0)
    # who decides + unit chart
    y = 540
    a = pr(t, 3.0)
    if a:
        b.text("WHO DECIDES", c1, y + 44, "meta", "muted", tracking=2, alpha=a)
        b.text("One emperor", c2, y + 44, "body", "text", alpha=a)
        b.text("~500 rival states", c3, y + 44, "body", "text", alpha=a)
        sa = pr(t, 3.4, 0.3)
        cv.drawRect(skia.Rect.MakeXYWH(c2 + 200, y + 22, 26 * ease_out_back(sa), 26 * ease_out_back(sa)),
                    P(col("orange", sa)))
        for i in range(500):
            r, c = divmod(i, 50)
            qa = pr(t, 3.6 + i * 0.003, 0.2)
            if qa:
                cv.drawRect(skia.Rect.MakeXYWH(c3 + 250 + c * 7, y + 12 + r * 7, 5, 5), P(col("blue", 0.9 * qa)))
        cv.drawLine(L, y + 110, L + (R - L) * a, y + 110, P(col("grid"), "stroke", 2))
    row(650, 4.6, "Stop exploring?", "1433: one decision at court ended the fleets",
        "Portugal turned Columbus down. Castile funded him.")
    row(760, 5.8, "Rich merchants", "Bought land and joined the gentry", "Lent money to competing kings")
    T(b, "*Competition,* not culture, made Europe a global power.", L, 960, "title", "text", t, 7.2, d=0.7)
    source(b, t, SOURCE + "  ·  ~500 units c. 1500: C. Tilly (1975)", 1.0)


# ───────────────────────────────────────────────────────────── 7. end card
def scene_end(b, t):
    cv = b.cv
    a = pr(t, 0.2, 0.6)
    sc = 0.9 + 0.1 * ease_out_back(a)
    cv.save(); cv.translate(W / 2, H / 2 - 40); cv.scale(sc, sc)
    diamond(cv, 0, -150, 110, col("orange", a))
    b.text("THE STRATEGIST", 0, 10, "title", "text", align="center", tracking=8, alpha=a)
    b.text("GEOPOLITICS  ·  ECONOMICS  ·  MARKETS", 0, 70, "kicker", "orange", align="center", tracking=5, alpha=a)
    cv.restore()
    T(b, "Next: why some empires out-competed others.", W / 2, 760, "label", "muted", t, 1.0, align="center")


SCENES = [(scene_cover, 8.6), (scene_power, 9.2), (scene_song, 8.6), (scene_fleets, 8.6),
          (scene_timeline, 9.4), (scene_thesis, 9.6), (scene_end, 3.6)]
DURATION = sum(d for _, d in SCENES)
FADE = 0.35


def frame(gt):
    acc = 0.0
    for fn, d in SCENES:
        if gt < acc + d or fn is SCENES[-1][0]:
            lt = gt - acc
            break
        acc += d
    b = Board(W, H, brand=fn is not scene_end)
    a = clamp01(min(lt / FADE, (d - lt) / FADE)) if fn is not scene_end else clamp01(lt / FADE)
    b.cv.saveLayerAlpha(None, int(255 * a))
    fn(b, lt)
    b.cv.restore()
    return b.surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)


def _render(i):
    return frame(i / FPS).tobytes()


def sfx_events():
    ev, acc = [], 0.0
    cues = {
        scene_cover: [(1.4, "swoosh"), (4.0, "pop"), (6.6, "hit_soft")],
        scene_power: [(0.8, "tick"), (2.4, "tick"), (4.0, "tick"), (5.6, "pop")],
        scene_song: [(1.2, "pop"), (3.0, "rise"), (5.6, "tick")],
        scene_fleets: [(0.8, "rise"), (4.3, "tick"), (5.8, "hit_soft")],
        scene_timeline: [(0.5, "swoosh")],
        scene_thesis: [(1.4, "tick"), (1.7, "tick"), (3.6, "rise"), (7.2, "hit_soft")],
        scene_end: [(0.2, "hit")],
    }
    for fn, d in SCENES:
        ev.append((acc, "whoosh_short"))
        ev += [(acc + t0, n) for t0, n in cues.get(fn, [])]
        acc += d
    return ev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default=None)
    ap.add_argument("--workers", type=int, default=mp.cpu_count())
    args = ap.parse_args()
    from PIL import Image
    from strategist.engine import A
    A.countries("50m")
    OUT.mkdir(exist_ok=True)
    if args.stills:
        for s in args.stills.split(","):
            p = OUT / f"mcneill_wide_{float(s):05.1f}s.png"
            Image.fromarray(frame(float(s))[..., :3]).save(p)
            print(p)
        return
    n = int(DURATION * FPS)
    vid, wav, out = OUT / "mcneill_wide_v.mp4", OUT / "mcneill_wide.wav", OUT / "mcneill_wide.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.get_context("fork").Pool(args.workers) as pool:
        for i, buf in enumerate(pool.imap(_render, range(n), chunksize=4)):
            ff.stdin.write(buf)
            if i % 150 == 0:
                print(f"frame {i}/{n}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close(); ff.wait()
    build_soundtrack(DURATION, sfx_events(), wav, music_gain=0.7)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(vid), "-i", str(wav), "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-t", str(DURATION), str(out)], check=True)
    vid.unlink(); wav.unlink()
    print(out, f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
