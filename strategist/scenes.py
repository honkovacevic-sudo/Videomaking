"""Scene-based animation framework for house-style explainer videos.

An episode is a list of Scene(fn, duration, cues). Each fn(b, t) draws one
frame onto a Board at local time t. Scenes crossfade through black.

  from strategist.scenes import *
  run(SCENES, "out/name.mp4")            # or run(..., stills=[3.0, 12.5])
"""
from __future__ import annotations

import math
import multiprocessing as mp
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import skia

from .audio import build_soundtrack
from .engine import clamp01, ease_in_out, ease_out, ease_out_back, smooth_path
from .stills import Board, P, col
from .theme import PRODUCTION, SAFE

FPS = 30
L, R = SAFE["left"], SAFE["right"]
FADE = 0.35

__all__ = ["Scene", "run", "pr", "ramp", "T", "dot", "arrow", "header", "chip", "stamp", "glow", "hatch",
           "L", "R", "clamp01", "ease_in_out", "ease_out", "ease_out_back", "P", "col", "skia", "math"]


@dataclass
class Scene:
    fn: callable
    dur: float
    cues: list = field(default_factory=list)   # [(t, sfx_name), ...] local times
    vo: str = ""                               # voiceover text spoken during this scene


def _scaled(fn, k):
    return lambda b, t: fn(b, t * k)


def fit_to_voice(scenes, voice=None, speed=None, lead=None, tail=None, hold=None, min_dur=3.0):
    """Synthesise each scene's VO, stretch/compress the scene's animation to fit it,
    then add `hold` seconds of reading time. Returns (new_scenes, voice_track_float32_24k)."""
    import numpy as np
    from .voice import SR, synth
    voice = voice or PRODUCTION["voice"]
    speed = speed or PRODUCTION["speed"]
    lead = PRODUCTION["lead"] if lead is None else lead
    tail = PRODUCTION["tail"] if tail is None else tail
    hold = PRODUCTION["hold"] if hold is None else hold
    out, clips, t_acc = [], [], 0.0
    for sc in scenes:
        if sc.vo:
            a = synth(sc.vo, voice, speed)
            window = max(min_dur, lead + len(a) / SR + tail)   # animation is synced to this window
            k = sc.dur / window
            out.append(Scene(_scaled(sc.fn, k), window + hold, [(t0 / k, n) for t0, n in sc.cues]))
            clips.append((t_acc + lead, a))
        else:
            out.append(sc)
        t_acc += out[-1].dur
    track = np.zeros(int((t_acc + 1) * SR), np.float32)
    for t0, a in clips:
        i = int(t0 * SR)
        track[i:i + len(a)] += a
    return out, track


# ------------------------------------------------------------------ timing --
def pr(t, t0, d=0.5):
    """0→1 eased progress of an entrance starting at t0 lasting d seconds."""
    return ease_out(clamp01((t - t0) / d))


def ramp(t, t0, d):
    """0→1 ease-in-out progress (for draws, growth, counters)."""
    return ease_in_out(clamp01((t - t0) / d))


# ---------------------------------------------------------------- elements --
def T(b, s, x, y, style, color="text", t=0.0, t0=0.0, d=0.5, rise=18, **kw):
    """Text that fades and rises in at t0. Returns y after the text."""
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


def arrow(cv, pts, prog, color="orange", w=6.0, a=1.0, dashed=False, head=True, glow_=True):
    """Arrow along screen-space waypoints, drawn up to `prog` (0..1)."""
    if prog <= 0 or a <= 0:
        return
    path = smooth_path(pts)
    pm = skia.PathMeasure(path, False)
    Lp = pm.getLength()
    seg = skia.Path()
    pm.getSegment(0, Lp * prog, seg, True)
    if glow_:
        cv.drawPath(seg, P(col(color, 0.35 * a), "stroke", w * 2.2, blur=8))
    p = P(col(color, a), "stroke", w)
    if dashed:
        p.setPathEffect(skia.DashPathEffect.Make([w * 2.6, w * 1.8], 0))
    cv.drawPath(seg, p)
    if head:
        pos, tan = pm.getPosTan(max(0.5, Lp * prog - 0.5))
        ang = math.degrees(math.atan2(tan.y(), tan.x()))
        cv.save(); cv.translate(pos.x(), pos.y()); cv.rotate(ang)
        s = w * 3.0
        tri = skia.Path.Polygon([skia.Point(s * 0.9, 0), skia.Point(-s * 0.6, -s * 0.75), skia.Point(-s * 0.6, s * 0.75)],
                                True)
        cv.drawPath(tri, P(col(color, a)))
        cv.restore()


def header(b, t, kicker, title, sub=None, y=250, title_color="orange"):
    """Kicker / title / subheading. The subheading says what the chart on this slide shows."""
    T(b, kicker.upper(), L, y, "kicker", "muted", t, 0.05, tracking=4)
    end = T(b, title, L, y + 82, "title", title_color, t, 0.15, max_w=R - L, lh=1.08)
    if sub:
        last = end - 72 * 1.08            # baseline of the title's last line
        return T(b, sub, L, last + 56, "subtitle", "muted", t, 0.3, max_w=R - L, lh=1.2)
    return end


def chip(b, text, x, y, color="orange", a=1.0, style="kicker", tracking=4, fill_a=0.08):
    """Outlined pill label. (x, y) = top-left. Returns width."""
    if a <= 0:
        return 0
    w = b.width(text, style, tracking) + 44
    h = 56
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), 8, 8)
    b.cv.drawRRect(rr, P(col(color, fill_a * a)))
    b.cv.drawRRect(rr, P(col(color, 0.8 * a), "stroke", 2))
    b.text(text, x + 22, y + 37, style, color, tracking=tracking, alpha=a)
    return w


