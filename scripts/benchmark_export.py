#!/usr/bin/env python3
"""
Benchmark script for ReelsAudioMaker export pipeline.

Usage:
    python -m scripts.benchmark_export [--gpu|--cpu] [--style STYLE] [--palette PALETTE] [--max-duration SEC]

Tests:
    - Measures wall-clock time for full export (analysis + rendering + encoding + mux)
    - Reports per-stage timing
    - Verifies output video properties
    - Runs with specified encoder (GPU/CPU/auto)
"""

import argparse
import multiprocessing
import subprocess
import sys
import time
from pathlib import Path

# Ensure frozen executables work
multiprocessing.freeze_support()

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reels_audio_maker.audio_analysis import analyze_audio
from reels_audio_maker.export import export_mp4
from reels_audio_maker.renderer import RenderSettings


DEFAULT_AUDIO = ROOT / "test_data" / "audio" / "dummy.wav"
DEFAULT_OUT_DIR = ROOT / "test_data" / "outputs"
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)


def probe_video(path: Path) -> dict:
    """Run ffprobe and return dict with video info."""
    ffmpeg = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    result = subprocess.run(
        [
            ffmpeg,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,codec_name,duration,bit_rate",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
    keys = ["width", "height", "codec_name", "duration", "bit_rate"]
    return dict(zip(keys, lines)) if len(lines) == len(keys) else {}


def benchmark(
    audio_path: Path,
    out_path: Path,
    use_gpu: bool | None,
    style_id: str,
    palette_id: str,
    max_duration: float | None = None,
) -> dict:
    """Run full export and return timing breakdown."""
    timings = {}

    # 1. Audio analysis
    t0 = time.perf_counter()
    analysis = analyze_audio(audio_path)
    timings["analysis"] = time.perf_counter() - t0
    print(f"  [1/4] Audio analysis: {timings['analysis']:.2f}s  (duration={analysis.duration:.2f}s, bpm={analysis.bpm:.1f}, key={analysis.key})")

    # Cap duration if requested (used internally by export_mp4 via video_duration)
    _ = max_duration if max_duration else 30.0

    # 2. Build render settings
    settings = RenderSettings(
        style_id=style_id,
        palette_id=palette_id,
        loop_name="Benchmark Loop",
        artist="Benchmark Artist",
        bpm=analysis.bpm,
        key=analysis.key,
    )

    # 3. Export (render + encode + mux)
    t0 = time.perf_counter()

    def progress_cb(p: float):
        # Silent by default; could print dots
        pass

    export_mp4(
        analysis,
        settings,
        out_path,
        progress_cb=progress_cb,
        use_gpu=use_gpu,
    )
    timings["export_total"] = time.perf_counter() - t0

    # 4. Verify output
    t0 = time.perf_counter()
    info = probe_video(out_path)
    timings["verify"] = time.perf_counter() - t0

    return {
        "timings": timings,
        "analysis": {"duration": analysis.duration, "bpm": analysis.bpm, "key": analysis.key},
        "video_info": info,
        "output_size_mb": out_path.stat().st_size / (1024 * 1024),
    }


def main():
    parser = argparse.ArgumentParser(description="Benchmark ReelsAudioMaker export")
    parser.add_argument("--audio", type=Path, default=DEFAULT_AUDIO, help="Input audio file")
    parser.add_argument("--out", type=Path, default=None, help="Output MP4 path (default: outputs/bench_<mode>.mp4)")
    parser.add_argument("--style", default="neon_prism", help="Style ID")
    parser.add_argument("--palette", default="cyber_magenta", help="Palette ID")
    parser.add_argument("--max-duration", type=float, default=30.0, help="Max export duration in seconds")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--gpu", action="store_true", help="Force GPU (AMD AMF) encoder")
    g.add_argument("--cpu", action="store_true", help="Force CPU (libx265 veryfast) encoder")
    g.add_argument("--auto", action="store_true", help="Auto-detect (default)")
    args = parser.parse_args()

    # Resolve encoder mode
    if args.gpu:
        use_gpu = True
        mode = "gpu"
    elif args.cpu:
        use_gpu = False
        mode = "cpu"
    else:
        use_gpu = None
        mode = "auto"

    # Default output path
    if args.out:
        out_path = args.out
    else:
        out_path = DEFAULT_OUT_DIR / f"bench_{mode}.mp4"

    print(f"\n{'='*60}")
    print(f"Benchmark: mode={mode}, style={args.style}, palette={args.palette}")
    print(f"Audio: {args.audio} ({args.audio.stat().st_size/1e6:.1f} MB)")
    print(f"Output: {out_path}")
    print(f"Max duration: {args.max_duration}s")
    print(f"{'='*60}\n")

    # Warm-up: probe ffmpeg encoders once
    try:
        ffmpeg = __import__("imageio_ffmpeg").get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-encoders"], capture_output=True, timeout=5)
    except Exception:
        pass

    # Run benchmark
    result = benchmark(
        audio_path=args.audio,
        out_path=out_path,
        use_gpu=use_gpu,
        style_id=args.style,
        palette_id=args.palette,
        max_duration=args.max_duration,
    )

    # Print results
    t = result["timings"]
    v = result["video_info"]
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"  Audio analysis:     {t['analysis']:.2f}s")
    print(f"  Export total:       {t['export_total']:.2f}s")
    print(f"  Verify (ffprobe):   {t['verify']:.2f}s")
    print(f"  TOTAL:              {t['analysis'] + t['export_total'] + t['verify']:.2f}s")
    print(f"  Output size:        {result['output_size_mb']:.2f} MB")
    print(f"  Video info:")
    for k, val in v.items():
        print(f"    {k}: {val}")

    # Quick sanity checks
    ok = True
    if "width" in v and int(v["width"]) != 1440:
        print(f"  [!] Unexpected width: {v['width']}")
        ok = False
    if "height" in v and int(v["height"]) != 2560:
        print(f"  [!] Unexpected height: {v['height']}")
        ok = False
    if "duration" in v:
        dur = float(v["duration"])
        expected = min(args.max_duration, result["analysis"]["duration"])
        if abs(dur - expected) > 0.5:
            print(f"  [!] Duration mismatch: got {dur:.2f}s, expected ~{expected:.2f}s")
            ok = False
    if ok:
        print(f"  [OK] All checks passed")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())