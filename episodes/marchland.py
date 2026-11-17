"""EP03 — The Marchland Theory (W. H. McNeill). Vertical 1080x1920, animated.

Run:
  python episodes/marchland.py                    # full MP4 -> out/marchland.mp4
  python episodes/marchland.py --stills 5,20,40   # PNG frames at those seconds

Scene lengths follow the creator's voiceover script at ~2.5 words/s.
Send the recorded VO and the scene durations below can be matched to it.

FACTS USED BEYOND THE SCRIPT (re-check before publishing)
  * Peter the Great rebuilt Russia's army on western lines (Great Northern War, 1700-21).
  * 1774 Treaty of Kuchuk Kainarji: Russia gains a foothold on the Black Sea; 1783 Crimea annexed.
  * Prussian marsh drainage, e.g. the Oderbruch (1747-53) under Frederick II.
  * 1740: Frederick the Great invades Silesia, a Habsburg province (First Silesian War 1740-42).
  * Seven Years' War 1756-63; Berlin briefly occupied by Russian and Austrian troops in October 1760.
  * The steppe area on the Russia map is a schematic approximation, not a historical boundary.
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategist.scenes import *  # noqa: F401,F403,E402
from strategist.stills import (FlatMap, icon_coins, icon_swords, icon_waves, icon_wheat)  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "out" / "marchland.mp4"
SOURCE = "Source: W. H. McNeill, The Pursuit of Power (1982)"


def source(b, t, s=SOURCE, t0=1.0):
    T(b, s, L, 1500, "meta", "faint", t, t0, rise=0)


def land(cv, m, t, t0=0.3):
    a = pr(t, t0, 1.0)
    if a > 0:
        cv.saveLayerAlpha(None, int(255 * a)); m.land(); cv.restore()


def pts(m, lonlats):
    return [m.xy(lo, la) for lo, la in lonlats]


# ─────────────────────────────────────────────────────── 1. hook  (7 s)
def s_hook(b, t):
    cv = b.cv
    T(b, "WILLIAM H. MCNEILL", L, 250, "kicker", "muted", t, 0.05, tracking=4)
    T(b, "The Marchland Theory", L, 332, "title", "orange", t, 0.2)
    T(b, "Europe's centre, and two powers that rose on its edges", L, 388, "subtitle", "muted", t, 0.3,
      max_w=R - L)
    m = FlatMap(b, (-12, 34, 60, 66), (0, 420, 1080, 800), fade=80)
    land(cv, m, t)
    cx, cy = m.xy(8.5, 49.5)
    glow(cv, cx, cy, 230, "blue", 0.38 * pr(t, 1.2, 1.0))
    T(b, "THE CENTRE", cx, cy + 12, "map_area", "blue", t, 1.5, align="center")
    arrow(cv, pts(m, [(56, 58), (45, 56), (31, 53.5)]), ramp(t, 2.3, 1.2), "orange", 7)
    arrow(cv, pts(m, [(23, 57.2), (19.5, 55.3), (15.2, 53.2)]), ramp(t, 2.7, 1.0), "orange", 7)
    rx, ry = m.xy(48, 59.5)
    T(b, "RUSSIA", rx, ry, "map_area", "orange", t, 3.3, align="center")
    px, py = m.xy(21, 58.4)
    T(b, "PRUSSIA", px, py, "map_area", "orange", t, 3.5, align="center")
    T(b, "Why do history's greatest powers rise on the *edges* of the political map?", L, 1330, "h2", "text",
      t, 4.2, max_w=R - L, lh=1.15)


# ──────────────────────────────────────────────── 2. march states (19 s)
_rng = random.Random(3)
_CELLS = [(x, y) for x in range(-6, 7) for y in range(-6, 7) if (x * 25) ** 2 + (y * 25) ** 2 < 150 ** 2]
_rng.shuffle(_CELLS)


def s_march(b, t):
    cv = b.cv
    header(b, t, "McNeill's pattern", "March states", "How a state on the edge comes to challenge the centre")
    cx, cy, ri, ro = 540, 790, 165, 320
    # marches: the outer band
    ba = pr(t, 2.4, 0.8)
    if ba:
        band = skia.Path(); band.addCircle(cx, cy, ro); band.addCircle(cx, cy, ri)
        band.setFillType(skia.PathFillType.kEvenOdd)
        hatch(cv, band, "orange", 0.16 * ba, 16, 2)
        for r in (ri, ro):
            p = P(col("orange", 0.45 * ba), "stroke", 2)
            p.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
            cv.drawCircle(cx, cy, r, p)
    T(b, "THE MARCHES", cx, cy - ro - 22, "kicker", "orange", t, 2.8, align="center", tracking=4)
    # centre: crowded with small states
    ca = pr(t, 0.6, 0.6)
    if ca:
        cv.drawCircle(cx, cy, ri, P(col("blue", 0.10 * ca)))
        cv.drawCircle(cx, cy, ri, P(col("blue", 0.6 * ca), "stroke", 2))
    for k, (gx, gy) in enumerate(_CELLS):
        qa = pr(t, 0.9 + k * 0.018, 0.2)
        if qa:
            cv.drawRect(skia.Rect.MakeXYWH(cx + gx * 25 - 9, cy + gy * 25 - 9, 18, 18), P(col("blue", 0.55 * qa)))
    T(b, "THE CENTRE", cx, cy + ri + 40, "kicker", "blue", t, 1.6, align="center", tracking=4)
    # a march state grows on the edge, then pushes in
    ang = math.radians(-38)
    mx, my = cx + 245 * math.cos(ang), cy + 245 * math.sin(ang)
    g = ramp(t, 4.6, 3.0)
    if g:
        cv.drawCircle(mx, my, 14 + 50 * g, P(col("orange", 0.35), blur=16))
        cv.drawCircle(mx, my, 10 + 46 * g, P(col("orange")))
    T(b, "MARCH STATE", cx + 395 * math.cos(ang), cy + 395 * math.sin(ang) - 30, "kicker", "orange", t, 5.0,
      align="center", tracking=3)
    arrow(cv, [(mx - 50 * math.cos(ang), my - 50 * math.sin(ang)), (cx + 40 * math.cos(ang), cy + 40 * math.sin(ang))],
          ramp(t, 8.0, 0.9), "orange", 8)
    # definition + the two advantages
    T(b, "MARCH STATE", L, 1215, "kicker", "orange", t, 9.6, tracking=4)
    T(b, "A state on the edge of a political system that grows strong enough to challenge its centre.", L, 1265,
      "label", "text", t, 9.8, max_w=R - L, lh=1.25)
    T(b, "TWO ADVANTAGES", L, 1385, "kicker", "muted", t, 13.4, tracking=4, rise=0)
    w1 = chip(b, "1  GEOGRAPHY", L, 1410, "orange", pr(t, 13.8, 0.4))
    chip(b, "2  EXPANSION", L + 20 + w1, 1410, "orange", pr(t, 14.6, 0.4))


# ────────────────────────────────────────────────── 3. geography (16 s)
def _square(cv, x, y, s, c, a, fill_a=0.85):
    if a <= 0:
        return
    k = ease_out_back(a, 2.0)
    r = skia.Rect.MakeXYWH(x - s * k / 2, y - s * k / 2, s * k, s * k)
    cv.drawRect(r, P(col(c, fill_a * a)))
    cv.drawRect(r, P(col("text", 0.55 * a), "stroke", 2))


def _bar(b, x, y, w, parts, labels, color, a, gap=0.0):
    cv = b.cv
    if a <= 0:
        return
    xx = x
    tot = sum(parts)
    n = len(parts)
    usable = w - gap * (n - 1)
    for p_, lab in zip(parts, labels):
        pw = usable * p_ / tot
        cv.drawRect(skia.Rect.MakeXYWH(xx, y, pw, 52), P(col(color, a)))
        b.text(lab, xx + pw / 2, y + 36, "kicker", "bg", align="center", alpha=a)
        xx += pw + gap


def s_geo(b, t):
    cv = b.cv
    header(b, t, "Advantage 1", "Geography", "Fronts to defend: a surrounded state vs a march state")
    # panel A: surrounded state
    T(b, "SURROUNDED STATE", L, 485, "kicker", "blue", t, 0.5, tracking=4)
    cx, cy, d = 245, 720, 165
    _square(cv, cx, cy, 104, "blue", pr(t, 0.6, 0.4), 0.5)
    for k, (dx, dy) in enumerate(((0, -1), (1, 0), (0, 1), (-1, 0))):
        a = pr(t, 1.0 + k * 0.3, 0.35)
        _square(cv, cx + dx * d, cy + dy * d, 62, "red", a)
        arrow(cv, [(cx + dx * (d - 40), cy + dy * (d - 40)), (cx + dx * 66, cy + dy * 66)], ramp(t, 2.3 + k * 0.15, 0.5),
              "red", 5, glow_=False)
    T(b, "Must divide troops and money between several enemies.", 500, 640, "label", "text", t, 1.4, max_w=R - 500,
      lh=1.25)
    split = ramp(t, 4.2, 0.6)
    _bar(b, 500, 770, R - 500, [1, 1, 1, 1], ["25%"] * 4 if split > 0.5 else ["", "", "", ""], "blue",
         pr(t, 3.4, 0.4), gap=14 * split)
    T(b, "STRENGTH PER FRONT", 500, 860, "meta", "muted", t, 3.6, tracking=2, rise=0)
    if t > 6:
        b.rule(940)
    # panel B: march state
    T(b, "MARCH STATE", L, 1010, "kicker", "orange", t, 6.6, tracking=4)
    bx, by = 245, 1235
    fa = pr(t, 6.8, 0.6)
    if fa:   # open frontier behind it
        for i in range(6):
            for j in range(7):
                cv.drawCircle(L + 10 + i * 22, by - 135 + j * 45, 3, P(col("orange", 0.35 * fa)))
        T(b, "OPEN FRONTIER", L, by + 190, "meta", "orange", t, 7.0, tracking=2, rise=0)
    _square(cv, bx, by, 104, "orange", pr(t, 7.0, 0.4))
    _square(cv, bx + d + 10, by, 62, "red", pr(t, 7.6, 0.35))
    arrow(cv, [(bx + 60, by), (bx + d - 30, by)], ramp(t, 8.4, 0.5), "orange", 14)
    T(b, "Fewer threatening fronts. Free to concentrate its strength.", 500, 1160, "label", "text", t, 7.8,
      max_w=R - 500, lh=1.25)
    _bar(b, 500, 1290, (R - 500) * ramp(t, 9.6, 0.8) + 1, [1], ["100%"] if t > 10.3 else [""], "orange",
         pr(t, 9.6, 0.3))
    T(b, "STRENGTH ON ONE FRONT", 500, 1380, "meta", "muted", t, 9.8, tracking=2, rise=0)


# ─────────────────────────────────────────────────── 4. expansion (10.5 s)
def s_expand(b, t):
    cv = b.cv
    header(b, t, "Advantage 2", "Expansion", "Crowded centre vs open frontier: who has room to grow?")
    T(b, "CROWDED CENTRE", L, 485, "kicker", "blue", t, 0.4, tracking=4)
    T(b, "OPEN FRONTIER", 560, 485, "kicker", "orange", t, 0.6, tracking=4)
    cells = [(c, r) for r in range(6) for c in range(4)]
    for k, (c, r) in enumerate(cells):
        a = pr(t, 0.5 + k * 0.03, 0.3)
        if a:
            cv.drawRect(skia.Rect.MakeXYWH(L + c * 100, 530 + r * 82, 76, 62), P(col("blue", 0.45 * a)))
    # competition sparks between neighbours
    if t > 1.5:
        rng = random.Random(int(t / 0.35))
        for _ in range(3):
            c, r = rng.randrange(3), rng.randrange(6)
            x0, y0 = L + c * 100 + 76, 530 + r * 82 + 31
            ph = (t % 0.35) / 0.35
            cv.drawLine(x0 - 6, y0, x0 + 30, y0, P(col("red", 1 - ph), "stroke", 5))
            cv.drawCircle(x0 + 12, y0, 10 * (1 + ph), P(col("red", 0.6 * (1 - ph)), "stroke", 2))
    # frontier: dots + growing state
    fx, fy = 560, 775
    g = ramp(t, 1.6, 6.0)
    R_ = 40 + 380 * g

    def rad(th):
        return R_ * (1 + 0.10 * math.sin(3 * th + 1) + 0.06 * math.sin(5 * th + 2))

    blob = skia.Path()
    for i in range(61):
        th = -math.pi / 2 + math.pi * i / 60
        x, y = fx + rad(th) * math.cos(th), fy + rad(th) * math.sin(th)
        (blob.moveTo if i == 0 else blob.lineTo)(x, y)
    blob.close()
    region = skia.Rect.MakeLTRB(fx, 530, R, 1020)
    da = pr(t, 0.8, 0.6)
    for i in range(20):
        for j in range(22):
            x, y = fx + 12 + i * 23, 540 + j * 22
            if x > R:
                continue
            inside = blob.contains(x, y)
            cv.drawCircle(x, y, 3.2, P(col("orange", (0.9 if inside else 0.25) * da)))
    cv.save(); cv.clipRect(region)
    cv.drawPath(blob, P(col("orange", 0.35 * pr(t, 1.6))))
    cv.drawPath(blob, P(col("orange", pr(t, 1.6)), "stroke", 3))
    cv.restore()
    cv.drawLine(fx, 530, fx, 1020, P(col("grid"), "stroke", 2))
    # resources mobilised
    for k, (lab, f) in enumerate((("LAND", 1.0), ("PEOPLE", 0.8), ("RESOURCES", 0.9))):
        y = 1120 + k * 95
        a = pr(t, 2.0 + k * 0.2)
        T(b, lab, L, y + 30, "kicker", "muted", t, 2.0 + k * 0.2, tracking=3, rise=0)
        if a:
            cv.drawRect(skia.Rect.MakeXYWH(L + 240, y, R - L - 240, 44), P(col("bg_raised", a)))
            cv.drawRect(skia.Rect.MakeXYWH(L + 240, y, (R - L - 240) * (0.06 + 0.94 * g * f), 44), P(col("orange", a)))
    T(b, "The centre fights over crowded ground. The frontier state *keeps growing.*", L, 1440, "label", "text",
      t, 7.6, max_w=R - L)


# ─────────────────────────────────────────────────────── 5. Russia (21 s)
STEPPE = [(26.5, 48.3), (31, 50.2), (36, 51.2), (41, 51.6), (46, 51.9), (52, 51.6), (56, 50.6), (54, 47.5),
          (50, 46.0), (46, 45.0), (42, 44.2), (38, 45.0), (35, 45.4), (33, 46.0), (30, 46.4), (27.5, 46.6)]


def s_russia(b, t):
    cv = b.cv
    header(b, t, "Case 1", "Russia", "Farming the southern steppe, fighting with western methods")
    m = FlatMap(b, (20, 40, 62, 62.5), (0, 420, 1080, 840), fade=70)
    land(cv, m, t)
    sa = pr(t, 3.0, 1.0)
    if sa:
        poly = skia.Path.Polygon([skia.Point(*m.xy(lo, la)) for lo, la in STEPPE], True)
        lp = m.land_path()
        cv.save(); cv.clipPath(lp, skia.ClipOp.kIntersect, True)
        cv.drawPath(poly, P(col("orange", 0.12 * sa)))
        hatch(cv, poly, "orange", 0.45 * sa, 16, 2.5)
        cv.restore()
        sx, sy = m.xy(51.5, 50.6)
        T(b, "SOUTHERN STEPPE", sx, sy, "map_area", "orange", t, 3.4, align="center")
        T(b, "new farmland", sx, sy + 36, "map_city", "muted", t, 3.6, align="center")
    bx, by = m.xy(34, 43.2)
    T(b, "Black Sea", bx, by, "map_city", "faint", t, 1.0, align="center", rise=0)
    kx, ky = m.xy(51, 42)
    T(b, "Caspian", kx, ky, "map_city", "faint", t, 1.0, align="center", rise=0)
    mx, my = m.xy(37.62, 55.75)
    dot(cv, mx, my, 10, "text", pr(t, 1.0), ring=True, pulse_t=t - 1.4)
    T(b, "Moscow", mx + 30, my - 18, "map_city", "text", t, 1.2)
    arrow(cv, pts(m, [(37.2, 54.6), (35.5, 51.5), (33.6, 48.4)]), ramp(t, 4.4, 1.2), "orange", 7)
    arrow(cv, pts(m, [(38.8, 54.6), (42, 51.6), (45.5, 48.6)]), ramp(t, 4.8, 1.2), "orange", 7)
    arrow(cv, pts(m, [(20.5, 57.6), (28, 57.2), (35.6, 56.2)]), ramp(t, 9.0, 1.2), "blue", 6, dashed=True)
    wx, wy = m.xy(25.5, 58.4)
    T(b, "Western military methods", wx, wy, "map_city", "blue", t, 9.6, align="center")
    rows = [(12.0, "1700s", "Peter the Great rebuilds the army on western lines"),
            (14.4, "1774", "A foothold on the Black Sea"),
            (16.4, "1783", "Crimea annexed")]
    for k, (t0, yr, txt) in enumerate(rows):
        y = 1310 + k * 62
        T(b, yr, L, y, "label", "orange", t, t0)
        T(b, txt, L + 120, y, "label", "text", t, t0 + 0.1)
    source(b, t, "Source: McNeill (1982)  ·  Steppe area schematic  ·  Coastlines: Natural Earth", 1.0)


# ────────────────────────────────────────────────────── 6. Prussia (26 s)
PILLARS = [(icon_waves, "Land reclamation", "marshes drained into farmland"),
           (icon_wheat, "Better farming", "more food, more taxpayers"),
           (icon_coins, "Central taxation", "revenue flows to the crown"),
           (icon_swords, "Military drill", "an unusually powerful army")]


def s_prussia(b, t):
    cv = b.cv
    header(b, t, "Case 2", "Prussia", "Where it sat, what made it strong, and the grab for Silesia")
    m = FlatMap(b, (3, 47.5, 26, 56.5), (0, 420, 1080, 520), fade=60)
    land(cv, m, t)
    hx, hy = m.xy(9.5, 50.0)
    glow(cv, hx, hy, 170, "blue", 0.3 * pr(t, 2.6, 1.0))
    T(b, "HOLY ROMAN EMPIRE", hx, hy + 10, "map_city", "blue", t, 2.8, align="center")
    bx, by = m.xy(13.40, 52.52)
    dot(cv, bx, by, 9, "orange", pr(t, 0.8), ring=True)
    T(b, "Berlin", bx - 26, by - 14, "map_city", "text", t, 1.0, align="right")
    kx, ky = m.xy(20.51, 54.71)
    dot(cv, kx, ky, 8, "orange", pr(t, 1.3), ring=True)
    T(b, "Königsberg", kx + 24, ky + 40, "map_city", "text", t, 1.5)
    px, py = m.xy(17.5, 55.9)
    T(b, "PRUSSIA", px, py, "map_area", "orange", t, 1.9, align="center")
    T(b, "a march state", px, py + 32, "map_city", "muted", t, 2.1, align="center")
    # Silesia
    sx, sy = m.xy(17.04, 51.11)
    glow(cv, sx, sy, 90, "orange", 0.45 * pr(t, 18.6, 0.8))
    arrow(cv, [(bx + 10, by + 16), (bx + 70, by + 70), (sx - 18, sy - 18)], ramp(t, 18.0, 1.2), "orange", 7)
    dot(cv, sx, sy, 8, "orange", pr(t, 19.0))
    T(b, "SILESIA", sx + 24, sy + 12, "map_area", "orange", t, 19.2)
    T(b, "1740: Frederick the Great seizes it from Austria", L, 930, "meta", "orange", t, 19.6, tracking=1)
    # pillars
    for k, (ico, name, desc) in enumerate(PILLARS):
        t0 = 6.0 + k * 2.6
        a = pr(t, t0)
        if not a:
            continue
        y = 1010 + k * 92
        ico(cv, L + 34 - 20 * (1 - a), y - 12, 58, col("orange", a))
        b.text(name, L + 95, y, "label", "text", alpha=a)
        b.text(desc, L + 95 + b.width(name, "label") + 16, y, "body", "muted", alpha=a)
    T(b, "= A place among Europe's *great powers*", L, 1400, "h2", "text", t, 21.5)


# ─────────────────────────────────────────────── 7. the limits (14 s)
def s_limits(b, t):
    cv = b.cv
    header(b, t, "The limits", "Surrounded, 1756–63", "The Seven Years' War: Prussia attacked from three sides")
    m = FlatMap(b, (-4, 42.5, 34, 58), (0, 420, 1080, 760), fade=70)
    land(cv, m, t)
    bx, by = m.xy(13.40, 52.52)
    dot(cv, bx, by, 11, "orange", pr(t, 0.8), ring=True, pulse_t=t - 1.2)
    T(b, "PRUSSIA", bx, by - 36, "map_area", "orange", t, 1.0, align="center")
    foes = [("FRANCE", [(1.0, 47.2), (6.0, 49.6), (10.6, 51.7)], (1.5, 46.0), 2.0),
            ("AUSTRIA", [(16.37, 48.21), (15.6, 49.9), (14.3, 51.4)], (17.5, 47.4), 2.6),
            ("RUSSIA", [(30.0, 55.2), (23.5, 54.0), (16.0, 52.8)], (30.0, 56.6), 3.2)]
    for name, route, (lx, ly), t0 in foes:
        arrow(cv, pts(m, route), ramp(t, t0, 1.0), "red", 8)
        x, y = m.xy(lx, ly)
        T(b, name, x, y, "map_area", "red", t, t0 + 0.4, align="center")
    stamp(b, "NEAR DISASTER", 540, 1250, t, 6.0, "red", 62, -5)
    T(b, "1760: Berlin itself is briefly occupied.", L, 1370, "label", "muted", t, 7.4)
    T(b, "Peripheral origins never *guaranteed safety.*", L, 1440, "h2", "text", t, 9.0, max_w=R - L)


# ────────────────────────────────────────────── 8. overstretch (13 s)
def s_overstretch(b, t):
    cv = b.cv
    header(b, t, "The paradox", "Success breeds enemies", "As a state expands, its borders, enemies and supply lines grow")
    cx, cy = 540, 790
    g = ramp(t, 1.0, 6.5)
    Rr = 70 + 230 * g

    def rad(th):
        return Rr * (1 + 0.08 * math.sin(4 * th + 0.5) + 0.05 * math.sin(7 * th))

    blob = skia.Path()
    for i in range(121):
        th = 2 * math.pi * i / 120
        (blob.moveTo if i == 0 else blob.lineTo)(cx + rad(th) * math.cos(th), cy + rad(th) * math.sin(th))
    blob.close()
    a = pr(t, 0.4)
    cv.drawPath(blob, P(col("orange", 0.25 * a)))
    cv.drawPath(blob, P(col("orange", a), "stroke", 3))
    # supply lines from the capital
    for th in (0.3, 2.4, 4.3):
        r = rad(th) - 12
        p = P(col("text", 0.6 * a), "stroke", 3)
        p.setPathEffect(skia.DashPathEffect.Make([10, 9], -t * 30))
        cv.drawLine(cx, cy, cx + r * math.cos(th), cy + r * math.sin(th), p)
    dot(cv, cx, cy, 9, "text", a)
    # enemies appear along the growing border
    n = int(3 + 9 * g)
    for k in range(n):
        th = 2 * math.pi * k / n + 0.2
        r = rad(th) + 46
        _square(cv, cx + r * math.cos(th), cy + r * math.sin(th), 28, "red", 1.0)
    # metrics
    for k, (lab, f) in enumerate((("BORDERS", 1.0), ("ENEMIES", 0.85), ("SUPPLY LINES", 0.95))):
        y = 1170 + k * 72
        T(b, lab, L, y + 30, "kicker", "muted", t, 1.4 + k * 0.2, tracking=3, rise=0)
        ma = pr(t, 1.4 + k * 0.2)
        if ma:
            cv.drawRect(skia.Rect.MakeXYWH(L + 270, y, R - L - 270, 40), P(col("bg_raised", ma)))
            cv.drawRect(skia.Rect.MakeXYWH(L + 270, y, (R - L - 270) * (0.12 + 0.88 * g * f), 40), P(col("red", ma)))
    T(b, "The rising frontier power can become the *overstretched giant.*", L, 1405, "h2", "text", t, 8.0,
      max_w=R - L, lh=1.15)


# ──────────────────────────────────────────────── 9. conclusion (18 s)
def s_verdict(b, t):
    cv = b.cv
    header(b, t, "The verdict", "Opportunity, not destiny", "What the centre holds vs what the edges offer")

    def card(y, h, color, title, items, t0):
        a = pr(t, t0, 0.6)
        if not a:
            return
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(L, y, R - L, h), 12, 12)
        cv.drawRRect(rr, P(col(color, 0.06 * a)))
        cv.drawRRect(rr, P(col(color, 0.6 * a), "stroke", 2))
        b.text(title, L + 40, y + 62, "kicker", color, tracking=4, alpha=a)
        for k, it in enumerate(items):
            ia = pr(t, t0 + 0.6 + k * 0.6)
            yy = y + 130 + k * 70
            if ia:
                cv.drawCircle(L + 52, yy - 14, 7, P(col(color, ia)))
                b.text(it, L + 80, yy, "h2", "text", alpha=ia)

    card(470, 340, "blue", "THE CENTRE HOLDS", ["Wealth", "Prestige", "Established institutions"], 1.0)
    card(850, 340, "orange", "THE EDGES OFFER", ["Room to expand", "Concentrated resources",
                                                  "Strength to overturn the order"], 6.0)
    T(b, "The centre has the riches.", L, 1300, "h2", "text", t, 11.5)
    T(b, "The edges have the *room to rise.*", L, 1370, "h2", "text", t, 12.5)
    source(b, t, SOURCE, 1.0)


# ─────────────────────────────────────────────────── 10. end (3.5 s)
def s_end(b, t):
    a = pr(t, 0.2, 0.6)
    b.text("THE STRATEGIST", 540, 930, "title", "text", align="center", tracking=8, alpha=a)
    b.text("GEOPOLITICS  ·  ECONOMICS  ·  MARKETS", 540, 1000, "kicker", "orange", align="center", tracking=5,
           alpha=pr(t, 0.6, 0.6))


VO = {
    "hook": "Why do some of history's greatest powers emerge on the edges of the political map?",
    "march": "Historian William McNeill identified a recurring pattern: states on the margins can grow strong "
             "enough to challenge the established centre. These are what he called march states. And their "
             "position can offer two powerful advantages.",
    "geo": "First, geography. A state surrounded by powerful neighbours must divide its attention, troops and "
           "money between several potential enemies. A peripheral state may face fewer threatening fronts, "
           "giving it greater freedom to concentrate its strength.",
    "expand": "Second, expansion. While established powers compete over a crowded centre, frontier states can "
              "conquer territory and mobilise additional resources.",
    "russia": "Consider Russia. Its expansion brought more land, people and resources under its control. McNeill "
              "particularly emphasised agricultural expansion into the southern steppe. Combined with military "
              "organisation borrowed from western Europe, this growing resource base helped Russia become a "
              "major European power.",
    "prussia": "Prussia offers a smaller, more complicated example. McNeill explicitly described it as a march "
               "state. Land reclamation and agricultural improvements increased its wealth, while centralised "
               "taxation and rigorous military organisation allowed its rulers to maintain an unusually powerful "
               "army. Frederick the Great's seizure of Silesia then helped secure its place among Europe's great "
               "powers.",
    "limits": "But Prussia also reveals the limits of the argument. Peripheral origins never guaranteed safety. "
              "During the Seven Years' War, it faced Austria, Russia and France, and came close to disaster.",
    "over": "Success can also undermine the original advantage. Expansion creates new borders, new enemies and "
            "longer supply lines. The rising frontier power can become the overstretched giant.",
    "verdict": "So this is a theory about opportunities, rather than destiny. The centre may hold the wealth, "
               "prestige and established institutions. But the edges can offer room to expand, concentrate "
               "resources and build the strength to overturn the existing order.",
}

SCENES = [
    Scene(s_hook, 7.0, [(2.3, "swoosh"), (2.7, "swoosh")], VO["hook"]),
    Scene(s_march, 19.0, [(0.9, "rise"), (4.6, "pop"), (8.0, "swoosh"), (13.8, "tick"), (14.6, "tick")], VO["march"]),
    Scene(s_geo, 16.0, [(1.0, "tick"), (1.3, "tick"), (1.6, "tick"), (1.9, "tick"), (4.2, "pop"),
                        (7.0, "pop"), (8.4, "swoosh"), (9.6, "rise")], VO["geo"]),
    Scene(s_expand, 10.5, [(1.6, "rise"), (7.6, "pop")], VO["expand"]),
    Scene(s_russia, 21.0, [(1.0, "pop"), (3.0, "rise"), (4.4, "swoosh"), (9.0, "swoosh"), (12.0, "tick"),
                           (14.4, "tick"), (16.4, "tick")], VO["russia"]),
    Scene(s_prussia, 26.0, [(0.8, "pop"), (6.0, "tick"), (8.6, "tick"), (11.2, "tick"), (13.8, "tick"),
                            (18.0, "swoosh"), (19.0, "pop"), (21.5, "hit_soft")], VO["prussia"]),
    Scene(s_limits, 14.0, [(2.0, "swoosh"), (2.6, "swoosh"), (3.2, "swoosh"), (6.12, "hit")], VO["limits"]),
    Scene(s_overstretch, 13.0, [(1.0, "rise"), (8.0, "pop")], VO["over"]),
    Scene(s_verdict, 18.0, [(1.0, "tick"), (6.0, "tick"), (12.5, "hit_soft")], VO["verdict"]),
    Scene(s_end, 3.5, [(0.2, "hit")]),
]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stills", default=None)
    ap.add_argument("--voice", default="default", help="voice preset / Kokoro id, 'default' = house voice, 'none'")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    voice = None if args.voice == "none" else args.voice
    out = Path(args.out) if args.out else OUT
    if args.stills:
        for p in run(SCENES, out, stills=[float(x) for x in args.stills.split(",")], voice=voice, speed=args.speed):
            print(p)
    else:
        run(SCENES, out, voice=voice, speed=args.speed)
