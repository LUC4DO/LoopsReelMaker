"""CustomTkinter LOOP REEL MAKER UI."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .audio_analysis import AudioAnalysis, analyze_audio
from .export import export_mp4
from .preview_player import PreviewPlayer, placeholder_image
from .renderer import RenderSettings
from .styles import STYLES

PREVIEW_SIZE = (360, 640)
AUDIO_TYPES = [
    ("Audio", "*.wav *.mp3 *.flac *.m4a *.ogg *.aac"),
    ("All files", "*.*"),
]


class LoopReelMakerApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("LOOP REEL MAKER")
        self.geometry("1100x780")
        self.minsize(960, 700)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.analysis: AudioAnalysis | None = None
        self.audio_path: Path | None = None
        self._exporting = False
        self._bpm_manual = False
        self._key_manual = False

        default_exports = Path.home() / "Videos" / "ReelsAudioMaker"
        default_exports.mkdir(parents=True, exist_ok=True)

        self._build_ui(default_exports)
        self._init_preview()
        self._on_style_change(self.style_var.get())

    def _build_ui(self, default_exports: Path) -> None:
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text="LOOP REEL MAKER", font=ctk.CTkFont(size=26, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(16, 8))

        # Left: preview
        left = ctk.CTkFrame(self, corner_radius=12)
        left.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=8)
        left.grid_rowconfigure(0, weight=1)
        left.grid_columnconfigure(0, weight=1)

        self.preview_label = ctk.CTkLabel(left, text="")
        self.preview_label.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        # Right: controls
        right = ctk.CTkScrollableFrame(self, corner_radius=12)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=8)

        def section(text: str) -> ctk.CTkLabel:
            return ctk.CTkLabel(right, text=text, font=ctk.CTkFont(size=13, weight="bold"))

        section("Audio").pack(anchor="w", padx=8, pady=(8, 2))
        self.audio_btn = ctk.CTkButton(right, text="Choose audio…", command=self._choose_audio)
        self.audio_btn.pack(fill="x", padx=8, pady=2)
        self.audio_label = ctk.CTkLabel(right, text="No file selected", text_color="gray70", wraplength=280)
        self.audio_label.pack(anchor="w", padx=8, pady=(0, 8))

        section("Loop name").pack(anchor="w", padx=8, pady=(4, 2))
        self.loop_name_var = tk.StringVar(value="Sample Loop")
        ctk.CTkEntry(right, textvariable=self.loop_name_var).pack(fill="x", padx=8, pady=2)

        section("Artist").pack(anchor="w", padx=8, pady=(8, 2))
        self.artist_var = tk.StringVar(value="")
        ctk.CTkEntry(right, textvariable=self.artist_var).pack(fill="x", padx=8, pady=2)

        section("Style").pack(anchor="w", padx=8, pady=(12, 2))
        self.style_var = tk.StringVar(value=STYLES[0].name)
        self.style_menu = ctk.CTkOptionMenu(
            right,
            values=[s.name for s in STYLES],
            variable=self.style_var,
            command=self._on_style_change,
        )
        self.style_menu.pack(fill="x", padx=8, pady=2)

        section("Color profile").pack(anchor="w", padx=8, pady=(8, 2))
        self.palette_var = tk.StringVar(value=STYLES[0].palettes[0].name)
        self.palette_menu = ctk.CTkOptionMenu(
            right,
            values=[p.name for p in STYLES[0].palettes],
            variable=self.palette_var,
            command=self._on_palette_change,
        )
        self.palette_menu.pack(fill="x", padx=8, pady=2)

        section("BPM").pack(anchor="w", padx=8, pady=(12, 2))
        self.bpm_var = tk.StringVar(value="120")
        bpm_entry = ctk.CTkEntry(right, textvariable=self.bpm_var)
        bpm_entry.pack(fill="x", padx=8, pady=2)
        bpm_entry.bind("<Key>", lambda _e: setattr(self, "_bpm_manual", True))

        section("Key").pack(anchor="w", padx=8, pady=(8, 2))
        self.key_var = tk.StringVar(value="C minor")
        key_entry = ctk.CTkEntry(right, textvariable=self.key_var)
        key_entry.pack(fill="x", padx=8, pady=2)
        key_entry.bind("<Key>", lambda _e: setattr(self, "_key_manual", True))

        section("Save folder").pack(anchor="w", padx=8, pady=(12, 2))
        folder_row = ctk.CTkFrame(right, fg_color="transparent")
        folder_row.pack(fill="x", padx=8, pady=2)
        self.folder_var = tk.StringVar(value=str(default_exports))
        ctk.CTkEntry(folder_row, textvariable=self.folder_var).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(folder_row, text="Browse", width=70, command=self._browse_folder).pack(
            side="left", padx=(6, 0)
        )

        section("Filename").pack(anchor="w", padx=8, pady=(8, 2))
        self.filename_var = tk.StringVar(value="my_loop_reel.mp4")
        ctk.CTkEntry(right, textvariable=self.filename_var).pack(fill="x", padx=8, pady=2)

        # Bottom bar
        bottom = ctk.CTkFrame(self, corner_radius=12)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 16))
        bottom.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        self.progress.set(0)
        self.progress_label = ctk.CTkLabel(bottom, text="Ready", width=80)
        self.progress_label.grid(row=0, column=1, padx=4)
        # Label showing when the style files were last modified
        self.change_label = ctk.CTkLabel(bottom, text="", width=200, font=ctk.CTkFont(size=10))
        self.change_label.grid(row=0, column=3, padx=8, pady=12, sticky="e")
        self.export_btn = ctk.CTkButton(bottom, text="Export MP4", width=140, command=self._export)
        self.export_btn.grid(row=0, column=2, padx=12, pady=12)

        self.use_gpu_var = tk.BooleanVar(value=False)
        self.gpu_checkbox = ctk.CTkCheckBox(bottom, text="Use GPU (if available)", variable=self.use_gpu_var)
        self.gpu_checkbox.grid(row=0, column=4, padx=12, pady=12)

    def _init_preview(self) -> None:
        self._preview_photo = None

        def on_frame(photo):
            self._preview_photo = photo
            self.preview_label.configure(image=photo, text="")

        def on_missing(msg: str):
            self._preview_photo = placeholder_image(PREVIEW_SIZE, msg)
            self.preview_label.configure(image=self._preview_photo, text="")

        self.player = PreviewPlayer(on_frame=on_frame, on_missing=on_missing, target_size=PREVIEW_SIZE)
        self.player.attach(self)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _style_from_ui(self):
        name = self.style_var.get()
        for s in STYLES:
            if s.name == name:
                return s
        return STYLES[0]

    def _palette_from_ui(self):
        style = self._style_from_ui()
        name = self.palette_var.get()
        for p in style.palettes:
            if p.name == name:
                return p
        return style.palettes[0]

    def _refresh_preview(self) -> None:
        style = self._style_from_ui()
        palette = self._palette_from_ui()
        # Update the timestamp label with the current time when style changes
        import time
        self.change_label.configure(text=f"Last change: {time.strftime('%H:%M:%S')}")
        self.player.play(style.id, palette.id)

    def _on_style_change(self, _value: str | None = None) -> None:
        style = self._style_from_ui()
        names = [p.name for p in style.palettes]
        self.palette_menu.configure(values=names)
        self.palette_var.set(names[0])
        self._refresh_preview()

    def _on_palette_change(self, _value: str | None = None) -> None:
        self._refresh_preview()

    def _choose_audio(self) -> None:
        path = filedialog.askopenfilename(title="Choose audio", filetypes=AUDIO_TYPES)
        if not path:
            return
        self.audio_btn.configure(state="disabled", text="Analyzing…")
        self.audio_label.configure(text=Path(path).name)
        self.update_idletasks()

        def work():
            try:
                analysis = analyze_audio(path)
            except Exception as exc:
                self.after(0, lambda: self._audio_failed(str(exc)))
                return
            self.after(0, lambda: self._audio_ready(Path(path), analysis))

        threading.Thread(target=work, daemon=True).start()

    def _audio_failed(self, err: str) -> None:
        self.audio_btn.configure(state="normal", text="Choose audio…")
        messagebox.showerror("Audio analysis failed", err)

    def _audio_ready(self, path: Path, analysis: AudioAnalysis) -> None:
        self.audio_path = path
        self.analysis = analysis
        self.audio_btn.configure(state="normal", text="Choose audio…")
        self.audio_label.configure(text=str(path))

        stem = path.stem.replace("_", " ").replace("-", " ").strip() or "Untitled Loop"
        self.loop_name_var.set(stem)
        if not self.filename_var.get().strip():
            self.filename_var.set(f"{path.stem}_reel.mp4")
        else:
            # Suggest filename from stem if still default-ish
            current = self.filename_var.get().strip().lower()
            if current in ("my_loop_reel.mp4", "reel.mp4", ""):
                self.filename_var.set(f"{path.stem}_reel.mp4")

        if not self._bpm_manual:
            self.bpm_var.set(str(int(round(analysis.bpm))))
        if not self._key_manual:
            self.key_var.set(analysis.key)

    def _browse_folder(self) -> None:
        path = filedialog.askdirectory(title="Save folder", initialdir=self.folder_var.get() or None)
        if path:
            self.folder_var.set(path)

    def _resolve_output(self) -> Path | None:
        folder = Path(self.folder_var.get().strip())
        name = self.filename_var.get().strip()
        if not name:
            messagebox.showwarning("Filename required", "Enter a filename for the export.")
            return None
        if not folder.exists():
            try:
                folder.mkdir(parents=True, exist_ok=True)
            except Exception as exc:
                messagebox.showerror("Save folder", f"Could not create folder:\n{exc}")
                return None
        out = folder / name
        if out.suffix.lower() != ".mp4":
            out = out.with_suffix(".mp4")
        return out

    def _export(self) -> None:
        if self._exporting:
            return
        if self.analysis is None:
            messagebox.showwarning("No audio", "Choose an audio file first.")
            return
        loop_name = self.loop_name_var.get().strip()
        if not loop_name:
            messagebox.showwarning("Loop name", "Enter a loop name.")
            return
        try:
            bpm = float(self.bpm_var.get().strip())
        except ValueError:
            messagebox.showwarning("BPM", "BPM must be a number.")
            return
        key = self.key_var.get().strip() or "C minor"
        out = self._resolve_output()
        if out is None:
            return
        if out.exists():
            if not messagebox.askyesno("Overwrite?", f"{out.name} already exists. Overwrite?"):
                return

        style = self._style_from_ui()
        palette = self._palette_from_ui()
        settings = RenderSettings(
            style_id=style.id,
            palette_id=palette.id,
            loop_name=loop_name,
            artist=self.artist_var.get().strip(),
            bpm=bpm,
            key=key,
        )

        self._exporting = True
        self.export_btn.configure(state="disabled", text="Exporting…")
        self.progress.set(0)
        self.progress_label.configure(text="0%")

        analysis = self.analysis

        def progress(p: float) -> None:
            self.after(0, lambda: self._set_progress(p))

        def work():
            try:
                export_mp4(
                    analysis,
                    settings,
                    out,
                    progress_cb=progress,
                    use_gpu=self.use_gpu_var.get(),
                )
            except Exception as exc:
                self.after(0, lambda: self._export_done(False, str(exc), out))
                return
            self.after(0, lambda: self._export_done(True, "", out))

        threading.Thread(target=work, daemon=True).start()

    def _set_progress(self, p: float) -> None:
        self.progress.set(max(0.0, min(1.0, p)))
        self.progress_label.configure(text=f"{int(p * 100)}%")

    def _export_done(self, ok: bool, err: str, out: Path) -> None:
        self._exporting = False
        self.export_btn.configure(state="normal", text="Export MP4")
        if ok:
            self.progress.set(1)
            self.progress_label.configure(text="100%")
            messagebox.showinfo("Export complete", f"Saved:\n{out}")
        else:
            self.progress_label.configure(text="Error")
            messagebox.showerror("Export failed", err)

    def _on_close(self) -> None:
        self.player.stop()
        self.destroy()


def main() -> None:
    app = LoopReelMakerApp()
    app.mainloop()
