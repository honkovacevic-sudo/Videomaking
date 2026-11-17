"""Procedural soundtrack: a tense documentary music bed + synced SFX.

Nothing here is sampled, so there are no licensing issues. Swap in a
licensed track later with `--music path/to/track.mp3` if you prefer.
"""
import math
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100


def _t(dur):
    return np.arange(int(SR * dur)) / SR


def _env(n, attack, release):
    e = np.ones(n)
    a, r = int(SR * attack), int(SR * release)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r) ** 2
    return e


def _bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], btype="band", fs=SR, output="sos"), x)


def _lp(x, f):
    return sosfilt(butter(2, f, btype="low", fs=SR, output="sos"), x)


rng = np.random.default_rng(3)


# ---------------------------------------------------------------- SFX --------
def whoosh(dur=0.9, lo=300, hi=3000, gain=0.35):
    dur = min(max(dur, 0.35), 1.4)
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    # sweep a band-pass upward by crossfading a few bands
    out = np.zeros(n)
    bands = np.geomspace(lo, hi, 6)
    t = np.linspace(0, 1, n)
    for i, f in enumerate(bands):
        w = np.exp(-((t - i / (len(bands) - 1)) ** 2) / 0.05)
        out += _bp(noise, f * 0.7, min(f * 1.4, SR / 2 - 100)) * w
    env = np.sin(np.pi * t) ** 1.5
    return out / (np.abs(out).max() + 1e-9) * env * gain


def pop(gain=0.22):
    t = _t(0.12)
    f = 520 + 380 * (1 - np.exp(-t * 60))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 38) * gain


def tick(gain=0.16):
    t = _t(0.05)
    return (np.sin(2 * np.pi * 1900 * t) * 0.6 + rng.standard_normal(len(t)) * 0.4) * np.exp(-t * 120) * gain


def hit(gain=0.75):
    t = _t(1.3)
    f = 38 + 70 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    crack = _bp(rng.standard_normal(len(t)), 900, 6000) * np.exp(-t * 45)
    return (boom * 0.9 + crack * 0.6) * gain


def rise(gain=0.18, dur=1.1):
    t = _t(dur)
    f = 180 * (4 ** (t / dur))
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 14 * t))
    return _lp(s, 2500) * (t / dur) ** 1.5 * _env(len(t), 0.0, 0.08) * gain


SFX = {
    "whoosh": lambda d=0.9: whoosh(d),
    "whoosh_short": lambda d=0.5: whoosh(0.5, 600, 4000, 0.25),
    "swoosh": lambda d=0.6: whoosh(0.6, 800, 5000, 0.18),
    "pop": lambda d=0: pop(),
    "tick": lambda d=0: tick(),
    "hit": lambda d=0: hit(),
    "hit_soft": lambda d=0: hit(0.4),
    "rise": lambda d=0: rise(),
}


# -------------------------------------------------------------- MUSIC --------
def music(duration, bpm=96):
    n = int(SR * duration)
    t = np.arange(n) / SR
    out = np.zeros(n)
    beat = 60 / bpm
    bar = beat * 4
    # i - VI - III - VII in A minor, root + fifth + third, two bars each
    chords = [(110.0, 130.81, 164.81), (87.31, 110.0, 130.81), (130.81, 164.81, 196.0), (98.0, 123.47, 146.83)]
    # pad
    for ci in range(int(duration / (bar * 2)) + 1):
        start = ci * bar * 2
        seg = (t >= start) & (t < start + bar * 2 + 0.6)
        tt = t[seg] - start
        env = np.minimum(1, tt / 0.6) * np.minimum(1, np.maximum(0, (bar * 2 + 0.6 - tt) / 0.6))
        for f in chords[ci % 4]:
            for det in (-0.12, 0.12):
                out[seg] += np.sin(2 * np.pi * (f + det) * tt) * env * 0.045
                out[seg] += np.sin(2 * np.pi * (f * 2 + det) * tt) * env * 0.012
    # sub drone with slow swell
    out += np.sin(2 * np.pi * 55 * t) * (0.06 + 0.03 * np.sin(2 * np.pi * t / (bar * 2)))
    # heartbeat kick on beats 1 and 3-and
    k = _t(0.35)
    kick = np.sin(2 * np.pi * np.cumsum(45 + 90 * np.exp(-k * 30)) / SR) * np.exp(-k * 11) * 0.42
    for b in np.arange(0, duration, bar):
        for off in (0, beat * 2.5):
            i = int((b + off) * SR)
            j = min(n, i + len(kick))
            if i < n:
                out[i:j] += kick[: j - i]
    # muted ticking hats on 8ths (clock-like tension)
    h = _bp(rng.standard_normal(int(SR * 0.04)), 6000, 12000) * np.exp(-_t(0.04) * 90) * 0.05
    for b in np.arange(beat / 2, duration, beat / 2):
        i = int(b * SR)
        j = min(n, i + len(h))
        if i < n:
            out[i:j] += h[: j - i]
    out = _lp(out, 7000)
    fade = np.minimum(1, t / 1.0) * np.minimum(1, (duration - t) / 1.5)
    return out * fade


def build_soundtrack(duration, events, path, music_gain=0.8, sfx_gain=1.0):
    n = int(SR * duration)
    mix = music(duration) * music_gain
    for ev in events:
        t0, name = ev[0], ev[1]
        d = ev[2] if len(ev) > 2 else 0
        s = SFX[name](d) * sfx_gain
        # whooshes peak in the middle of a move: start them slightly early
        if name.startswith("whoosh"):
            t0 = max(0, t0 - 0.1)
        i = int(t0 * SR)
        j = min(n, i + len(s))
        if i < n:
            mix[i:j] += s[: j - i]
    peak = np.abs(mix).max()
    if peak > 0.95:
        mix = mix / peak * 0.95
    stereo = np.stack([mix, mix], 1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path
