"""
app.py - PRO VIDEO SUITE v9
============================
Unified single-window app with sidebar navigation.
6 pages: Video Processor, Batch Queue, Thumbnail Generator, SEO Generator,
         YouTube Upload, Settings & Cleanup.
No popups, no separate windows.
"""

import os
import sys
import threading
import time
import random
import json
import glob
import logging
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    HAS_CTK = True
except ImportError:
    HAS_CTK = False

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter, ImageEnhance
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Import engines
from pro_engine import build_video
from thumbnail_maker import (
    find_ffmpeg, get_video_duration, extract_frames,
    create_thumbnail, THUMBNAIL_STYLES
)
from seo_generator import generate_seo_assets, generate_html
from growth_hacks_data import HACKS_LEVELS
from template_compiler import get_template_info
from shadow_ledger import audit_video, get_all_videos, get_checklist, get_video

try:
    from youtube_uploader import (
        is_available as yt_available, has_credentials as yt_has_creds,
        upload_video as yt_upload, CATEGORIES as YT_CATEGORIES,
        get_authenticated_channels as yt_get_channels
    )
    HAS_YT = True
except ImportError:
    HAS_YT = False

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

from transcriber import transcribe_video
from proxy_manager import (
    get_all_data as proxy_get_all, add_proxy, remove_proxy,
    add_channel as proxy_add_channel, remove_channel as proxy_remove_channel,
    assign_proxy_to_channel, health_check as proxy_health_check,
    kill_switch_check, save_proxy_data, check_ip_direct
)


# ═══════════════════════════════════════════════════════════
#  THEMES
# ═══════════════════════════════════════════════════════════

THEMES = {
    "dark": {
        "BG": "#0d0d1a", "BG_DARK": "#0a0a14", "BG_CARD": "#12101f",
        "BG_INPUT": "#1a1a2e", "BORDER": "#2d2b55",
        "ACCENT": "#7c3aed", "ACCENT_LIGHT": "#a78bfa",
        "ACCENT_HOVER": "#5b21b6", "ACCENT_DARK": "#1e1b4b",
        "TEXT": "#e2e8f0", "TEXT_DIM": "#64748b", "TEXT_MID": "#94a3b8",
        "GREEN": "#22c55e", "RED": "#ef4444", "AMBER": "#f59e0b",
    },
    "light": {
        "BG": "#f0f0f5", "BG_DARK": "#e4e4ec", "BG_CARD": "#ffffff",
        "BG_INPUT": "#e8e8f0", "BORDER": "#c0bfe0",
        "ACCENT": "#7c3aed", "ACCENT_LIGHT": "#6d28d9",
        "ACCENT_HOVER": "#5b21b6", "ACCENT_DARK": "#ddd6fe",
        "TEXT": "#1e1b4b", "TEXT_DIM": "#64748b", "TEXT_MID": "#475569",
        "GREEN": "#16a34a", "RED": "#dc2626", "AMBER": "#d97706",
    }
}

# Default theme
BG = THEMES["dark"]["BG"]
BG_DARK = THEMES["dark"]["BG_DARK"]
BG_CARD = THEMES["dark"]["BG_CARD"]
BG_INPUT = THEMES["dark"]["BG_INPUT"]
BORDER = THEMES["dark"]["BORDER"]
ACCENT = THEMES["dark"]["ACCENT"]
ACCENT_LIGHT = THEMES["dark"]["ACCENT_LIGHT"]
ACCENT_HOVER = THEMES["dark"]["ACCENT_HOVER"]
ACCENT_DARK = THEMES["dark"]["ACCENT_DARK"]
TEXT = THEMES["dark"]["TEXT"]
TEXT_DIM = THEMES["dark"]["TEXT_DIM"]
TEXT_MID = THEMES["dark"]["TEXT_MID"]
GREEN = THEMES["dark"]["GREEN"]
RED = THEMES["dark"]["RED"]
AMBER = THEMES["dark"]["AMBER"]
SIDEBAR_W = 170


# ═══════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═══════════════════════════════════════════════════════════

