"""
thumbnail_maker.py - Auto YouTube Thumbnail Generator
=====================================================
Extracts best frames from any video, adds text overlays,
borders, and styling. One click = YouTube-ready thumbnail.
"""

import os
import sys
import json
import subprocess
import threading
import random
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ─── FFMPEG HELPERS ─────────────────────────────────────────

def find_ffmpeg():
    for name in ["ffmpeg", "ffprobe"]:
        local = os.path.join(BASE_DIR, "ffmpeg_bin", name + ".exe")
        if os.path.isfile(local):
            continue
    ffmpeg = os.path.join(BASE_DIR, "ffmpeg_bin", "ffmpeg.exe")
    ffprobe = os.path.join(BASE_DIR, "ffmpeg_bin", "ffprobe.exe")
    if not os.path.isfile(ffmpeg):
        import shutil
        ffmpeg = shutil.which("ffmpeg") or "ffmpeg"
        ffprobe = shutil.which("ffprobe") or "ffprobe"
    return ffmpeg, ffprobe


def get_video_duration(ffprobe, path):
    try:
        r = subprocess.run(
            [ffprobe, "-v", "quiet", "-print_format", "json",
             "-show_format", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        data = json.loads(r.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except:
        return 0


def extract_frames(ffmpeg, ffprobe, video_path, output_dir, count=8):
    """Extract evenly-spaced frames + scene-change frames from video."""
    os.makedirs(output_dir, exist_ok=True)
    duration = get_video_duration(ffprobe, video_path)
    if duration <= 0:
        return []

    frames = []

    # Method 1: Evenly spaced frames (skip first/last 10%)
    start = duration * 0.10
    end = duration * 0.90
    interval = (end - start) / count

    for i in range(count):
        t = start + (i * interval) + (interval * 0.5)
        out_path = os.path.join(output_dir, f"frame_{i:02d}.jpg")
        cmd = [
            ffmpeg, "-y", "-ss", str(t), "-i", video_path,
            "-vframes", "1", "-q:v", "2",
            "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
            out_path
        ]
        subprocess.run(cmd, capture_output=True)
        if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
            frames.append(out_path)

    # Method 2: Scene change detection (bonus frames)
    scene_dir = os.path.join(output_dir, "scenes")
    os.makedirs(scene_dir, exist_ok=True)
    cmd = [
        ffmpeg, "-y", "-i", video_path,
        "-vf", "select='gt(scene,0.4)',scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-vsync", "vfr", "-frames:v", "6", "-q:v", "2",
        os.path.join(scene_dir, "scene_%02d.jpg")
    ]
    subprocess.run(cmd, capture_output=True)

    for f in sorted(os.listdir(scene_dir)):
        fp = os.path.join(scene_dir, f)
        if fp.endswith(".jpg") and os.path.getsize(fp) > 0:
            frames.append(fp)

    return frames


# ─── THUMBNAIL CREATOR ──────────────────────────────────────

THUMBNAIL_STYLES = {
    "Bold Impact": {
        "border_color": (124, 58, 237),
        "border_width": 8,
        "text_color": (255, 255, 255),
        "text_stroke": (0, 0, 0),
        "stroke_width": 4,
        "overlay_opacity": 0.3,
        "overlay_color": (0, 0, 0),
        "font_size_ratio": 0.08,
        "vignette": True,
        "saturation": 1.4,
        "contrast": 1.2,
    },
    "Fire Red": {
        "border_color": (239, 68, 68),
        "border_width": 10,
        "text_color": (255, 255, 255),
        "text_stroke": (180, 0, 0),
        "stroke_width": 5,
        "overlay_opacity": 0.25,
        "overlay_color": (50, 0, 0),
        "font_size_ratio": 0.09,
        "vignette": True,
        "saturation": 1.5,
        "contrast": 1.3,
    },
    "Clean White": {
        "border_color": (255, 255, 255),
        "border_width": 6,
        "text_color": (255, 255, 255),
        "text_stroke": (30, 30, 30),
        "stroke_width": 3,
        "overlay_opacity": 0.35,
        "overlay_color": (0, 0, 20),
        "font_size_ratio": 0.07,
        "vignette": False,
        "saturation": 1.2,
        "contrast": 1.15,
    },
    "Neon Purple": {
        "border_color": (167, 139, 250),
        "border_width": 8,
        "text_color": (255, 255, 255),
        "text_stroke": (88, 28, 135),
        "stroke_width": 4,
        "overlay_opacity": 0.2,
        "overlay_color": (20, 0, 40),
        "font_size_ratio": 0.08,
        "vignette": True,
        "saturation": 1.3,
        "contrast": 1.25,
    },
    "YouTube Classic": {
        "border_color": (255, 0, 0),
        "border_width": 12,
        "text_color": (255, 255, 0),
        "text_stroke": (0, 0, 0),
        "stroke_width": 5,
        "overlay_opacity": 0.15,
        "overlay_color": (0, 0, 0),
        "font_size_ratio": 0.09,
        "vignette": True,
        "saturation": 1.6,
        "contrast": 1.3,
    },
}


def create_thumbnail(frame_path, title_text, style_name="Bold Impact",
                     output_path=None, emoji_text=""):
    """Create a YouTube-ready thumbnail from a frame."""
    if not HAS_PIL:
        return None

    style = THUMBNAIL_STYLES.get(style_name, THUMBNAIL_STYLES["Bold Impact"])

    # Load and resize to YouTube standard
    img = Image.open(frame_path).convert("RGB")
    img = img.resize((1280, 720), Image.LANCZOS)

    # Enhance colors
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(style["saturation"])
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(style["contrast"])

    # Vignette effect (darken edges, keep center bright)
    if style["vignette"]:
        import math
        vignette = Image.new("L", (1280, 720), 255)
        pixels = vignette.load()
        cx, cy = 640, 360
        max_dist = math.sqrt(cx * cx + cy * cy)
        for y_px in range(720):
            for x_px in range(1280):
                dist = math.sqrt((x_px - cx) ** 2 + (y_px - cy) ** 2)
                ratio = dist / max_dist
                # Smooth falloff: center=255 (fully original), edges=0 (fully overlay)
                val = int(255 * max(0, 1.0 - ratio * ratio * 1.8))
                pixels[x_px, y_px] = val
        vignette = vignette.filter(ImageFilter.GaussianBlur(radius=60))
        img = Image.composite(img, Image.new("RGB", (1280, 720), style["overlay_color"]), vignette)

    # Dark overlay at bottom for text
    overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
    draw_overlay = ImageDraw.Draw(overlay)
    # Gradient at bottom
    for y in range(400, 720):
        alpha = int((y - 400) / 320 * style["overlay_opacity"] * 255)
        draw_overlay.rectangle([0, y, 1280, y + 1], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)

    # Border
    bw = style["border_width"]
    bc = style["border_color"]
    draw.rectangle([0, 0, 1279, bw - 1], fill=bc)           # top
    draw.rectangle([0, 720 - bw, 1279, 719], fill=bc)       # bottom
    draw.rectangle([0, 0, bw - 1, 719], fill=bc)            # left
    draw.rectangle([1280 - bw, 0, 1279, 719], fill=bc)      # right

    # Text
    font_size = int(720 * style["font_size_ratio"])
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
        font_small = ImageFont.truetype("arial.ttf", int(font_size * 0.5))
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", font_size)
            font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", int(font_size * 0.5))
        except:
            font = ImageFont.load_default()
            font_small = font

    if title_text:
        # Word wrap
        words = title_text.upper().split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + " " + word if current_line else word
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] > 1100:
                if current_line:
                    lines.append(current_line)
                current_line = word
            else:
                current_line = test
        if current_line:
            lines.append(current_line)

        # Position text at bottom
        line_height = font_size + 10
        total_height = len(lines) * line_height
        y_start = 720 - total_height - 40 - bw

        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_w = bbox[2] - bbox[0]
            x = (1280 - text_w) // 2
            y = y_start + (i * line_height)

            # Stroke/outline
            sw = style["stroke_width"]
            sc = style["text_stroke"]
            for dx in range(-sw, sw + 1):
                for dy in range(-sw, sw + 1):
                    if dx * dx + dy * dy <= sw * sw:
                        draw.text((x + dx, y + dy), line, font=font, fill=sc)
            draw.text((x, y), line, font=font, fill=style["text_color"])

    # Emoji overlay (top-right corner)
    if emoji_text:
        try:
            emoji_font = ImageFont.truetype("seguiemj.ttf", 72)
        except:
            emoji_font = font_small
        draw.text((1280 - 120, 20 + bw), emoji_text, font=emoji_font, fill=(255, 255, 255))

    # Save
    if not output_path:
        output_path = os.path.splitext(frame_path)[0] + "_thumb.jpg"
    img.save(output_path, "JPEG", quality=95)
    return output_path


# ─── GUI ─────────────────────────────────────────────────────

class ThumbnailMakerApp:
    def __init__(self):
        if HAS_CTK:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title("Auto Thumbnail Generator")
        self.root.geometry("920x780")
        self.root.minsize(800, 650)
        self.root.configure(bg="#0d0d1a")

        self.video_path = tk.StringVar(value="")
        self.title_text = tk.StringVar(value="")
        self.emoji_text = tk.StringVar(value="🔥")
        self.style_var = tk.StringVar(value="Bold Impact")
        self.extracted_frames = []
        self.selected_frame = tk.IntVar(value=0)
        self.frame_labels = []
        self.output_path = ""

        self._build_ui()
        self.root.mainloop()

    def _build_ui(self):
        # ── Header ──
        header = self._frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))
        self._label(header, "AUTO THUMBNAIL GENERATOR", size=22, bold=True, color="#a78bfa").pack(side="left")
        self._label(header, "v1.0 | Any Video → YouTube Thumbnail", size=12, color="#64748b").pack(side="left", padx=15)

        # ── Video Input ──
        sec1 = self._frame(self.root)
        sec1.pack(fill="x", padx=20, pady=8)
        self._label(sec1, "Video File", size=14, bold=True).pack(anchor="w")
        row1 = self._frame(sec1)
        row1.pack(fill="x", pady=4)
        self._entry(row1, self.video_path).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row1, "Browse", self._browse_video, width=90).pack(side="right", padx=(0, 6))
        self._button(row1, "📸 Extract Frames", self._extract, width=140, color="#7c3aed").pack(side="right")

        # ── Thumbnail Title ──
        sec2 = self._frame(self.root)
        sec2.pack(fill="x", padx=20, pady=8)
        self._label(sec2, "Thumbnail Title Text", size=14, bold=True).pack(anchor="w")
        row2 = self._frame(sec2)
        row2.pack(fill="x", pady=4)
        self._entry(row2, self.title_text, width=500).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._label(row2, "Emoji:", size=12).pack(side="left", padx=(8, 4))
        self._entry(row2, self.emoji_text, width=60).pack(side="left")

        # ── Style Selection ──
        sec3 = self._frame(self.root)
        sec3.pack(fill="x", padx=20, pady=8)
        row3_header = self._frame(sec3)
        row3_header.pack(fill="x")
        self._label(row3_header, "Thumbnail Style", size=14, bold=True).pack(side="left")

        style_row = self._frame(sec3)
        style_row.pack(fill="x", pady=4)
        for style_name in THUMBNAIL_STYLES:
            if HAS_CTK:
                ctk.CTkRadioButton(
                    style_row, text=style_name, variable=self.style_var,
                    value=style_name, font=("Segoe UI", 12),
                    fg_color="#7c3aed", hover_color="#5b21b6"
                ).pack(side="left", padx=8)
            else:
                tk.Radiobutton(
                    style_row, text=style_name, variable=self.style_var,
                    value=style_name, bg="#0d0d1a", fg="white",
                    selectcolor="#7c3aed", font=("Segoe UI", 11)
                ).pack(side="left", padx=5)

        # ── Frame Selection (scrollable, fixed height) ──
        sec4 = self._frame(self.root)
        sec4.pack(fill="both", expand=True, padx=20, pady=8)
        self._label(sec4, "Select Best Frame (click to select)", size=14, bold=True).pack(anchor="w")

        # Scrollable canvas for frame previews
        self.frames_canvas = tk.Canvas(sec4, bg="#0d0d1a", highlightthickness=0, height=280)
        scrollbar = tk.Scrollbar(sec4, orient="vertical", command=self.frames_canvas.yview)
        self.frames_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.frames_canvas.pack(side="left", fill="both", expand=True, pady=4)

        self.frame_scroll = tk.Frame(self.frames_canvas, bg="#0d0d1a")
        self._frames_window = self.frames_canvas.create_window((0, 0), window=self.frame_scroll, anchor="nw")

        self.frame_scroll.bind("<Configure>",
            lambda e: self.frames_canvas.configure(scrollregion=self.frames_canvas.bbox("all")))
        self.frames_canvas.bind("<Configure>",
            lambda e: self.frames_canvas.itemconfig(self._frames_window, width=e.width))
        # Mouse wheel scrolling
        self.frames_canvas.bind_all("<MouseWheel>",
            lambda e: self.frames_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.frames_canvas_label = self._label(self.frame_scroll,
            "Extract frames from a video to see previews here", size=13, color="#64748b")
        self.frames_canvas_label.pack(fill="both", expand=True)

        # ── Bottom bar: Generate Buttons + Status (always visible) ──
        bottom_bar = self._frame(self.root)
        bottom_bar.pack(fill="x", side="bottom", padx=20, pady=(5, 12))

        self.status_label = self._label(bottom_bar, "Ready — Select a video to start", size=13, color="#64748b")
        self.status_label.pack(anchor="w", pady=(0, 6))

        btn_frame = self._frame(bottom_bar)
        btn_frame.pack(fill="x")
        self.gen_btn = self._button(btn_frame, "🎨 GENERATE THUMBNAIL", self._generate_thumbnail,
                                     width=250, height=45, color="#7c3aed")
        self.gen_btn.pack(side="left")
        self._button(btn_frame, "🎲 RANDOM BEST", self._random_select,
                      width=140, height=45, color="#5b21b6").pack(side="left", padx=10)

    # ── UI Helpers ──
    def _frame(self, parent):
        if HAS_CTK:
            return ctk.CTkFrame(parent, fg_color="transparent")
        return tk.Frame(parent, bg="#0d0d1a")

    def _label(self, parent, text, size=12, bold=False, color="white"):
        weight = "bold" if bold else "normal"
        if HAS_CTK:
            return ctk.CTkLabel(parent, text=text, font=("Segoe UI", size, weight), text_color=color)
        return tk.Label(parent, text=text, font=("Segoe UI", size, weight), fg=color, bg="#0d0d1a")

    def _entry(self, parent, var, width=None):
        if HAS_CTK:
            e = ctk.CTkEntry(parent, textvariable=var, height=36,
                              fg_color="#1a1a2e", border_color="#2d2b55",
                              text_color="white", font=("Consolas", 12), corner_radius=6)
            if width: e.configure(width=width)
            return e
        e = tk.Entry(parent, textvariable=var, bg="#1a1a2e", fg="white",
                     font=("Consolas", 12), relief="flat", bd=4)
        if width: e.configure(width=width // 7)
        return e

    def _button(self, parent, text, command, width=120, height=36, color="#2d2b55"):
        if HAS_CTK:
            return ctk.CTkButton(parent, text=text, command=command,
                                  width=width, height=height,
                                  fg_color=color, hover_color="#5b21b6",
                                  font=("Segoe UI", 13, "bold"), corner_radius=8)
        return tk.Button(parent, text=text, command=command,
                         bg=color, fg="white", font=("Segoe UI", 12, "bold"),
                         relief="flat", bd=0, padx=12, pady=6)

    def _set_status(self, msg, color="#64748b"):
        def _update():
            self.status_label.configure(text=msg)
            if HAS_CTK:
                self.status_label.configure(text_color=color)
            else:
                self.status_label.configure(fg=color)
        self.root.after(0, _update)

    # ── Actions ──
    def _browse_video(self):
        f = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if f:
            self.video_path.set(f)
            self._set_status(f"Video loaded: {os.path.basename(f)}", "#22c55e")

    def _extract(self):
        video = self.video_path.get()
        if not video or not os.path.isfile(video):
            messagebox.showerror("Error", "Please select a valid video file.")
            return

        self._set_status("Extracting frames... please wait", "#f59e0b")

        def run():
            ffmpeg, ffprobe = find_ffmpeg()
            temp_dir = os.path.join(BASE_DIR, "_thumb_frames")
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)

            frames = extract_frames(ffmpeg, ffprobe, video, temp_dir, count=8)
            self.extracted_frames = frames

            self.root.after(0, lambda: self._display_frames(frames))
            if frames:
                self._set_status(f"✓ Extracted {len(frames)} frames — click one to select", "#22c55e")
            else:
                self._set_status("✗ Failed to extract frames", "#ef4444")

        threading.Thread(target=run, daemon=True).start()

    def _display_frames(self, frames):
        # Clear previous
        for widget in self.frame_scroll.winfo_children():
            widget.destroy()
        self.frame_labels = []

        if not frames:
            self._label(self.frame_scroll, "No frames extracted", size=13, color="#ef4444").pack()
            return

        if not HAS_PIL:
            self._label(self.frame_scroll, "Install Pillow to see previews: pip install Pillow",
                        size=13, color="#f59e0b").pack()
            return

        # Create scrollable grid of frames
        row_frame = None
        for i, fp in enumerate(frames):
            if i % 4 == 0:
                row_frame = self._frame(self.frame_scroll)
                row_frame.pack(fill="x", pady=2)

            try:
                pil_img = Image.open(fp)
                pil_img = pil_img.resize((220, 124), Image.LANCZOS)

                from PIL import ImageTk
                tk_img = ImageTk.PhotoImage(pil_img)

                frame_container = self._frame(row_frame)
                frame_container.pack(side="left", padx=4, pady=2)

                if HAS_CTK:
                    lbl = ctk.CTkLabel(frame_container, text="", image=tk_img,
                                        fg_color="#1a1a2e", corner_radius=6)
                else:
                    lbl = tk.Label(frame_container, image=tk_img, bg="#1a1a2e", bd=2, relief="solid")

                lbl.image = tk_img  # Keep reference
                lbl.pack()

                idx = i
                lbl.bind("<Button-1>", lambda e, idx=idx: self._select_frame(idx))

                num_label = self._label(frame_container, f"Frame {i+1}", size=10, color="#94a3b8")
                num_label.pack()

                self.frame_labels.append((lbl, frame_container))
            except Exception as e:
                print(f"Frame display error: {e}")

    def _select_frame(self, idx):
        self.selected_frame.set(idx)
        # Highlight selected
        for i, (lbl, container) in enumerate(self.frame_labels):
            if i == idx:
                if HAS_CTK:
                    lbl.configure(fg_color="#7c3aed")
                else:
                    lbl.configure(bg="#7c3aed", bd=3)
            else:
                if HAS_CTK:
                    lbl.configure(fg_color="#1a1a2e")
                else:
                    lbl.configure(bg="#1a1a2e", bd=2)

        self._set_status(f"Selected Frame {idx + 1}", "#a78bfa")

    def _random_select(self):
        if self.extracted_frames:
            idx = random.randint(0, len(self.extracted_frames) - 1)
            self._select_frame(idx)

    def _generate_thumbnail(self):
        if not self.extracted_frames:
            messagebox.showerror("Error", "Extract frames from a video first.")
            return
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow is required: pip install Pillow")
            return

        idx = self.selected_frame.get()
        if idx >= len(self.extracted_frames):
            idx = 0

        frame_path = self.extracted_frames[idx]
        title = self.title_text.get()
        style = self.style_var.get()
        emoji = self.emoji_text.get()

        # Ask where to save
        save_path = filedialog.asksaveasfilename(
            title="Save Thumbnail",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")],
            initialfile="thumbnail.jpg"
        )
        if not save_path:
            return

        self._set_status("Generating thumbnail...", "#f59e0b")

        def run():
            try:
                result = create_thumbnail(frame_path, title, style, save_path, emoji)
                if result:
                    self.output_path = result
                    self._set_status(f"✅ Thumbnail saved: {os.path.basename(result)}", "#22c55e")
                    # Open the result
                    os.startfile(result)
                else:
                    self._set_status("✗ Failed to generate thumbnail", "#ef4444")
            except Exception as e:
                self._set_status(f"Error: {e}", "#ef4444")

        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    if not HAS_PIL:
        print("WARNING: Pillow not installed. Run: pip install Pillow")
        print("The app will work but thumbnail generation requires Pillow.")
    ThumbnailMakerApp()