def stamp(b, text, x, y, t, t0, color="red", size=64, angle=-6):
    """Slammed bordered stamp, centred on (x, y)."""
    lt = t - t0
    if lt <= 0:
        return
    k = ease_out(clamp01(lt / 0.16))
    a = clamp01(lt / 0.08)
    sc = 1.9 - 0.9 * k
    from .stills import font
    f = font("Barlow-Bold", size)
    tw = f.measureText(text) + 4 * (len(text) - 1)
    bw, bh = tw + 70, size * 1.5
    cv = b.cv
    cv.save(); cv.translate(x, y); cv.rotate(angle); cv.scale(sc, sc)
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-bw / 2, -bh / 2, bw, bh), 10, 10)
    cv.drawRRect(rr, P(col(color, 0.10 * a)))
    cv.drawRRect(rr, P(col(color, a), "stroke", 6))
    x0 = -tw / 2
    for ch in text:
        cv.drawString(ch, x0, size * 0.36, f, P(col(color, a)))
        x0 += f.measureText(ch) + 4
    cv.restore()


def glow(cv, x, y, r, color="blue", a=0.35):
    if a <= 0:
        return
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r, [col(color, a), col(color, 0)])
    cv.drawCircle(x, y, r, skia.Paint(AntiAlias=True, Shader=sh))


def hatch(cv, clip_path, color="orange", a=0.4, spacing=14, w=3):
    """Diagonal hatching inside a path."""
    if a <= 0:
        return
    bnd = clip_path.getBounds()
    cv.save(); cv.clipPath(clip_path, skia.ClipOp.kIntersect, True)
    p = P(col(color, a), "stroke", w, cap="butt")
    span = bnd.width() + bnd.height()
    k = -bnd.height()
    while k < bnd.width():
        cv.drawLine(bnd.left() + k, bnd.bottom(), bnd.left() + k + span, bnd.bottom() - span, p)
        k += spacing
    cv.restore()


# ------------------------------------------------------------------ render --
class _Runner:
    def __init__(self, scenes, size, brand):
        self.scenes, self.size, self.brand = scenes, size, brand
        self.duration = sum(s.dur for s in scenes)

    def frame(self, gt):
        acc = 0.0
        for i, sc in enumerate(self.scenes):
            if gt < acc + sc.dur or i == len(self.scenes) - 1:
                break
            acc += sc.dur
        lt = gt - acc
        last = i == len(self.scenes) - 1
        b = Board(*self.size, brand=self.brand and not last)
        a = clamp01(lt / FADE) if last else clamp01(min(lt / FADE, (sc.dur - lt) / FADE))
        b.cv.saveLayerAlpha(None, int(255 * a))
        sc.fn(b, lt)
        b.cv.restore()
        return b.surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)

    def sfx(self):
        muted = set(PRODUCTION.get("sfx_muted", []))
        trans = PRODUCTION.get("transition_sfx")
        ev, acc = [], 0.0
        for sc in self.scenes:
            if trans:
                ev.append((acc, trans))
            ev += [(acc + t0, n) for t0, n in sc.cues]
            acc += sc.dur
        return [e for e in ev if e[1] not in muted]


_RUN = None


def _render(i):
    return _RUN.frame(i / FPS).tobytes()


def run(scenes, out, size=(1080, 1920), stills=None, workers=None, brand=True, music_gain=0.7,
        voice="default", speed=None):
    """Render scenes to MP4. With voice='am_michael' (etc.), scenes carrying `vo` text are
    narrated by Kokoro and retimed to the narration."""
    global _RUN
    from PIL import Image
    from .engine import A
    A.countries("50m")
    vo_track = None
    if voice == "default":
        voice = PRODUCTION["voice"]
    if voice and any(sc.vo for sc in scenes):
        scenes, vo_track = fit_to_voice(scenes, voice, speed)
    _RUN = _Runner(scenes, size, brand)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if stills:
        paths = []
        for s in stills:
            p = out.with_name(f"{out.stem}_{s:06.2f}s.png")
            Image.fromarray(_RUN.frame(s)[..., :3]).save(p)
            paths.append(p)
        return paths
    n = int(_RUN.duration * FPS)
    vid, wav = out.with_name(out.stem + "_v.mp4"), out.with_name(out.stem + ".wav")
    W, H = size
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s",
                           f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                           "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.get_context("fork").Pool(workers or mp.cpu_count()) as pool:
        for i, buf in enumerate(pool.imap(_render, range(n), chunksize=4)):
            ff.stdin.write(buf)
            if i % 300 == 0:
                print(f"frame {i}/{n}  {time.time() - t0:.0f}s", flush=True)
    ff.stdin.close(); ff.wait()
    build_soundtrack(_RUN.duration, _RUN.sfx(), wav, music_gain=music_gain)
    if vo_track is None:
        cmd = ["-i", str(vid), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
    else:
        from .voice import write_wav
        vwav = out.with_name(out.stem + "_vo.wav")
        write_wav(vwav, vo_track)
        filt = ("[2:a]aresample=44100,highpass=f=70,acompressor=threshold=0.1:ratio=3:attack=5:release=120,"
                "volume=1.6,asplit=2[v1][v2];"
                "[1:a]volume=0.55[bed0];[bed0][v1]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[bed];"
                "[bed][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        cmd = ["-i", str(vid), "-i", str(wav), "-i", str(vwav), "-filter_complex", filt, "-map", "0:v", "-map", "[a]"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *cmd, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", "-t", str(_RUN.duration), str(out)], check=True)
    vid.unlink(); wav.unlink()
    if vo_track is not None:
        vwav.unlink()
    print(out, f"{time.time() - t0:.0f}s")
    return out
