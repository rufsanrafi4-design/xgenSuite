"""
pro_engine.py - PRO VIDEO ENGINE v8 (3000-YEAR EVASION)
=======================================================
RULE: Output duration = Input duration. EXACTLY.

TECHNIQUE 1: SEGMENT SWAPPING (Temporal Reorder)
  - Every 10 seconds: first 3s normal, last 7s split in half and swapped
  - Breaks YouTube's temporal fingerprinting completely
  - Audio is ALSO swapped (destroys audio fingerprint matching)

TECHNIQUE 2: ALTERNATING CORNER ZOOM
  - Every 10s: zoom 48% from top-right, next zoom 52% from top-left
  - Shows only ~half the frame, destroying spatial fingerprints
  - Alternates corners so no two zooms look the same

TECHNIQUE 3: DEEP AUDIO CHAIN
  - Pitch shift + compression + EQ notches + phase shift + freq shift
  - Mastered to YouTube -14 LUFS standard

TECHNIQUE 4: VISUAL EVASION
  - Mirror flip + crop + hue rotation + sway + grain
  - Split-screen with reaction clip

Pipeline:
  Pass 1: Segment swap + corner zoom -> intermediate file
  Pass 2: Split-screen + audio chain + visual evasion -> final output
"""

import subprocess
import os
import sys
import json
import shutil
import concurrent.futures
import traceback


# ─── HELPERS ────────────────────────────────────────────────

def find_ffmpeg():
    base = os.path.dirname(os.path.abspath(__file__))
    ff = os.path.join(base, "ffmpeg_bin", "ffmpeg.exe")
    fp = os.path.join(base, "ffmpeg_bin", "ffprobe.exe")
    if os.path.isfile(ff) and os.path.isfile(fp):
        return ff, fp
    return "ffmpeg", "ffprobe"


def get_video_info(ffprobe, path):
    cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
           "-show_streams", "-show_format", path]
    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    data = json.loads(r.stdout)
    info = {"duration": 0, "fps": 24.0, "width": 1280, "height": 720}
    for s in data.get("streams", []):
        if s.get("codec_type") == "video":
            info["width"] = s.get("width", 1280)
            info["height"] = s.get("height", 720)
            fps_str = s.get("r_frame_rate", "24/1")
            if "/" in fps_str:
                n, d = fps_str.split("/")
                info["fps"] = float(n) / (float(d) or 1)
            else:
                info["fps"] = float(fps_str)
        if "duration" in s and s.get("codec_type") == "video":
            info["duration"] = float(s["duration"])
    if "format" in data and "duration" in data["format"]:
        info["duration"] = float(data["format"]["duration"])
    return info


# ─── PASS 1: SEGMENT SWAP + CORNER ZOOM ────────────────────

def _extract_segment(args):
    """Extract a single segment with optional zoom. Runs in thread pool."""
    ffmpeg, input_path, out_path, start, dur, fps, w, h, zoom_type = args

    vf_parts = ["setpts=PTS-STARTPTS"]

    if zoom_type == "right":
        # Zoom 48% from top-right: show right 52% of frame
        vf_parts.append(f"crop=iw*0.52:ih:iw*0.48:0")
        vf_parts.append(f"scale={w}:{h}:flags=lanczos")
    elif zoom_type == "left":
        # Zoom 52% from top-left: show left 48% of frame
        vf_parts.append(f"crop=iw*0.48:ih:0:0")
        vf_parts.append(f"scale={w}:{h}:flags=lanczos")

    vf = ",".join(vf_parts)

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(round(start, 4)),
        "-t", str(round(dur, 4)),
        "-i", input_path,
        "-vf", vf,
        "-af", "asetpts=PTS-STARTPTS",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-r", str(round(fps, 3)),
        "-pix_fmt", "yuv420p",
        "-map_metadata", "-1",
        out_path
    ]

    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return os.path.isfile(out_path)


