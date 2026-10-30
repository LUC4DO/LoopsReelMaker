"""Load audio, detect BPM/key, and cache features for export rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import librosa
import numpy as np

# Krumhansl-Schmuckler key profiles
MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88], dtype=np.float64
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17], dtype=np.float64
)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class AudioAnalysis:
    path: Path
    y: np.ndarray
    sr: int
    duration: float
    bpm: float
    key: str
    # Precomputed helpers
    hop_length: int = 512
    stft_mag: np.ndarray = field(repr=False, default_factory=lambda: np.zeros((1, 1)))
    # Mel-ish band energies over time for spectrum (n_frames, n_bands)
    band_energies: np.ndarray = field(repr=False, default_factory=lambda: np.zeros((1, 32)))
    times: np.ndarray = field(repr=False, default_factory=lambda: np.zeros(1))


def estimate_key(y: np.ndarray, sr: int) -> str:
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = np.mean(chroma, axis=1)
    chroma_mean = chroma_mean / (np.linalg.norm(chroma_mean) + 1e-9)

    best_score = -1e9
    best = "C major"
    for i in range(12):
        maj = np.roll(MAJOR_PROFILE, i)
        maj = maj / (np.linalg.norm(maj) + 1e-9)
        score_maj = float(np.dot(chroma_mean, maj))
        if score_maj > best_score:
            best_score = score_maj
            best = f"{NOTE_NAMES[i]} major"

        minor = np.roll(MINOR_PROFILE, i)
        minor = minor / (np.linalg.norm(minor) + 1e-9)
        score_min = float(np.dot(chroma_mean, minor))
        if score_min > best_score:
            best_score = score_min
            best = f"{NOTE_NAMES[i]} minor"
    return best


def analyze_audio(path: str | Path, n_bands: int = 32) -> AudioAnalysis:
    path = Path(path)
    y, sr = librosa.load(str(path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(np.atleast_1d(tempo)[0])
    if not np.isfinite(bpm) or bpm <= 0:
        bpm = 120.0

    key = estimate_key(y, sr)

    hop = 512
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    # Map FFT bins to log-spaced bands
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    edges = np.geomspace(max(freqs[1], 30), max(freqs[-1], 31), n_bands + 1)
    bands = np.zeros((S.shape[1], n_bands), dtype=np.float32)
    for i in range(n_bands):
        mask = (freqs >= edges[i]) & (freqs < edges[i + 1])
        if not np.any(mask):
            continue
        bands[:, i] = S[mask, :].mean(axis=0)
    # Normalize per-frame
    peak = bands.max(axis=1, keepdims=True) + 1e-6
    bands = bands / peak
    times = librosa.frames_to_time(np.arange(bands.shape[0]), sr=sr, hop_length=hop)

    return AudioAnalysis(
        path=path,
        y=y,
        sr=sr,
        duration=duration,
        bpm=bpm,
        key=key,
        hop_length=hop,
        stft_mag=S,
        band_energies=bands,
        times=times,
    )


def spectrum_at(analysis: AudioAnalysis, t: float) -> np.ndarray:
    if analysis.band_energies.shape[0] == 0:
        return np.zeros(32, dtype=np.float32)
    idx = int(np.argmin(np.abs(analysis.times - t)))
    idx = int(np.clip(idx, 0, analysis.band_energies.shape[0] - 1))
    return analysis.band_energies[idx].astype(np.float32)


def waveform_window(analysis: AudioAnalysis, t: float, window_sec: float = 0.05) -> np.ndarray:
    start = int(max(0, (t - window_sec / 2) * analysis.sr))
    end = int(min(len(analysis.y), (t + window_sec / 2) * analysis.sr))
    if end <= start:
        return np.zeros(256, dtype=np.float32)
    chunk = analysis.y[start:end]
    # Downsample for drawing
    target = 512
    if len(chunk) > target:
        idxs = np.linspace(0, len(chunk) - 1, target).astype(int)
        chunk = chunk[idxs]
    return chunk.astype(np.float32)


def beat_pulse_at(t: float, bpm: float) -> float:
    if bpm <= 0:
        return 0.0
    period = 60.0 / bpm
    phase = (t % period) / period
    # sharp attack, quick decay
    return float(np.exp(-6.0 * phase))
