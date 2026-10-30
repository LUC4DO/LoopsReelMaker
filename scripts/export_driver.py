"""Command‑line driver that safely invokes the parallel export.
It adds the required `if __name__ == '__main__'` guard (and `freeze_support`
for frozen executables) so that the multiprocessing pool works on Windows.
The driver simply forwards the arguments to the library's `export_mp4`.
"""
import sys
import multiprocessing
from pathlib import Path

# Required for frozen executables (PyInstaller, py2exe, etc.)
multiprocessing.freeze_support()

from reels_audio_maker.audio_analysis import analyze_audio
from reels_audio_maker.renderer import RenderSettings
from reels_audio_maker.export import export_mp4

def main(argv: list[str] | None = None) -> None:
    argv = argv or sys.argv[1:]
    if len(argv) != 2:
        print("Usage: python -m scripts.export_driver <audio_file> <output_mp4>")
        sys.exit(1)

    audio_path = Path(argv[0])
    out_path = Path(argv[1])

    # Load and analyse the audio (pure NumPy/Librosa, safe for multiprocessing)
    analysis = analyze_audio(audio_path)

    # Pick a default style/palette – you can edit these values as you like.
    settings = RenderSettings(
        style_id="neon_prism",
        palette_id="cyber_magenta",
        loop_name=audio_path.stem,
        artist="CLI Demo",
        bpm=analysis.bpm,
        key=analysis.key,
    )

    # Run the export (this will use the parallel rendering inside export_mp4)
    export_mp4(analysis, settings, out_path)

if __name__ == "__main__":
    main()
