# The Strategist: video engine

Code that makes the channel's animated explainer videos: black & orange slides, flat maps,
charts, AI narration and a soundtrack, rendered straight to MP4.

## Starting a new video (in a new Claude session)
1. Start a session with this repository attached.
2. Say something like: *"Make an episode about <topic>. Here's my script: …"*
3. Claude runs `setup.sh`, builds the slides in the house style (see `DESIGN.md`), and sends you the MP4.

## Running it yourself
```bash
bash setup.sh                                  # once per machine
python episodes/marchland.py                   # → out/marchland.mp4
python episodes/marchland.py --stills 4,18     # → PNG frames (thumbnails)
python episodes/marchland.py --voice none      # music only, no narration
```

## Episodes
| File | Video |
|---|---|
| `episodes/marchland.py` | The Marchland Theory (current house style, reference episode) |
| `episodes/mcneill_stills.py` / `mcneill_wide.py` | McNeill, *The Pursuit of Power*: stills / widescreen |
| `episodes/hormuz.py` | Strait of Hormuz (early satellite-map style, legacy) |

## Credits & licences
- Voice: Kokoro-82M (Apache-2.0), via the `kokoro-q8-shards` / `kokoro-js` npm packages
- Fonts: Barlow and Inter (SIL Open Font License 1.1)
- Map data: Natural Earth (public domain) via `world-atlas`. Satellite image: NASA Blue Marble (public domain)
- Music & sound effects: synthesised in `strategist/audio.py`
