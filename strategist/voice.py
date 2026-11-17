"""AI voiceover with Kokoro-82M (Apache-2.0), fully offline.

Model: assets/voice/kokoro-q8.onnx (from the kokoro-q8-shards npm package,
sha256 fbae9257…a1478, byte-identical to onnx-community/Kokoro-82M-v1.0-ONNX).
Voices: assets/voice/voices.npz (from the kokoro-js npm package).

Good narrator voices: am_michael, am_fenrir, am_puck, am_onyx (US male),
bm_george, bm_fable, bm_daniel (UK male), af_heart, af_bella (US female).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
VDIR = ROOT / "assets" / "voice"
CACHE = ROOT / "out" / ".vo_cache"
SR = 24000
_K = None

# Named voice presets: a blend of Kokoro voices + post-processing.
#   blend : [(voice, weight), ...]  style vectors are mixed linearly
#   pitch : semitones (negative = deeper), formants preserved so it stays natural
#   bass  : dB low-shelf boost around 110 Hz for a fuller, broadcast sound
PRESETS = {
    # house voice: pure am_fenrir ("Voice 2"), no blending, deeper via pitch + bass only
    "strategist": {"blend": [("am_fenrir", 1.0)], "pitch": -2.5, "bass": 3.5},
    "strategist_deeper": {"blend": [("am_fenrir", 1.0)], "pitch": -3.5, "bass": 4.0},
}


def _kokoro():
    global _K
    if _K is None:
        import glob
        from kokoro_onnx import Kokoro
        npz = VDIR / "voices.npz"
        v = {Path(f).stem: np.fromfile(f, dtype=np.float32).reshape(-1, 1, 256)
             for f in glob.glob(str(VDIR / "voices" / "*.bin"))}
        for name, pre in PRESETS.items():
            v[name] = sum(v[n] * w for n, w in pre["blend"]).astype(np.float32)
        np.savez(npz, **v)
        _K = Kokoro(str(VDIR / "kokoro-q8.onnx"), str(npz))
    return _K


def normalize(text: str) -> str:
    rep = {"’": "'", "‘": "'", "“": '"', "”": '"', "—": ", ", "–": "-", "…": "..."}
    for a, b in rep.items():
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", text).strip()


def sentences(text: str):
    return [s for s in re.split(r"(?<=[.!?])\s+", normalize(text)) if s]


def _trim(a, thr=0.008, pad=0.04):
    idx = np.where(np.abs(a) > thr)[0]
    if not len(idx):
        return a
    p = int(pad * SR)
    return a[max(0, idx[0] - p): idx[-1] + p]


def _fx(a, pitch=0.0, bass=0.0):
    """Pitch-shift (formant-preserving) + bass shelf via ffmpeg/rubberband. Duration unchanged."""
    import subprocess
    if not pitch and not bass:
        return a
    chain = []
    if pitch:
        chain.append(f"rubberband=pitch={2 ** (pitch / 12):.5f}:formant=preserved:pitchq=quality")
    if bass:
        chain.append(f"bass=g={bass}:f=110:w=0.7")
    r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", ",".join(chain), "-f", "f32le", "-ar", str(SR), "-ac", "1", "-"],
                       input=a.astype(np.float32).tobytes(), capture_output=True, check=True)
    out = np.frombuffer(r.stdout, dtype=np.float32).copy()
    peak = np.abs(out).max()
    return out / peak * 0.9 if peak > 0.95 else out


def synth(text: str, voice="am_michael", speed=1.05, gap=0.32) -> np.ndarray:
    """Speak `text` sentence by sentence; returns float32 mono at 24 kHz. Cached on disk.
    `voice` is a Kokoro voice id or a PRESETS name."""
    CACHE.mkdir(parents=True, exist_ok=True)
    pre = PRESETS.get(voice, {})
    key = hashlib.sha1(f"{voice}|{pre}|{speed}|{gap}|{text}".encode()).hexdigest()[:16]
    f = CACHE / f"{key}.npy"
    if f.exists():
        return np.load(f)
    lang = "en-gb" if voice[:1] == "b" else "en-us"   # presets are US-based
    parts = []
    for s in sentences(text):
        a, sr = _kokoro().create(s, voice=voice, speed=speed, lang=lang)
        assert sr == SR
        parts.append(_trim(a.astype(np.float32)))
        parts.append(np.zeros(int(gap * SR), np.float32))
    out = np.concatenate(parts[:-1]) if parts else np.zeros(1, np.float32)
    if pre:
        out = _fx(out, pre.get("pitch", 0), pre.get("bass", 0))
    np.save(f, out)
    return out


def write_wav(path, a, sr=SR):
    import soundfile as sf
    sf.write(str(path), a, sr)
    return path
