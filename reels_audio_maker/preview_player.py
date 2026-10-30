"""Loop short pre-baked preview MP4s. Does not import export renderers."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from PIL import Image, ImageTk

# Project root = parent of package
ROOT = Path(__file__).resolve().parent.parent
PREVIEWS_ROOT = ROOT / "assets" / "previews"


def preview_path(style_id: str, palette_id: str) -> Path:
    return PREVIEWS_ROOT / style_id / f"{palette_id}.mp4"


class PreviewPlayer:
    """Decode and loop a preview file into a Tk label via PhotoImage callbacks."""

    def __init__(
        self,
        on_frame: Callable[[ImageTk.PhotoImage], None],
        on_missing: Callable[[str], None],
        target_size: tuple[int, int] = (360, 640),
    ) -> None:
        self.on_frame = on_frame
        self.on_missing = on_missing
        self.target_size = target_size
        self._cap: Optional[cv2.VideoCapture] = None
        self._path: Optional[Path] = None
        self._photo: Optional[ImageTk.PhotoImage] = None
        self._after_id = None
        self._widget = None
        self._running = False

    def attach(self, widget) -> None:
        """Widget used for .after scheduling (usually the preview label or root)."""
        self._widget = widget

    def play(self, style_id: str, palette_id: str) -> None:
        path = preview_path(style_id, palette_id)
        self.stop()
        if not path.is_file():
            self.on_missing(f"Preview missing:\n{style_id}/{palette_id}.mp4\n\nRun scripts/bake_previews.py")
            return
        cap = cv2.VideoCapture(str(path))
        if not cap.isOpened():
            self.on_missing(f"Could not open preview:\n{path.name}")
            return
        self._cap = cap
        self._path = path
        self._running = True
        self._tick()

    def stop(self) -> None:
        self._running = False
        if self._widget is not None and self._after_id is not None:
            try:
                self._widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def _tick(self) -> None:
        if not self._running or self._cap is None or self._widget is None:
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            # loop
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
            if not ok or frame is None:
                self.on_missing("Preview ended unexpectedly")
                return

        tw, th = self.target_size
        frame = cv2.resize(frame, (tw, th), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        photo = ImageTk.PhotoImage(img)
        self._photo = photo  # keep ref
        self.on_frame(photo)

        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
        delay = max(16, int(1000 / fps))
        self._after_id = self._widget.after(delay, self._tick)


def placeholder_image(size: tuple[int, int], message: str) -> ImageTk.PhotoImage:
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    arr[:] = (28, 28, 32)
    # OpenCV text
    y = h // 2 - 40
    for i, line in enumerate(message.split("\n")):
        cv2.putText(
            arr,
            line[:48],
            (20, y + i * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (200, 200, 210),
            1,
            cv2.LINE_AA,
        )
    rgb = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(rgb))
