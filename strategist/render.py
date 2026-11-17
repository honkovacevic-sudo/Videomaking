"""Render an episode to MP4 (or a few still frames for quick review).

  python -m strategist.render episodes/hormuz.py                 # full video
  python -m strategist.render episodes/hormuz.py --stills 1,4.5,9 # PNG stills
  python -m strategist.render episodes/hormuz.py --voice vo.mp3   # add voiceover
"""
import argparse
import importlib.util
import multiprocessing as mp
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image

from . import engine
from .audio import build_soundtrack

_EP = None


def load_episode(path):
    spec = importlib.util.spec_from_file_location("episode", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build()


def _frame(i):
    return engine.render_frame(_EP, i / engine.FPS, i).tobytes()


def main():
    global _EP
    ap = argparse.ArgumentParser()
    ap.add_argument("episode")
    ap.add_argument("--out", default=None)
    ap.add_argument("--stills", default=None, help="comma-separated times in seconds")
    ap.add_argument("--workers", type=int, default=mp.cpu_count())
    ap.add_argument("--voice", default=None, help="voiceover audio file to mix in (music ducks under it)")
    ap.add_argument("--music", default=None, help="replace generated music with this audio file")
    ap.add_argument("--no-audio", action="store_true")
    args = ap.parse_args()

    ep_path = Path(args.episode)
    _EP = load_episode(ep_path)
    out_dir = engine.ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    engine.load_all()

    if args.stills:
        for s in args.stills.split(","):
            t = float(s)
            arr = engine.render_frame(_EP, t, int(t * engine.FPS))
            p = out_dir / f"{ep_path.stem}_{t:05.2f}s.png"
            Image.fromarray(arr[..., :3]).save(p)
            print(p)
        return

    n = int(_EP.duration * engine.FPS)
    video = out_dir / f"{ep_path.stem}_video.mp4"
    out = Path(args.out) if args.out else out_dir / f"{ep_path.stem}.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{engine.W}x{engine.H}",
         "-r", str(engine.FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video)], stdin=subprocess.PIPE)
    t0 = time.time()
    ctx = mp.get_context("fork")
    with ctx.Pool(args.workers) as pool:
        for i, buf in enumerate(pool.imap(_frame, range(n), chunksize=4)):
            ff.stdin.write(buf)
            if i % 60 == 0:
                print(f"\rframe {i}/{n}  {time.time() - t0:.0f}s", end="", flush=True)
    ff.stdin.close(); ff.wait()
    print(f"\rrendered {n} frames in {time.time() - t0:.0f}s")

    if args.no_audio:
        video.rename(out)
        print(out); return

    wav = out_dir / f"{ep_path.stem}_sfx.wav"
    build_soundtrack(_EP.duration, _EP.sfx_events(), wav, music_gain=0.0 if args.music else 0.8)
    inputs = ["-i", str(video), "-i", str(wav)]
    filt = "[1:a]volume=1.0[s]"
    mixes = ["[s]"]
    k = 2
    if args.music:
        inputs += ["-i", args.music]
        filt += f";[{k}:a]volume=0.35,afade=t=out:st={_EP.duration - 1.5}:d=1.5[m]"
        mixes.append("[m]"); k += 1
    if args.voice:
        inputs += ["-i", args.voice]
        # duck everything under the voice
        bed = "".join(mixes)
        filt += f";{bed}amix=inputs={len(mixes)}:normalize=0[bed];[{k}:a]asplit[v1][v2];" \
                f"[bed][v1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[duck];" \
                f"[duck][v2]amix=inputs=2:normalize=0[pre]"
    else:
        filt += f";{''.join(mixes)}amix=inputs={len(mixes)}:normalize=0[pre]"
    filt += ";[pre]loudnorm=I=-14:TP=-1.5:LRA=11[a]"   # YouTube loudness target
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", filt, "-map", "0:v",
                    "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(_EP.duration),
                    str(out)], check=True)
    video.unlink(missing_ok=True)
    print(out)


if __name__ == "__main__":
    sys.exit(main())
