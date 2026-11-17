"""EP02 stills — McNeill, *The Pursuit of Power*: why China didn't become a global power.

Run:  python episodes/mcneill_stills.py      -> out/mcneill/01..06.png

FACTS TO DOUBLE-CHECK BEFORE PUBLISHING
  * ~80% of Song state income to the army, ~40% of it in cash: as given in the
    creator's notes on McNeill; check the exact figures/year in the book (ch. 2).
  * 1024: first government-issued paper money (jiaozi, Sichuan/Chengdu).
  * Zheng He's first voyage (1405): 317 ships, ~27,800 men (Ming records; commonly cited).
  * Columbus 1492: 3 ships, ~90 men. Portugal's John II turned him down (1484/85).
  * 1433: last treasure voyage returns. 1525: edict ordering ocean-going ships destroyed.
  * ~500 independent political units in Europe c. 1500: Charles Tilly (1975).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategist.stills import (Board, FlatMap, P, col, icon_caravel, icon_coins, icon_cross, icon_crown,  # noqa: E402
                               icon_junk, icon_scales, icon_swords)
from strategist.theme import SAFE  # noqa: E402
import skia  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "out" / "mcneill"
L, R = SAFE["left"], SAFE["right"]
SOURCE = "Source: W. H. McNeill, The Pursuit of Power (1982)"


# 1 ─────────────────────────────────────────────────────────────── cover map
def board_cover():
    b = Board()
    b.text("WILLIAM H. MCNEILL  ·  THE PURSUIT OF POWER", L, 250, "kicker", "muted", tracking=4)
    b.text("One empire.", L, 345, "title", "orange")
    b.text("Many rivals.", L, 425, "title", "text")
    m = FlatMap(b, (-12, 4, 134, 68), (0, 470, 1080, 760), fade=70)
    m.land()
    europe = [(-9.14, 38.72), (-4.02, 39.86), (-0.88, 41.65), (-1.64, 42.81), (2.35, 48.86), (-0.13, 51.5),
              (-3.19, 55.95), (12.57, 55.68), (18.07, 59.33), (19.94, 50.06), (25.28, 54.69), (37.62, 55.75),
              (16.37, 48.21), (14.42, 50.09), (19.04, 47.50), (12.33, 45.44), (9.19, 45.46), (8.93, 44.41),
              (11.25, 43.77), (12.50, 41.90), (14.27, 40.85), (28.98, 41.01), (4.48, 51.03), (10.69, 53.87),
              (7.45, 46.95), (11.34, 44.49), (10.40, 43.72), (13.40, 52.52), (6.96, 50.94), (30.52, 50.45)]
    for lon, lat in europe:
        m.city(lon, lat, color="orange", r=7)
    bx, by = m.city(116.40, 39.90, color="text", r=11, ring=True)
    b.text("BEIJING", bx - 34, by - 40, "map_area", "text", align="right")
    b.text("one emperor", bx - 34, by - 6, "map_city", "muted", align="right")
    ex, ey = m.xy(24, 63)
    b.text("EUROPE", ex, ey - 30, "map_area", "orange", align="center")
    b.text("dozens of rival courts", ex, ey + 4, "map_city", "muted", align="center")
    # legend
    y = 1255
    b.cv.drawCircle(L + 8, y - 9, 6, P(col("orange")))
    b.text("Seats of independent power, c. 1500 (selection)", L + 26, y, "meta", "muted")
    b.text("China had the money, the ships and the technology.", L, 1335, "label", "text", max_w=R - L)
    b.text("What it lacked was *competition.*", L, 1398, "h2", "text")
    b.source(SOURCE + "  ·  Coastlines: Natural Earth")
    return b


# 2 ───────────────────────────────────────────────────────── power ladder
def board_power():
    b = Board()
    b.header("From plunder to markets", "How power was organised")
    rows = [
        (icon_swords, "Plunder", "Earliest times",
         "Distance was vast and travel slow. Cities and peoples dealt with each other by raiding."),
        (icon_coins, "Conquer & tax", "Ancient empires",
         "As disease and war became endemic, rulers learned that taxing the conquered paid better, and longer, "
         "than looting them."),
        (icon_crown, "Command", "Bronze to the stirrup",
         "Elites with new military tech (bronze, chariots, cavalry) seized the surplus. Priests and kings "
         "ruled by fear, tradition and faith."),
        (icon_scales, "Markets", "From the 11th century, China first",
         "Prices and money began to coordinate human effort across long distances."),
    ]
    y0, gap = 500, 218
    # progress arrow
    b.cv.drawLine(L + 10, y0 - 30, L + 10, y0 + gap * 3 + 120, P(col("orange_dim"), "stroke", 4))
    tip = skia.Path.Polygon([skia.Point(L + 10, y0 + gap * 3 + 150), skia.Point(L - 4, y0 + gap * 3 + 118),
                             skia.Point(L + 24, y0 + gap * 3 + 118)], True)
    b.cv.drawPath(tip, P(col("orange_dim")))
    for i, (ico, name, era, desc) in enumerate(rows):
        y = y0 + i * gap
        active = i == len(rows) - 1
        c_title = "orange" if active else "text"
        c_icon = col("orange") if active else col("muted")
        if active:
            b.cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L + 50, y - 62, R + 10, y + 168), 10, 10),
                           P(col("orange", 0.07)))
            b.cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(L + 50, y - 62, R + 10, y + 168), 10, 10),
                           P(col("orange", 0.5), "stroke", 2))
        b.cv.drawCircle(L + 10, y - 10, 9, P(col("orange") if active else col("faint")))
        ico(b.cv, L + 125, y + 20, 92, c_icon)
        b.text(name, L + 200, y, "h2", c_title)
        b.text(era.upper(), L + 200 + b.width(name, "h2") + 20, y - 4, "meta", "orange" if active else "muted",
               tracking=2)
        b.text(desc, L + 200, y + 48, "body", "text" if active else "muted", max_w=R - L - 210, lh=1.28)
    b.text("Every technology that shrank time and space (the horse, rail, the telegraph, the phone) "
           "reset this balance.", L, 1408, "body", "muted", max_w=R - L)
    b.source(SOURCE)
    return b


# 3 ─────────────────────────────────────────────────────────── Song China
def board_song():
    b = Board()
    b.header("11th-century China  ·  Song dynasty", "Money meets power")
    m = FlatMap(b, (98, 20.5, 125, 41.5), (0, 440, 1080, 560), fade=60)
    m.land()
    kx, ky = m.city(114.31, 34.80, color="text", r=8, ring=True, label="Kaifeng", dx=22, dy=-12)
    b.text("Song capital", kx + 22, ky + 24, "meta", "muted")
    cx, cy = m.city(104.07, 30.67, color="orange", r=9, ring=True, label="Chengdu", dx=-22, dy=-12, align="right")
    b.text("1024: first state-issued", cx - 22, cy + 24, "meta", "orange", align="right")
    b.text("paper money", cx - 22, cy + 52, "meta", "orange", align="right")

    y = 1135
    b.text("~80%", L - 6, y, "big", "orange")
    b.text("of government income paid the soldiers guarding the frontiers", L + 450, y - 92, "label", "text",
           max_w=R - L - 450, lh=1.22)
    # stacked bar: 80% army (40% of it cash) / 20% everything else
    by, bh, bw = 1205, 54, R - L
    army = bw * 0.8
    b.cv.drawRect(skia.Rect.MakeXYWH(L, by, bw, bh), P(col("bg_raised")))
    b.cv.drawRect(skia.Rect.MakeXYWH(L, by, army, bh), P(col("orange")))
    cash = army * 0.4
    b.cv.save(); b.cv.clipRect(skia.Rect.MakeXYWH(L, by, cash, bh))
    for k in range(-10, 60):
        x = L + k * 16
        b.cv.drawLine(x, by + bh, x + bh, by, P(col("bg", 0.55), "stroke", 5, cap="butt"))
    b.cv.restore()
    b.text("ARMY", L + army - 14, by + 37, "kicker", "bg", align="right", tracking=3)
    b.text("OTHER", L + army + (bw - army) / 2, by + 37, "kicker", "muted", align="center", tracking=3)
    b.cv.drawLine(L, by + bh + 16, L + cash, by + bh + 16, P(col("orange"), "stroke", 3))
    b.cv.drawLine(L, by + bh + 8, L, by + bh + 24, P(col("orange"), "stroke", 3))
    b.cv.drawLine(L + cash, by + bh + 8, L + cash, by + bh + 24, P(col("orange"), "stroke", 3))
    b.text("~40% of it paid in cash", L, by + bh + 60, "label", "orange")
    b.text("A state that bought its army with money was already *running on markets.*", L, 1385, "body", "text",
           max_w=R - L)
    b.source("Figures as cited by W. H. McNeill, The Pursuit of Power (1982)  ·  Coastlines: Natural Earth")
    return b


# 4 ──────────────────────────────────────────────────────────── fleets
def board_fleets():
    b = Board()
    b.header("The scale of Ming sea power", "1405 vs 1492")
    b.text("ZHENG HE'S FIRST VOYAGE  ·  1405", L, 470, "kicker", "orange", tracking=4)
    cols, pitch_x, pitch_y, s = 20, 46.5, 38, 34
    for i in range(317):
        r, c = divmod(i, cols)
        icon_junk(b.cv, L + 20 + c * pitch_x, 540 + r * pitch_y, s, col("orange"))
    b.text("317 ships  ·  ~28,000 men", L, 1185, "h2", "text")
    b.rule(1225)
    b.text("COLUMBUS  ·  1492", L, 1290, "kicker", "muted", tracking=4)
    for i in range(3):
        icon_caravel(b.cv, L + 20 + i * pitch_x, 1345, s, col("text"))
    b.text("3 ships  ·  ~90 men", L + 170, 1358, "h2", "text")
    b.text("Then, in 1433, *China stopped sailing.*", L, 1438, "h2", "text")
    b.source("Fleet figures: Ming records, commonly cited estimates  ·  1 icon = 1 ship")
    return b


# 5 ──────────────────────────────────────────────────────────── timeline
def board_timeline():
    b = Board()
    b.header("China turns inward  ·  Europe sails out", "Two paths after 1433")
    ax = 540
    top, brk0, brk1, bot = 470, 560, 610, 1400

    def Y(year):  # piecewise axis: 1000-1100 compressed, break, 1400-1550 expanded
        if year <= 1100:
            return top + (year - 1000) / 100 * (brk0 - top)
        return brk1 + (year - 1400) / 150 * (bot - brk1)

    b.text("CHINA", ax - 40, top - 50, "kicker", "orange", align="right", tracking=4)
    b.text("EUROPE", ax + 40, top - 50, "kicker", "blue", tracking=4)
    lp = P(col("grid"), "stroke", 3)
    b.cv.drawLine(ax, top, ax, brk0, lp)
    b.cv.drawLine(ax, brk1, ax, bot, lp)
    for yy in (brk0 + 12, brk1 - 12):          # axis break  ≈
        path = skia.Path(); path.moveTo(ax - 16, yy + 5); path.cubicTo(ax - 6, yy - 6, ax + 6, yy + 12, ax + 16, yy - 3)
        b.cv.drawPath(path, P(col("faint"), "stroke", 3))
    for yr in (1000, 1100, 1400, 1450, 1500, 1550):
        y = Y(yr)
        b.cv.drawLine(ax - 10, y, ax + 10, y, P(col("faint"), "stroke", 3))
    # voyages bar 1405-1433
    b.cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(ax - 9, Y(1405), ax - 1, Y(1433)), 3, 3),
                   P(col("orange")))

    def event(year, text, side, label_y=None, color="orange", year_txt=None):
        y = Y(year)
        ly = label_y or y
        sgn = -1 if side == "L" else 1
        x0, x1 = ax + sgn * 14, ax + sgn * 64
        b.cv.drawCircle(ax, y, 7, P(col(color)))
        path = skia.Path(); path.moveTo(x0, y); path.lineTo(x0 + sgn * 20, y); path.lineTo(x1 - sgn * 8, ly); path.lineTo(x1, ly)
        b.cv.drawPath(path, P(col(color, 0.7), "stroke", 2))
        tx = x1 + sgn * 10
        al = "right" if side == "L" else "left"
        b.text(year_txt or str(year), tx, ly + 10, "h2", color, align=al)
        b.text(text, tx, ly + 50, "body", "text", align=al, max_w=360, lh=1.2)

    event(1024, "First state paper money", "L", label_y=top + 10)
    event(1405, "Treasure fleets reach India, Arabia, East Africa", "L", label_y=Y(1405) + 6, year_txt="1405–33")
    event(1433, "Last voyage returns. The fleets are never sent again", "L", label_y=Y(1433) + 120, year_txt="1433")
    event(1525, "Edict orders ocean-going ships destroyed", "L", label_y=Y(1525) + 10)
    event(1415, "Portugal takes Ceuta and pushes down Africa", "R", label_y=Y(1415) - 40, color="blue")
    event(1488, "Dias rounds the Cape of Good Hope", "R", label_y=Y(1488) - 60, color="blue")
    event(1492, "Columbus: Portugal said no, so Castile said yes", "R", label_y=Y(1492) + 70, color="blue")
    event(1498, "Da Gama reaches India", "R", label_y=Y(1498) + 215, color="blue")
    for yr in (1450, 1550):
        b.text(str(yr), ax, Y(yr) - 14, "meta", "faint", align="center")
    b.text("China could stop. *Europe's rivals couldn't.*", L, 1448, "h2", "text")
    b.source(SOURCE, y=1505)
    return b


# 6 ─────────────────────────────────────────────────────────── thesis table
def board_thesis():
    b = Board()
    b.header("McNeill's thesis", "Not religion. Institutions.")
    c1, c2, c3 = L, 330, 690
    y = 500
    b.text("CHINA", c2, y, "kicker", "orange", tracking=4)
    b.text("EUROPE", c3, y, "kicker", "blue", tracking=4)
    b.rule(y + 26)

    def row(y, label, left, right, h=170, mark=False):
        b.text(label.upper(), c1, y + 36, "meta", "muted", tracking=2, max_w=230, lh=1.35)
        if mark:
            icon_cross(b.cv, c2 + 14, y + 26, 22, col("red"), 5)
            icon_cross(b.cv, c3 + 14, y + 26, 22, col("red"), 5)
        off = 44 if mark else 0
        b.text(left, c2 + off, y + 36, "body", "text", max_w=330 - off, lh=1.22)
        b.text(right, c3 + off, y + 36, "body", "text", max_w=320 - off, lh=1.22)
        b.rule(y + h)
        return y + h

    y = row(y + 30, "Faith on profit", "Confucians ranked merchants last", "The Church condemned usury",
            h=170, mark=True)
    b.text("Both distrusted profit, so religion isn't the difference.", c2, y - 26, "meta", "red")
    y += 10
    # who decides + unit chart
    b.text("WHO DECIDES", c1, y + 36, "meta", "muted", tracking=2)
    b.text("One emperor", c2, y + 36, "body", "text")
    b.text("~500 rival states", c3, y + 36, "body", "text")
    b.cv.drawRect(skia.Rect.MakeXYWH(c2, y + 66, 10, 10), P(col("orange")))
    for i in range(500):
        r, c = divmod(i, 40)
        b.cv.drawRect(skia.Rect.MakeXYWH(c3 + c * 8, y + 66 + r * 8, 6, 6), P(col("blue", 0.9)))
    y += 66 + 13 * 8 + 24
    b.rule(y)
    y = row(y, "Stop exploring?", "1433: one decision at court ended the fleets",
            "Portugal turned Columbus down. Castile funded him.", h=190)
    y = row(y, "Rich merchants", "Bought land and joined the gentry", "Lent money to competing kings", h=150)
    b.text("*Competition,* not culture, made Europe a global power.", L, 1380, "h2", "text", max_w=R - L, lh=1.15)
    b.source(SOURCE + "  ·  ~500 units c. 1500: C. Tilly (1975)")
    return b


BOARDS = [("01_one_empire_many_rivals", board_cover), ("02_plunder_to_markets", board_power),
          ("03_song_money_meets_power", board_song), ("04_fleets_1405_vs_1492", board_fleets),
          ("05_two_paths_after_1433", board_timeline), ("06_thesis_institutions", board_thesis)]

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1:]
    for name, fn in BOARDS:
        if only and not any(o in name for o in only):
            continue
        print(fn().save(OUT / f"{name}.png"))