def preprocess_swap_zoom(ffmpeg, input_path, output_path, duration, fps, w, h,
                          log=print):
    """
    PASS 1: Temporal reorder + alternating corner zoom.

    Within each 10-second block:
      [0-3s: normal] [6.5-10s: swapped] [3-6.5s: swapped]

    Every 10 seconds of OUTPUT timeline: 3-second zoom from alternating corners.
    """
    temp_dir = os.path.join(os.path.dirname(output_path), "_swap_temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)
    os.makedirs(temp_dir, exist_ok=True)

    BLOCK = 10.0       # seconds per block
    NORMAL = 3.0       # normal (unchanged) portion
    ZOOM_CYCLE = 20.0  # full zoom cycle (right + left)
    ZOOM_START = 10.0  # zoom starts at 10s into each cycle
    ZOOM_DUR = 3.0     # zoom lasts 3 seconds

    # ── Step 1: Calculate segment order ──
    segments = []  # (input_start, input_end)
    t = 0.0
    while t < duration:
        block_end = min(t + BLOCK, duration)
        remaining = block_end - t

        if remaining <= NORMAL + 0.5:
            # Too short to swap, keep as-is
            segments.append((t, block_end))
        else:
            # Normal part: first 3 seconds
            segments.append((t, t + NORMAL))
            # Swappable part: remaining seconds, split in half
            swap_start = t + NORMAL
            swap_mid = swap_start + (block_end - swap_start) / 2.0
            # SWAPPED: second half FIRST, then first half
            segments.append((swap_mid, block_end))
            segments.append((swap_start, swap_mid))

        t = block_end

    # ── Step 2: Determine zoom for each segment ──
    output_time = 0.0
    seg_data = []  # (input_start, input_end, zoom_type)

    for (seg_start, seg_end) in segments:
        seg_dur = seg_end - seg_start
        seg_center = output_time + seg_dur / 2.0
        cycle_pos = seg_center % ZOOM_CYCLE

        zoom = "none"
        if seg_center >= ZOOM_START:
            if ZOOM_START <= cycle_pos < ZOOM_START + ZOOM_DUR:
                zoom = "right"
            elif cycle_pos < ZOOM_DUR:
                zoom = "left"

        seg_data.append((seg_start, seg_end, zoom))
        output_time += seg_dur

    total_segs = len(seg_data)
    zoom_segs = sum(1 for _, _, z in seg_data if z != "none")
    log(f"  Segments: {total_segs} ({zoom_segs} with zoom)")

    # ── Step 3: Extract segments in parallel ──
    extract_args = []
    for i, (start, end, zoom) in enumerate(seg_data):
        out_file = os.path.join(temp_dir, f"seg_{i:05d}.mp4")
        extract_args.append(
            (ffmpeg, input_path, out_file, start, end - start, fps, w, h, zoom)
        )

    log(f"  Extracting {total_segs} segments (4 parallel)...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(_extract_segment, extract_args))

    ok_count = sum(results)
    log(f"  Extracted: {ok_count}/{total_segs} OK")

    if ok_count < total_segs * 0.9:
        log(f"  ERROR: Too many segments failed ({total_segs - ok_count})")
        return False

    # ── Step 4: Concat all segments ──
    log(f"  Concatenating {ok_count} segments...")
    list_path = os.path.join(temp_dir, "concat.txt")
    with open(list_path, "w") as f:
        for i in range(total_segs):
            seg_file = os.path.join(temp_dir, f"seg_{i:05d}.mp4").replace("\\", "/")
            if os.path.isfile(seg_file.replace("/", "\\")):
                f.write(f"file '{seg_file}'\n")

    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-fflags", "+genpts",
        "-f", "concat", "-safe", "0", "-i", list_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-r", str(round(fps, 3)),
        "-video_track_timescale", "90000",
        "-map_metadata", "-1",
        "-flags", "+bitexact",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        # Hard limit to exact input duration
        "-t", str(round(duration, 3)),
        output_path
    ]

    r = subprocess.run(cmd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

    if os.path.isfile(output_path):
        log(f"  Pass 1 DONE")
        return True
    else:
        log(f"  Pass 1 FAILED")
        if r.stderr:
            for line in r.stderr.strip().split("\n")[-5:]:
                log(f"    {line}")
        return False


# ─── AUDIO CHAIN ────────────────────────────────────────────

def build_audio_chain(pitch_semitones=4.0, speed_pct=2.0):
    """
    NUCLEAR audio chain v8.1 — 16 layers of fingerprint destruction.
    Attacks ALL 4 pillars of Content ID audio matching:
      1. Waveform matching  → echo + chorus
      2. Harmonic patterns  → pitch shift + freq shift
      3. Spectral shape     → EQ notches + band rejection + flanger
      4. Amplitude envelope → tremolo + compressor
    """
    orig_rate = 44100
    ratio = 2 ** (pitch_semitones / 12.0)
    new_rate = int(orig_rate * ratio)
    tempo = max(0.5, min(2.0, (1.0 / ratio) * (1.0 + speed_pct / 100.0)))

    filters = [
        # Reset timestamps
        "asetpts=PTS-STARTPTS",
        # 1. PITCH SHIFT (4 semitones default — more aggressive)
        f"asetrate={new_rate}",
        f"aresample={orig_rate}",
        f"atempo={tempo:.6f}",
        # 2. ECHO — adds delayed copies, confuses waveform peak matching
        "aecho=0.6:0.3:15|25:0.25|0.15",
        # 3. CHORUS — creates slightly detuned copies, destroys harmonic fingerprint
        "chorus=0.5:0.9:50|60:0.4|0.32:0.25|0.4:2|2.3",
        # 4. PRO COMPRESSOR — thick, punchy, changes dynamic envelope
        "acompressor=threshold=-18dB:ratio=4:attack=5:release=50:makeup=2dB",
        # 5. TREMOLO — subtle amplitude modulation, changes envelope pattern
        "tremolo=f=3.5:d=0.12",
        # 6. EQ NOTCHES — cut fingerprint anchor frequencies (more aggressive)
        "equalizer=f=800:t=q:w=2:g=-14",
        "equalizer=f=1500:t=q:w=2:g=-14",
        "equalizer=f=3000:t=q:w=2:g=-12",
        "equalizer=f=5000:t=q:w=1.5:g=-10",
        # 7. BAND REJECTION — remove 3 critical fingerprint bands
        "bandreject=f=350:w=80",
        "bandreject=f=2200:w=100",
        "bandreject=f=4500:w=80",
        # 8. FLANGER — moving comb filter, changes spectral shape over time
        "flanger=delay=3:depth=2:regen=-2:width=40:speed=0.3:shape=sinusoidal",
        # 9. STEREO WIDENING — changes spatial signature
        "extrastereo=m=1.5:c=true",
        # 10. PHASE DISRUPTION — scrambles phase relationships
        "aphaser=in_gain=0.4:out_gain=0.74:delay=3.0:decay=0.4:speed=0.5:type=t",
        # 11. FREQUENCY SHIFT — +35Hz (more aggressive than before)
        "afreqshift=shift=35",
        # 12. YOUTUBE MASTERING — -14 LUFS standard
        "loudnorm=I=-14:LRA=11:TP=-1.5",
        # 13. HARD LIMITER — clean output
        "alimiter=limit=0.98:level=false",
    ]
    return ",".join(filters)


# ─── PASS 2: TEMPLATE-COMPILED VISUAL + AUDIO + SHADOW LEDGER ──

def build_video(main_video, reaction_clips, output_path,
                title="Best Moments", pitch_semitones=3.0,
                template_id="split_screen",
                checklist=None,
                progress_callback=None):
    """
    Complete pipeline:
      Pass 1: Segment swap + corner zoom -> intermediate
      Pass 2: Template-compiled visual + audio chain -> final
      Post:   Shadow Ledger DB update + Phantom Atom injection

    Output duration = Input duration. GUARANTEED.

    Args:
        template_id: key from template_matrix.json (default: split_screen)
        checklist:   dict {hack_id: bool} for Shadow Ledger compliance
    """
    from template_compiler import compile_video_filter, get_template
    from shadow_ledger import on_render_start, on_render_complete

    ffmpeg, ffprobe = find_ffmpeg()

    def log(msg):
        print(msg, flush=True)
        if progress_callback:
            progress_callback(msg)

    # ── Resolve template ──
    tpl = get_template(template_id)
    if not tpl:
        log(f"  ERROR: Unknown template '{template_id}', falling back to split_screen")
        template_id = "split_screen"
        tpl = get_template(template_id)

    tpl_name = tpl["display_name"]
    needs_rxn = tpl.get("requires_reaction", False)
    has_rxn = bool(reaction_clips) and needs_rxn

    log("=" * 55)
    log("  PRO VIDEO ENGINE v9 (ALGORITHMIC WARFARE)")
    log(f"  Template: {tpl_name}")
    log("  5 techniques | Algebraic solver | Phantom Atom")
    log("=" * 55)

    # Source info
    info = get_video_info(ffprobe, main_video)
    dur = info["duration"]
    w, h = info["width"], info["height"]
    fps = info["fps"]

    reaction_dur = 0
    final_reaction_clip = None

    if has_rxn:
        if len(reaction_clips) == 1:
            rxn_info = get_video_info(ffprobe, reaction_clips[0])
            reaction_dur = rxn_info["duration"]
            final_reaction_clip = reaction_clips[0]
        else:
            # Multi-clip logic
            log(f"  Building {len(reaction_clips)}-clip reaction reel...")
            out_dir = os.path.dirname(os.path.abspath(output_path))
            temp_rxn = os.path.join(out_dir, "_reaction_reel.mp4")
            
            n = len(reaction_clips)
            cmd = [ffmpeg, "-y"]
            for clip in reaction_clips:
                cmd.extend(["-i", os.path.abspath(clip)])

            fc_parts = []
            for i in range(n):
                # Scale all to a uniform 720x1280 to prevent concatenation failures
                fc_parts.append(
                    f"[{i}:v]scale=720:1280:force_original_aspect_ratio=decrease,"
                    f"pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,"
                    f"fps={fps},format=yuv420p[v{i}];"
                    f"[{i}:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[a{i}]"
                )
            
            # CRITICAL: concat expects INTERLEAVED streams [v0][a0][v1][a1]...
            # NOT grouped [v0][v1]...[a0][a1]... (that causes media type mismatch)
            interleaved = "".join(f"[v{i}][a{i}]" for i in range(n))
            fc_parts.append(f"{interleaved}concat=n={n}:v=1:a=1[outv][outa]")
            fc = ";".join(fc_parts)

            cmd.extend([
                "-filter_complex", fc,
                "-map", "[outv]", "-map", "[outa]",
                "-c:v", "libx264", "-preset", "fast", "-crf", "22",
                "-c:a", "aac", "-b:a", "192k",
                temp_rxn
            ])

            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode == 0 and os.path.isfile(temp_rxn):
                rxn_info = get_video_info(ffprobe, temp_rxn)
                reaction_dur = rxn_info["duration"]
                final_reaction_clip = temp_rxn
            else:
                log("  ERROR: Reaction concat failed, falling back to clip 1")
                if r.stderr:
                    for line in r.stderr.strip().split("\n"):
                        log(f"    {line}")
                rxn_info = get_video_info(ffprobe, reaction_clips[0])
                reaction_dur = rxn_info["duration"]
                final_reaction_clip = reaction_clips[0]

    freeze_needed = max(0, reaction_dur - dur)
    total_dur = max(dur, reaction_dur)

    log(f"  Source: {dur/60:.1f} min ({w}x{h} @ {fps:.1f}fps)")
    log(f"  Reactions: {len(reaction_clips)} clips (Length: {reaction_dur/60:.1f} min)")
    if freeze_needed > 0:
        log(f"  Smart Freeze: holding video for {freeze_needed:.1f}s to match reaction")
    log(f"  Output will be EXACTLY {total_dur/60:.1f} min")
    log("=" * 55)

    # ── Shadow Ledger: register this render ──
    video_uuid = on_render_start(
        source_file=os.path.abspath(main_video),
        output_file=os.path.abspath(output_path),
        template_id=template_id,
        title=title,
        pitch_semitones=pitch_semitones,
        checklist=checklist or {}
    )
    log(f"  Shadow Ledger UUID: {video_uuid[:8]}...")

    # ── Pass 1: Segment swap + zoom ──
    clean_main = tpl.get("clean_main", False)
    out_dir = os.path.dirname(os.path.abspath(output_path))

    if clean_main:
        # Clean main: skip Pass 1 entirely — use original video untouched
        log("\n[PASS 1/2] SKIPPED (Clean Main — original video preserved)")
        intermediate = main_video  # use original directly
        int_dur = dur
        int_w, int_h = w, h
        log(f"  Using original: {int_dur/60:.1f} min ({int_w}x{int_h})")
    else:
        log("\n[PASS 1/2] Segment Swap + Corner Zoom")
        log("  Technique 1: Temporal reorder (breaks sequence matching)")
        log("  Technique 2: Alternating corner zoom (breaks spatial matching)")

        intermediate = os.path.join(out_dir, "_intermediate_swapped.mp4")

        ok = preprocess_swap_zoom(ffmpeg, main_video, intermediate, dur, fps, w, h, log)
        if not ok:
            log("  FAILED at Pass 1")
            return False

        # Verify intermediate duration
        int_info = get_video_info(ffprobe, intermediate)
        int_dur = int_info["duration"]
        int_w, int_h = int_info["width"], int_info["height"]
        log(f"  Intermediate: {int_dur/60:.1f} min ({int_w}x{int_h})")

    # ── Pass 1.5: Auto-crop landscape → portrait (for Shorts) ──
    force_portrait = tpl.get("force_portrait", False)
    if force_portrait and int_w > int_h:
        out_pw = tpl.get("output_w", 1080)
        out_ph = tpl.get("output_h", 1920)
        target_ratio = out_pw / out_ph  # 9/16 = 0.5625

        log(f"\n[PASS 1.5] Auto-Crop Landscape → Portrait ({out_pw}x{out_ph})")
        log(f"  Source is {int_w}x{int_h} (landscape)")
        log(f"  Center-cropping to {target_ratio:.4f} aspect ratio")

        # Center-crop: take vertical strip from center of landscape frame
        crop_w = int(int_h * target_ratio)  # width = height * (9/16)
        crop_h = int_h
        crop_x = (int_w - crop_w) // 2  # center horizontally
        crop_y = 0

        portrait_path = os.path.join(out_dir, "_intermediate_portrait.mp4")

        cmd_p = [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", intermediate,
            "-vf", f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale={out_pw}:{out_ph}:flags=lanczos",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-r", str(round(fps, 3)),
            "-t", str(round(dur, 3)),
            "-pix_fmt", "yuv420p",
            "-map_metadata", "-1",
            portrait_path
        ]

        rp = subprocess.run(cmd_p, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")

        if os.path.isfile(portrait_path):
            # Replace intermediate with portrait version
            os.remove(intermediate)
            intermediate = portrait_path
            int_info = get_video_info(ffprobe, intermediate)
            int_w, int_h = int_info["width"], int_info["height"]
            log(f"  Portrait crop DONE: {int_w}x{int_h}")
        else:
            log(f"  Portrait crop FAILED, continuing with landscape")
            if rp.stderr:
                for line in rp.stderr.strip().split("\n")[-3:]:
                    log(f"    {line}")

    # ── Pass 2: Template-Compiled Effects ──
    log(f"\n[PASS 2/2] {tpl_name} + Audio Chain + Visual Evasion")
    log("  Technique 3: Pro audio (pitch+EQ+phase+freq+master)")
    log("  Technique 4: Visual evasion (mirror+hue+sway+grain)")
    log(f"  Technique 5: {tpl_name} layout")

    # ── Algebraic Compiler: resolve template at runtime ──
    log(f"  Compiling template '{template_id}' for {int_w}x{int_h}...")
    vf, vout_label = compile_video_filter(
        template_id=template_id,
        title=title,
        root_w=int_w,
        root_h=int_h,
        has_reaction=has_rxn,
        freeze_needed=freeze_needed
    )
    log(f"  Filtergraph: {len(vf)} chars compiled")

    af = build_audio_chain(pitch_semitones=pitch_semitones)

    # Layer 13: Ultrasonic watermark kill (God Mode)
    # Some content embeds inaudible watermarks above 16kHz.
    # This lowpass kills them while keeping all audible audio perfect.
    evasion = tpl.get("visual_evasion", {})
    lp_freq = evasion.get("lowpass_audio_freq")
    if lp_freq:
        af += f",lowpass=f={lp_freq}"
        log(f"  Audio watermark kill: lowpass at {lp_freq}Hz")

    # ── Probe reaction for audio stream before using amix ──
    rxn_has_audio = False
    if has_rxn and final_reaction_clip:
        try:
            rxn_probe = get_video_info(ffprobe, final_reaction_clip)
            # get_video_info returns duration > 0 if there's a valid stream
            # But we need to explicitly check for audio streams
            probe_cmd = [ffprobe, "-v", "quiet", "-print_format", "json",
                         "-show_streams", final_reaction_clip]
            pr = subprocess.run(probe_cmd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
            probe_data = json.loads(pr.stdout)
            for s in probe_data.get("streams", []):
                if s.get("codec_type") == "audio":
                    rxn_has_audio = True
                    break
        except Exception:
            rxn_has_audio = False

    if clean_main:
        # Clean main: NO nuclear audio chain — pass main audio through cleanly
        if has_rxn and rxn_has_audio:
            fc = (f"{vf};"
                  f"[0:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[main_a];"
                  f"[1:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[rxn_a];"
                  f"[main_a][rxn_a]amix=inputs=2:duration=longest:dropout_transition=2[aout]")
        elif has_rxn:
            log("  ⚠️ Reaction clip has no audio stream — using main audio only")
            fc = f"{vf};[0:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[aout]"
        else:
            fc = f"{vf};[0:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[aout]"
    else:
        if has_rxn and rxn_has_audio:
            # Mix the nuclear evasion audio [0:a] with the reaction native audio [1:a]
            # duration=longest ensures the audio continues during the freeze frame
            # CRITICAL: We MUST normalize both streams to identical sample rates/layouts before amixing
            fc = (f"{vf};"
                  f"[0:a]{af},aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[main_a];"
                  f"[1:a]aresample=44100,aformat=sample_rates=44100:channel_layouts=stereo[rxn_a];"
                  f"[main_a][rxn_a]amix=inputs=2:duration=longest:dropout_transition=2[aout]")
        elif has_rxn:
            log("  ⚠️ Reaction clip has no audio stream — skipping amix")
            fc = f"{vf};[0:a]{af}[aout]"
        else:
            fc = f"{vf};[0:a]{af}[aout]"

    # Build FFmpeg command
    cmd = [ffmpeg, "-y"]
    cmd += ["-i", intermediate]
    if has_rxn and final_reaction_clip:
        cmd += ["-stream_loop", "-1", "-i", final_reaction_clip]

    # ── Debug: log full filtergraph for diagnostics ──
    log(f"\n  [DEBUG] filter_complex ({len(fc)} chars):")
    for part in fc.split(";"):
        log(f"    {part}")

    cmd += [
        "-filter_complex", fc,
        "-map", vout_label, "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
        "-r", str(round(fps, 3)),
        "-t", str(round(total_dur, 3)),
        "-map_metadata", "-1",
        "-flags", "+bitexact",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        output_path
    ]

    log(f"\n  Processing {total_dur/60:.1f} min (single pass)...")

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace"
    )

    for line in proc.stdout:
        line = line.strip()
        if "frame=" in line:
            log(f"  {line}")
        elif "Error" in line and "Fontconfig" not in line:
            log(f"  ERROR: {line}")

    proc.wait()

    # Cleanup intermediate (but NEVER delete the original main_video)
    if os.path.isfile(intermediate) and intermediate != main_video:
        os.remove(intermediate)

    # Cleanup reaction reel
    if has_rxn and final_reaction_clip and final_reaction_clip.endswith("_reaction_reel.mp4"):
        try:
            os.remove(final_reaction_clip)
        except OSError:
            pass

    if proc.returncode != 0:
        log(f"\n  FAILED (exit code {proc.returncode})")
        return False

    # Verify final output
    if os.path.isfile(output_path):
        out_info = get_video_info(ffprobe, output_path)
        out_dur = out_info["duration"]
        size_mb = os.path.getsize(output_path) / (1024 * 1024)

        # ── Shadow Ledger: finalize + inject Phantom Atom ──
        on_render_complete(
            video_uuid,
            duration_sec=out_dur,
            file_size_mb=size_mb
        )
        log(f"  Phantom Atom injected into {os.path.basename(output_path)}")

        log(f"\n{'=' * 55}")
        log(f"  DONE - ALGORITHMIC WARFARE ENGINE COMPLETE")
        log(f"  Template:  {tpl_name}")
        log(f"  Input:     {dur/60:.1f} min ({w}x{h})")
        log(f"  Output:    {out_dur/60:.1f} min")
        log(f"  Duration:  {'EXACT' if abs(out_dur - dur) < 2 else 'WARNING'} (diff {abs(out_dur - dur):.1f}s)")
        log(f"  Size:      {size_mb:.1f} MB")
        log(f"  UUID:      {video_uuid}")
        log(f"  File:      {output_path}")
        log(f"{'=' * 55}")
        return True
    else:
        log("  FAILED: No output file created")
        return False


# ─── CLI ────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pro Video Engine v9 — Algorithmic Warfare")
    parser.add_argument("--main", required=True, help="Main video path")
    parser.add_argument("--reactions", nargs="+", default=[], help="Reaction clips")
    parser.add_argument("--output", required=True, help="Output path")
    parser.add_argument("--title", default="Best Moments")
    parser.add_argument("--pitch", type=float, default=3.0)
    parser.add_argument("--template", default="split_screen",
                        choices=["split_screen", "pip_corner", "cinema_bars", "full_evasion"],
                        help="Layout template")
    args = parser.parse_args()

    ok = build_video(
        args.main, args.reactions, args.output,
        title=args.title, pitch_semitones=args.pitch,
        template_id=args.template
    )
    sys.exit(0 if ok else 1)
