"""Benchmark just the gradient function performance."""
import time
import numpy as np
from reels_audio_maker.styles.base import vertical_gradient

def benchmark_gradient():
    print("=" * 60)
    print("GRADIENT FUNCTION BENCHMARK")
    print("=" * 60)

    # Test different resolutions and resize operations
    resolutions = [
        ("Preview (360x640)", 360, 640),
        ("Half (720x1280)", 720, 1280),
        ("Full (1440x2560)", 1440, 2560),
    ]

    top = (40, 0, 40)
    bottom = (10, 0, 20)

    for name, w, h in resolutions:
        print(f"\n{name} ({w}x{h}):")

        # Warmup
        grad = vertical_gradient(h, w, top, bottom)

        # Benchmark
        iterations = 5
        times = []
        for i in range(iterations):
            start = time.time()
            grad = vertical_gradient(h, w, top, bottom)
            times.append(time.time() - start)

        avg_time = np.mean(times) * 1000  # ms
        fps = 1000 / avg_time
        print(f"  Avg: {avg_time:.3f}ms per frame")
        print(f"  FPS: {fps:.1f} gradient frames/sec")

    print("\n" + "=" * 60)
    print("If this is >10fps, gradients are not the bottleneck!")
    print("The bottleneck is likely in rendering loops, audio analysis, or MP4 encoding.")
    print("=" * 60)

if __name__ == "__main__":
    benchmark_gradient()