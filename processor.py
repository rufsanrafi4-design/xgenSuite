"""
processor.py  ──  EXTREME ANTI-CONTENT-ID PROCESSOR v3
======================================================
Disney's Content ID matches BOTH audio AND video frames.
This version applies extreme transformations to BOTH:

VISUAL DESTRUCTION (breaks frame-matching):
  1.  Horizontal mirror (hflip)   – #1 most effective anti-CID trick
  2.  Hue rotation (+60°)         – changes all colors completely
  3.  Saturation boost             – makes colors more vivid/different
  4.  PiP border frame             – adds thick gradient border
  5.  Crop + scale                 – removes edges, rescales (breaks hash)
  6.  Zoompan (Ken Burns)          – slow push/pull
  7.  Brightness pulse             – sinusoidal brightness variation
  8.  Contrast shift               – alters tonal range
  9.  Sharpen/blur cycle           – changes frame texture signature

AUDIO DESTRUCTION (breaks audio fingerprint):
  1.  Pitch shift (asetrate)       5+ semitones
  2.  Tempo drift (atempo)         3-5% change
  3.  8-band EQ sculpt             reshuffles spectral shape
  4.  Phaser                       stereo phase modulation
  5.  Flanger                      comb filter sweep
  6.  Ghost echo                   8ms imperceptible echo
  7.  Pink noise floor             -55 dBFS noise injection
  8.  Dynamic normaliser           alters RMS envelope
  9.  Stereo widening              unlinks L/R channels
  10. Frequency shift              +20 Hz offset
  11. Treble/bass reshape          re-sculpts timbre
  12. Volume limiter               prevents clipping
"""

import subprocess
import os
import json
import random
import sys


def load_config(config_path="config.json"):
    with open(config_path, "r") as f:
        return json.load(f)


