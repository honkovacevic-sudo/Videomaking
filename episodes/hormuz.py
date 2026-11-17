"""EP01 — The Strait of Hormuz: the world's oil valve.

VOICEOVER / CAPTION SCRIPT (≈36 s)
  1. One fifth of the world's oil flows through this gap.
  2. At its narrowest, it's just 33 km wide.
  3. Iran holds the northern shore — and has threatened to close it for decades.
  4. Most of that oil sails east — to China, India, Japan and Korea.
  5. 84% of it ends up in Asian refineries.
  6. Pipelines can bypass only a fraction. The rest has nowhere to go.
  7. One strait. Every market.

FACT SOURCES (re-check before publishing)
  * ~20 million b/d through Hormuz ≈ 20% of global petroleum liquids
    consumption — U.S. EIA, "Amid regional conflict, the Strait of Hormuz
    remains critical oil chokepoint" (June 2025), 2024 data.
  * 84% of Hormuz crude & condensate went to Asia in 2024 — same EIA note.
  * ~2.6 million b/d of unused Saudi/UAE bypass pipeline capacity — EIA.
  * Narrowest width ~33 km (21 miles) — EIA chokepoint profile.
"""
from strategist.engine import (Backdrop, Bars, Borders, Camera, Captions, Donut, EndCard, Episode, Key,
                               Measure, Pin, Region, Route, Stamp, Tag, TopCard, WaterLabel)

GULF = [(50.4, 27.3), (52.6, 26.6), (55.0, 26.25), (56.45, 26.5), (57.3, 25.5), (59.3, 23.7), (61.5, 21.6)]
EAST = [(66.5, 16.5), (73.0, 9.5), (78.0, 5.6), (81.0, 5.2), (88.0, 5.6), (94.5, 6.4), (98.3, 4.9),
        (100.8, 2.7), (103.6, 1.15), (105.0, 2.2), (108.0, 7.0), (112.0, 13.5), (116.5, 19.0), (121.2, 20.7),
        (123.4, 24.5)]

ROUTES = {
    "India": GULF + [(65.0, 21.9), (68.6, 22.3)],
    "China": GULF + EAST + [(123.4, 27.5), (122.6, 29.6)],
    "South Korea": GULF + EAST + [(125.6, 30.5), (128.3, 34.0), (129.1, 34.9)],
    "Japan": GULF + EAST + [(128.0, 29.0), (131.6, 30.6), (134.5, 32.9), (139.6, 34.9)],
}


