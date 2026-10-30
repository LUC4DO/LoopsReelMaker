"""Encode Reels MP4 via imageio-ffmpeg and mux trimmed audio."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Callable

import imageio_ffmpeg
import numpy as np
import cv2

from .audio_analysis import AudioAnalysis
from .renderer import (
    EXPORT_FPS,
    RenderSettings,
    draw_export_frame,
    video_duration,
)

ProgressCb = Callable[[float], None]

# Enable OpenCL acceleration if available (does nothing if not supported)
try:
    if cv2.ocl.haveOpenCL():
        cv2.ocl.setUseOpenCL(True)
except Exception:
    # OpenCL not available or not supported on this platform
    pass

# 10-bit HEVC keeps smooth gradients; 8-bit H.264 (yuv420p) always bands on soft fills.
VIDEO_CRF = "16"
VIDEO_PRESET = "medium"
VIDEO_MAXRATE = "50M"
VIDEO_BUFSIZE = "100M"
AUDIO_BITRATE = "320k"


def _ensure_mp4(path: Path) -> Path:
    if path.suffix.lower() != ".mp4":
        path = path.with_suffix(".mp4")
    return path


def _render_chunk(start: int, end: int, analysis: AudioAnalysis, settings: RenderSettings, fps: int) -> str:
    """Render a chunk of frames to a temporary rawvideo file and return its path."""
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".raw")
    for idx in range(start, end):
        t_val = idx / fps
        frm = draw_export_frame(analysis, settings, t_val)
        if frm.dtype != np.uint8:
            frm = frm.astype(np.uint8)
        tmp.write(frm.tobytes())
    tmp.close()
    return tmp.name


def export_mp4(
    analysis: AudioAnalysis,
    settings: RenderSettings,
    output_path: str | Path,
    progress_cb: ProgressCb | None = None,
    *,
    use_gpu: bool | None = None,
) -> Path:
    output_path = _ensure_mp4(Path(output_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    duration = video_duration(analysis)
    fps = settings.fps or EXPORT_FPS
    total_frames = max(1, int(duration * fps))
    w, h = settings.width, settings.height

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()

    # ------------------------------------------------------------
    # 1️⃣  ffmpeg multithreading / hardware acceleration (AMD AMF)
    # ------------------------------------------------------------
    # Detect available hardware encoder – AMD GPUs can use the AMF
    # (Accelerated Media Framework) for H.265. If the encoder is not
    # present ffmpeg will fall back to libx265.
    # We also request explicit thread count for libx265 to utilise all
    # CPU cores.
    import os, subprocess
    cpu_threads = os.cpu_count() or 1
    # Probe ffmpeg for amf support (quick check, ignore errors)
    amf_supported = False
    try:
        probe = subprocess.run([ffmpeg, "-encoders"], capture_output=True, text=True, timeout=5)
        if "hevc_amf" in probe.stdout:
            amf_supported = True
    except Exception:
        amf_supported = False

    # Resolve final decision based on user request (use_gpu) and availability.
    if use_gpu is True:
        use_amf = amf_supported
    elif use_gpu is False:
        use_amf = False
    else:
        # Auto‑detect: use GPU if available.
        use_amf = amf_supported

    amf_opts = []
    if use_amf:
        # Hardware encoder: hevc_amf. We keep the same CRF quality via
        # qp (quantizer). The exact mapping of CRF to qp varies, but a
        # qp of 24 is visually comparable to CRF 16 for HEVC.
        codec = "hevc_amf"
        amf_opts = ["-c:v", codec, "-qp", "24"]
    else:
        codec = "libx265"
        amf_opts = ["-c:v", codec, "-preset", "veryfast", "-crf", VIDEO_CRF, "-x265-params", f"threads={cpu_threads}:aq-mode=3:aq-strength=1.0:psy-rd=1.0:hdr-opt=0"]

    with tempfile.TemporaryDirectory(prefix="reels_audio_maker_") as tmp:
        tmp_path = Path(tmp)
        silent_video = tmp_path / "silent.mp4"

        cmd = [
            ffmpeg,
            "-y",
            "-f",
            "rawvideo",
            "-vcodec",
            "rawvideo",
            "-s",
            f"{w}x{h}",
            "-pix_fmt",
            "bgr24",
            "-r",
            str(fps),
            "-i",
            "-",
            "-an",
        ] + amf_opts + [
            "-pix_fmt",
            "yuv420p10le" if codec == "libx265" else "yuv420p",
            "-tag:v",
            "hvc1" if codec == "libx265" else "",  # tag only for HEVC libx265
            str(silent_video),
        ]
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        assert proc.stdin is not None

        try:
            # ------------------------------------------------------------
            # 2️⃣  Parallel frame rendering (multiprocessing Pool)
            # ------------------------------------------------------------
            from multiprocessing import Pool
            import os

            # Use a smaller chunk size for smoother progress (~0.5 s per chunk).
            chunk_size = max(1, int(fps * 0.5))
            tasks = []
            for start_i in range(0, total_frames, chunk_size):
                end_i = min(start_i + chunk_size, total_frames)
                tasks.append((start_i, end_i, analysis, settings, fps))

            # Cap workers at 8 (or the number of CPU cores, whichever is lower)
            num_workers = min(os.cpu_count() or 2, 8)
            # Initial progress bump to avoid silent period.
            if progress_cb:
                progress_cb(0.0)
            with Pool(processes=num_workers) as pool:
                chunk_files = pool.starmap(_render_chunk, tasks)

            # Stream the raw‑video chunks to ffmpeg in the original order.
            for c_idx, cf in enumerate(chunk_files):
                with open(cf, "rb") as cf_obj:
                    while True:
                        buf = cf_obj.read(65536)
                        if not buf:
                            break
                        proc.stdin.write(buf)
                # Clean up the temporary chunk file.
                try:
                    os.remove(cf)
                except Exception:
                    pass

                end_i = tasks[c_idx][1]
                if progress_cb:
                    progress_cb(0.9 * end_i / total_frames)
        except Exception:
            proc.kill()
            raise
        finally:
            try:
                proc.stdin.close()
            except Exception:
                pass

        stderr = proc.stderr.read() if proc.stderr else b""
        code = proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg encode failed ({code}): {stderr.decode(errors='ignore')[-800:]}")

        if progress_cb:
            progress_cb(0.92)

        # Mux audio trimmed to duration
        audio_src = str(analysis.path)
        mux_cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(silent_video),
            "-ss",
            "0",
            "-t",
            f"{duration:.4f}",
            "-i",
            audio_src,
            "-map",
            "0:v:0",
            "-map",
            "1:a:0?",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            AUDIO_BITRATE,
            "-shortest",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        mux = subprocess.run(mux_cmd, capture_output=True)
        if mux.returncode != 0:
            raise RuntimeError(
                f"ffmpeg mux failed ({mux.returncode}): {mux.stderr.decode(errors='ignore')[-800:]}"
            )

    if progress_cb:
        progress_cb(1.0)
    return output_path
