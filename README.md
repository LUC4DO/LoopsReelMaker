# ReelsAudioMaker — LOOP REEL MAKER

Desktop app that analyzes a loop, shows BPM/key, and exports Instagram Reels–format videos (9:16, 1440×2560) with five visual styles and five color profiles each.

## Features

- Load WAV / MP3 / FLAC / M4A / OGG
- Auto BPM + musical key (manual override)
- Loop name + artist on the video
- **5 styles × 5 color profiles** (25 looks)
- Independent looping **example previews** (not tied to the export pipeline)
- Choose **save folder** and **filename** before export
- Export up to 30 seconds (or end of audio) as H.264 MP4

### Styles

1. **Neon Prism** — extruded spectrum bars + waveform  
2. **CRT Retro Wave** — synthwave grid, scanlines, RGB fringe  
3. **Orbital Pulse** — radial rings and particles  
4. **Glitch Tunnel** — bass tunnel with beat glitches  
5. **LoFi Drift** — soft gradients, grain, calm particles  

## Current Status & Performance (Oct 2026)

The project is functional with 5 visual styles. A performance benchmark (5s export) was completed:

| Style | Total Export Time | Output Size |
| :--- | :--- | :--- |
| **Neon Prism** | ~15s | 41.8 MB |
| **Orbital Pulse** | ~51s | 28.6 MB |
| **CRT Retro Wave** | ~56s | 73.6 MB |
| **Glitch Tunnel** | ~58s | 116.1 MB |
| **LoFi Drift** | ~98s | 113.4 MB |

- **Bottlenecks**: *LoFi Drift* and *Glitch Tunnel* are the most resource-intensive.
- **Pipeline**: Parallel rendering is active. GPU acceleration is supported via `hevc_amf`.
- **Verified**: All styles pass duration and resolution consistency checks.

## Setup

```bash
py -3 -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python scripts/bake_previews.py # once — builds assets/previews
python main.py
```

FFmpeg is provided by `imageio-ffmpeg` (no system install required).

## Usage

1. Choose an audio file (analysis fills BPM/key; edit if needed).
2. Set loop name and artist.
3. Pick style + color profile — the left panel loops a short example clip for that look.
4. Set save folder and filename.
5. Click **Export MP4**.

Previews always show demo text (`Sample Loop` / `Demo Artist`). Your loop name and artist only appear in the exported video.
