"""EP04 — Gaugamela, 331 BCE: how Alexander brought down Persia. Vertical 1080x1920, animated.

Run:
  python episodes/gaugamela.py                    # full MP4 -> out/gaugamela.mp4
  python episodes/gaugamela.py --stills 5,20,40   # PNG frames at those seconds

Narration = the creator's script, word for word (VO dict below), one scene per paragraph.
Scene lengths are estimates (~2.5 words/s); the framework re-times each slide to the real narration.

FACTS USED BEYOND THE SCRIPT (re-check before publishing)
  * 480 BCE: Xerxes' invasion; Athens burned (Acropolis sacked) in 480 BCE.
  * 336-335 BCE: Alexander secures Macedon and Greece; 334 BCE crossing at the Hellespont.
  * Persia's Greek city-state rivals named on screen: Athens, Sparta (from script); member cities
    shown on the League map: Athens, Sparta, Thebes, Corinth, Argos (Sparta never actually joined
    the League; it appears only as a Greek city, not as a member).
  * Alexander's route 334-331: Granicus -> Issus -> Tyre -> Egypt (Memphis) -> back through Tyre -> Gaugamela.
  * Tyre's siege took about seven months (332 BCE) — on screen only as "332 BCE".
  * Gaugamela schematic: Parmenion commanded the Macedonian left; Alexander led the Companions on the right.
    Unit counts and positions are schematic, not to scale.
  * Persepolis burned in 330 BCE.
  * Persian Empire and Alexander's empire areas are schematic approximations, not historical boundaries.
  * Strengths chart (slide 6) is a qualitative rating built from the script, not measured data.
  * Source line: Arrian, Anabasis of Alexander; Diodorus Siculus, Library, Book XVII.
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategist.scenes import *  # noqa: F401,F403,E402
from strategist.engine import smooth_path  # noqa: E402
from strategist.stills import (FlatMap, icon_check, icon_coins, icon_cross, icon_crown, icon_swords)  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "out" / "gaugamela.mp4"
SOURCE = "Sources: Arrian, Anabasis  ·  Diodorus, Library XVII"


def source(b, t, s=SOURCE, t0=1.0):
    T(b, s, L, 1500, "meta", "faint", t, t0, rise=0)


def land(cv, m, t, t0=0.3):
    a = pr(t, t0, 1.0)
    if a > 0:
        cv.saveLayerAlpha(None, int(255 * a)); m.land(); cv.restore()


def pts(m, lonlats):
    return [m.xy(lo, la) for lo, la in lonlats]


def region(cv, m, poly, color, a, fill=0.12, hatch_a=0.45, clip=None):
    """Schematic historical region: hatched polygon clipped to land (and optionally a rect)."""
    if a <= 0:
        return
    path = skia.Path.Polygon([skia.Point(*m.xy(lo, la)) for lo, la in poly], True)
    cv.save()
    cv.clipRect(m.rect, True)
    if clip is not None:
        cv.clipRect(clip, True)
    cv.clipPath(m.land_path(), skia.ClipOp.kIntersect, True)
    cv.drawPath(path, P(col(color, fill * a)))
    hatch(cv, path, color, hatch_a * a, 16, 2.5)
    cv.restore()


def _box(cv, x, y, w, h, c, a, kind="inf", fill_a=0.85):
    """NATO-style unit box: inf = X, cav = single diagonal."""
    if a <= 0:
        return
    r = skia.Rect.MakeXYWH(x - w / 2, y - h / 2, w, h)
    cv.drawRect(r, P(col(c, fill_a * a)))
    cv.drawRect(r, P(col("text", 0.6 * a), "stroke", 2))
    p = P(col("bg", 0.8 * a), "stroke", 2.5)
    cv.drawLine(x - w / 2, y + h / 2, x + w / 2, y - h / 2, p)
    if kind == "inf":
        cv.drawLine(x - w / 2, y - h / 2, x + w / 2, y + h / 2, p)


# Schematic areas (lon, lat). Not historical boundaries.
PERSIA = [(26.2, 40.6), (29, 41.2), (33, 42), (36, 41.6), (41, 41.2), (45, 41.5), (49, 40), (53, 38.5), (58, 38.3),
          (62, 37.5), (66, 37.5), (69, 37), (71, 35), (72, 32), (70, 28), (66, 25.2), (61, 25.2), (57, 25.6),
          (54, 26.8), (51, 28.2), (49.5, 29.8), (47.5, 30), (45, 30.5), (42, 31), (38.5, 29.5), (35, 28.5),
          (33.5, 28), (32, 24), (30, 24), (29, 28.5), (29.5, 31), (31.5, 31.4), (34.5, 31.6), (35.8, 34.5),
          (36, 36), (32, 36.2), (29, 36.5), (27, 37.2), (26.4, 38.6)]
ALEX = [(19.5, 42.3), (24, 42), (27, 41.6)] + PERSIA[1:]
CITY = {"Pella": (22.52, 40.76), "Athens": (23.73, 37.98), "Sparta": (22.43, 37.07), "Thebes": (23.32, 38.32),
        "Corinth": (22.93, 37.91), "Argos": (22.72, 37.63), "Granicus": (27.3, 40.2), "Issus": (36.2, 36.85),
        "Tyre": (35.2, 33.27), "Memphis": (31.25, 29.85), "Gaugamela": (43.5, 36.6), "Babylon": (44.42, 32.54),
        "Susa": (48.25, 32.19), "Persepolis": (52.89, 29.93), "Erbil": (44.01, 36.19)}


# ─────────────────────────────────────────────────────── 1. hook (13.6 s)
def s_hook(b, t):
    cv = b.cv
    header(b, t, "The wars of Alexander", "Gaugamela, 331 BCE",
           "Where Macedon and the Persian Empire met for the last time")
    m = FlatMap(b, (18, 25, 62, 46), (0, 450, 1080, 700), fade=70)
    land(cv, m, t)
    region(cv, m, PERSIA, "blue", pr(t, 2.0, 1.2))
    px, py = m.xy(49.0, 29.6)
    T(b, "PERSIAN EMPIRE", px, py, "map_area", "blue", t, 2.6, align="center")
    T(b, "the largest the world had yet seen", px, py + 34, "map_city", "muted", t, 3.0, align="center")
    mx, my = m.xy(*CITY["Pella"])
    dot(cv, mx, my, 8, "text", pr(t, 1.2), ring=True)
    T(b, "MACEDON", mx, my - 28, "map_area", "text", t, 1.4, align="center")
    arrow(cv, pts(m, [(23.5, 40.6), (31, 39.6), (38, 38.4), (42.4, 36.9)]), ramp(t, 5.0, 2.0), "orange", 7,
          dashed=True)
    gx, gy = m.xy(*CITY["Gaugamela"])
    dot(cv, gx, gy, 11, "orange", pr(t, 6.8), ring=True, pulse_t=t - 7.2)
    T(b, "GAUGAMELA", gx, gy - 34, "map_area", "orange", t, 7.0, align="center")
    T(b, "northern Mesopotamia", gx + 30, gy + 10, "map_city", "muted", t, 7.3)
    T(b, "How Alexander of Macedon brought down *Achaemenid Persia*", L, 1300, "h2", "text", t, 9.6,
      max_w=R - L, lh=1.15)
    source(b, t, "Areas schematic  ·  Coastlines: Natural Earth", 1.0)


# ──────────────────────────────────────────────────── 2. context (19.2 s)
GREEKS = ["Pella", "Athens", "Thebes", "Corinth", "Argos", "Sparta"]


def s_context(b, t):
    cv = b.cv
    header(b, t, "Historical context", "Two worlds collide", "A united Greece in the west, the Persian Empire to the east")
    m = FlatMap(b, (17, 27, 60, 45), (0, 450, 1080, 600), fade=70)
    land(cv, m, t)
    for k, n in enumerate(GREEKS):
        x, y = m.xy(*CITY[n])
        dot(cv, x, y, 5, "orange", pr(t, 1.0 + k * 0.25, 0.4))
    # the League ring draws around Greece
    cx, cy = m.xy(23, 38.9)
    rp = ramp(t, 3.4, 1.4)
    if rp:
        arc = skia.Path(); arc.addArc(skia.Rect.MakeXYWH(cx - 95, cy - 95, 190, 190), -90, 360 * rp)
        p = P(col("orange", 0.9), "stroke", 4)
        p.setPathEffect(skia.DashPathEffect.Make([12, 8], 0))
        cv.drawPath(arc, p)
    T(b, "LEAGUE OF CORINTH", cx, cy - 115, "map_area", "orange", t, 4.6, align="center")
    region(cv, m, PERSIA, "blue", pr(t, 7.4, 1.2))
    px, py = m.xy(49, 33)
    T(b, "PERSIAN EMPIRE", px, py, "map_area", "blue", t, 8.0, align="center")
    T(b, "multi-ethnic superpower", px, py + 34, "map_city", "muted", t, 8.4, align="center")
    rows = [(1.0, "PHILIP II", "orange", "Subdues the Greek city-states and binds them into one league"),
            (7.4, "DARIUS III", "blue", "Rules the vast Persian Empire to the east")]
    for k, (t0, name, c, txt) in enumerate(rows):
        y = 1110 + k * 120
        a = pr(t, t0)
        chip(b, name, L, y - 40, c, a)
        T(b, txt, L + 250, y, "body", "text", t, t0 + 0.2, max_w=R - L - 250, lh=1.2)
    T(b, "A united, militarized Greece: an *existential threat*", L, 1400, "h2", "text", t, 14.0, max_w=R - L,
      lh=1.15)
    source(b, t, "Areas schematic  ·  Coastlines: Natural Earth", 1.0)


# ──────────────────────────────────────────────────── 3. causes (14.8 s)
CAUSES = [(icon_coins, "Persian gold", "Decades of bribes and money for Greek rivals", ["ATHENS", "SPARTA"], 1.6),
          (icon_swords, "Panhellenic revenge", "For Xerxes' invasion and the burning of Athens", ["480 BCE"], 6.4),
          (icon_crown, "Macedonian ambition", "Land, security and wealth", [], 11.4)]


def s_causes(b, t):
    cv = b.cv
    header(b, t, "Underlying causes", "Three grievances", "The forces pushing Macedon toward war with Persia")
    for k, (ico, name, desc, chips, t0) in enumerate(CAUSES):
        a = pr(t, t0, 0.6)
        if not a:
            continue
        nxt = CAUSES[k + 1][4] if k + 1 < len(CAUSES) else 99
        active = t < nxt
        c = "orange" if active else "orange_dim"
        y = 500 + k * 280
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(L, y, R - L, 240), 12, 12)
        cv.drawRRect(rr, P(col("bg_raised", a)))
        cv.drawRRect(rr, P(col(c, (0.8 if active else 0.35) * a), "stroke", 2))
        ico(cv, L + 90, y + 95, 96, col(c, a))
        b.text(f"{k + 1}  {name}", L + 180, y + 80, "h2", "text" if active else "muted", alpha=a)
        b.text(desc, L + 180, y + 130, "body", "text" if active else "muted", max_w=R - L - 210, lh=1.2, alpha=a)
        xx = L + 180
        for j, ch in enumerate(chips):
            xx += chip(b, ch, xx, y + 160, c, pr(t, t0 + 1.2 + j * 0.4, 0.4)) + 16
    T(b, "Old grudges, new *ambition*", L, 1400, "h2", "text", t, 12.6)
    source(b, t, SOURCE, 1.0)


# ──────────────────────────────────────────────────── 4. trigger (14.8 s)
def s_trigger(b, t):
    cv = b.cv
    header(b, t, "Trigger and escalation", "The spark, 336 BCE", "Two years from an assassination to a war of conquest")
    ax = L + 150
    g = ramp(t, 0.6, 9.0)
    cv.drawLine(ax, 520, ax, 520 + 520 * g, P(col("grid"), "stroke", 4))
    events = [(0.8, "336 BCE", "Philip II is assassinated", "red", None),
              (4.6, "", "Persia hopes Macedon will fall apart", "muted", None),
              (7.0, "336–335", "Young Alexander seizes control", "text", None),
              (9.6, "334 BCE", "He crosses into Asia", "orange", None)]
    for k, (t0, yr, txt, c, _) in enumerate(events):
        y = 560 + k * 150
        a = pr(t, t0)
        if not a:
            continue
        if yr:
            dot(cv, ax, y - 12, 12, "orange" if c == "orange" else ("red" if c == "red" else "text"), a, ring=True)
            T(b, yr, ax - 34, y, "label", "orange" if c == "orange" else "muted", t, t0, align="right")
        T(b, txt, ax + 50, y, "h2" if yr else "body", "text" if c != "muted" else "muted", t, t0 + 0.1,
          max_w=R - ax - 50)
    # scope of the war
    T(b, "SCOPE OF THE WAR", L, 1180, "kicker", "muted", t, 10.8, tracking=4, rise=0)
    bars = [("Punitive expedition", 0.32, "orange_dim", 11.2), ("War of conquest", 1.0, "orange", 12.4)]
    for k, (lab, f, c, t0) in enumerate(bars):
        y = 1220 + k * 110
        a = pr(t, t0, 0.4)
        if not a:
            continue
        w = (R - L) * f * ramp(t, t0, 1.0)
        cv.drawRect(skia.Rect.MakeXYWH(L, y, R - L, 60), P(col("bg_raised", a)))
        cv.drawRect(skia.Rect.MakeXYWH(L, y, w, 60), P(col(c, a)))
        b.text(lab, L + 20, y + 42, "label", "bg" if c == "orange" else "text", alpha=a)
    source(b, t, SOURCE, 1.0)


# ─────────────────────────────────────────────────── 5. objectives (22.8 s)
ALEX_AIMS = [(1.2, "Liberate the Greek cities of Asia Minor", 0.30), (3.4, "Take revenge", 0.40),
             (4.4, "Seize plunder", 0.50), (5.8, "Overthrow the Achaemenid dynasty", 0.80),
             (7.6, "Rule as King of Asia", 1.0)]
DAR_AIMS = [(10.6, "Crush the invader", 1.0), (16.4, "Save the empire", 0.70), (15.4, "Save the family", 0.50),
            (14.4, "Save the throne", 0.35), (17.6, "Offer land and ransoms", 0.20)]


def s_objectives(b, t):
    cv = b.cv
    header(b, t, "Political objectives", "Aims that grew and shrank", "Each bar is the scale of a war aim, start to finish")
    cw = (R - L - 60) / 2
    for side, (x0, name, c, aims, t0) in enumerate(((L, "ALEXANDER", "orange", ALEX_AIMS, 0.8),
                                                    (L + cw + 60, "DARIUS III", "blue", DAR_AIMS, 10.2))):
        T(b, name, x0, 490, "kicker", c, t, t0, tracking=4)
        T(b, "aims expand" if side == 0 else "aims shrink", x0, 530, "meta", "muted", t, t0 + 0.2, rise=0)
        for k, (ta, txt, f) in enumerate(aims):
            y = 620 + k * 150
            a = pr(t, ta)
            if not a:
                continue
            b.text(txt, x0, y, "body", "text", max_w=cw, lh=1.15, alpha=a)
            by = y + (50 if b.width(txt, "body") > cw else 18)
            cv.drawRect(skia.Rect.MakeXYWH(x0, by, cw, 22), P(col("bg_raised", a)))
            cv.drawRect(skia.Rect.MakeXYWH(x0, by, cw * f * ramp(t, ta, 0.8), 22), P(col(c, a)))
    stamp(b, "REFUSED", L + cw + 60 + cw / 2, 1335, t, 20.4, "red", 50, -6)
    T(b, "Alexander's aims *grew* with every victory", L, 1455, "h2", "text", t, 8.6, max_w=R - L)
    source(b, t, SOURCE, 1.0)


# ─────────────────────────────────────────────────── 6. strengths (24 s)
STRENGTHS = [("MANPOWER", 95, 2.0, 25, 14.6), ("TREASURE", 95, 2.8, 25, 15.4), ("SEA POWER", 85, 3.6, 20, 16.2),
             ("STRATEGIC DEPTH", 90, 4.6, 25, 16.6), ("PROFESSIONAL ARMY", 30, 7.6, 95, 18.4),
             ("COHESION", 30, 9.2, 90, 19.6), ("COMMAND", 30, 10.6, 98, 21.4)]


def s_strengths(b, t):
    cv = b.cv
    header(b, t, "Strengths and constraints", "Mass against quality", "How the two sides compared, rated qualitatively")
    w1 = chip(b, "PERSIA", L, 450, "blue", pr(t, 0.8, 0.4))
    chip(b, "MACEDON", L + w1 + 20, 450, "orange", pr(t, 1.0, 0.4))
    bx, bw = L + 330, R - L - 330
    for k, (lab, pv, pt, mv, mt) in enumerate(STRENGTHS):
        y = 580 + k * 112
        T(b, lab, L, y + 36, "kicker", "muted", t, pt - 0.2, tracking=2, rise=0)
        for j, (v, t0, c) in enumerate(((pv, pt, "blue"), (mv, mt, "orange"))):
            a = pr(t, t0, 0.3)
            if not a:
                continue
            yy = y + j * 30
            cv.drawRect(skia.Rect.MakeXYWH(bx, yy, bw, 24), P(col("bg_raised", a)))
            cv.drawRect(skia.Rect.MakeXYWH(bx, yy, bw * v / 100 * ramp(t, t0, 0.8), 24), P(col(c, a)))
    T(b, "Persia had the mass. Macedon had *the quality.*", L, 1420, "h2", "text", t, 20.0, max_w=R - L)
    source(b, t, "Qualitative ratings from the narration, not measured data", 1.0)


# ──────────────────────────────────────────────────── 7. strategy (13.2 s)
def s_strategy(b, t):
    cv = b.cv
    header(b, t, "Strategy", "Speed against scale", "Macedon's fast thrust vs Persia's plan to envelop it")
    T(b, "MACEDON: MOVE FAST", L, 500, "kicker", "orange", t, 0.6, tracking=4)
    nodes = [(220, "Decisive battles", icon_swords, 1.6), (540, "Seize treasuries", icon_coins, 3.0),
             (860, "Before the money runs out", icon_crown, 4.6)]
    arrow(cv, [(L + 10, 700), (R - 10, 700)], ramp(t, 1.0, 4.4), "orange", 7)
    for x, lab, ico, t0 in nodes:
        a = pr(t, t0, 0.4)
        if a:
            cv.drawCircle(x, 700, 58, P(col("bg", a)))
            cv.drawCircle(x, 700, 58, P(col("orange", a), "stroke", 4))
            ico(cv, x, 700, 66, col("orange", a))
        T(b, lab, x, 820, "body", "text", t, t0 + 0.2, align="center", max_w=300, lh=1.15)
    if t > 6:
        b.rule(930)
    T(b, "PERSIA: ONE COLOSSAL ARMY", L, 990, "kicker", "blue", t, 6.4, tracking=4)
    cx, cy = 540, 1215
    for i in range(3):
        for j in range(2):
            _box(cv, cx - 40 + i * 40, cy - 16 + j * 34, 34, 26, "orange", pr(t, 6.6, 0.4), "inf")
    T(b, "MACEDONIANS", cx, cy + 80, "meta", "orange", t, 6.8, align="center", tracking=2, rise=0)
    close = ramp(t, 8.6, 3.0)
    for ring, R_ in enumerate((190, 240)):
        n = 26 + ring * 6
        for k in range(n):
            th = math.pi / 2 + (k / (n - 1) - 0.5) * 2 * math.pi * (0.25 + 0.72 * close)
            x, y = cx + R_ * 1.9 * math.cos(th) * 0.5, cy + R_ * 0.68 * math.sin(th)
            dot(cv, x, y, 6, "blue", pr(t, 7.6 + k * 0.02, 0.3))
    T(b, "Envelop and annihilate", cx, 1450, "label", "blue", t, 10.4, align="center")
    source(b, t, SOURCE, 1.0)


# ───────────────────────────────────────────────────── 8. phases (19.6 s)
ROUTE = [(22.9, 40.6), (26.4, 40.3), (27.3, 40.2), (31, 38.6), (34.5, 37.4), (36.2, 36.85), (35.5, 35),
         (35.2, 33.27), (33, 31.2), (31.25, 29.85), (33.6, 31.5), (35.9, 33.6), (38.6, 36.4), (43.5, 36.6)]
BATTLES = [("Granicus", "334", 2.6, (0, -34)), ("Issus", "333", 8.4, (0, -34)), ("Gaugamela", "331", 16.4, (0, -38))]


def s_phases(b, t):
    cv = b.cv
    header(b, t, "Main phases", "Three battles", "Alexander's route, 334–331 BCE, and where the war was decided")
    m = FlatMap(b, (19, 28, 48, 43), (0, 450, 1080, 600), fade=60)
    land(cv, m, t)
    arrow(cv, pts(m, ROUTE), ramp(t, 1.0, 15.4), "orange", 6, dashed=True)
    for n, lab, dx, dy in (("Tyre", "Tyre", -20, 8), ("Memphis", "Egypt", -20, 8)):
        x, y = m.xy(*CITY[n])
        dot(cv, x, y, 6, "text", pr(t, 11.0 if n == "Tyre" else 12.4))
        T(b, lab, x + dx, y + dy, "map_city", "muted", t, 11.2 if n == "Tyre" else 12.6, align="right")
    for n, yr, t0, (dx, dy) in BATTLES:
        x, y = m.xy(*CITY[n])
        last = n == "Gaugamela"
        dot(cv, x, y, 10, "orange" if last else "text", pr(t, t0), ring=True, pulse_t=(t - t0) if last else None)
        T(b, n.upper(), x + dx, y + dy, "map_area", "orange" if last else "text", t, t0 + 0.2, align="center")
    rows = [(2.6, "334", "Granicus", "Opens Asia Minor; the ports blunt Persian sea power"),
            (8.4, "333", "Issus", "Darius routed, the royal family captured"),
            (16.4, "331", "Gaugamela", "The decisive battle")]
    for k, (t0, yr, name, txt) in enumerate(rows):
        y = 1140 + k * 110
        T(b, yr, L, y, "h2", "orange", t, t0)
        T(b, name, L + 130, y, "h2", "text", t, t0 + 0.1)
        T(b, txt, L + 130, y + 40, "body", "muted", t, t0 + 0.2, max_w=R - L - 130)
    source(b, t, "Route simplified  ·  Coastlines: Natural Earth", 1.0)


# ───────────────────────────────────────────────────── 9. battle (22.8 s)
STEPS = [(5.0, "1  Line edges right"), (12.4, "2  A gap opens"), (13.6, "3  Hammer hits Darius"),
         (18.6, "4  The king flees")]


def s_battle(b, t):
    cv = b.cv
    header(b, t, "The battle", "Hammer and anvil", "Gaugamela, 331 BCE: how the battle unfolded (schematic)")
    # field
    fa = pr(t, 0.4, 0.6)
    cv.drawRect(skia.Rect.MakeXYWH(L, 460, R - L, 760), P(col("bg_raised", fa)))
    T(b, "flat plain near modern Erbil, cleared for cavalry and chariots", 540, 1200, "meta", "muted", t, 1.0,
      align="center", rise=0)
    shift = 110 * ramp(t, 5.0, 3.6)       # Macedonian line edges right
    pull = 120 * ramp(t, 5.6, 4.6)        # Persian left wing follows, opening a gap
    rout = ramp(t, 18.8, 2.4)
    pa = pr(t, 0.8, 0.6) * (1 - 0.7 * rout)
    # Persian line (blue)
    for k in range(13):
        x = 130 + k * 60 + (pull if k >= 9 else 0)
        _box(cv, x, 620, 50, 32, "blue", pa, "cav" if k in (0, 1, 9, 10, 11, 12) else "inf", 0.7)
    T(b, "PERSIAN LINE", 130 - 26, 580, "meta", "blue", t, 1.2, tracking=2, rise=0)
    # Darius
    fl = ramp(t, 18.6, 2.0)
    da = pr(t, 1.0) * (1 - fl)
    dx, dy = 560 - 40 * fl, 540 - 60 * fl
    if da:
        cv.drawCircle(dx, dy, 30, P(col("bg", da)))
        cv.drawCircle(dx, dy, 30, P(col("blue", da), "stroke", 3))
        icon_crown(cv, dx, dy, 38, col("blue", da))
        b.text("DARIUS", dx - 44, dy + 10, "meta", "blue", align="right", tracking=2, alpha=da)
    # scythed chariots
    ch = ramp(t, 7.0, 1.6)
    ca = pr(t, 2.4, 0.5) * (1 - ch)
    for k in range(6):
        x, y = 380 + k * 70, 690 + 220 * ch
        if ca:
            tri = skia.Path.Polygon([skia.Point(x, y + 18), skia.Point(x - 14, y - 10), skia.Point(x + 14, y - 10)], True)
            cv.drawPath(tri, P(col("blue", ca)))
    if t < 7.2:
        T(b, "SCYTHED CHARIOTS", 560, 740, "meta", "blue", t, 2.6, align="center", tracking=2, rise=0)
    # gap highlight
    ga = pr(t, 12.2, 0.5) * (1 - rout)
    if ga:
        gx = 130 + 8 * 60 + 25
        r = skia.Rect.MakeXYWH(gx + 6, 590, 60 + pull - 50 - 12, 60)
        p = P(col("orange", ga), "stroke", 3)
        p.setPathEffect(skia.DashPathEffect.Make([10, 8], 0))
        cv.drawRect(r, p)
        b.text("GAP", r.centerX(), 572, "meta", "orange", align="center", tracking=3, alpha=ga)
    # Macedonian line (orange)
    ma = pr(t, 1.4, 0.6)
    adv = 70 * ramp(t, 9.6, 2.4)          # phalanx holds and presses: the anvil
    for k in range(3):
        _box(cv, 230 + k * 58 + shift, 1040, 50, 30, "orange_dim", ma, "cav")
    T(b, "LEFT: PARMENION", 230 - 25 + shift, 1100, "meta", "muted", t, 1.6, tracking=1, rise=0)
    for k in range(6):
        _box(cv, 420 + k * 58 + shift, 1040 - adv, 50, 32, "orange", ma, "inf")
    T(b, "PHALANX", 565 + shift, 1100 - adv, "meta", "orange", t, 1.8, align="center", tracking=2, rise=0)
    T(b, "THE ANVIL", 565 + shift, 990 - adv, "label", "orange", t, 10.6, align="center", rise=0)
    # Companions: the hammer
    cx0, cy0 = 800 + shift, 1040
    hp = ramp(t, 13.6, 4.4)
    gxm = 130 + 8 * 60 + 30 + pull * 0.5
    path_pts = [(cx0, cy0), (cx0 - 20, 860), (gxm, 640), (dx + 50, dy + 30)]
    if hp:
        arrow(cv, path_pts, hp, "orange", 7, dashed=True)
    if hp < 1:
        seg = skia.PathMeasure(smooth_path(path_pts), False)
        pos, _ = seg.getPosTan(seg.getLength() * hp)
        ux, uy = (pos.x(), pos.y()) if hp > 0 else (cx0, cy0)
        _box(cv, ux, uy, 58, 36, "orange", ma, "cav", 1.0)
        if hp == 0:
            T(b, "COMPANIONS", cx0, 1100, "meta", "orange", t, 2.0, align="center", tracking=2, rise=0)
    T(b, "THE HAMMER", 815, 800, "label", "orange", t, 14.4, align="right", rise=0)
    # steps
    for k, (t0, txt) in enumerate(STEPS):
        nxt = STEPS[k + 1][0] if k + 1 < len(STEPS) else 99
        x, y = L + (k % 2) * 470, 1300 + (k // 2) * 70
        T(b, txt, x, y, "label", "orange" if t < nxt else "muted", t, t0)
    source(b, t, "Schematic, not to scale  ·  " + SOURCE.replace("Sources: ", ""), 1.0)


# ───────────────────────────────────────────────────── 10. outcome (17.6 s)
REASONS = [(10.2, "Combined arms cancelled out numbers"), (12.0, "A cohesive army against a fragmented host"),
           (14.4, "A relentless focus on the enemy king")]


def s_outcome(b, t):
    cv = b.cv
    header(b, t, "Outcome and termination", "Total conquest", "The capitals that fell, and three reasons Alexander won")
    m = FlatMap(b, (38, 27.5, 56, 37), (0, 440, 1080, 420), fade=60)
    land(cv, m, t, 0.2)
    for k, n in enumerate(("Babylon", "Susa", "Persepolis")):
        x, y = m.xy(*CITY[n])
        t0 = 0.6 + k * 0.9
        a = pr(t, t0)
        dot(cv, x, y, 9, "orange", a, ring=True)
        T(b, n, x, y + 50, "map_city", "text", t, t0 + 0.1, align="center")
        if a:
            icon_check(cv, x + 34, y - 26, 26, col("orange", a), 5)
    T(b, "330 BCE", L, 950, "h2", "red", t, 3.6)
    T(b, "Darius murdered by his own satrap, Bessus", L + 190, 950, "label", "text", t, 3.8, max_w=R - L - 190)
    stamp(b, "NO TREATY", 540, 1060, t, 6.6, "red", 54, -5)
    T(b, "WHY ALEXANDER WON", L, 1190, "kicker", "muted", t, 9.2, tracking=4)
    for k, (t0, txt) in enumerate(REASONS):
        y = 1260 + k * 72
        a = pr(t, t0)
        if a:
            cv.drawCircle(L + 22, y - 12, 20, P(col("orange", a), "stroke", 3))
            b.text(str(k + 1), L + 22, y - 1, "meta", "orange", align="center", alpha=a)
        T(b, txt, L + 62, y, "label", "text", t, t0 + 0.1, max_w=R - L - 62)
    source(b, t, SOURCE, 1.0)


# ─────────────────────────────────────────────────────── 11. cost (15.2 s)
def s_cost(b, t):
    cv = b.cv
    header(b, t, "Scale and human impact", "The human cost", "Where the war's toll fell hardest")
    m = FlatMap(b, (30, 27.5, 56, 39), (0, 440, 1080, 560), fade=60)
    land(cv, m, t)
    marks = [("Gaugamela", 2.8, (0, -36)), ("Tyre", 7.0, (0, -32)), ("Persepolis", 10.0, (0, 50))]
    for n, t0, (dx, dy) in marks:
        x, y = m.xy(*CITY[n])
        dot(cv, x, y, 10, "red", pr(t, t0), ring=True, pulse_t=t - t0)
        T(b, n.upper(), x + dx, y + dy, "map_area", "red", t, t0 + 0.2, align="center")
    rows = [(2.8, "Gaugamela, 331", "Tens of thousands killed in one battle"),
            (7.0, "Tyre, 332", "A brutal siege; civilians uprooted"),
            (10.0, "Persepolis, 330", "Burned: the end of Persian imperial culture")]
    for k, (t0, name, txt) in enumerate(rows):
        y = 1080 + k * 95
        T(b, name, L, y, "label", "red", t, t0)
        T(b, txt, L + 300, y, "body", "text", t, t0 + 0.1, max_w=R - L - 300)
    T(b, "Ancient figures are exaggerated. The true toll is unknown, but it was *immense.*", L, 1390, "label",
      "muted", t, 1.4, max_w=R - L, lh=1.25)
    source(b, t, SOURCE, 1.0)


# ────────────────────────────────────────────────────── 12. legacy (10 s)
def s_legacy(b, t):
    cv = b.cv
    header(b, t, "Consequences", "A new age", "Hellenistic rule, from Greece to the Indus")
    m = FlatMap(b, (17, 21, 78, 46), (0, 450, 1080, 560), fade=60)
    land(cv, m, t, 0.2)
    g = ramp(t, 0.8, 4.0)
    x0, _ = m.xy(17, 0)
    x1, _ = m.xy(78, 0)
    region(cv, m, ALEX, "orange", pr(t, 0.8, 0.3), 0.14, 0.5, clip=skia.Rect.MakeLTRB(0, 0, x0 + (x1 - x0) * g, 1920))
    gx, gy = m.xy(21.5, 39.8)
    T(b, "GREECE", gx, gy - 30, "map_area", "text", t, 0.8, align="center")
    ix, iy = m.xy(70.5, 27.5)
    T(b, "INDUS", ix, iy + 50, "map_area", "text", t, 4.4, align="center")
    chips = [("GREEK LANGUAGE", 5.2), ("CULTURE", 5.7), ("GOVERNMENT", 6.2), ("COMBINED ARMS", 7.6)]
    x, y = L, 1110
    for k, (c, t0) in enumerate(chips):
        w = b.width(c, "kicker", 4) + 44
        if x + w > R:
            x, y = L, y + 80
        x += chip(b, c, x, y, "orange" if k == 3 else "text", pr(t, t0, 0.4)) + 18
    T(b, "The *Hellenistic* age begins", L, 1400, "h2", "text", t, 6.8)
    source(b, t, "Area schematic  ·  Coastlines: Natural Earth", 1.0)


# ────────────────────────────────────────────────────── 13. lessons (14.8 s)
def _mini(cv, k, x, y, w, h, t, t0, c):
    a = pr(t, t0, 0.4)
    if not a:
        return
    if k == 0:      # escalation: a rising step line
        g = ramp(t, t0, 1.6)
        path = skia.Path(); path.moveTo(x, y + h)
        for i in range(5):
            path.lineTo(x + w * i / 5, y + h - h * (i + 1) / 5); path.lineTo(x + w * (i + 1) / 5, y + h - h * (i + 1) / 5)
        pm = skia.PathMeasure(path, False); seg = skia.Path()
        pm.getSegment(0, pm.getLength() * g, seg, True)
        cv.drawPath(seg, P(col(c, a), "stroke", 6))
    elif k == 1:    # sustainment: a supply chain of nodes
        for i in range(4):
            xx = x + w * i / 3
            ia = pr(t, t0 + i * 0.4, 0.3)
            if i:
                cv.drawLine(x + w * (i - 1) / 3 + 18, y + h / 2, xx - 18, y + h / 2, P(col(c, ia), "stroke", 4))
            cv.drawCircle(xx, y + h / 2, 16, P(col(c, ia)))
    else:           # decapitation: hit the apex, the pyramid falls
        fall = ramp(t, t0 + 1.4, 1.2)
        for row in range(3):
            for i in range(row + 1):
                bx = x + w / 2 - (row + 1) * 30 + i * 60 + 4
                by = y + row * 44 + (0 if row == 0 else 30 * fall * (row + i % 2))
                aa = a * (1 - fall) if row == 0 else a * (1 - 0.6 * fall)
                cv.drawRect(skia.Rect.MakeXYWH(bx, by, 52, 36), P(col(c if row == 0 else "muted", aa)))
        if t > t0 + 1.2:
            icon_cross(cv, x + w / 2, y + 18, 40, col("red", a), 7)


LESSONS = [("Escalation", "A limited campaign became total war", 2.4),
           ("Sustainment", "Speed, ports and captured treasuries", 6.4),
           ("Decapitation", "Strike the head and the body can fall", 10.6)]


def s_lessons(b, t):
    cv = b.cv
    header(b, t, "Strategic concepts", "Three lessons", "The strategic ideas the campaign illustrates")
    for k, (name, desc, t0) in enumerate(LESSONS):
        a = pr(t, t0, 0.5)
        if not a:
            continue
        nxt = LESSONS[k + 1][2] if k + 1 < len(LESSONS) else 99
        c = "orange" if t < nxt else "orange_dim"
        y = 480 + k * 320
        rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(L, y, R - L, 280), 12, 12)
        cv.drawRRect(rr, P(col("bg_raised", a)))
        cv.drawRRect(rr, P(col(c, 0.7 * a), "stroke", 2))
        b.text(f"{k + 1}", L + 40, y + 90, "h2", c, alpha=a)
        b.text(name, L + 90, y + 90, "h2", "text", alpha=a)
        b.text(desc, L + 40, y + 160, "body", "muted", max_w=440, lh=1.2, alpha=a)
        _mini(cv, k, 640, y + 70, 320, 140, t, t0 + 0.3, c)
    source(b, t, SOURCE, 1.0)


# ─────────────────────────────────────────────────────── 14. close (6 s)
def s_close(b, t):
    cv = b.cv
    header(b, t, "Gaugamela, 331 BCE", "The world remade", "Who held the Near East before and after the war")
    for k, (poly, c, lab, t0) in enumerate(((PERSIA, "blue", "BEFORE: THE PERSIAN EMPIRE", 0.4),
                                            (ALEX, "orange", "AFTER: ALEXANDER'S EMPIRE", 1.4))):
        y = 470 + k * 430
        T(b, lab, L, y + 20, "kicker", c, t, t0, tracking=4)
        m = FlatMap(b, (17, 21, 78, 46), (0, y + 40, 1080, 360), fade=50)
        land(cv, m, t, t0)
        region(cv, m, poly, c, pr(t, t0 + 0.2, 0.6))
    T(b, "One battle. One afternoon.", L, 1400, "h2", "text", t, 2.6)


# ─────────────────────────────────────────────────────── 15. end (3.5 s)
def s_end(b, t):
    a = pr(t, 0.2, 0.6)
    b.text("THE STRATEGIST", 540, 930, "title", "text", align="center", tracking=8, alpha=a)
    b.text("GEOPOLITICS  ·  ECONOMICS  ·  MARKETS", 540, 1000, "kicker", "orange", align="center", tracking=5,
           alpha=pr(t, 0.6, 0.6))


VO = {
    "hook": "Gaugamela, 331 BCE. On one afternoon, on a dusty plain in northern Mesopotamia, the largest empire the "
            "world had yet seen was broken. This is how Alexander of Macedon brought down Achaemenid Persia.",
    "context": "By the 330s BCE, Philip the Second of Macedon had subdued the Greek city-states and bound them into "
               "the League of Corinth. To the east lay the Persian Empire of Darius the Third — a vast, multi-ethnic "
               "superpower that now saw a united, militarized Greece as an existential threat.",
    "causes": "The grievances ran deep. For decades Persia had bribed and bankrolled Greek rivals like Athens and "
              "Sparta. Panhellenic ideology demanded revenge for Xerxes' invasion and the burning of Athens. And "
              "Macedon wanted land, security and wealth.",
    "trigger": "The spark came in 336 BCE, when Philip was assassinated. Persia hoped Macedon would fall apart. "
               "Instead, young Alexander seized control and, in 334, crossed into Asia — turning a punitive "
               "expedition into a war of conquest.",
    "objectives": "Alexander's goals grew with every victory: from liberating the Greek cities of Asia Minor, taking "
                  "revenge and seizing plunder, to overthrowing the Achaemenid dynasty and ruling as King of Asia. "
                  "Darius began by trying to crush the invader — and ended fighting to save his throne, his family "
                  "and his empire, offering territory and ransoms that Alexander refused.",
    "strengths": "On paper, Persia held every advantage: endless manpower, vast treasure, control of the sea and "
                 "enormous strategic depth. But its army was a decentralized satrapal levy, divided by ethnicity and "
                 "run by a rigid autocracy. Macedon was outnumbered, short of money and lacked a strong navy — yet "
                 "it had a professional army, the phalanx, the Companion cavalry… and Alexander.",
    "strategy": "So Alexander moved fast — seeking decisive battles and seizing treasuries before his money ran out. "
                "Darius, after failing to contain him, gambled on one colossal army to envelop and annihilate the "
                "Macedonians.",
    "phases": "Three battles decided the war. At the Granicus in 334, Alexander opened Asia Minor and began taking "
              "the ports that blunted Persian sea power. At Issus in 333, he routed Darius and captured the royal "
              "family, opening the road to the Levant and Egypt. Then, in 331, came Gaugamela.",
    "battle": "Darius chose a flat plain near modern Erbil, cleared for his cavalry and scythed chariots. Alexander "
              "edged his line to the right, stretching the Persians thin. The phalanx held firm — the anvil. When a "
              "gap opened in the Persian line, Alexander led the Companion cavalry — the hammer — straight at "
              "Darius. The king fled, and his army collapsed.",
    "outcome": "Babylon, Susa and Persepolis fell. In 330, Darius was murdered by his own satrap, Bessus. There was "
               "no treaty — only total conquest. Why? Combined arms that cancelled out numbers. A cohesive army "
               "against a fragmented host. And a relentless focus on the enemy king.",
    "cost": "The cost was immense. Ancient figures are exaggerated, but tens of thousands died at Gaugamela alone. "
            "Tyre endured a brutal siege, civilians were uprooted, and the burning of Persepolis marked the violent "
            "end of Persian imperial culture.",
    "legacy": "From Greece to the Indus, Hellenistic rule replaced Persian power — spreading Greek language, culture "
              "and government across Asia, and reshaping warfare around combined arms.",
    "lessons": "Gaugamela still teaches three lessons. Escalation: a limited campaign became total war. Sustainment: "
               "speed, ports and captured treasuries kept Alexander going. And decapitation: strike the head of an "
               "autocratic state, and the whole body can fall.",
    "close": "One battle. One afternoon. And the ancient world was remade.",
}

SCENES = [
    Scene(s_hook, 13.6, [(1.2, "pop"), (2.0, "rise"), (6.8, "pop"), (9.6, "hit_soft")], VO["hook"]),
    Scene(s_context, 19.2, [(1.0, "tick"), (1.5, "tick"), (2.0, "tick"), (3.4, "rise"), (7.4, "rise"),
                            (14.0, "hit_soft")], VO["context"]),
    Scene(s_causes, 14.8, [(1.6, "pop"), (6.4, "pop"), (11.4, "pop")], VO["causes"]),
    Scene(s_trigger, 14.8, [(0.8, "hit"), (7.0, "tick"), (9.6, "pop"), (12.4, "rise")], VO["trigger"]),
    Scene(s_objectives, 22.8, [(1.2, "tick"), (5.8, "tick"), (7.6, "pop"), (10.6, "tick"), (20.4, "hit")],
          VO["objectives"]),
    Scene(s_strengths, 24.0, [(2.0, "tick"), (7.6, "tick"), (14.6, "tick"), (18.4, "rise"), (21.4, "pop")],
          VO["strengths"]),
    Scene(s_strategy, 13.2, [(1.6, "pop"), (3.0, "pop"), (4.6, "pop"), (8.6, "rise")], VO["strategy"]),
    Scene(s_phases, 19.6, [(1.0, "rise"), (2.6, "pop"), (8.4, "pop"), (16.4, "hit_soft")], VO["phases"]),
    Scene(s_battle, 22.8, [(2.4, "tick"), (5.0, "rise"), (12.2, "pop"), (13.6, "rise"), (18.6, "hit")],
          VO["battle"]),
    Scene(s_outcome, 17.6, [(0.6, "tick"), (1.5, "tick"), (2.4, "tick"), (3.6, "pop"), (6.6, "hit"), (10.2, "tick"),
                            (12.0, "tick"), (14.4, "tick")], VO["outcome"]),
    Scene(s_cost, 15.2, [(2.8, "pop"), (7.0, "pop"), (10.0, "pop")], VO["cost"]),
    Scene(s_legacy, 10.0, [(0.8, "rise"), (7.6, "pop")], VO["legacy"]),
    Scene(s_lessons, 14.8, [(2.4, "pop"), (6.4, "pop"), (10.6, "pop"), (12.0, "hit_soft")], VO["lessons"]),
    Scene(s_close, 6.0, [(1.4, "rise"), (2.6, "hit_soft")], VO["close"]),
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