class ProVideoSuite:
    def __init__(self):
        if HAS_CTK:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()

        self.root.title("Pro Video Suite v9")
        self.root.geometry("1100x820")
        self.root.minsize(900, 650)
        self.root.configure(bg=BG)

        # ── Shared state ──
        self.current_page = None
        self.is_building = False

        # Video processor state
        self.main_video = tk.StringVar(value="")
        self.reaction_clips = []
        self.output_path = tk.StringVar(value="")
        self.title_var = tk.StringVar(value="Best Moments")
        self.pitch_var = tk.DoubleVar(value=4.0)

        # Thumbnail state
        self.thumb_video = tk.StringVar(value="")
        self.thumb_title = tk.StringVar(value="")
        self.thumb_emoji = tk.StringVar(value="🔥")
        self.thumb_style = tk.StringVar(value="Bold Impact")
        self.extracted_frames = []
        self.selected_frame = tk.IntVar(value=0)
        self.frame_labels = []

        # SEO state
        self.seo_topic = tk.StringVar(value="")
        self.seo_show = tk.StringVar(value="")
        self.seo_char = tk.StringVar(value="")
        self.seo_last_output = None

        # Queue state
        self.queue_items = []
        self.queue_running = False
        self.queue_paused = False
        self.queue_pitch = tk.DoubleVar(value=4.0)
        self.queue_title = tk.StringVar(value="Best Moments")
        self._load_queue_state()

        # Upload state
        self.upload_file = tk.StringVar(value="")
        self.upload_title = tk.StringVar(value="")
        self.upload_desc = tk.StringVar(value="")
        self.upload_tags = tk.StringVar(value="")
        self.upload_privacy = tk.StringVar(value="unlisted")
        self.upload_category = tk.StringVar(value="Entertainment")
        self.upload_thumb = tk.StringVar(value="")
        self.upload_channel = tk.StringVar(value="Default")

        # Template state
        self._template_choices = get_template_info()  # [(id, name, desc, needs_rxn)]
        self.template_var = tk.StringVar(value=self._template_choices[0][0])  # default: split_screen

        # Settings state
        self._load_settings()

        # Transcript state
        self.last_transcript = ""
        self.last_processed_video = ""

        # Theme state
        self.current_theme = "dark"

        # Audit state
        self.audit_video_path = tk.StringVar(value="")
        self.audit_report = tk.StringVar(value="")
        self.audit_video_data = None
        self.audit_checklist_vars = {}

        self._build_shell()
        self._switch_page("video")
        self.root.mainloop()

    # ═══════════════════════════════════════════════════════════
    #  SHELL: Top Bar + Sidebar + Content + Footer
    # ═══════════════════════════════════════════════════════════

    def _build_shell(self):
        # ── TOP BAR ──
        top = tk.Frame(self.root, bg=ACCENT_DARK, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="  PRO VIDEO SUITE", font=("Segoe UI", 18, "bold"),
                 fg=ACCENT_LIGHT, bg=ACCENT_DARK).pack(side="left", padx=10)
        tk.Label(top, text="v9  |  Algorithmic Warfare Engine",
                 font=("Segoe UI", 11), fg=TEXT_DIM, bg=ACCENT_DARK).pack(side="left", padx=10)

        # Theme toggle button
        self.theme_btn = tk.Button(
            top, text="☀️ Light", font=("Segoe UI", 10),
            fg="white", bg=ACCENT, activebackground=ACCENT_HOVER,
            bd=0, padx=12, pady=4, cursor="hand2",
            command=self._toggle_theme
        )
        self.theme_btn.pack(side="right", padx=15)

        # ── MIDDLE (sidebar + content) ──
        middle = tk.Frame(self.root, bg=BG)
        middle.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(middle, bg=BG_DARK, width=SIDEBAR_W)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Sidebar separator line
        tk.Frame(middle, bg=BORDER, width=1).pack(side="left", fill="y")

        # Content area
        self.content = tk.Frame(middle, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)

        # Build sidebar buttons
        self.sidebar_btns = {}
        nav_items = [
            ("video", "🎬  Video", "Process single video"),
            ("queue", "📋  Queue", "Batch process files"),
            ("thumb", "📸  Thumbnail", "Generate thumbnails"),
            ("seo",   "📝  SEO", "SEO content generator"),
            ("upload","📤  Upload", "YouTube auto-upload"),
            ("proxy", "📡  Proxy", "IP manager & kill switch"),
            ("hacks", "🚀  Hacks", "YouTube growth checklist"),
            ("audit", "🔍  Audit", "Shadow Ledger compliance"),
            ("settings","⚙️  Settings", "Cleanup & storage"),
        ]

        tk.Label(self.sidebar, text="TOOLS", font=("Segoe UI", 9, "bold"),
                 fg=TEXT_DIM, bg=BG_DARK).pack(pady=(15, 8), padx=15, anchor="w")

        for key, label, tip in nav_items:
            btn = tk.Frame(self.sidebar, bg=BG_DARK, cursor="hand2")
            btn.pack(fill="x", padx=8, pady=2)

            lbl = tk.Label(btn, text=label, font=("Segoe UI", 13, "bold"),
                           fg=TEXT_MID, bg=BG_DARK, anchor="w", padx=12, pady=10)
            lbl.pack(fill="x")

            tip_lbl = tk.Label(btn, text=tip, font=("Segoe UI", 9),
                               fg=TEXT_DIM, bg=BG_DARK, anchor="w", padx=14)
            tip_lbl.pack(fill="x", pady=(0, 4))

            # Click handlers
            for w in [btn, lbl, tip_lbl]:
                w.bind("<Button-1>", lambda e, k=key: self._switch_page(k))

            self.sidebar_btns[key] = (btn, lbl, tip_lbl)

        # ── FOOTER ──
        footer = tk.Frame(self.root, bg=ACCENT_DARK, height=32)
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)

        self.footer_status = tk.Label(footer, text="Ready",
                                       font=("Segoe UI", 11), fg=TEXT_DIM, bg=ACCENT_DARK)
        self.footer_status.pack(side="left", padx=15)

        tk.Label(footer, text="Pro Video Suite v9.0",
                 font=("Segoe UI", 9), fg=TEXT_DIM, bg=ACCENT_DARK).pack(side="right", padx=15)

    def _switch_page(self, page_id):
        if page_id is None:
            for w in self.content.winfo_children():
                w.destroy()
            self.current_page = None
            return
        if self.current_page == page_id:
            return

        # Update sidebar highlight
        for key, (btn, lbl, tip) in self.sidebar_btns.items():
            if key == page_id:
                btn.configure(bg=ACCENT_DARK)
                lbl.configure(bg=ACCENT_DARK, fg=TEXT)
                tip.configure(bg=ACCENT_DARK)
            else:
                btn.configure(bg=BG_DARK)
                lbl.configure(bg=BG_DARK, fg=TEXT_MID)
                tip.configure(bg=BG_DARK)

        # Clear content
        for w in self.content.winfo_children():
            w.destroy()

        self.current_page = page_id

        # Build selected page
        if page_id == "video":
            self._build_video_page()
        elif page_id == "queue":
            self._build_queue_page()
        elif page_id == "thumb":
            self._build_thumb_page()
        elif page_id == "seo":
            self._build_seo_page()
        elif page_id == "upload":
            self._build_upload_page()
        elif page_id == "proxy":
            self._build_proxy_page()
        elif page_id == "hacks":
            self._build_hacks_page()
        elif page_id == "audit":
            self._build_audit_page()
        elif page_id == "settings":
            self._build_settings_page()

    def _set_footer(self, msg, color=TEXT_DIM):
        self.footer_status.configure(text=msg, fg=color)

    # ═══════════════════════════════════════════════════════
    #  PAGE 8: YOUTUBE GROWTH HACKS
    # ═══════════════════════════════════════════════════════

    def _build_hacks_page(self):
        c = self.content

        # Load state
        self._hacks_load_state()

        # Title
        self._label(c, "🚀 YouTube Growth Hacks", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 2))
        self._label(c, "Levels 1–10  •  Interactive Checklist  •  Tick items as you implement them",
                    11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # Progress bar row
        prog_f = self._frame(c)
        prog_f.pack(fill="x", padx=20, pady=(10, 4))
        total_items = sum(len(lv["items"]) for lv in HACKS_LEVELS)
        done_items = sum(1 for v in self.hacks_checked.values() if v)
        pct = int(done_items / total_items * 100) if total_items else 0
        self.hacks_prog_label = self._label(prog_f, f"{done_items}/{total_items} completed ({pct}%)", 11, True, ACCENT_LIGHT)
        self.hacks_prog_label.pack(side="left")
        self._button(prog_f, "🔄 Reset All", self._hacks_reset, width=100, color=RED).pack(side="right")

        # Progress bar visual
        bar_f = tk.Frame(c, bg=BG_INPUT, height=6)
        bar_f.pack(fill="x", padx=20, pady=(0, 10))
        bar_f.pack_propagate(False)
        self.hacks_bar_fill = tk.Frame(bar_f, bg=ACCENT, height=6)
        self.hacks_bar_fill.place(relx=0, rely=0, relheight=1, relwidth=pct / 100)

        # Scrollable canvas
        canvas = tk.Canvas(c, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(c, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, padx=(20, 0))

        inner = tk.Frame(canvas, bg=BG)
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.hacks_checkbuttons = {}

        for lv in HACKS_LEVELS:
            # Level header
            hdr = tk.Frame(inner, bg=BG_CARD)
            hdr.pack(fill="x", pady=(12, 4))
            badge_text = f"  {lv['level_emoji']}  LEVEL {lv['level']}  —  {lv['level_name']}  "
            badge = tk.Label(hdr, text=badge_text, font=("Segoe UI", 13, "bold"),
                            fg="white", bg=lv["level_color"], padx=10, pady=6)
            badge.pack(side="left", padx=8, pady=6)
            tk.Label(hdr, text=lv["level_desc"], font=("Segoe UI", 10),
                     fg=TEXT_DIM, bg=BG_CARD).pack(side="left", padx=6)

            # Items
            for item in lv["items"]:
                row = tk.Frame(inner, bg=BG)
                row.pack(fill="x", padx=12, pady=2)

                var = tk.BooleanVar(value=self.hacks_checked.get(item["id"], False))
                cb = tk.Checkbutton(row, variable=var, bg=BG, activebackground=BG,
                                    selectcolor=BG_INPUT, bd=0, highlightthickness=0,
                                    command=lambda iid=item["id"], v=var: self._hacks_toggle(iid, v))
                cb.pack(side="left", padx=(4, 8), pady=4)

                text_f = tk.Frame(row, bg=BG)
                text_f.pack(side="left", fill="x", expand=True)
                tk.Label(text_f, text=item["name"], font=("Segoe UI", 12, "bold"),
                         fg=TEXT, bg=BG, anchor="w").pack(anchor="w")
                tk.Label(text_f, text=item["core_logic"], font=("Segoe UI", 10),
                         fg=TEXT_DIM, bg=BG, anchor="w", wraplength=700,
                         justify="left").pack(anchor="w")

                self.hacks_checkbuttons[item["id"]] = var

    def _hacks_toggle(self, item_id, var):
        self.hacks_checked[item_id] = var.get()
        self._hacks_save_state()
        # Update progress
        total = sum(len(lv["items"]) for lv in HACKS_LEVELS)
        done = sum(1 for v in self.hacks_checked.values() if v)
        pct = int(done / total * 100) if total else 0
        if hasattr(self, 'hacks_prog_label'):
            self.hacks_prog_label.configure(text=f"{done}/{total} completed ({pct}%)")
        if hasattr(self, 'hacks_bar_fill'):
            self.hacks_bar_fill.place(relx=0, rely=0, relheight=1, relwidth=pct / 100)

    def _hacks_load_state(self):
        path = os.path.join(BASE_DIR, "hacks_state.json")
        try:
            if os.path.isfile(path):
                with open(path, "r", encoding="utf-8") as f:
                    self.hacks_checked = json.load(f)
            else:
                self.hacks_checked = {}
        except Exception:
            self.hacks_checked = {}

    def _hacks_save_state(self):
        path = os.path.join(BASE_DIR, "hacks_state.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.hacks_checked, f, indent=2)
        except Exception:
            pass

    def _hacks_reset(self):
        if messagebox.askyesno("Reset", "Clear ALL checkmarks?"):
            self.hacks_checked = {}
            self._hacks_save_state()
            self._switch_page(None)
            self.current_page = None
            self._switch_page("hacks")

    # ═══════════════════════════════════════════════════════
    #  TEMPLATE SELECTOR HELPER
    # ═══════════════════════════════════════════════════════

    def _update_tpl_desc(self, selected_id):
        tpl = next((t for t in self._template_choices if t[0] == selected_id), None)
        if tpl and hasattr(self, 'tpl_desc_label'):
            self.tpl_desc_label.configure(text=tpl[2])
        if tpl and hasattr(self, 'tpl_rxn_label'):
            needs = tpl[3]
            tag = "  ⚠️ Requires reaction clip" if needs else "  ✅ No reaction needed"
            self.tpl_rxn_label.configure(text=tag, fg=AMBER if needs else GREEN)

    # ═══════════════════════════════════════════════════════
    #  PAGE 9: SHADOW LEDGER AUDIT
    # ═══════════════════════════════════════════════════════

    def _build_audit_page(self):
        c = self.content
        pad = {"padx": 20, "pady": 6}

        # Title
        self._label(c, "🔍 Shadow Ledger Audit", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 2))
        self._label(c, "Drag an MP4 or browse to read its Phantom Atom compliance data",
                    11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # File picker
        sec = self._frame(c)
        sec.pack(fill="x", **pad)
        self._label(sec, "Video File", 13, True).pack(anchor="w")
        row = self._frame(sec)
        row.pack(fill="x", pady=3)
        self._entry(row, self.audit_video_path).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row, "Browse", self._audit_browse, width=80).pack(side="right", padx=(0, 6))
        self._button(row, "🔍 Read Atom", self._audit_read, width=120, color=ACCENT).pack(side="right")

        # Compliance report area
        report_f = self._frame(c)
        report_f.pack(fill="both", expand=True, padx=20, pady=(6, 4))
        self._label(report_f, "Compliance Report", 13, True).pack(anchor="w", pady=(0, 4))

        # Scrollable canvas for report
        canvas = tk.Canvas(report_f, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(report_f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.audit_inner = tk.Frame(canvas, bg=BG)
        canvas_win = canvas.create_window((0, 0), window=self.audit_inner, anchor="nw")
        self.audit_inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Show placeholder or last read
        self._label(self.audit_inner, "No video scanned yet. Browse an MP4 and click 'Read Atom'.",
                    11, color=TEXT_DIM).pack(anchor="w", pady=20, padx=10)

        # Recent videos from Shadow Ledger DB
        hist_f = self._frame(c)
        hist_f.pack(fill="x", padx=20, pady=(4, 10))
        self._label(hist_f, "Recent Renders (Shadow Ledger DB)", 12, True, ACCENT_LIGHT).pack(anchor="w")
        try:
            videos = get_all_videos()[:5]  # Last 5
            if videos:
                for v in videos:
                    vrow = self._frame(hist_f)
                    vrow.pack(fill="x", pady=2)
                    uuid_short = v["uuid"][:8]
                    created = v.get("created_at", "")[:19]
                    tpl = v.get("template_id", "?")
                    title = v.get("title", "")
                    size = v.get("file_size_mb")
                    size_str = f"{size:.1f}MB" if size else "?"
                    text = f"  {uuid_short}...  │  {created}  │  {tpl}  │  {title}  │  {size_str}"
                    self._label(vrow, text, 10, color=TEXT_MID).pack(side="left")
            else:
                self._label(hist_f, "  No renders yet.", 10, color=TEXT_DIM).pack(anchor="w")
        except Exception:
            self._label(hist_f, "  DB not available.", 10, color=TEXT_DIM).pack(anchor="w")

    def _audit_browse(self):
        path = filedialog.askopenfilename(
            title="Select MP4 to Audit",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if path:
            self.audit_video_path.set(path)

    def _audit_read(self):
        path = self.audit_video_path.get()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid MP4 file.")
            return

        # Clear previous report
        for w in self.audit_inner.winfo_children():
            w.destroy()

        # Read Phantom Atom
        data = audit_video(path)
        if not data:
            self._label(self.audit_inner,
                "❌ No Phantom Atom found in this file.\n\n"
                "This video was either not processed by our engine,\n"
                "or the Phantom Atom was stripped.",
                12, color=RED).pack(anchor="w", pady=20, padx=10)
            return

        # Header info
        hdr = self._frame(self.audit_inner)
        hdr.pack(fill="x", pady=(8, 4), padx=6)
        self._label(hdr, f"✅ Phantom Atom Found — v{data.get('shadow_ledger_version', '?')}",
                    14, True, GREEN).pack(anchor="w")

        info_lines = [
            f"UUID:     {data.get('video_uuid', 'N/A')}",
            f"Template: {data.get('template_id', 'N/A')}",
            f"Title:    {data.get('title', 'N/A')}",
            f"Created:  {data.get('created_at', 'N/A')[:19]}",
            f"Source:   {data.get('source_file', 'N/A')}",
        ]
        for line in info_lines:
            self._label(hdr, f"  {line}", 11, color=TEXT_MID).pack(anchor="w")

        # Score
        score = data.get("score", "?")
        score_f = self._frame(self.audit_inner)
        score_f.pack(fill="x", pady=(8, 4), padx=6)
        self._label(score_f, f"COMPLIANCE SCORE:  {score}", 16, True, ACCENT_LIGHT).pack(anchor="w")

        # Checklist items
        compliance = data.get("compliance", {})
        if compliance:
            for hack_id, info in sorted(compliance.items()):
                row = self._frame(self.audit_inner)
                row.pack(fill="x", padx=10, pady=1)
                checked = info.get("checked", False)
                icon = "✅" if checked else "❌"
                color = GREEN if checked else RED
                name = info.get("name", hack_id)
                self._label(row, f"  {icon}  {hack_id}  —  {name}", 11, color=color).pack(anchor="w")

    # ═══════════════════════════════════════════════════════
    #  THEME TOGGLE
    # ═══════════════════════════════════════════════════════

    def _toggle_theme(self):
        global BG, BG_DARK, BG_CARD, BG_INPUT, BORDER
        global ACCENT, ACCENT_LIGHT, ACCENT_HOVER, ACCENT_DARK
        global TEXT, TEXT_DIM, TEXT_MID, GREEN, RED, AMBER

        # Switch theme
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        t = THEMES[self.current_theme]

        # Update all global color variables
        BG = t["BG"]; BG_DARK = t["BG_DARK"]; BG_CARD = t["BG_CARD"]
        BG_INPUT = t["BG_INPUT"]; BORDER = t["BORDER"]
        ACCENT = t["ACCENT"]; ACCENT_LIGHT = t["ACCENT_LIGHT"]
        ACCENT_HOVER = t["ACCENT_HOVER"]; ACCENT_DARK = t["ACCENT_DARK"]
        TEXT = t["TEXT"]; TEXT_DIM = t["TEXT_DIM"]; TEXT_MID = t["TEXT_MID"]
        GREEN = t["GREEN"]; RED = t["RED"]; AMBER = t["AMBER"]

        # Rebuild the entire UI with new theme
        for w in self.root.winfo_children():
            w.destroy()

        # Update toggle button text for next toggle
        self._build_shell()
        if self.current_theme == "light":
            self.theme_btn.configure(text="🌙 Dark")
        else:
            self.theme_btn.configure(text="☀️ Light")

        # Re-navigate to the page we were on
        page = self.current_page or "video"
        self.current_page = None
        self._switch_page(page)

    # ═══════════════════════════════════════════════════════
    #  UI HELPERS
    # ═══════════════════════════════════════════════════════

    def _frame(self, parent, bg_color=BG):
        return tk.Frame(parent, bg=bg_color)

    def _label(self, parent, text, size=12, bold=False, color=TEXT, bg_color=BG):
        weight = "bold" if bold else "normal"
        return tk.Label(parent, text=text, font=("Segoe UI", size, weight),
                        fg=color, bg=bg_color)

    def _entry(self, parent, var, width=None):
        e = tk.Entry(parent, textvariable=var, bg=BG_INPUT, fg="white",
                     font=("Consolas", 12), relief="flat", bd=4,
                     insertbackground="white")
        if width:
            e.configure(width=width // 7)
        return e

    def _button(self, parent, text, command, width=120, height=36, color=BORDER):
        btn = tk.Button(parent, text=text, command=command,
                        bg=color, fg="white", font=("Segoe UI", 12, "bold"),
                        relief="flat", bd=0, padx=12, pady=6,
                        activebackground=ACCENT_HOVER, activeforeground="white",
                        cursor="hand2")
        return btn

    def _textbox(self, parent, height=8):
        t = tk.Text(parent, height=height, bg=BG_DARK, fg="#c8c8e0",
                    font=("Consolas", 11), relief="flat", bd=0,
                    insertbackground="white")
        return t

    def _log_to(self, textbox, msg):
        textbox.insert("end", msg + "\n")
        textbox.see("end")

    # ═══════════════════════════════════════════════════════
    #  PAGE 1: VIDEO PROCESSOR
    # ═══════════════════════════════════════════════════════

    def _build_video_page(self):
        c = self.content
        pad = {"padx": 20, "pady": 6}

        # Title
        self._label(c, "🎬 Video Processor", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Process a single video with 5 evasion techniques", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # Main video
        sec = self._frame(c)
        sec.pack(fill="x", **pad)
        self._label(sec, "Main Video", 13, True).pack(anchor="w")
        row = self._frame(sec)
        row.pack(fill="x", pady=3)
        self._entry(row, self.main_video).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row, "Browse", self._browse_main, width=80).pack(side="right")

        # Reactions
        sec2 = self._frame(c)
        sec2.pack(fill="x", **pad)
        r2h = self._frame(sec2)
        r2h.pack(fill="x")
        self._label(r2h, "Reaction Clips", 13, True).pack(side="left")
        self._label(r2h, " (Optional)", 11, color=ACCENT).pack(side="left")
        row2 = self._frame(sec2)
        row2.pack(fill="x", pady=3)
        self.rxn_label = self._label(row2, "No reactions selected", 11, color=TEXT_MID)
        self.rxn_label.pack(side="left", fill="x", expand=True)
        self._button(row2, "Clear", self._clear_reactions, width=55).pack(side="right", padx=(0, 6))
        self._button(row2, "Browse", self._browse_reactions, width=80).pack(side="right")

        # Settings
        sec3 = self._frame(c)
        sec3.pack(fill="x", **pad)
        self._label(sec3, "Settings", 13, True).pack(anchor="w")
        row3 = self._frame(sec3)
        row3.pack(fill="x", pady=3)
        self._label(row3, "Episode Title:", 11).pack(side="left")
        self._entry(row3, self.title_var, width=250).pack(side="left", padx=(6, 20))
        self._label(row3, "Pitch:", 11).pack(side="left")
        sc = tk.Scale(row3, from_=1, to=6, resolution=0.5, orient="horizontal",
                      variable=self.pitch_var, bg=BG, fg="white", troughcolor=BG_INPUT,
                      highlightthickness=0, length=120, font=("Segoe UI", 9))
        sc.pack(side="left", padx=5)

        # Template selector
        sec_tpl = self._frame(c)
        sec_tpl.pack(fill="x", **pad)
        self._label(sec_tpl, "Layout Template", 13, True).pack(anchor="w")
        row_tpl = self._frame(sec_tpl)
        row_tpl.pack(fill="x", pady=3)
        tpl_names = {t[0]: t[1] for t in self._template_choices}
        tpl_menu = tk.OptionMenu(row_tpl, self.template_var,
                                 *[t[0] for t in self._template_choices],
                                 command=lambda v: self._update_tpl_desc(v))
        tpl_menu.configure(bg=BG_INPUT, fg="white", font=("Segoe UI", 11),
                           activebackground=ACCENT, highlightthickness=0, bd=0)
        tpl_menu["menu"].configure(bg=BG_CARD, fg="white", font=("Segoe UI", 10),
                                   activebackground=ACCENT)
        tpl_menu.pack(side="left", padx=(0, 12))
        cur_tpl = next((t for t in self._template_choices if t[0] == self.template_var.get()), None)
        self.tpl_desc_label = self._label(row_tpl, cur_tpl[2] if cur_tpl else "", 10, color=TEXT_DIM)
        self.tpl_desc_label.pack(side="left")
        needs_rxn = cur_tpl[3] if cur_tpl else False
        rxn_tag = "  ⚠️ Requires reaction clip" if needs_rxn else "  ✅ No reaction needed"
        self.tpl_rxn_label = self._label(row_tpl, rxn_tag, 10, color=AMBER if needs_rxn else GREEN)
        self.tpl_rxn_label.pack(side="left", padx=12)

        # Output
        sec4 = self._frame(c)
        sec4.pack(fill="x", **pad)
        self._label(sec4, "Save To", 13, True).pack(anchor="w")
        row4 = self._frame(sec4)
        row4.pack(fill="x", pady=3)
        self._entry(row4, self.output_path).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row4, "Browse", self._browse_output, width=80).pack(side="right")

        # Build button
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=12)
        self.build_btn = self._button(btn_f, "🚀  BUILD VIDEO", self._start_build,
                                      width=200, height=45, color=ACCENT)
        self.build_btn.pack(side="left")
        self._button(btn_f, "📜 Transcript", self._generate_transcript,
                     width=130, height=45, color=ACCENT_DARK).pack(side="left", padx=8)
        self.video_status = self._label(btn_f, "", 11, color=TEXT_DIM)
        self.video_status.pack(side="left", padx=15)

        # Preview
        prev_f = self._frame(c)
        prev_f.pack(fill="x", padx=20, pady=3)
        self._label(prev_f, "🎬 Video Preview", 11, True, ACCENT_LIGHT).pack(anchor="w")
        self.preview_label = self._label(prev_f, "Select a video to see info", 11, color=TEXT_DIM)
        self.preview_label.pack(anchor="w", pady=3)

        # Log
        log_f = self._frame(c)
        log_f.pack(fill="both", expand=True, padx=20, pady=(3, 10))
        self._label(log_f, "Build Log", 11, True).pack(anchor="w", pady=(0, 3))
        self.build_log = self._textbox(log_f, height=8)
        self.build_log.pack(fill="both", expand=True)

    # Video page actions
    def _browse_main(self):
        f = filedialog.askopenfilename(
            title="Select Main Video",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if f:
            self.main_video.set(f)
            self.output_path.set(os.path.splitext(f)[0] + "_PRO.mp4")
            self._load_preview(f)

    def _browse_reactions(self):
        files = filedialog.askopenfilenames(
            title="Select Reaction Clips",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if files:
            self.reaction_clips = list(files)
            names = [os.path.basename(f) for f in files]
            self.rxn_label.configure(text=f"{len(files)} clip(s): {', '.join(names[:3])}{'...' if len(names) > 3 else ''}")

    def _browse_output(self):
        f = filedialog.asksaveasfilename(title="Save Output As", defaultextension=".mp4",
                                          filetypes=[("MP4", "*.mp4")])
        if f:
            self.output_path.set(f)

    def _clear_reactions(self):
        self.reaction_clips = []
        self.rxn_label.configure(text="No reactions selected")

    def _load_preview(self, filepath):
        try:
            import json as _json
            import subprocess
            name = os.path.basename(filepath)
            size = os.path.getsize(filepath) / (1024 * 1024)
            ffp = os.path.join(BASE_DIR, "ffmpeg_bin", "ffprobe.exe")
            if not os.path.isfile(ffp):
                import shutil
                ffp = shutil.which("ffprobe") or "ffprobe"
            r = subprocess.run([ffp, "-v", "quiet", "-print_format", "json",
                                "-show_streams", "-show_format", filepath],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            data = _json.loads(r.stdout)
            dur = float(data.get("format", {}).get("duration", 0))
            mins, secs = int(dur // 60), int(dur % 60)
            res = ""
            for s in data.get("streams", []):
                if s.get("codec_type") == "video":
                    res = f" | {s.get('width', '?')}x{s.get('height', '?')}"
                    break
            self.preview_label.configure(text=f"🎬 {name}  |  {size:.1f} MB  |  {mins}m {secs}s{res}")
        except:
            self.preview_label.configure(text=f"🎬 {os.path.basename(filepath)}")

    def _start_build(self):
        if self.is_building:
            return
        main = self.main_video.get()
        if not main or not os.path.isfile(main):
            messagebox.showerror("Error", "Please select a valid main video file.")
            return
        out = self.output_path.get()
        if not out:
            messagebox.showerror("Error", "Please set an output path.")
            return

        self.is_building = True
        self.build_btn.configure(state="disabled", text="BUILDING...")
        self.build_log.delete("1.0", "end")
        self._set_footer("Building video...", AMBER)

        def run():
            # Load current hacks checklist for Shadow Ledger compliance
            _checklist = {}
            try:
                _hp = os.path.join(BASE_DIR, "hacks_state.json")
                if os.path.isfile(_hp):
                    with open(_hp, "r", encoding="utf-8") as _hf:
                        _checklist = json.load(_hf)
            except Exception:
                pass

            try:
                ok = build_video(
                    main_video=main,
                    reaction_clips=self.reaction_clips,
                    output_path=out,
                    title=self.title_var.get(),
                    pitch_semitones=self.pitch_var.get(),
                    template_id=self.template_var.get(),
                    checklist=_checklist,
                    progress_callback=lambda m: self.root.after(0, lambda: self._log_to(self.build_log, m))
                )
                if ok:
                    self._set_footer("✅ BUILD SUCCESS!", GREEN)
                    self.last_processed_video = out
                else:
                    self._set_footer("❌ Build failed", RED)
            except Exception as e:
                self._set_footer(f"Error: {e}", RED)
            finally:
                self.is_building = False
                self.root.after(0, lambda: self.build_btn.configure(state="normal", text="🚀  BUILD VIDEO"))

        threading.Thread(target=run, daemon=True).start()

    def _generate_transcript(self):
        """Generate transcript from last processed video."""
        video = self.last_processed_video or self.main_video.get()
        if not video or not os.path.isfile(video):
            messagebox.showerror("Error", "No video file available for transcription.")
            return

        self._set_footer("Generating transcript...", AMBER)
        self.build_log.insert("end", "\n📜 Starting transcript generation...\n")
        self.build_log.see("end")

        def run():
            key = self.settings.get("groq_api_key", "")
            transcript = transcribe_video(
                video, api_key=key,
                log=lambda m: self.root.after(0, lambda: (
                    self._log_to(self.build_log, m),
                    self.build_log.see("end")
                ))
            )
            if transcript:
                self.last_transcript = transcript
                self.root.after(0, lambda: self._set_footer(
                    f"✅ Transcript ready! {len(transcript.split())} words", GREEN))
                self.root.after(0, lambda: self._log_to(
                    self.build_log, f"\n📜 Transcript ({len(transcript.split())} words):\n{transcript[:300]}..."))
            else:
                self.root.after(0, lambda: self._set_footer("❌ Transcript failed", RED))

        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════════════════
    #  PAGE 2: BATCH QUEUE
    # ═══════════════════════════════════════════════════════

    def _build_queue_page(self):
        c = self.content
        pad = {"padx": 20, "pady": 6}

        # Title
        self._label(c, "📋 Batch Queue", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Add 10-20 videos — processes one-by-one automatically", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # Settings row
        set_f = self._frame(c)
        set_f.pack(fill="x", **pad)
        self._label(set_f, "Episode Title:", 11).pack(side="left")
        self._entry(set_f, self.queue_title, width=200).pack(side="left", padx=(6, 15))
        self._label(set_f, "Pitch:", 11).pack(side="left")
        sc = tk.Scale(set_f, from_=1, to=6, resolution=0.5, orient="horizontal",
                      variable=self.queue_pitch, bg=BG, fg="white", troughcolor=BG_INPUT,
                      highlightthickness=0, length=100, font=("Segoe UI", 9))
        sc.pack(side="left", padx=5)

        # Reaction clips for queue
        rxn_f = self._frame(c)
        rxn_f.pack(fill="x", **pad)
        self._label(rxn_f, "Reaction Clips (shared):", 11).pack(side="left")
        self.queue_rxn_label = self._label(rxn_f, "None", 11, color=TEXT_MID)
        self.queue_rxn_label.pack(side="left", padx=8)
        self._button(rxn_f, "Browse", self._queue_browse_reactions, width=70).pack(side="left")
        self.queue_reactions = []

        # Buttons
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=8)
        self._button(btn_f, "➕ Add Videos", self._queue_add, width=130, color=ACCENT_DARK).pack(side="left")
        self._button(btn_f, "🗑️ Clear All", self._queue_clear, width=100, color=ACCENT_DARK).pack(side="left", padx=8)
        self.queue_start_btn = self._button(btn_f, "▶️  START QUEUE", self._queue_start,
                                             width=160, color=ACCENT)
        self.queue_start_btn.pack(side="left", padx=8)
        self.queue_stop_btn = self._button(btn_f, "⏹️ STOP", self._queue_stop, width=80, color=RED)
        self.queue_stop_btn.pack(side="left")
        self.queue_pause_btn = self._button(btn_f, "⏸️ PAUSE", self._queue_pause_toggle, width=90, color=AMBER)
        self.queue_pause_btn.pack(side="left", padx=8)

        # Progress label
        self.queue_progress = self._label(c, "", 12, True, color=ACCENT_LIGHT)
        self.queue_progress.pack(anchor="w", padx=20, pady=4)

        # Queue list (scrollable)
        list_f = self._frame(c)
        list_f.pack(fill="both", expand=True, padx=20, pady=(4, 10))

        # Header row
        hdr = self._frame(list_f, bg_color=BG_CARD)
        hdr.pack(fill="x")
        self._label(hdr, "#", 10, True, TEXT_DIM, BG_CARD).pack(side="left", padx=(10, 0))
        self._label(hdr, "Filename", 10, True, TEXT_DIM, BG_CARD).pack(side="left", padx=20)
        self._label(hdr, "Time", 10, True, TEXT_DIM, BG_CARD).pack(side="right", padx=15)
        self._label(hdr, "Status", 10, True, TEXT_DIM, BG_CARD).pack(side="right", padx=15)

        # Scrollable list
        canvas = tk.Canvas(list_f, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(list_f, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.queue_list_frame = tk.Frame(canvas, bg=BG)
        self._queue_canvas_window = canvas.create_window((0, 0), window=self.queue_list_frame, anchor="nw")
        self.queue_list_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._queue_canvas_window, width=e.width))
        canvas.bind_all("<MouseWheel>",
            lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self.queue_canvas = canvas
        self._queue_refresh_list()

    def _queue_browse_reactions(self):
        files = filedialog.askopenfilenames(
            title="Select Reaction Clips for Queue",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if files:
            self.queue_reactions = list(files)
            self.queue_rxn_label.configure(text=f"{len(files)} clip(s)")

    def _queue_add(self):
        files = filedialog.askopenfilenames(
            title="Add Videos to Queue",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        for f in files:
            self.queue_items.append({
                "path": f,
                "name": os.path.basename(f),
                "status": "⏳ Waiting",
                "elapsed": "",
                "output": os.path.splitext(f)[0] + "_PRO.mp4"
            })
        self._queue_refresh_list()
        self._save_queue_state()
        self._set_footer(f"{len(self.queue_items)} videos in queue", TEXT_DIM)

    def _queue_clear(self):
        if self.queue_running:
            messagebox.showwarning("Warning", "Stop the queue first.")
            return
        self.queue_items = []
        self._queue_refresh_list()
        self._save_queue_state()
        self._set_footer("Queue cleared", TEXT_DIM)

    def _queue_refresh_list(self):
        for w in self.queue_list_frame.winfo_children():
            w.destroy()

        if not self.queue_items:
            self._label(self.queue_list_frame, "No videos in queue. Click '➕ Add Videos' to start.",
                        12, color=TEXT_DIM).pack(pady=20)
            return

        for i, item in enumerate(self.queue_items):
            row = self._frame(self.queue_list_frame, bg_color=BG_CARD if i % 2 == 0 else BG)
            row.pack(fill="x", pady=1)

            bg = BG_CARD if i % 2 == 0 else BG
            self._label(row, f"{i + 1:02d}", 11, color=TEXT_DIM, bg_color=bg).pack(side="left", padx=(10, 0))
            self._label(row, item["name"], 11, color=TEXT, bg_color=bg).pack(side="left", padx=15)
            self._label(row, item["elapsed"] or "—", 11, color=TEXT_DIM, bg_color=bg).pack(side="right", padx=15)

            # Color-coded status
            status_color = TEXT_DIM
            if "✅" in item["status"]:
                status_color = GREEN
            elif "🔄" in item["status"]:
                status_color = AMBER
            elif "❌" in item["status"]:
                status_color = RED

            self._label(row, item["status"], 11, color=status_color, bg_color=bg).pack(side="right", padx=15)

            # Remove button (only if not running)
            if not self.queue_running:
                rm_btn = tk.Label(row, text="✕", font=("Segoe UI", 11, "bold"),
                                 fg=RED, bg=bg, cursor="hand2")
                rm_btn.pack(side="right", padx=5)
                rm_btn.bind("<Button-1>", lambda e, idx=i: self._queue_remove_item(idx))

    def _queue_start(self):
        if self.queue_running:
            return
        if not self.queue_items:
            messagebox.showinfo("Info", "Add videos to the queue first.")
            return

        self.queue_running = True
        self.queue_start_btn.configure(state="disabled")
        self._set_footer("Queue running...", AMBER)

        def process_queue():
            total = len(self.queue_items)
            done = 0
            for i, item in enumerate(self.queue_items):
                if not self.queue_running:
                    break
                if "✅" in item["status"]:
                    done += 1
                    continue

                # Pause check
                while self.queue_paused and self.queue_running:
                    time.sleep(0.5)

                item["status"] = "🔄 Processing"
                self.root.after(0, self._queue_refresh_list)
                self.root.after(0, lambda d=done, t=total:
                    self.queue_progress.configure(text=f"Processing {d + 1}/{t}..."))

                start_time = time.time()
                try:
                    ok = build_video(
                        main_video=item["path"],
                        reaction_clips=self.queue_reactions,
                        output_path=item["output"],
                        title=self.queue_title.get(),
                        pitch_semitones=self.queue_pitch.get(),
                        progress_callback=lambda m: None  # silent
                    )
                    elapsed = time.time() - start_time
                    mins = int(elapsed // 60)
                    secs = int(elapsed % 60)
                    item["elapsed"] = f"{mins}m {secs}s"

                    if ok:
                        item["status"] = "✅ Done"
                        done += 1
                    else:
                        item["status"] = "❌ Failed"
                except Exception as e:
                    item["status"] = f"❌ Error"
                    elapsed = time.time() - start_time
                    item["elapsed"] = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

                self.root.after(0, self._queue_refresh_list)

            self.queue_running = False
            self.root.after(0, lambda: self.queue_start_btn.configure(state="normal"))
            self.root.after(0, lambda: self.queue_progress.configure(text=f"Done! {done}/{total} completed"))
            self.root.after(0, lambda: self._set_footer(f"Queue finished: {done}/{total} done", GREEN))

        threading.Thread(target=process_queue, daemon=True).start()

    def _queue_stop(self):
        self.queue_running = False
        self.queue_paused = False
        self._set_footer("Queue stopped", AMBER)

    def _queue_pause_toggle(self):
        if not self.queue_running:
            return
        self.queue_paused = not self.queue_paused
        if self.queue_paused:
            self.queue_pause_btn.configure(text="▶️ RESUME")
            self._set_footer("Queue paused", AMBER)
        else:
            self.queue_pause_btn.configure(text="⏸️ PAUSE")
            self._set_footer("Queue resumed", GREEN)

    def _queue_remove_item(self, idx):
        if 0 <= idx < len(self.queue_items):
            self.queue_items.pop(idx)
            self._queue_refresh_list()
            self._save_queue_state()
            self._set_footer(f"{len(self.queue_items)} videos in queue", TEXT_DIM)

    # ═══════════════════════════════════════════════════════
    #  PAGE 3: THUMBNAIL GENERATOR
    # ═══════════════════════════════════════════════════════

    def _build_thumb_page(self):
        c = self.content
        pad = {"padx": 20, "pady": 6}

        # Title
        self._label(c, "📸 Thumbnail Generator", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Extract frames from any video → create YouTube-ready thumbnail", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # Video input
        sec1 = self._frame(c)
        sec1.pack(fill="x", **pad)
        self._label(sec1, "Video File", 13, True).pack(anchor="w")
        row1 = self._frame(sec1)
        row1.pack(fill="x", pady=3)
        self._entry(row1, self.thumb_video).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row1, "Browse", self._thumb_browse, width=80).pack(side="right", padx=(0, 6))
        self._button(row1, "📸 Extract", self._thumb_extract, width=100, color=ACCENT).pack(side="right")

        # Title + Emoji
        sec2 = self._frame(c)
        sec2.pack(fill="x", **pad)
        self._label(sec2, "Thumbnail Title Text", 13, True).pack(anchor="w")
        row2 = self._frame(sec2)
        row2.pack(fill="x", pady=3)
        self._entry(row2, self.thumb_title).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._label(row2, "Emoji:", 11).pack(side="left", padx=(8, 4))
        self._entry(row2, self.thumb_emoji, width=60).pack(side="left")

        # Style
        sec3 = self._frame(c)
        sec3.pack(fill="x", **pad)
        self._label(sec3, "Thumbnail Style", 13, True).pack(anchor="w")
        style_row = self._frame(sec3)
        style_row.pack(fill="x", pady=3)
        for sname in THUMBNAIL_STYLES:
            tk.Radiobutton(style_row, text=sname, variable=self.thumb_style,
                           value=sname, bg=BG, fg="white", selectcolor=ACCENT,
                           font=("Segoe UI", 10), activebackground=BG,
                           activeforeground="white").pack(side="left", padx=5)

        # Frame selection (scrollable)
        sec4 = self._frame(c)
        sec4.pack(fill="both", expand=True, **pad)
        self._label(sec4, "Select Best Frame (click to select)", 13, True).pack(anchor="w")

        canvas = tk.Canvas(sec4, bg=BG, highlightthickness=0, height=240)
        sb = tk.Scrollbar(sec4, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True, pady=3)

        self.thumb_frame_container = tk.Frame(canvas, bg=BG)
        self._thumb_canvas_win = canvas.create_window((0, 0), window=self.thumb_frame_container, anchor="nw")
        self.thumb_frame_container.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
            lambda e: canvas.itemconfig(self._thumb_canvas_win, width=e.width))
        self.thumb_canvas = canvas

        self.thumb_placeholder = self._label(self.thumb_frame_container,
            "Extract frames from a video to see previews here", 12, color=TEXT_DIM)
        self.thumb_placeholder.pack(pady=15)

        # Bottom buttons (always visible)
        bot = self._frame(c)
        bot.pack(fill="x", padx=20, pady=(4, 10), side="bottom")
        self.thumb_status = self._label(bot, "Ready — Select a video to start", 11, color=TEXT_DIM)
        self.thumb_status.pack(anchor="w", pady=(0, 5))
        btn_row = self._frame(bot)
        btn_row.pack(fill="x")
        self._button(btn_row, "🎨 GENERATE THUMBNAIL", self._thumb_generate,
                     width=220, height=40, color=ACCENT).pack(side="left")
        self._button(btn_row, "🎲 Random", lambda: self._thumb_select_random(),
                     width=90, height=40, color=ACCENT_HOVER).pack(side="left", padx=8)

        # Re-display frames if already extracted
        if self.extracted_frames:
            self._thumb_display_frames(self.extracted_frames)

    def _thumb_browse(self):
        f = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if f:
            self.thumb_video.set(f)
            self.thumb_status.configure(text=f"Video: {os.path.basename(f)}", fg=GREEN)

    def _thumb_extract(self):
        video = self.thumb_video.get()
        if not video or not os.path.isfile(video):
            messagebox.showerror("Error", "Select a valid video file first.")
            return

        self.thumb_status.configure(text="Extracting frames... please wait", fg=AMBER)
        self._set_footer("Extracting frames...", AMBER)

        def run():
            ffmpeg, ffprobe = find_ffmpeg()
            temp_dir = os.path.join(BASE_DIR, "_thumb_frames")
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            frames = extract_frames(ffmpeg, ffprobe, video, temp_dir, count=8)
            self.extracted_frames = frames
            self.root.after(0, lambda: self._thumb_display_frames(frames))
            if frames:
                msg = f"✓ Extracted {len(frames)} frames — click one to select"
                self.root.after(0, lambda: self.thumb_status.configure(text=msg, fg=GREEN))
                self.root.after(0, lambda: self._set_footer(msg, GREEN))
            else:
                self.root.after(0, lambda: self.thumb_status.configure(text="✗ Failed to extract", fg=RED))

        threading.Thread(target=run, daemon=True).start()

    def _thumb_display_frames(self, frames):
        for w in self.thumb_frame_container.winfo_children():
            w.destroy()
        self.frame_labels = []

        if not frames:
            self._label(self.thumb_frame_container, "No frames extracted", 12, color=RED).pack()
            return
        if not HAS_PIL:
            self._label(self.thumb_frame_container, "Install Pillow: pip install Pillow",
                        12, color=AMBER).pack()
            return

        row_frame = None
        for i, fp in enumerate(frames):
            if i % 4 == 0:
                row_frame = self._frame(self.thumb_frame_container)
                row_frame.pack(fill="x", pady=2)
            try:
                pil_img = Image.open(fp).resize((200, 112), Image.LANCZOS)
                tk_img = ImageTk.PhotoImage(pil_img)

                fc = self._frame(row_frame)
                fc.pack(side="left", padx=4, pady=2)

                lbl = tk.Label(fc, image=tk_img, bg=BG_INPUT, bd=2, relief="solid")
                lbl.image = tk_img
                lbl.pack()
                lbl.bind("<Button-1>", lambda e, idx=i: self._thumb_select(idx))

                self._label(fc, f"Frame {i + 1}", 9, color=TEXT_MID).pack()
                self.frame_labels.append((lbl, fc))
            except Exception as e:
                print(f"Frame display error: {e}")

    def _thumb_select(self, idx):
        self.selected_frame.set(idx)
        for i, (lbl, _) in enumerate(self.frame_labels):
            lbl.configure(bg=ACCENT if i == idx else BG_INPUT, bd=3 if i == idx else 2)
        self.thumb_status.configure(text=f"Selected Frame {idx + 1}", fg=ACCENT_LIGHT)

    def _thumb_select_random(self):
        if self.extracted_frames:
            self._thumb_select(random.randint(0, len(self.extracted_frames) - 1))

    def _thumb_generate(self):
        if not self.extracted_frames:
            messagebox.showerror("Error", "Extract frames first.")
            return
        if not HAS_PIL:
            messagebox.showerror("Error", "Pillow required: pip install Pillow")
            return

        idx = self.selected_frame.get()
        if idx >= len(self.extracted_frames):
            idx = 0

        save_path = filedialog.asksaveasfilename(
            title="Save Thumbnail", defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")], initialfile="thumbnail.jpg"
        )
        if not save_path:
            return

        self.thumb_status.configure(text="Generating thumbnail...", fg=AMBER)

        def run():
            try:
                result = create_thumbnail(
                    self.extracted_frames[idx], self.thumb_title.get(),
                    self.thumb_style.get(), save_path, self.thumb_emoji.get()
                )
                if result:
                    self.root.after(0, lambda: self.thumb_status.configure(
                        text=f"✅ Saved: {os.path.basename(result)}", fg=GREEN))
                    os.startfile(result)
                else:
                    self.root.after(0, lambda: self.thumb_status.configure(text="✗ Failed", fg=RED))
            except Exception as e:
                self.root.after(0, lambda: self.thumb_status.configure(text=f"Error: {e}", fg=RED))

        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════════════════
    #  PAGE 4: SEO GENERATOR
    # ═══════════════════════════════════════════════════════

    def _build_seo_page(self):
        c = self.content
        pad = {"padx": 20, "pady": 6}

        # Title
        self._label(c, "📝 SEO Content Generator", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Generate keywords, titles, descriptions, tags, hooks, and CTAs", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # Topic
        sec1 = self._frame(c)
        sec1.pack(fill="x", **pad)
        self._label(sec1, "Video Topic / Content Title", 13, True).pack(anchor="w")
        self._entry(sec1, self.seo_topic).pack(fill="x", pady=3)
        self._label(sec1, 'Example: "Family Guy highlights" or "React to Marvel trailer"',
                    10, color=TEXT_DIM).pack(anchor="w")

        # Show + Character
        sec2 = self._frame(c)
        sec2.pack(fill="x", **pad)
        row2 = self._frame(sec2)
        row2.pack(fill="x")
        col1 = self._frame(row2)
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._label(col1, "Show / Brand Name", 12, True).pack(anchor="w")
        self._entry(col1, self.seo_show).pack(fill="x", pady=3)

        col2 = self._frame(row2)
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._label(col2, "Main Character / Subject", 12, True).pack(anchor="w")
        self._entry(col2, self.seo_char).pack(fill="x", pady=3)

        # Key Moments
        sec3 = self._frame(c)
        sec3.pack(fill="x", **pad)
        self._label(sec3, "Key Moments (one per line, optional)", 12, True).pack(anchor="w")
        self.seo_moments_box = self._textbox(sec3, height=4)
        self.seo_moments_box.configure(bg=BG_INPUT)
        self.seo_moments_box.pack(fill="x", pady=3)

        # Buttons
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=10)
        self._button(btn_f, "⚡ GENERATE SEO ASSETS", self._seo_generate,
                     width=240, height=42, color=ACCENT).pack(side="left")
        self._button(btn_f, "📜 Load Transcript", self._seo_load_transcript,
                     width=160, height=42, color=ACCENT_DARK).pack(side="left", padx=8)
        self._button(btn_f, "📂 Open Last", self._seo_open_last,
                     width=120, height=42).pack(side="left", padx=10)

        # Status
        self.seo_status = self._label(c, "Ready — Enter a topic and generate", 11, color=TEXT_DIM)
        self.seo_status.pack(anchor="w", padx=20, pady=3)

        # Preview log
        log_f = self._frame(c)
        log_f.pack(fill="both", expand=True, padx=20, pady=(3, 10))
        self._label(log_f, "Preview", 11, True, ACCENT_LIGHT).pack(anchor="w", pady=(0, 3))
        self.seo_log = self._textbox(log_f, height=8)
        self.seo_log.pack(fill="both", expand=True)

    def _seo_generate(self):
        topic = self.seo_topic.get().strip()
        if not topic:
            messagebox.showerror("Error", "Enter a video topic.")
            return

        show = self.seo_show.get().strip()
        char = self.seo_char.get().strip()
        moments = self.seo_moments_box.get("1.0", "end").strip()

        self.seo_log.delete("1.0", "end")
        self.seo_status.configure(text="Generating SEO assets...", fg=AMBER)

        self._log_to(self.seo_log, f"📝 Topic: {topic}")
        self._log_to(self.seo_log, f"🎬 Show: {show or '(auto)'}")
        self._log_to(self.seo_log, f"👤 Character: {char or '(auto)'}")
        self._log_to(self.seo_log, "")

        assets = generate_seo_assets(topic, show, char, moments)

        self._log_to(self.seo_log, "═" * 45)
        self._log_to(self.seo_log, "  GENERATED SEO ASSETS")
        self._log_to(self.seo_log, "═" * 45)

        self._log_to(self.seo_log, f"\n🔑 Keywords ({len(assets['keywords'])})")
        for k in assets["keywords"][:5]:
            self._log_to(self.seo_log, f"  • {k}")

        self._log_to(self.seo_log, f"\n💡 Titles ({len(assets['titles'])})")
        for i, t in enumerate(assets["titles"][:3]):
            self._log_to(self.seo_log, f"  {i + 1}. {t}")

        self._log_to(self.seo_log, f"\n🏷️ Tags: {', '.join(assets['tags'][:5])}...")
        self._log_to(self.seo_log, f"# Hashtags: {' '.join(assets['hashtags'][:5])}")

        # Save HTML
        output_dir = os.path.join(BASE_DIR, "seo_output")
        os.makedirs(output_dir, exist_ok=True)
        safe = "".join(ch if ch.isalnum() or ch in " -_" else "" for ch in topic)[:40].strip()
        out_path = os.path.join(output_dir, f"SEO_{safe}.html")

        generate_html(assets, out_path)
        self.seo_last_output = out_path

        self._log_to(self.seo_log, f"\n✅ Saved to: {out_path}")
        self.seo_status.configure(text="✅ SEO report generated! Opening in browser...", fg=GREEN)
        self._set_footer("SEO report saved", GREEN)

        webbrowser.open(f"file:///{out_path.replace(os.sep, '/')}")

    def _seo_open_last(self):
        if self.seo_last_output and os.path.isfile(self.seo_last_output):
            webbrowser.open(f"file:///{self.seo_last_output.replace(os.sep, '/')}")
        else:
            messagebox.showinfo("Info", "Generate SEO assets first.")

    def _seo_load_transcript(self):
        """Load transcript into SEO topic field."""
        if self.last_transcript:
            self.seo_topic.set(self.last_transcript[:200])
            self.seo_moments_box.delete("1.0", "end")
            self.seo_moments_box.insert("1.0", self.last_transcript)
            self.seo_status.configure(
                text=f"✅ Transcript loaded! {len(self.last_transcript.split())} words", fg=GREEN)
        else:
            # Try generating from current video
            video = self.last_processed_video or ""
            if video and os.path.isfile(video):
                messagebox.showinfo("Info",
                    "No transcript yet. Go to Video page and click '📜 Transcript' first.")
            else:
                messagebox.showinfo("Info",
                    "No transcript available. Process a video first, then generate transcript.")

    # ═══════════════════════════════════════════════════════
    #  PAGE 5: YOUTUBE UPLOAD
    # ═══════════════════════════════════════════════════════

    def _build_upload_page(self):
        c = self.content

        self._label(c, "📤 YouTube Auto-Upload", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Upload processed videos directly to YouTube", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        # ── Connection Status Panel ──
        status_f = self._frame(c, bg_color=BG_CARD)
        status_f.pack(fill="x", padx=20, pady=10)
        self._label(status_f, "🔗 Connection Status", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))

        # Step 1: Google API installed?
        s1_ok = HAS_YT
        s1_icon = "✅" if s1_ok else "❌"
        s1_color = GREEN if s1_ok else RED
        s1_text = "Google API libraries installed" if s1_ok else "Google API NOT installed — run: pip install google-api-python-client google-auth-oauthlib"
        self._label(status_f, f"  {s1_icon}  Step 1: {s1_text}", 11, color=s1_color, bg_color=BG_CARD).pack(anchor="w", padx=15, pady=2)

        # Step 2: client_secret.json?
        s2_ok = HAS_YT and yt_has_creds()
        s2_icon = "✅" if s2_ok else "❌"
        s2_color = GREEN if s2_ok else RED
        s2_text = "client_secret.json found" if s2_ok else "client_secret.json NOT found — place it in the project folder"
        self._label(status_f, f"  {s2_icon}  Step 2: {s2_text}", 11, color=s2_color, bg_color=BG_CARD).pack(anchor="w", padx=15, pady=2)

        # Step 3: Authenticated?
        from youtube_uploader import is_authenticated as yt_is_auth
        s3_ok = HAS_YT and s2_ok and yt_is_auth()
        s3_icon = "✅" if s3_ok else "⏳"
        s3_color = GREEN if s3_ok else AMBER
        s3_text = "YouTube account connected!" if s3_ok else "Not connected yet — click button below to sign in"
        self._label(status_f, f"  {s3_icon}  Step 3: {s3_text}", 11, color=s3_color, bg_color=BG_CARD).pack(anchor="w", padx=15, pady=2)

        # Connect button (if not authenticated yet)
        if HAS_YT and s2_ok and not s3_ok:
            connect_f = self._frame(status_f, bg_color=BG_CARD)
            connect_f.pack(fill="x", padx=15, pady=(5, 10))
            self._button(connect_f, "🔑 Connect YouTube Account", self._upload_authenticate,
                         width=250, color=ACCENT).pack(side="left")
            self._label(connect_f, "Opens browser for Google sign-in", 10, color=TEXT_DIM, bg_color=BG_CARD).pack(side="left", padx=10)
        else:
            tk.Frame(status_f, bg=BG_CARD, height=8).pack()

        # If not ready, stop here
        if not s1_ok or not s2_ok:
            return

        pad = {"padx": 20, "pady": 4}

        # Channel selector
        ch_sec = self._frame(c)
        ch_sec.pack(fill="x", **pad)
        self._label(ch_sec, "YouTube Channel", 13, True).pack(anchor="w")
        ch_row = self._frame(ch_sec)
        ch_row.pack(fill="x", pady=3)
        if HAS_YT:
            channels = yt_get_channels() or ["Default"]
        else:
            channels = ["Default"]
        ch_menu = tk.OptionMenu(ch_row, self.upload_channel, *channels)
        ch_menu.configure(bg=BG_INPUT, fg="white", font=("Segoe UI", 11),
                         highlightthickness=0, relief="flat")
        ch_menu.pack(side="left", padx=(0, 10))
        self._button(ch_row, "🔑 Add Channel", lambda: self._upload_authenticate(prompt_for_name=True),
                     width=130, color=ACCENT_DARK).pack(side="left")

        # Video file
        sec = self._frame(c)
        sec.pack(fill="x", **pad)
        self._label(sec, "Video File", 13, True).pack(anchor="w")
        row = self._frame(sec)
        row.pack(fill="x", pady=3)
        self._entry(row, self.upload_file).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(row, "Browse", self._upload_browse_video, width=80).pack(side="right")

        # Title
        sec2 = self._frame(c)
        sec2.pack(fill="x", **pad)
        self._label(sec2, "Title", 13, True).pack(anchor="w")
        self._entry(sec2, self.upload_title).pack(fill="x", pady=3)

        # Description
        sec3 = self._frame(c)
        sec3.pack(fill="x", **pad)
        self._label(sec3, "Description", 13, True).pack(anchor="w")
        self.upload_desc_box = self._textbox(sec3, height=4)
        self.upload_desc_box.configure(bg=BG_INPUT)
        self.upload_desc_box.pack(fill="x", pady=3)

        # Tags
        sec4 = self._frame(c)
        sec4.pack(fill="x", **pad)
        self._label(sec4, "Tags (comma-separated)", 13, True).pack(anchor="w")
        self._entry(sec4, self.upload_tags).pack(fill="x", pady=3)

        # Row: Privacy + Category + Thumbnail
        sec5 = self._frame(c)
        sec5.pack(fill="x", **pad)
        row5 = self._frame(sec5)
        row5.pack(fill="x")

        # Privacy
        priv_f = self._frame(row5)
        priv_f.pack(side="left", padx=(0, 15))
        self._label(priv_f, "Privacy", 12, True).pack(anchor="w")
        for p in ["public", "unlisted", "private"]:
            tk.Radiobutton(priv_f, text=p.title(), variable=self.upload_privacy,
                           value=p, bg=BG, fg="white", selectcolor=ACCENT,
                           font=("Segoe UI", 10), activebackground=BG,
                           activeforeground="white").pack(side="left", padx=4)

        # Category
        cat_f = self._frame(row5)
        cat_f.pack(side="left", padx=15)
        self._label(cat_f, "Category", 12, True).pack(anchor="w")
        if HAS_YT:
            cat_names = list(YT_CATEGORIES.keys())
        else:
            cat_names = ["Entertainment"]
        cat_menu = tk.OptionMenu(cat_f, self.upload_category, *cat_names)
        cat_menu.configure(bg=BG_INPUT, fg="white", font=("Segoe UI", 10),
                          highlightthickness=0, relief="flat")
        cat_menu.pack(pady=3)

        # Thumbnail
        thm_f = self._frame(row5)
        thm_f.pack(side="left", padx=15)
        self._label(thm_f, "Thumbnail (optional)", 12, True).pack(anchor="w")
        trow = self._frame(thm_f)
        trow.pack(fill="x", pady=3)
        self._entry(trow, self.upload_thumb).pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._button(trow, "Browse", self._upload_browse_thumb, width=70).pack(side="right")

        # Upload button
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=10)
        self.upload_btn = self._button(btn_f, "🚀  UPLOAD TO YOUTUBE", self._upload_start,
                                        width=260, height=44, color=ACCENT)
        self.upload_btn.pack(side="left")

        # Status + log
        self.upload_status = self._label(c, "Ready — Select a video to upload", 11, color=TEXT_DIM)
        self.upload_status.pack(anchor="w", padx=20, pady=3)

        log_f = self._frame(c)
        log_f.pack(fill="both", expand=True, padx=20, pady=(3, 10))
        self.upload_log = self._textbox(log_f, height=6)
        self.upload_log.pack(fill="both", expand=True)

    def _upload_authenticate(self, prompt_for_name=False):
        """Run OAuth flow in thread, then refresh the page."""
        channel_name = None
        if prompt_for_name:
            channel_name = simpledialog.askstring("Add Channel", "Enter a name to save this channel token as (e.g. MyGamingChannel):")
            if not channel_name:
                return  # Cancelled

        self._set_footer("Opening browser for Google sign-in...", AMBER)

        def run():
            try:
                from youtube_uploader import authenticate
                svc = authenticate(channel_name=channel_name, log=lambda m: self.root.after(0, lambda: self._set_footer(m, AMBER)))
                if svc:
                    self.root.after(0, lambda: self._set_footer("✅ YouTube connected!", GREEN))
                    self.root.after(500, lambda: self._switch_page(None))  # Force refresh
                    self.root.after(600, lambda: self._switch_page("upload"))
                else:
                    self.root.after(0, lambda: self._set_footer("❌ Authentication failed", RED))
            except Exception as e:
                self.root.after(0, lambda: self._set_footer(f"Error: {e}", RED))

        threading.Thread(target=run, daemon=True).start()

    def _upload_browse_video(self):
        f = filedialog.askopenfilename(
            title="Select Video to Upload",
            filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All", "*.*")]
        )
        if f:
            self.upload_file.set(f)
            if not self.upload_title.get():
                self.upload_title.set(os.path.splitext(os.path.basename(f))[0])

    def _upload_browse_thumb(self):
        f = filedialog.askopenfilename(
            title="Select Thumbnail",
            filetypes=[("Image", "*.jpg *.jpeg *.png"), ("All", "*.*")]
        )
        if f:
            self.upload_thumb.set(f)

    def _upload_start(self):
        filepath = self.upload_file.get()
        if not filepath or not os.path.isfile(filepath):
            messagebox.showerror("Error", "Select a valid video file.")
            return

        title = self.upload_title.get().strip() or "My Video"
        desc = self.upload_desc_box.get("1.0", "end").strip() if hasattr(self, 'upload_desc_box') else ""
        tags = [t.strip() for t in self.upload_tags.get().split(",") if t.strip()]
        privacy = self.upload_privacy.get()
        category = self.upload_category.get()
        thumb = self.upload_thumb.get()

        cat_id = "24"
        if HAS_YT:
            cat_id = YT_CATEGORIES.get(category, "24")

        self.upload_btn.configure(state="disabled", text="UPLOADING...")
        self.upload_log.delete("1.0", "end")
        self.upload_status.configure(text="Uploading to YouTube...", fg=AMBER)
        self._set_footer("Uploading video...", AMBER)

        def log_msg(msg):
            self.root.after(0, lambda: self._log_to(self.upload_log, msg))

        def run():
            try:
                vid_id = yt_upload(
                    filepath=filepath, title=title, description=desc,
                    tags=tags, category_id=cat_id, privacy=privacy,
                    thumbnail_path=thumb if thumb and os.path.isfile(thumb) else None,
                    log=log_msg
                )
                if vid_id:
                    self.root.after(0, lambda: self.upload_status.configure(
                        text=f"✅ Uploaded! ID: {vid_id}", fg=GREEN))
                    self.root.after(0, lambda: self._set_footer(
                        f"Upload success: {vid_id}", GREEN))
                else:
                    self.root.after(0, lambda: self.upload_status.configure(
                        text="❌ Upload failed", fg=RED))
            except Exception as e:
                self.root.after(0, lambda: self.upload_status.configure(
                    text=f"Error: {e}", fg=RED))
            finally:
                self.root.after(0, lambda: self.upload_btn.configure(
                    state="normal", text="🚀  UPLOAD TO YOUTUBE"))

        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════════════════
    #  PAGE 6: PROXY MANAGER & KILL SWITCH
    # ═══════════════════════════════════════════════════════

    def _build_proxy_page(self):
        c = self.content

        self._label(c, "📡 Proxy Manager & Kill Switch", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Manage SOCKS5 proxies, bind IPs to channels, prevent IP leaks", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        data = proxy_get_all()

        # ── Direct IP ──
        ip_f = self._frame(c, bg_color=BG_CARD)
        ip_f.pack(fill="x", padx=20, pady=8)
        self._label(ip_f, "🌐 Your Direct IP", 13, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(8, 3))
        self.proxy_direct_ip = self._label(ip_f, "Checking...", 11, color=TEXT_MID, bg_color=BG_CARD)
        self.proxy_direct_ip.pack(anchor="w", padx=15, pady=(0, 8))
        threading.Thread(target=self._proxy_check_direct_ip, daemon=True).start()

        # ── Kill Switch Toggle ──
        ks_f = self._frame(c)
        ks_f.pack(fill="x", padx=20, pady=4)
        self.kill_switch_var = tk.BooleanVar(value=data.get("kill_switch", True))
        tk.Checkbutton(ks_f, text="🛡️ Kill Switch (block upload if IP mismatch)",
                       variable=self.kill_switch_var, bg=BG, fg="white",
                       selectcolor=BG_INPUT, font=("Segoe UI", 12, "bold"),
                       activebackground=BG, activeforeground="white",
                       command=self._proxy_save_kill_switch).pack(anchor="w")

        # ── Proxy List ──
        prx_sec = self._frame(c, bg_color=BG_CARD)
        prx_sec.pack(fill="x", padx=20, pady=8)
        self._label(prx_sec, "🔌 Proxy List", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(8, 5))

        # Header
        hdr = self._frame(prx_sec, bg_color=ACCENT_DARK)
        hdr.pack(fill="x", padx=15)
        for txt, w in [("Name", 12), ("Host:Port", 18), ("Type", 8), ("IP", 15), ("Status", 8)]:
            self._label(hdr, txt, 10, True, TEXT_DIM, ACCENT_DARK).pack(side="left", padx=5)

        # Proxy rows
        self.proxy_list_frame = self._frame(prx_sec, bg_color=BG_CARD)
        self.proxy_list_frame.pack(fill="x", padx=15, pady=3)
        self._proxy_refresh_list(data)

        # Add proxy row
        add_f = self._frame(prx_sec, bg_color=BG_CARD)
        add_f.pack(fill="x", padx=15, pady=(3, 8))
        self.proxy_name_var = tk.StringVar(value="")
        self.proxy_host_var = tk.StringVar(value="")
        self.proxy_port_var = tk.StringVar(value="")
        self.proxy_user_var = tk.StringVar(value="")
        self.proxy_pass_var = tk.StringVar(value="")

        self._entry(add_f, self.proxy_name_var, width=80).pack(side="left", padx=2)
        self._label(add_f, "Host:", 10, color=TEXT_DIM, bg_color=BG_CARD).pack(side="left")
        self._entry(add_f, self.proxy_host_var, width=120).pack(side="left", padx=2)
        self._label(add_f, "Port:", 10, color=TEXT_DIM, bg_color=BG_CARD).pack(side="left")
        self._entry(add_f, self.proxy_port_var, width=50).pack(side="left", padx=2)
        self._button(add_f, "➕ Add", self._proxy_add, width=70, color=ACCENT).pack(side="left", padx=5)

        # Action buttons
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=6)
        self._button(btn_f, "🔍 Health Check All", self._proxy_health_all,
                     width=170, color=ACCENT_DARK).pack(side="left")

        # ── Channel Mapping ──
        ch_sec = self._frame(c, bg_color=BG_CARD)
        ch_sec.pack(fill="x", padx=20, pady=8)
        self._label(ch_sec, "🔗 Channel → Proxy Mapping", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(8, 5))

        self.channel_list_frame = self._frame(ch_sec, bg_color=BG_CARD)
        self.channel_list_frame.pack(fill="x", padx=15, pady=3)
        self._proxy_refresh_channels(data)

        # Add channel
        ch_add_f = self._frame(ch_sec, bg_color=BG_CARD)
        ch_add_f.pack(fill="x", padx=15, pady=(3, 8))
        self.channel_name_var = tk.StringVar(value="")
        self._label(ch_add_f, "Channel name:", 10, color=TEXT_DIM, bg_color=BG_CARD).pack(side="left")
        self._entry(ch_add_f, self.channel_name_var, width=150).pack(side="left", padx=5)
        self._button(ch_add_f, "➕ Add Channel", self._proxy_add_channel, width=120, color=ACCENT).pack(side="left", padx=5)

        # Status
        self.proxy_status = self._label(c, "", 11, color=TEXT_DIM)
        self.proxy_status.pack(anchor="w", padx=20, pady=3)

    def _proxy_check_direct_ip(self):
        ip = check_ip_direct(log=lambda m: None)
        msg = f"Direct IP: {ip}" if ip else "Could not detect IP"
        self.root.after(0, lambda: self.proxy_direct_ip.configure(text=msg))

    def _proxy_refresh_list(self, data=None):
        for w in self.proxy_list_frame.winfo_children():
            w.destroy()
        if data is None:
            data = proxy_get_all()
        for i, p in enumerate(data.get("proxies", [])):
            row = self._frame(self.proxy_list_frame, bg_color=BG if i % 2 == 0 else BG_CARD)
            row.pack(fill="x", pady=1)
            bg = BG if i % 2 == 0 else BG_CARD
            self._label(row, p["name"], 10, color=TEXT, bg_color=bg).pack(side="left", padx=5)
            self._label(row, f"{p['host']}:{p['port']}", 10, color=TEXT_MID, bg_color=bg).pack(side="left", padx=5)
            self._label(row, p.get("type", "socks5"), 10, color=TEXT_DIM, bg_color=bg).pack(side="left", padx=5)
            self._label(row, p.get("last_ip", "—"), 10, color=TEXT_MID, bg_color=bg).pack(side="left", padx=5)
            status = p.get("status", "unknown")
            sc = GREEN if status == "active" else (RED if status == "down" else TEXT_DIM)
            icon = "🟢" if status == "active" else ("🔴" if status == "down" else "⚪")
            self._label(row, f"{icon} {status}", 10, color=sc, bg_color=bg).pack(side="left", padx=5)
            rm = tk.Label(row, text="✕", font=("Segoe UI", 10, "bold"), fg=RED, bg=bg, cursor="hand2")
            rm.pack(side="right", padx=8)
            rm.bind("<Button-1>", lambda e, idx=i: self._proxy_remove(idx))

    def _proxy_refresh_channels(self, data=None):
        for w in self.channel_list_frame.winfo_children():
            w.destroy()
        if data is None:
            data = proxy_get_all()
        proxy_names = ["None"] + [p["name"] for p in data.get("proxies", [])]
        for i, ch in enumerate(data.get("channels", [])):
            row = self._frame(self.channel_list_frame, bg_color=BG_CARD)
            row.pack(fill="x", pady=2)
            self._label(row, f"📺 {ch['name']}", 11, color=TEXT, bg_color=BG_CARD).pack(side="left", padx=10)
            self._label(row, "→", 11, color=TEXT_DIM, bg_color=BG_CARD).pack(side="left", padx=5)
            var = tk.StringVar(value=ch.get("assigned_proxy", "None") or "None")
            menu = tk.OptionMenu(row, var, *proxy_names,
                                 command=lambda val, idx=i: self._proxy_assign(idx, val))
            menu.configure(bg=BG_INPUT, fg="white", font=("Segoe UI", 10),
                          highlightthickness=0, relief="flat")
            menu.pack(side="left", padx=5)
            rm = tk.Label(row, text="✕", font=("Segoe UI", 10, "bold"), fg=RED, bg=BG_CARD, cursor="hand2")
            rm.pack(side="right", padx=8)
            rm.bind("<Button-1>", lambda e, idx=i: self._proxy_remove_channel(idx))

    def _proxy_add(self):
        name = self.proxy_name_var.get().strip()
        host = self.proxy_host_var.get().strip()
        port = self.proxy_port_var.get().strip()
        if not name or not host or not port:
            messagebox.showerror("Error", "Fill in name, host, and port.")
            return
        try:
            add_proxy(name, host, int(port))
            self._proxy_refresh_list()
            self.proxy_status.configure(text=f"✅ Proxy '{name}' added", fg=GREEN)
        except Exception as e:
            self.proxy_status.configure(text=f"Error: {e}", fg=RED)

    def _proxy_remove(self, idx):
        remove_proxy(idx)
        self._proxy_refresh_list()

    def _proxy_add_channel(self):
        name = self.channel_name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Enter a channel name.")
            return
        proxy_add_channel(name)
        self._proxy_refresh_channels()
        self.proxy_status.configure(text=f"✅ Channel '{name}' added", fg=GREEN)

    def _proxy_remove_channel(self, idx):
        proxy_remove_channel(idx)
        self._proxy_refresh_channels()

    def _proxy_assign(self, channel_idx, proxy_name):
        if proxy_name == "None":
            proxy_name = ""
        assign_proxy_to_channel(channel_idx, proxy_name)
        self.proxy_status.configure(text=f"✅ Proxy assigned", fg=GREEN)

    def _proxy_save_kill_switch(self):
        data = proxy_get_all()
        data["kill_switch"] = self.kill_switch_var.get()
        save_proxy_data(data)

    def _proxy_health_all(self):
        self.proxy_status.configure(text="Checking all proxies...", fg=AMBER)
        def run():
            proxy_health_check(
                log=lambda m: self.root.after(0, lambda: self.proxy_status.configure(text=m)))
            self.root.after(0, self._proxy_refresh_list)
            self.root.after(0, lambda: self.proxy_status.configure(text="✅ Health check complete", fg=GREEN))
        threading.Thread(target=run, daemon=True).start()

    # ═══════════════════════════════════════════════════════
    #  PAGE 7: SETTINGS & CLEANUP
    # ═══════════════════════════════════════════════════════

    def _build_settings_page(self):
        c = self.content

        self._label(c, "⚙️ Settings & Storage", 18, True, ACCENT_LIGHT).pack(anchor="w", padx=20, pady=(15, 6))
        self._label(c, "Auto-cleanup, storage management, and preferences", 11, color=TEXT_DIM).pack(anchor="w", padx=20)

        pad = {"padx": 20, "pady": 6}

        # Auto-delete originals
        sec1 = self._frame(c, bg_color=BG_CARD)
        sec1.pack(fill="x", padx=20, pady=10)
        self._label(sec1, "📁 File Management", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))

        self.auto_del_var = tk.BooleanVar(value=self.settings.get("auto_delete_originals", False))
        cb1 = tk.Checkbutton(sec1, text="Delete original video files after successful processing",
                             variable=self.auto_del_var, bg=BG_CARD, fg="white",
                             selectcolor=BG_INPUT, font=("Segoe UI", 11),
                             activebackground=BG_CARD, activeforeground="white",
                             command=self._save_settings)
        cb1.pack(anchor="w", padx=15, pady=3)

        # Cleanup old files
        cleanup_f = self._frame(sec1, bg_color=BG_CARD)
        cleanup_f.pack(fill="x", padx=15, pady=(5, 10))
        self._label(cleanup_f, "Auto-delete processed files older than", 11, color=TEXT, bg_color=BG_CARD).pack(side="left")
        self.cleanup_days_var = tk.IntVar(value=self.settings.get("cleanup_days", 7))
        sc = tk.Spinbox(cleanup_f, from_=1, to=90, textvariable=self.cleanup_days_var,
                       width=4, bg=BG_INPUT, fg="white", font=("Segoe UI", 11),
                       relief="flat", bd=2, buttonbackground=ACCENT_DARK)
        sc.pack(side="left", padx=6)
        self._label(cleanup_f, "days", 11, color=TEXT, bg_color=BG_CARD).pack(side="left")

        # Cleanup buttons
        btn_f = self._frame(c)
        btn_f.pack(fill="x", padx=20, pady=8)
        self._button(btn_f, "🧹 Clean Old Files Now", self._settings_cleanup_now,
                     width=200, color=ACCENT_DARK).pack(side="left")
        self._button(btn_f, "💾 Save Settings", self._save_settings,
                     width=140, color=ACCENT).pack(side="left", padx=10)
        # Groq API Key (for Transcript)
        api_f = self._frame(c, bg_color=BG_CARD)
        api_f.pack(fill="x", padx=20, pady=8)
        self._label(api_f, "🔑 Groq API Key (for Whisper Transcript)", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(8, 3))
        key_row = self._frame(api_f, bg_color=BG_CARD)
        key_row.pack(fill="x", padx=15, pady=(0, 8))
        self.groq_key_var = tk.StringVar(value=self.settings.get("groq_api_key", ""))
        self._entry(key_row, self.groq_key_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._button(key_row, "Save Key", self._save_settings, width=90, color=ACCENT).pack(side="right")

        # Status
        self.settings_status = self._label(c, "", 11, color=TEXT_DIM)
        self.settings_status.pack(anchor="w", padx=20, pady=3)

        # Disk usage
        disk_f = self._frame(c, bg_color=BG_CARD)
        disk_f.pack(fill="x", padx=20, pady=10)
        self._label(disk_f, "💾 Disk Usage", 14, True, ACCENT_LIGHT, BG_CARD).pack(anchor="w", padx=15, pady=(10, 5))

        self.disk_info_label = self._label(disk_f, "Calculating...", 11, color=TEXT_MID, bg_color=BG_CARD)
        self.disk_info_label.pack(anchor="w", padx=15, pady=(0, 10))
        self._update_disk_usage()

    def _update_disk_usage(self):
        """Calculate folder sizes for display."""
        def calc():
            total = 0
            pro_count = 0
            for root, dirs, files in os.walk(BASE_DIR):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        sz = os.path.getsize(fp)
                        total += sz
                        if f.endswith("_PRO.mp4"):
                            pro_count += 1
                    except OSError:
                        pass
            total_mb = total / (1024 * 1024)
            msg = f"Project folder: {total_mb:.1f} MB  |  Processed videos (_PRO.mp4): {pro_count} files"
            self.root.after(0, lambda: self.disk_info_label.configure(text=msg))
        threading.Thread(target=calc, daemon=True).start()

    def _settings_cleanup_now(self):
        days = self.cleanup_days_var.get()
        cutoff = time.time() - (days * 86400)
        deleted = 0
        freed = 0

        for root, dirs, files in os.walk(BASE_DIR):
            for f in files:
                if f.endswith("_PRO.mp4"):
                    fp = os.path.join(root, f)
                    try:
                        if os.path.getmtime(fp) < cutoff:
                            sz = os.path.getsize(fp)
                            os.remove(fp)
                            deleted += 1
                            freed += sz
                    except OSError:
                        pass

        freed_mb = freed / (1024 * 1024)
        msg = f"Cleaned {deleted} files ({freed_mb:.1f} MB freed)"
        self.settings_status.configure(text=msg, fg=GREEN if deleted else TEXT_DIM)
        self._set_footer(msg, GREEN if deleted else TEXT_DIM)
        self._update_disk_usage()

    # ── Queue State Persistence ──
    QUEUE_STATE_PATH = os.path.join(BASE_DIR, "queue_state.json")

    def _load_queue_state(self):
        """Load saved queue items from disk."""
        if os.path.isfile(self.QUEUE_STATE_PATH):
            try:
                with open(self.QUEUE_STATE_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, list):
                    self.queue_items = saved
            except Exception:
                pass

    def _save_queue_state(self):
        """Save current queue items to disk."""
        try:
            with open(self.QUEUE_STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.queue_items, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_settings(self):
        """Load settings from config.json."""
        self.settings = {
            "auto_delete_originals": False,
            "cleanup_days": 7,
        }
        if os.path.isfile(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.settings.update(data)
            except Exception:
                pass

    def _save_settings(self):
        """Save settings to config.json."""
        self.settings["auto_delete_originals"] = getattr(self, 'auto_del_var', None) and self.auto_del_var.get()
        self.settings["cleanup_days"] = getattr(self, 'cleanup_days_var', None) and self.cleanup_days_var.get() or 7
        if hasattr(self, 'groq_key_var') and self.groq_key_var.get():
            self.settings["groq_api_key"] = self.groq_key_var.get()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            if hasattr(self, 'settings_status'):
                self.settings_status.configure(text="✅ Settings saved!", fg=GREEN)
        except Exception as e:
            if hasattr(self, 'settings_status'):
                self.settings_status.configure(text=f"Error saving: {e}", fg=RED)


# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(filename=os.path.join(BASE_DIR, "error.txt"), level=logging.ERROR,
                        format="%(asctime)s [%(levelname)s] %(message)s")
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception
    
    try:
        ProVideoSuite()
    except Exception as e:
        logging.error(f"App crashed: {e}", exc_info=True)
        raise

