"""Benchmark script for ReelsAudioMaker export pipeline."""

import argparse
import time
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\lucas\IdeaProjects\LoopsReelMaker")
OUTPUT_DIR = ROOT / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))

from reels_audio_maker.audio_analysis import analyze_audio
from reels_audio_maker.export import export_mp4
from reels_audio_maker.renderer import RenderSettings

def run_benchmark(mode: str, use_gpu: bool | None, out_path: Path):
    audio_path = ROOT / "test_data" / "audio" / "dummy.wav"
    analysis = analyze_audio(audio_path)

    settings = RenderSettings(
        style_id="neon_prism",
        palette_id="cyber_magenta",
        loop_name="Benchmark",
        artist="Test",
        bpm=analysis.bpm,
        key=analysis.key,
    )

    # Cap to 5 seconds for quick testing
    import reels_audio_maker.renderer as rd
    rd.MAX_DURATION_SEC = 5.0

    t0 = time.perf_counter()
    export_mp4(analysis, settings, out_path, use_gpu=use_gpu)
    t1 = time.perf_counter()

    print(f"[{mode.upper()}] Time: {t1-t0:.2f}s, Size: {out_path.stat().st_size/1e6:.2f}MB")

print("Running CPU Benchmark...")
run_benchmark("cpu", False, OUTPUT_DIR / "bench_cpu.mp4")

print("Running GPU Benchmark...")
run_benchmark("gpu", True, OUTPUT_DIR / "bench_gpu.mp4")
