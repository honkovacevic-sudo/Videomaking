# The Strategist: video production repo

Animated explainer videos (geopolitics, economics, markets, history) for the YouTube channel
**The Strategist**. Everything is rendered in code: Skia graphics → ffmpeg, offline AI voice (Kokoro).

## First thing in every new session
```bash
bash setup.sh        # ~3–5 min; installs deps, downloads voice model + map data from npm
```
Large assets are not in git (see .gitignore). They come from npm because cloud sessions
can reach npm/PyPI but usually not Hugging Face or GitHub releases.

## House rules: read DESIGN.md before making anything
- Black (#000000, flat, no lighting) and orange (#F28C28). One orange idea per slide.
- Font: Barlow. Brand: the words THE STRATEGIST only, no logo mark.
- Format: **vertical 1080×1920** by default (Shorts). Widescreen only if asked.
- Every slide: kicker → title → **subheading saying what the chart shows** → visual.
- Narration: **Kokoro `am_fenrir`, unmodified** ("Voice 2"). No pitch shift, blending or EQ.
- Pacing: each slide holds **2 s** after its narration ends (`PRODUCTION["hold"]`).
- Sound: **no whooshes/swooshes** (slide changes are silent). Only subtle tick/pop/rise/hit + ducked music.
- All of the above are defaults in `strategist/theme.py` (`COLORS`, `TYPE`, `PRODUCTION`). Don't override per episode.

## Making an episode (the user usually gives a topic or a full script)
1. Copy `episodes/marchland.py` (the reference episode) to `episodes/<slug>.py`.
2. Split the script into slides. One `Scene(fn, est_seconds, sfx_cues, vo_text)` per slide.
   `est_seconds` ≈ words / 2.5. The framework re-times each slide to the real narration
   and scales its animation timings to match.
3. Each scene fn draws with `header(b, t, kicker, title, sub)` plus building blocks:
   `T` (text that fades in), `dot`, `arrow`, `chip`, `stamp`, `glow`, `hatch`,
   `FlatMap` (flat vector maps: `.land()`, `.xy(lon, lat)`, `.land_path()`), icons in `strategist/stills.py`.
4. Preview fully built slides before the full render:
   `python episodes/<slug>.py --stills 5,20,40` (renders PNGs to out/). Check for overlaps.
5. Render: `python episodes/<slug>.py` → `out/<slug>.mp4` (~2–5 min for 2–3 min of video).
6. Send the MP4 to the user. Re-check any facts added beyond the user's script and list them
   at the top of the episode file.

## Layout
- `strategist/theme.py`: design tokens + production defaults (single source of truth)
- `strategist/scenes.py`: scene framework, timing, voice fitting, audio mix, render
- `strategist/stills.py`: Board (canvas), text, FlatMap, icons
- `strategist/voice.py`: Kokoro TTS (sentence-by-sentence, cached in out/.vo_cache)
- `strategist/audio.py`: procedural music bed + SFX (no licensing issues)
- `strategist/engine.py`, `render.py`: legacy satellite-map engine (episodes/hormuz.py, old yellow style)
- `episodes/`: one file per video. `marchland.py` = current reference.

## Gotchas
- Subheadings must fit one line (≤ ~900 px at 34 px). Measure with `Board().width(s, "subtitle")`.
- Safe area x 70–1010, y 170–1500; YouTube UI covers the bottom ~400 px.
- Map country names follow Natural Earth (e.g. "United States of America", "Dem. Rep. Congo").
- Only modern borders are available; historical regions must be drawn as labelled schematics.
