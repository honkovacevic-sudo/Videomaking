# The Strategist: design system

**Black and orange. Flat, precise, analytical.** The look of a briefing room, not a meme page.
Tokens live in `strategist/theme.py`. Change them there and everything follows.

## Colour
| Token | Hex | Use |
|---|---|---|
| `bg` | `#000000` | Canvas. Pure black, flat, no vignette or lighting |
| `bg_raised` | `#121519` | Cards, panels, chart tracks |
| `grid` | `#1E2328` | Hairlines, axes, gridlines |
| `land` / `land_edge` | `#1B262C` / `#2C3A42` | Flat vector maps: dark slate land, subtle borders; water = canvas |
| **`orange`** | **`#F28C28`** | **The point of the frame.** Titles, the key number, the active row, the thesis word |
| `orange_dim` | `#7A4A1C` | Inactive or secondary orange |
| `red` | `#D9573B` | Adversary, danger, negative, "✕" |
| `blue` | `#4EA8DE` | The other side, for contrast only. Use sparingly |
| `text` / `muted` / `faint` | `#ECE9E4` / `#8A9099` / `#4A5058` | Primary / secondary / sources |

Rules
- **One orange idea per frame.** If everything is orange, nothing is.
- Orange vs blue for two sides; red only for threat or negative.
- No gradients on data, no drop-shadow glow on text. A soft glow is allowed on map markers only.

## Type
**Barlow** for everything (free, technical, slightly military). **Barlow Condensed** for map area names.
- Kicker: SemiBold 26, UPPERCASE, letter-spacing 4, `muted` or `orange`
- Title: SemiBold 72, `orange` (or `text` with one orange word)
- H2 46 · Label 34 · Body 32 · Meta/source 24
- Hero numbers: SemiBold 170, `orange`
- Video captions: Bold 76, `text`, with the key word in `orange`

## Layout (vertical 1080×1920)
- Safe area x 70–1010, y 170–1500. YouTube's UI covers the bottom ~400 px and the right edge.
- Structure: **kicker → title → visual → takeaway → source**.
- Left-aligned text for lists and tables; centred only for single statements.
- Every factual frame carries a source line in `faint`.
- Brand: the words THE STRATEGIST only (no logo mark), top-left, small, `muted`, letter-spaced.
- Default format: **vertical 1080×1920**. Widescreen 1920×1080 is available on request.

## Slides & pacing
- Every slide: **kicker → title → subheading → visual**. The subheading (Barlow Medium 34, `muted`)
  says in plain words what the chart or map shows.
- Each slide stays fully built for **2 s after the narration ends** before switching (`PRODUCTION["hold"]`).

## Voice
- House voice: Kokoro `am_fenrir` ("Voice 2"), unmodified. Pitched-down presets exist in `strategist/voice.py` but aren't used.
- Narration speed 1.05. Music ducks automatically under the voice. Loudness -14 LUFS.
- Sound effects: no whooshes or swooshes (not on slide changes, arrows or text). Only subtle ticks, pops and impact hits.

## Visual vocabulary
- **Flat maps**: no satellite. Land as one dark-slate mass, borders only when they matter,
  cities as dot + ring, rivals as many small dots vs one big dot.
- **Hierarchy lists**: icon · name · description; inactive rows dimmed, active row orange.
- **Timelines**: one axis, two tracks (side A left, side B right), leader lines, axis breaks (≈) for quiet centuries.
- **Unit charts**: one icon = one thing (317 ships vs 3 ships).
- **Comparison tables**: row labels in muted caps, ✕ in red, the verdict in orange.
- **Tactical schematics**: simple shapes, NATO-style symbols, dashed arrows for movement.