def build():
    cam = Camera([
        Key(0.0, 52.5, 25.0, 44),
        Key(4.6, 54.0, 25.8, 34),
        Key(5.9, 56.4, 26.3, 9.5),
        Key(9.2, 56.4, 26.3, 8.5),
        Key(10.4, 56.2, 25.8, 18),
        Key(14.6, 56.2, 25.8, 15.5),
        Key(16.0, 68.0, 17.0, 50),      # pull out over the Arabian Sea
        Key(17.6, 70.0, 16.0, 48),
        Key(20.4, 122.0, 25.0, 56),     # follow the tankers east
        Key(21.4, 123.0, 26.0, 54),
        Key(22.8, 56.0, 25.0, 30),      # (behind the chart backdrop)
        Key(30.2, 56.0, 25.0, 27),
        Key(31.3, 56.4, 26.2, 12),
        Key(37.3, 56.4, 26.2, 10),
    ])

    els = [
        Borders(),
        # --- 1. hook ---------------------------------------------------------
        TopCard("The Strategist · Geopolitics", "The world's oil valve", "Why every market watches one strait",
                0.2, 4.7, y=300),
        WaterLabel("PERSIAN GULF", 51.0, 27.6, 0.6, 5.2, angle=-28),
        WaterLabel("ARABIAN SEA", 63.0, 16.0, 0.6, 5.2),
        Pin("Strait of Hormuz", 56.45, 26.55, 1.7, 5.3, dx=-110, dy=150),

        # --- 2. close-up -----------------------------------------------------
        WaterLabel("PERSIAN GULF", 54.9, 26.9, 5.6, 9.6, size=34),
        WaterLabel("GULF OF OMAN", 57.7, 25.1, 5.6, 9.6, size=34, angle=-38),
        Measure((56.364, 26.386), (56.342, 26.827), "33 KM", 6.0, 9.4, side=1),

        # --- 3. who controls it ----------------------------------------------
        Region("Iran", 10.0, 14.9, color="red"),
        Tag("Iran", 57.0, 29.6, 10.4, 14.9, size=58, bg="red"),
        Region(["Oman", "United Arab Emirates"], 11.6, 14.9, color="blue"),
        Tag("UAE", 54.2, 23.7, 11.9, 14.9, size=44),
        Tag("Oman", 57.4, 23.1, 12.1, 14.9, size=44),
        Region(["Saudi Arabia", "Qatar", "Kuwait", "Iraq", "Bahrain"], 11.6, 14.9, color="grey", fill_alpha=0.45,
               glow=False, flash=False),

        # --- 4. where the oil goes -------------------------------------------
        Region(["India"], 16.6, 21.6, color="blue", fill_alpha=0.6),
        Region(["China"], 19.6, 21.6, color="blue", fill_alpha=0.6),
        Region(["South Korea", "Japan"], 20.2, 21.6, color="blue", fill_alpha=0.6),
        Route(ROUTES["India"], 15.4, 21.6, draw_time=1.6),
        Route(ROUTES["China"], 16.4, 21.6, draw_time=3.8),
        Route(ROUTES["South Korea"], 16.5, 21.6, draw_time=4.0),
        Route(ROUTES["Japan"], 16.6, 21.6, draw_time=4.2),
        Tag("India", 78.5, 21.0, 16.7, 21.6, size=42),
        Tag("China", 106.0, 32.0, 19.7, 21.6, size=42),
        Tag("Korea", 127.6, 39.2, 20.3, 21.6, size=36),
        Tag("Japan", 138.5, 33.0, 20.4, 21.6, size=36),

        # --- 5 & 6. the numbers ----------------------------------------------
        Backdrop(21.4, 30.5),
        Donut(21.6, 25.2, 84, "goes to Asia", "Hormuz crude exports", "Asia's factories run on this strait",
              "Crude & condensate, 2024 · Source: U.S. EIA"),
        Bars(25.4, 30.4, "If Hormuz closes", [("Oil through Hormuz", 20.0, "yellow"),
                                              ("Spare bypass pipelines", 2.6, "red")],
             "million barrels per day", "Source: U.S. EIA, 2024 estimates"),

        # --- 7. close --------------------------------------------------------
        Region("Iran", 30.6, 34.1, color="red", fill_alpha=0.55),
        Stamp("Chokepoint", 540, 640, 31.4, 34.0, size=118),
        Backdrop(33.8, 37.3, dark=0.55),
        EndCard(34.0, 37.3),

        Captions([
            (0.3, 2.5, "*One fifth* of the world's oil"),
            (2.5, 5.0, "flows through *this gap.*"),
            (5.6, 9.4, "At its narrowest, it's just *33 km* wide."),
            (10.0, 12.0, "*Iran* holds the northern shore"),
            (12.0, 14.8, "and has threatened to *close it.*"),
            (15.0, 17.6, "Most of that oil sails *east*"),
            (17.6, 21.2, "to *China, India, Japan* and *Korea.*"),
            (21.7, 25.1, "*84%* of it ends up in *Asian* refineries."),
            (25.5, 27.9, "Pipelines can bypass only a *fraction.*"),
            (27.9, 30.4, "The rest has *nowhere to go.*"),
            (30.8, 32.2, "One strait."),
            (32.2, 33.8, "*Every market.*"),
        ]),
    ]
    return Episode(duration=37.3, camera=cam, elements=els)
