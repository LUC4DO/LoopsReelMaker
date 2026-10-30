"""Benchmark video export performance."""
import time
from pathlib import Path
from reels_audio_maker.audio_analysis import AudioAnalysis, analyze_audio
from reels_audio_maker.export import export_mp4
from reels_audio_maker.renderer import RenderSettings

# Test with a short clip
test_file = Path("./test_audio/sample.mp3")

if not test_file.exists():
    test_file = Path("./assets/test_audio/sample.mp3")

def benchmark():
    print("=" * 60)
    print("BENCHMARKING VIDEO EXPORT PERFORMANCE")
    print("=" * 60)

    # Test with a short 10-second clip (instead of full length)
    settings = RenderSettings(
        style_id="neon_prism",
        palette_id="cyber_magenta",
        loop_name="Benchmark Test",
        artist="Benchmark",
        bpm=120,
        key="C minor",
        width=1440,
        height=2560,
        fps=30,
    )

    print(f"\nSettings:")
    print(f"  Style: {settings.style_id}")
    print(f"  Palette: {settings.palette_id}")
    print(f"  Resolution: {settings.width}x{settings.height}")
    print(f"  FPS: {settings.fps}")

    print(f"\nRunning export for ~10 seconds (30 frames)...")
    print("-" * 60)

    start = time.time()
    result_path = export_mp4(
        settings=settings,
        output_path=Path("./benchmark_output.mp4"),
    )
    elapsed = time.time() - start
    # result is Path, not ExportResult; benchmark is outdated and unused
    result = type("obj", (), {"duration": 0, "fps": settings.fps})()

    print(f"Export complete in {elapsed:.2f}s")
    print("-" * 60)

    # result is just a Path; duration info not available here
    print(f"Export complete in {elapsed:.2f}s")
    print("⚠️  Benchmark script is deprecated; use scripts/benchmark_export.py for accurate metrics.")

    print("\n" + "=" * 60)
    print("Benchmark complete!")
    print("Output saved to: benchmark_output.mp4")
    print("=" * 60)

if __name__ == "__main__":
    benchmark()