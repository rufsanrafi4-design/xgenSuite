# Pro Video Processor — Full Project Documentation
### Complete Project Overview | All Tools & UIs
### February 27, 2026

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Tool 1: Pro Video Processor (Main App)](#tool-1-pro-video-processor-main-app)
4. [Tool 2: Auto Thumbnail Generator](#tool-2-auto-thumbnail-generator)
5. [Tool 3: YouTube SEO Content Generator](#tool-3-youtube-seo-content-generator)
6. [Processing Engine (pro_engine.py)](#processing-engine)
7. [The 5 Evasion Techniques](#the-5-evasion-techniques)
8. [The Nuclear Audio Chain (16+ Layers)](#the-nuclear-audio-chain)
9. [Setup & Launch](#setup--launch)
10. [Configuration](#configuration)
11. [Technical Pipeline](#technical-pipeline)
12. [Version History](#version-history)
13. [Troubleshooting](#troubleshooting)
14. [Quick Reference](#quick-reference)

---

## Project Overview

**Pro Video Processor** is a Python desktop toolkit for YouTube content creators. It consists of **3 independent tools**, each with its own GUI:

| # | Tool | File | Purpose |
|---|------|------|---------|
| 1 | **Pro Video Processor** | `app.py` | Process videos to bypass Content ID (5 evasion techniques) |
| 2 | **Auto Thumbnail Generator** | `thumbnail_maker.py` | Extract frames → create styled YouTube thumbnails |
| 3 | **YouTube SEO Generator** | `seo_generator.py` | Generate keywords, titles, descriptions, tags, hashtags |

All tools share:
- **UI Framework**: customtkinter (modern dark theme, purple accent)
- **Engine**: FFmpeg (bundled in `ffmpeg_bin/`)
- **Language**: Python 3.10+
- **Launch**: `LAUNCH.bat` (one-click) or `python app.py`

---

## Project Structure

### Active Files (in use)

```
video_processor/
├── app.py                     ← Main app UI (customtkinter, launches all 3 tools)
├── pro_engine.py              ← Core processing engine (2-pass pipeline, 5 techniques)
├── thumbnail_maker.py         ← Thumbnail generator tool (frame extraction + styling)
├── seo_generator.py           ← SEO content generator tool (keywords, titles, tags)
├── config.json                ← Settings (pitch_semitones, speed_variation_pct)
├── requirements.txt           ← Python deps (customtkinter, Pillow)
├── ffmpeg_bin/                ← Bundled FFmpeg binaries
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── sounds/                    ← Ambient audio files (optional)
├── _thumb_frames/             ← Temp directory for extracted thumbnail frames
├── LAUNCH.bat                 ← One-click launcher (checks Python, deps, FFmpeg)
├── setup.bat                  ← First-time setup (downloads FFmpeg, installs deps)
├── BUILD_ZIP.bat              ← Build portable ZIP package
├── _build_zip_helper.ps1      ← PowerShell helper for ZIP creation
├── PROJECT_DOCUMENTATION.md   ← This file
└── README.md                  ← Quick readme
```

### Legacy Files (from earlier versions, not used in v8+)

```
├── processor.py               ← Old v3 extreme processor (replaced by pro_engine.py)
├── compilation_builder.py     ← Old v6 compilation builder (replaced by pro_engine.py)
├── reaction_builder.py        ← Old reaction PiP builder (replaced by pro_engine.py)
├── main.py                    ← Old CLI entry point (used processor.py)
├── server.py                  ← Old Flask web server for UI
├── main.js                    ← Old Electron main process
├── preload.js                 ← Old Electron preload script
├── package.json               ← Old Electron/Node config
├── package-lock.json          ← Old Node lock file
├── ui/index.html              ← Old Electron web UI
├── process_video.bat          ← Old batch launcher
├── start_ui.bat               ← Old UI launcher
└── test_concat_audio.py       ← Old audio test script
```

---

## Tool 1: Pro Video Processor (Main App)

**File**: `app.py` (431 lines) — **Class**: `ProVideoApp`

### What It Does
The main application processes videos to bypass YouTube's Content ID system using 5 evasion techniques across a 2-pass pipeline.

### UI Layout
```
┌──────────────────────────────────────────────────┐
│  PRO VIDEO PROCESSOR v7              [dark theme] │
├──────────────────────────────────────────────────┤
│  Main Video:    [path entry] [Browse]             │
│  Reactions:     [path entry] [Browse] [Clear]     │
│  Episode Title: [text entry]                      │
│  Pitch Shift:   [━━━━●━━━] 4.0 semitones         │
│  Save To:       [path entry] [Browse]             │
├──────────────────────────────────────────────────┤
│  [🚀 BUILD VIDEO]  [📸 Thumbnail]  [🔍 SEO]     │
├──────────────────────────────────────────────────┤
│  Video Preview: codec, resolution, fps, duration  │
├──────────────────────────────────────────────────┤
│  Build Log:  (scrollable log output)              │
│  > Starting Pass 1...                             │
│  > Extracting segments... 45/390                  │
│  > ...                                            │
├──────────────────────────────────────────────────┤
│  Status: Ready                                    │
└──────────────────────────────────────────────────┘
```

### Key Features
- **File browsers** for main video, reaction clips, and output path
- **Pitch slider** (1–6 semitones, default 4.0)
- **Episode title** input (burned into the video overlay)
- **BUILD button** with threaded execution + live log
- **Thumbnail launcher** — opens `thumbnail_maker.py` as subprocess
- **SEO launcher** — opens `seo_generator.py` as subprocess
- **Video preview** — shows codec, resolution, fps, duration on file select
- **Auto output path** — generates output filename from input

### Functions

| Function | Lines | Purpose |
|----------|-------|---------|
| `__init__` | 30–50 | Init window (920×850), variables, build UI |
| `_build_ui` | 52–197 | Constructs all sections of the UI |
| `_browse_main` | 246–257 | File dialog for main video + auto-set output |
| `_browse_reactions` | 259–267 | Multi-file dialog for reaction clips |
| `_browse_output` | 269–276 | Save dialog for output path |
| `_launch_thumbnail` | 282–287 | Spawns `thumbnail_maker.py` as subprocess |
| `_launch_seo` | 289–294 | Spawns `seo_generator.py` as subprocess |
| `_load_preview` | 296–344 | Runs ffprobe, displays video info in UI |
| `_log` | 348–357 | Thread-safe log append |
| `_start_build` | 368–426 | Validates inputs, calls `build_video()` in thread |

---

## Tool 2: Auto Thumbnail Generator

**File**: `thumbnail_maker.py` (620 lines) — **Class**: `ThumbnailMakerApp`

### What It Does
Extracts the best frames from any video, lets you pick one, then generates a styled YouTube-ready thumbnail (1280×720) with text overlays, borders, color enhancement, and vignette effects.

### UI Layout
```
┌──────────────────────────────────────────────────┐
│  AUTO THUMBNAIL GENERATOR  v1.0                   │
├──────────────────────────────────────────────────┤
│  Video File: [path entry] [Browse] [📸 Extract]  │
├──────────────────────────────────────────────────┤
│  Thumbnail Title Text: [text entry]  Emoji: [🔥] │
├──────────────────────────────────────────────────┤
│  Style: ● Bold Impact ○ Fire Red ○ Clean White   │
│         ○ Neon Purple ○ YouTube Classic            │
├──────────────────────────────────────────────────┤
│  Select Best Frame (click to select):             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │ Fr 1 │ │ Fr 2 │ │ Fr 3 │ │ Fr 4 │  (scroll)  │
│  └──────┘ └──────┘ └──────┘ └──────┘             │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐             │
│  │ Fr 5 │ │ Fr 6 │ │ Fr 7 │ │ Fr 8 │             │
│  └──────┘ └──────┘ └──────┘ └──────┘             │
├──────────────────────────────────────────────────┤
│  Status: ✓ Extracted 14 frames                    │
│  [🎨 GENERATE THUMBNAIL]  [🎲 RANDOM BEST]       │
└──────────────────────────────────────────────────┘
```

### Frame Extraction
- **Method 1**: 8 evenly-spaced frames (skipping first/last 10% of video)
- **Method 2**: Up to 6 scene-change detection frames (threshold >0.4)
- All frames scaled to 1920×1080 with aspect-ratio-preserving padding

### 5 Thumbnail Styles

| Style | Border | Text Color | Overlay | Vignette | Saturation |
|-------|--------|------------|---------|----------|------------|
| **Bold Impact** | Purple 8px | White/Black stroke | 30% dark | ✓ | 1.4× |
| **Fire Red** | Red 10px | White/Red stroke | 25% dark | ✓ | 1.5× |
| **Clean White** | White 6px | White/Dark stroke | 35% dark | ✗ | 1.2× |
| **Neon Purple** | Light purple 8px | White/Purple stroke | 20% dark | ✓ | 1.3× |
| **YouTube Classic** | Red 12px | Yellow/Black stroke | 15% dark | ✓ | 1.6× |

### Thumbnail Generation Pipeline
1. Load frame → resize to 1280×720
2. Enhance saturation and contrast
3. Apply radial vignette (darkens edges, preserves center)
4. Apply gradient overlay at bottom for text readability
5. Draw colored border
6. Word-wrap title text, center at bottom with stroke outline
7. Optional emoji overlay (top-right corner)
8. Save as JPEG 95% quality

### Key Functions

| Function | Purpose |
|----------|---------|
| `find_ffmpeg()` | Locate FFmpeg in `ffmpeg_bin/` or PATH |
| `get_video_duration()` | Get duration via ffprobe |
| `extract_frames()` | Extract 8 evenly-spaced + 6 scene-change frames |
| `create_thumbnail()` | Generate styled thumbnail from frame + text |
| `_display_frames()` | Show frame grid in scrollable canvas |
| `_select_frame()` | Highlight selected frame with purple border |
| `_generate_thumbnail()` | Save dialog → generate in thread → open result |

---

## Tool 3: YouTube SEO Content Generator

**File**: `seo_generator.py` (767 lines) — **Class**: `SEOGeneratorApp`

### What It Does
Generates complete YouTube SEO assets for any video topic — titles, descriptions, tags, hashtags, hooks, CTAs, and thumbnail prompts. Outputs a premium HTML report.

### UI Layout
```
┌──────────────────────────────────────────────────┐
│  YOUTUBE SEO CONTENT GENERATOR                    │
├──────────────────────────────────────────────────┤
│  Video Topic:    [text entry]                     │
│  Show Name:      [text entry]                     │
│  Main Character: [text entry]                     │
│  Key Moments:    [text entry]                     │
├──────────────────────────────────────────────────┤
│  [🚀 GENERATE SEO ASSETS]  [📂 OPEN LAST]       │
├──────────────────────────────────────────────────┤
│  Generation Log:                                  │
│  > Generating 25 seed keywords...                 │
│  > Building 8 title variations...                 │
│  > Writing description template...                │
│  > HTML report saved!                             │
├──────────────────────────────────────────────────┤
│  Status: ✅ SEO report generated                  │
└──────────────────────────────────────────────────┘
```

### Generated SEO Assets

| Asset | Count | Example |
|-------|-------|---------|
| **Keywords** | 25 | "family guy funny moments", "peter griffin compilation" |
| **Titles** | 8 | "The Time Peter Actually Crossed the Line..." |
| **Description** | 1 | Full YouTube description template with timestamps |
| **Tags** | 30 | "family guy, funny moments, peter griffin, compilation" |
| **Hashtags** | 15 | "#FamilyGuy #BestMoments #FunnyMoments" |
| **Hooks** | 5 | "You WON'T believe what Peter did in this episode!" |
| **CTAs** | 5 | "Smash that like button if Peter is the real MVP!" |
| **Thumbnail prompts** | 3 | Text descriptions for ideal thumbnail images |

### Output
- Saves as `seo_{topic}_{timestamp}.html` in project directory
- Premium dark-theme HTML page with copy buttons for each section
- Auto-opens in browser after generation

### Key Functions

| Function | Purpose |
|----------|---------|
| `generate_seo_assets()` | Build all SEO data from topic/show/character inputs |
| `generate_html()` | Create premium styled HTML report |
| `_generate()` | UI action: validate inputs → generate → open HTML |

---

## Processing Engine

**File**: `pro_engine.py` (514 lines)

The core engine that powers Tool 1. Implements a **2-pass pipeline** with 5 evasion techniques.

### Functions

| Function | Lines | Purpose |
|----------|-------|---------|
| `find_ffmpeg()` | 39–45 | Locate FFmpeg in `ffmpeg_bin/` or PATH |
| `get_video_info()` | 48–69 | Extract duration, fps, resolution via ffprobe |
| `_extract_segment()` | 74–108 | Extract one segment with optional zoom (thread pool) |
| `preprocess_swap_zoom()` | 111–236 | **Pass 1**: Temporal reorder + corner zoom |
| `build_audio_chain()` | 241–292 | Generate 16-layer nuclear audio filter string |
| `build_video()` | 297–494 | **Main entry**: Pass 1 → Pass 2 → final output |

### Pipeline
```
INPUT → Pass 1 (segment swap + zoom) → _intermediate_swapped.mp4
     → Pass 2 (split-screen + audio + visual) → FINAL OUTPUT
```

### Key Rules
- **Output duration = Input duration** (EXACTLY, enforced by `-t` flag)
- **Metadata stripped** (`-map_metadata -1`)
- **Bitexact encoding** (`-flags +bitexact`)
- **Fast-start** (`-movflags +faststart`) for YouTube upload optimization

---

## The 5 Evasion Techniques

### 1. Segment Swapping (Temporal Reorder)
Every 10s: 3s normal, then swap the two 3.5s halves. Breaks temporal fingerprinting.

### 2. Alternating Corner Zoom
Every 10s of output: 3s zoom into top-right or top-left corner (52%/48% crop). Breaks spatial fingerprinting.

### 3. Nuclear Audio Chain (16+ Layers)
Attacks all 4 pillars of audio fingerprinting. See next section.

### 4. Visual Evasion (6 Layers)
1. **Mirror flip** (hflip)
2. **8% edge crop** (removes logos/watermarks)
3. **Hue rotation** (+55°)
4. **Contrast/saturation boost** (+10%/+12%)
5. **Subtle rotation sway** (0.002 rad, 7s cycle)
6. **Film grain** (2% temporal noise)

### 5. Split-Screen Layout
```
┌────────────────────────────────────────┐
│  "Episode Title"          [TOP BAR]    │
├────────────────┬──┬───────────────────┤
│  Main Video    │▐▐│  Reaction Clip    │
│  (740×600)     │▐▐│  (loops)          │
├────────────────┴──┴───────────────────┤
│  "Like and Subscribe"  [BOTTOM BAR]    │
└────────────────────────────────────────┘
```
Original content = 48% of output pixels.

---

## The Nuclear Audio Chain

### All Layers in Processing Order

```
INPUT AUDIO
    │
    ├─ 1.  asetpts=PTS-STARTPTS          Reset timestamps
    ├─ 2.  asetrate={new_rate}             Pitch shift (step 1)
    ├─ 3.  aresample=44100                 Pitch shift (step 2)
    ├─ 4.  atempo={correction}             Speed correction
    ├─ 5.  aecho=0.6:0.3:15|25:0.25|0.15  Echo (dual delay)
    ├─ 6.  chorus=0.5:0.9:50|60:...       Chorus (detuned copies)
    ├─ 7.  acompressor=-18dB:4:1:...      Radio compression
    ├─ 8.  tremolo=f=3.5:d=0.12           Amplitude modulation
    ├─ 9.  equalizer@800Hz  -14dB         EQ notch 1
    ├─ 10. equalizer@1500Hz -14dB         EQ notch 2
    ├─ 11. equalizer@3000Hz -12dB         EQ notch 3
    ├─ 12. equalizer@5000Hz -10dB         EQ notch 4
    ├─ 13. bandreject@350Hz               Band reject 1
    ├─ 14. bandreject@2200Hz              Band reject 2
    ├─ 15. bandreject@4500Hz              Band reject 3
    ├─ 16. flanger (sinusoidal)           Moving comb filter
    ├─ 17. extrastereo=1.5                Stereo widening
    ├─ 18. aphaser                        Phase scrambling
    ├─ 19. afreqshift=+35Hz              Frequency shift
    ├─ 20. loudnorm=-14 LUFS             YouTube mastering
    └─ 21. alimiter=0.98                  Hard limiter
    │
OUTPUT AUDIO
```

### Attack Strategy

| Pillar | What Content ID Checks | Our Attack |
|--------|------------------------|------------|
| **Waveform** | Shape of audio wave | Echo + Chorus |
| **Harmonics** | Frequency relationships | Pitch Shift + Freq Shift |
| **Spectrum** | Energy distribution | EQ Notches + Band Reject + Flanger |
| **Envelope** | Volume changes over time | Tremolo + Compressor |

---

## Setup & Launch

### Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Must be in system PATH |
| customtkinter | Latest | `pip install customtkinter` |
| Pillow | Latest | `pip install Pillow` (for thumbnails) |
| FFmpeg | 5.0+ | Bundled in `ffmpeg_bin/` or auto-downloaded |

### First-Time Setup
```bash
# Run setup.bat — downloads FFmpeg + installs Python deps
setup.bat
```

### Launch
```bash
# Option 1: One-click launcher
LAUNCH.bat

# Option 2: Direct Python
cd video_processor
python app.py

# Option 3: Individual tools
python thumbnail_maker.py
python seo_generator.py
```

### CLI Usage
```bash
python pro_engine.py \
  --main "video.mp4" \
  --reactions "reaction.mp4" \
  --output "output.mp4" \
  --title "Best Moments" \
  --pitch 4.0
```

---

## Configuration

### config.json
```json
{
  "pitch_semitones": 1,
  "speed_variation_pct": 1.5
}
```

### Pitch Guide

| Value | Effect | Detection Risk |
|-------|--------|----------------|
| 1.0 | Very subtle | Higher |
| 2.0 | Noticeable | Moderate |
| **3.0–4.0** | **Recommended** | **Low** |
| 5.0–6.0 | Chipmunk-like | Very low |

### Internal Constants (in `pro_engine.py`)

| Constant | Default | Controls |
|----------|---------|----------|
| BLOCK | 10.0s | Segment-swapping block size |
| NORMAL | 3.0s | Unchanged portion per block |
| ZOOM_CYCLE | 20.0s | Full zoom alternation cycle |
| ZOOM_DUR | 3.0s | Duration of each zoom |
| CRF | 22 | Video quality |
| Hue rotation | 55° | Color shift |
| Freq shift | +35 Hz | Audio frequency offset |

---

## Technical Pipeline

```
┌─────────────────────────────────────────────────┐
│                 INPUT VIDEO                      │
└──────────────────────┬──────────────────────────┘
                       ▼
╔══════════════════════════════════════════════════╗
║  PASS 1: Segment Swap + Corner Zoom              ║
║  → 390 segments (4 parallel FFmpeg threads)      ║
║  → Concatenate with clean timestamps             ║
║  → Output: _intermediate_swapped.mp4             ║
╚══════════════════════╤═══════════════════════════╝
                       ▼
╔══════════════════════════════════════════════════╗
║  PASS 2: Split-Screen + Audio + Visual           ║
║  → Video: hflip → crop → hue → eq → scale       ║
║    → hstack with reaction → pad → text overlays  ║
║    → rotate sway → noise grain                   ║
║  → Audio: 16-layer nuclear chain                 ║
║  → Output: FINAL.mp4 (exact same duration)       ║
╚══════════════════════════════════════════════════╝
```

### Performance

| Video Length | Pass 1 | Pass 2 | Total | Output Size |
|-------------|--------|--------|-------|-------------|
| 10 min | ~2.5 min | ~3.5 min | ~6 min | ~350 MB |
| 21 min | ~5 min | ~7 min | ~12 min | ~720 MB |
| 40 min | ~10 min | ~14 min | ~24 min | ~1.4 GB |
| 60 min | ~15 min | ~20 min | ~35 min | ~2.1 GB |

---

## Version History

| Ver | Changes | Result |
|-----|---------|--------|
| v1–v5 | Progressive audio/visual additions | ❌ Caught |
| v6 | Fixed 12-hour duration bug, added sway + grain | ❌ Caught |
| v7 | Single-pass engine, Python UI | ❌ Caught |
| **v8** | **Segment swapping + corner zoom** | **✅ No issues (Family Guy)** |
| v8.1 | +Echo +Chorus +Flanger +Tremolo | Audio-only caught on American Dad |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `can't open file 'app.py'` | Run from `video_processor/` folder |
| Fontconfig error | Harmless Windows warning, ignore |
| Build stuck on segments | Normal — 390 segments takes ~5 min |
| Audio sounds too altered | Lower pitch to 2.0–3.0 |
| FFmpeg not found | Put binaries in `ffmpeg_bin/` or run `setup.bat` |
| YouTube catches audio | Try pitch 5.0+ or add more EQ notches |
| YouTube catches video | Increase zoom % in `pro_engine.py` |
| Thumbnail has dark center | Fixed in v1.1 — radial vignette now correct |
| Buttons pushed off-screen | Fixed in v1.1 — scrollable frame preview area |

---

## Quick Reference

```
┌─────────────────────────────────────────────────┐
│  MAIN APP:     python app.py                     │
│  THUMBNAILS:   python thumbnail_maker.py         │
│  SEO:          python seo_generator.py           │
│  ONE-CLICK:    LAUNCH.bat                        │
│                                                  │
│  CLI:          python pro_engine.py              │
│                  --main video.mp4                │
│                  --reactions react.mp4            │
│                  --output output.mp4             │
│                  --title "Best Moments"          │
│                  --pitch 4.0                     │
│                                                  │
│  TIME:         ~12 min for 21 min video          │
│  RULE:         Output = Input duration (EXACTLY) │
│  RESULT:       YouTube "No issues found" ✅      │
└─────────────────────────────────────────────────┘
```

---

*Full Project Documentation — Pro Video Processor + Thumbnail Generator + SEO Generator*
*February 27, 2026*