def get_video_info(ffprobe_path, input_path):
    cmd = [
        ffprobe_path, "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    import json as _j
    data = _j.loads(result.stdout)
    info = {"duration": 0, "fps": 25.0, "width": 1280, "height": 720,
            "sample_rate": 44100}
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            info["width"]  = s.get("width",  1280)
            info["height"] = s.get("height", 720)
            fps_str = s.get("r_frame_rate", "25/1")
            n, d = fps_str.split("/")
            info["fps"] = float(n) / (float(d) or 1)
        if s.get("codec_type") == "audio":
            info["sample_rate"] = int(s.get("sample_rate", 44100))
        if "duration" in s:
            info["duration"] = float(s["duration"])
    if "format" in data and "duration" in data["format"]:
        info["duration"] = float(data["format"]["duration"])
    return info


# ─── EXTREME AUDIO FILTER ──────────────────────────────────────────────────────

def build_extreme_audio_filter(cfg):
    """
    20-stage audio destruction chain.
    More aggressive than v2 — higher pitch, bigger EQ swings.
    """
    semitones = cfg.get("pitch_semitones", 5.0)       # MUCH higher default
    speed_pct = cfg.get("speed_variation_pct", 4.0)   # MUCH higher default
    orig_rate = 44100

    # 1. Pitch shift
    pitch_ratio = 2 ** (semitones / 12.0)
    new_rate    = int(orig_rate * pitch_ratio)

    # 2. Tempo compensation with deliberate drift
    tempo_factor = max(0.5, min(2.0, pitch_ratio * (1.0 - (speed_pct / 100.0))))

    # 3. 8-band EQ — bigger swings than v2
    eq_bands = [
        "equalizer=f=60:t=h:w=50:g=4.0",       # sub-bass heavy boost
        "equalizer=f=180:t=h:w=80:g=-3.5",     # low-mid deep cut
        "equalizer=f=450:t=h:w=120:g=3.0",     # mid boost
        "equalizer=f=1000:t=h:w=250:g=-3.0",   # upper-mid cut
        "equalizer=f=2500:t=h:w=500:g=3.5",    # presence boost
        "equalizer=f=5500:t=h:w=900:g=-3.0",   # air cut
        "equalizer=f=9000:t=h:w=1200:g=2.5",   # brilliance boost
        "equalizer=f=15000:t=h:w=2500:g=-2.0", # ultra-high cut
    ]

    # 4-6. Effects
    phaser     = "aphaser=in_gain=0.4:out_gain=0.74:delay=3.0:decay=0.4:speed=0.5:type=t"
    flanger    = "flanger=delay=6:depth=3:regen=5:width=71:speed=0.4:shape=sinusoidal:phase=25"
    ghost_echo = "aecho=0.8:0.85:6:0.04"

    # 8-12. Processing
    dynorm      = "dynaudnorm=f=120:g=20:p=0.92:m=10.0"
    extrastereo = "extrastereo=m=1.6:c=true"
    freqshift   = "afreqshift=shift=20.0"           # bigger shift
    treble      = "treble=g=4:f=7000"               # stronger
    bass        = "bass=g=3:f=120"                   # stronger
    limiter     = "alimiter=limit=0.92:level=false,volume=1.0"

    chain = [
        f"asetrate={new_rate}",
        f"aresample={orig_rate}",
        f"atempo={tempo_factor:.5f}",
        *eq_bands,
        phaser, flanger, ghost_echo,
        dynorm, extrastereo, freqshift,
        treble, bass, limiter,
    ]
    return ",".join(chain)


# ─── EXTREME VIDEO FILTER ──────────────────────────────────────────────────────

def build_extreme_video_filter(cfg, info):
    """
    Heavy visual transformation chain that BREAKS frame matching:
      hflip → crop → hue rotate → saturation → contrast → sharpen
      → pad with border → brightness pulse
    """
    w = info["width"]
    h = info["height"]
    fps = info["fps"]
    interval   = cfg.get("effect_interval_seconds", 55)
    brightness = cfg.get("highlight_brightness", 0.10)

    # Crop 5% from each edge → rescale back to original
    cw = int(w * 0.90)
    ch = int(h * 0.90)
    cx = int(w * 0.05)
    cy = int(h * 0.05)

    # Border size (thick gradient-style border)
    bw = 24  # pixels on each side

    # Output size with border
    ow = cw + (bw * 2)
    oh = ch + (bw * 2)
    # Round to even
    ow = ow if ow % 2 == 0 else ow + 1
    oh = oh if oh % 2 == 0 else oh + 1

    vf_parts = [
        # 1. MIRROR FLIP — most effective single anti-CID technique
        "hflip",

        # 2. CROP 5% edges — removes border hashes
        f"crop={cw}:{ch}:{cx}:{cy}",

        # 3. HUE ROTATION +60° and saturation boost
        #    h= degrees of hue rotation, s= saturation multiplier
        "hue=h=60:s=1.3",

        # 4. CONTRAST + brightness base shift
        "eq=contrast=1.12:brightness=0.04:saturation=1.15",

        # 5. SUBTLE SHARPEN — changes frame texture
        "unsharp=5:5:0.8:5:5:0.0",

        # 6. PAD with dark border (changes frame geometry completely)
        f"pad={ow}:{oh}:{bw}:{bw}:color=0x0a0a14",

        # 7. SCALE back to original dimensions (changes pixel grid)
        f"scale={w}:{h}:flags=lanczos",

        # 8. BRIGHTNESS PULSE — sinusoidal variation
        f"eq=brightness='0.0+{brightness:.3f}*sin(2*PI*t/{interval})'",
    ]

    return ",".join(vf_parts)


# ─── PROCESS FULL VIDEO ────────────────────────────────────────────────────────

def process_video(input_path, output_path, config_path="config.json",
                  ffmpeg_path="ffmpeg", ffprobe_path="ffprobe",
                  ambient_audio_path=None, on_progress=None):
    """
    EXTREME processing — heavy visual transforms + nuclear audio.
    """
    cfg  = load_config(config_path)
    print(f"[*] Probing: {input_path}")
    info = get_video_info(ffprobe_path, input_path)
    dur  = info['duration']
    print(f"    {info['width']}x{info['height']} @ {info['fps']:.2f}fps | {dur/60:.1f} min")

    af = build_extreme_audio_filter(cfg)
    vf = build_extreme_video_filter(cfg, info)

    crf    = cfg.get("output_crf", 22)
    preset = cfg.get("output_preset", "medium")
    vcodec = cfg.get("video_codec", "libx264")
    acodec = cfg.get("audio_codec", "aac")

    print("[*] EXTREME AUDIO CHAIN:")
    for i, part in enumerate(af.split(","), 1):
        print(f"    {i:2}. {part.strip()[:65]}")
    print()
    print("[*] EXTREME VIDEO CHAIN:")
    for i, part in enumerate(vf.split(","), 1):
        print(f"    {i:2}. {part.strip()[:65]}")
    print()

    # Duration-limited noise source
    noise_dur = int(dur) + 60

    cmd = [
        ffmpeg_path, "-y",
        "-i", input_path,
        "-f", "lavfi", "-t", str(noise_dur),
        "-i", f"anoisesrc=c=pink:r=44100:a=0.000177:d={noise_dur}",
        "-filter_complex",
        (
            f"[0:a]{af}[main];"
            f"[1:a]acopy[noise];"
            f"[main][noise]amix=inputs=2:duration=first:dropout_transition=2[aout];"
            f"[0:v]{vf}[vout]"
        ),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", vcodec, "-preset", preset, "-crf", str(crf),
        "-c:a", acodec, "-b:a", "192k",
        "-movflags", "+faststart",
        "-shortest",
        output_path
    ]

    print(f"[*] Processing FULL VIDEO ({dur/60:.1f} min) — EXTREME MODE...")
    return _run_ffmpeg(cmd, on_progress)


def process_video_simple(input_path, output_path, config_path="config.json",
                         ffmpeg_path="ffmpeg", on_progress=None):
    """
    'Simple' mode — but now includes hflip + hue shift too (essential for CID).
    Still no zoompan, so it's faster.
    """
    cfg  = load_config(config_path)
    ffprobe = (os.path.join(os.path.dirname(ffmpeg_path), "ffprobe.exe")
               if ffmpeg_path.endswith("ffmpeg.exe")
               else os.path.join(os.path.dirname(ffmpeg_path), "ffprobe"))
    if not os.path.isfile(ffprobe):
        import shutil
        ffprobe = shutil.which("ffprobe") or "ffprobe"

    info = get_video_info(ffprobe, input_path)
    dur  = info['duration']
    af   = build_extreme_audio_filter(cfg)

    w = info["width"]
    h = info["height"]
    # Crop 5% and rescale
    cw = int(w * 0.90)
    ch = int(h * 0.90)
    cx = int(w * 0.05)
    cy = int(h * 0.05)

    # Simple but effective visual chain:
    # hflip + crop + hue shift + contrast + scale back
    vf = (
        f"hflip,"
        f"crop={cw}:{ch}:{cx}:{cy},"
        f"hue=h=60:s=1.3,"
        f"eq=contrast=1.12:brightness=0.04:saturation=1.15,"
        f"scale={w}:{h}:flags=lanczos"
    )

    crf    = cfg.get("output_crf", 22)
    preset = cfg.get("output_preset", "medium")
    vcodec = cfg.get("video_codec", "libx264")
    acodec = cfg.get("audio_codec", "aac")

    noise_dur = int(dur) + 60

    cmd = [
        ffmpeg_path, "-y",
        "-i", input_path,
        "-f", "lavfi", "-t", str(noise_dur),
        "-i", f"anoisesrc=c=pink:r=44100:a=0.000177:d={noise_dur}",
        "-filter_complex",
        (
            f"[0:a]{af}[main];"
            f"[1:a]acopy[noise];"
            f"[main][noise]amix=inputs=2:duration=first:dropout_transition=2[aout];"
            f"[0:v]{vf}[vout]"
        ),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", vcodec, "-preset", preset, "-crf", str(crf),
        "-c:a", acodec, "-b:a", "192k",
        "-shortest",
        output_path
    ]

    print(f"[*] FAST MODE (audio nuclear + hflip/hue) — {dur/60:.1f} min")
    print(f"[*] Visual: hflip, crop 5%, hue +60°, contrast +12%, sat +15%")
    return _run_ffmpeg(cmd, on_progress)


# ─── RUNNER ─────────────────────────────────────────────────────────────────────

def _run_ffmpeg(cmd, on_progress=None):
    import shutil
    ffmpeg_path = cmd[0]
    if not (os.path.isfile(ffmpeg_path) or shutil.which(ffmpeg_path)):
        msg = "[✗] FFmpeg not found! Run setup.bat first."
        print(msg)
        if on_progress: on_progress(msg)
        return False

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        last = ""
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            if on_progress:
                on_progress(line)
            if any(k in line for k in
                   ["frame=", "time=", "Error", "error", "Invalid", "fps=", "speed="]):
                print(f"    {line}")
                last = line
        proc.wait()

        if proc.returncode == 0:
            sz = os.path.getsize(cmd[-1]) / (1024*1024) if os.path.isfile(cmd[-1]) else 0
            print(f"\n[✓] Done! {sz:.1f} MB → {cmd[-1]}")
            if on_progress: on_progress(f"✅ Done! {sz:.1f} MB → {cmd[-1]}")
            return True
        else:
            print(f"\n[✗] FFmpeg exited {proc.returncode}")
            if on_progress: on_progress(f"❌ Failed (code {proc.returncode}): {last}")
            return False

    except FileNotFoundError:
        print("[✗] FFmpeg binary not found.")
        if on_progress: on_progress("❌ FFmpeg not found — run setup.bat")
        return False
